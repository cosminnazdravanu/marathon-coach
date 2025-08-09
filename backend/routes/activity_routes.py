# backend/routes/activity_routes.py

from fastapi import Request, APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import os
import httpx
import secrets
from collections import defaultdict
from datetime import datetime

from backend.deps.auth import get_current_user
from backend.services.token_manager import get_access_token, save_tokens, delete_tokens
from backend.services.identity_manager import link_strava_identity, unlink_strava_identity
from backend.utils.utils import (
    safe_str, safe_round, safe_int, safe_int_scaled,
    format_date, format_duration, format_pace
)
from backend.utils.hr_plot import save_hr_plot_plotly
from backend.services.gpt_helper import call_chat_completion

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

# --- CSRF helper (matches your /auth/* approach) ---
def require_csrf(request: Request):
    sess = request.session.get("csrf")
    hdr = request.headers.get("X-CSRF-Token")
    if not sess or not hdr or hdr != sess:
        raise HTTPException(status_code=403, detail="CSRF check failed")

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    """
    Public home. If logged in, try to show Strava info for the *local* user.
    """
    local_user_id = request.session.get("user_id")  # local user id from session-auth

    valid_token = False
    athlete = None
    activities_list = []

    if local_user_id:
        # Always key by our local user id (cast to str if your token manager stores strings)
        access_token = get_access_token(str(local_user_id))
        if access_token:
            valid_token = True
            headers = {"Authorization": f"Bearer {access_token}"}
            try:
                r = httpx.get("https://www.strava.com/api/v3/athlete", headers=headers, timeout=10.0)
                if r.status_code == 200:
                    athlete = r.json()
            except httpx.HTTPError:
                pass

            # If your helper expects the same key as token storage, pass local id
            from backend.services.strava_api import get_last_20_activities
            activities_list = get_last_20_activities(str(local_user_id))

    return templates.TemplateResponse("index.html", {
        "request": request,
        "valid_token": valid_token,
        "athlete": athlete,
        "activities_list": activities_list
    })

@router.get("/connect_strava")
def connect_strava(request: Request, current_user = Depends(get_current_user)):
    """
    Start OAuth for the currently logged-in local user.
    """
    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state
    return RedirectResponse(
        url=(
            "https://www.strava.com/oauth/authorize"
            f"?client_id={os.getenv('STRAVA_CLIENT_ID')}"
            f"&response_type=code"
            f"&redirect_uri={os.getenv('STRAVA_REDIRECT_URI')}"
            f"&approval_prompt=auto&scope=activity:read"
            f"&state={state}"
        )
    )

@router.get("/strava_callback")
def strava_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    current_user = Depends(get_current_user),
):
    """
    Finish OAuth: store Strava tokens for the logged-in local user and persist the identity link.
    """
    if not code:
        return HTMLResponse("Authorization failed", status_code=400)

    saved = request.session.get("oauth_state")
    if not state or not saved or state != saved:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")
    request.session.pop("oauth_state", None)  # one-time use

    token_url = "https://www.strava.com/api/v3/oauth/token"
    payload = {
        "client_id": os.getenv("STRAVA_CLIENT_ID"),
        "client_secret": os.getenv("STRAVA_CLIENT_SECRET"),
        "code": code,
        "grant_type": "authorization_code",
    }
    try:
        r = httpx.post(token_url, data=payload, timeout=20.0)
        r.raise_for_status()
    except httpx.HTTPError as e:
        return HTMLResponse(f"Token exchange failed: {e}", status_code=400)

    tokens = r.json()

    # 🔑 Save tokens under *local* user id
    save_tokens(str(current_user.id), tokens)

    # 🔗 Persist the identity link (provider='strava', provider_user_id=<athlete.id>)
    try:
        link_strava_identity(current_user.id, tokens)
    except Exception as e:
        # Non-fatal; log for now
        print(f"⚠️ identity link warning: {e}")

    return RedirectResponse(url="/activity_feedback")

@router.post("/disconnect_strava")
def disconnect_strava(request: Request, current_user = Depends(get_current_user)):
    """
    Disconnect Strava for the logged-in user WITHOUT logging them out of your app.
    """
    require_csrf(request)  # enable CSRF on state-changing POSTs
    # 🧹 Remove only Strava tokens/link; keep the session
    delete_tokens(str(current_user.id))
    try:
        unlink_strava_identity(current_user.id)
    except Exception as e:
        print(f"⚠️ unlink warning: {e}")
    return RedirectResponse(url="/", status_code=303)

@router.get("/activity_feedback", response_class=HTMLResponse)
async def activity_feedback(request: Request, activity_id: str | None = None, current_user = Depends(get_current_user)):
    """
    Requires login + a connected Strava account.
    """
    local_user_id = str(current_user.id)
    access_token = get_access_token(local_user_id)
    if not access_token:
        return RedirectResponse("/connect_strava")

    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1) Latest activity if none specified
        if not activity_id:
            r = await client.get("https://www.strava.com/api/v3/athlete/activities", headers=headers)
            r.raise_for_status()
            activities = r.json()
            if not activities:
                return HTMLResponse("No activities found", status_code=200)
            latest_activity = activities[0]
            activity_id = latest_activity["id"]

        # 2) Detailed activity
        activity_url = f"https://www.strava.com/api/v3/activities/{activity_id}"
        r = await client.get(activity_url, headers=headers)
        r.raise_for_status()
        activity = r.json()

        # Basic fields
        name = safe_str(activity.get("name"), "Unnamed Activity")
        start_time = format_date(activity.get("start_date_local"))
        distance_km = safe_round(activity.get("distance"), divisor=1000)
        elapsed = format_duration(activity.get("elapsed_time"), "long")
        moving = format_duration(activity.get("moving_time"), "long")
        avg_hr = safe_int(activity.get("average_heartrate"))
        max_hr = safe_int(activity.get("max_heartrate"))
        elev = safe_int(activity.get("total_elevation_gain"))
        calories = safe_int(activity.get("calories"))
        temp = safe_str(activity.get("average_temp"))
        cadence = safe_int(safe_round(activity.get("average_cadence"), multiplier=2, decimals=0))
        splits = activity.get("splits_metric", [])

        # 3) HR Stream
        stream_url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams"
        params = {"keys": "heartrate,distance", "key_by_type": True}
        r = await client.get(stream_url, headers=headers, params=params)
        r.raise_for_status()
        streams = r.json()
        hr_data = streams.get("heartrate", {}).get("data", [])
        dist_data = streams.get("distance", {}).get("data", [])

        if hr_data and dist_data:
            save_hr_plot_plotly(dist_data, hr_data, distance_km)

        # 4) HR split map
        split_hr_map = defaultdict(list)
        for dist, hr in zip(dist_data, hr_data):
            split_index = int(dist // 1000)
            split_hr_map[split_index].append(hr)

        split_max_hrs = {}
        for i in range(1, len(splits) + 1):
            split_max_hr = max(split_hr_map.get(i - 1, []), default="N/A")
            split_max_hrs[i] = split_max_hr

        # 5) Format splits
        split_text = ""
        for i, split in enumerate(splits, 1):
            pace = format_pace(1000, split.get("average_speed", 0))
            move_sec = split.get("moving_time", 0)
            move_str = f"{move_sec//60:.0f}:{move_sec%60:02.0f}"
            hr = safe_int(split.get("average_heartrate"))
            max_hr_s = split_max_hrs.get(i, "N/A")
            elev_s = f"{safe_round(split.get('elevation_difference', 0), decimals=1):+}m"
            dist_km_s = split.get("distance", 0) / 1000
            split_text += f"{i:>2}: {dist_km_s:.2f} km | {pace:<8} | {move_str:<8} | HR {hr:<3} | Max HR {max_hr_s:<3} | Elev {elev_s}\n"

        # 6) Custom laps
        lap_text = "Custom Laps:\n"
        r = await client.get(f"https://www.strava.com/api/v3/activities/{activity_id}/laps", headers=headers)
        r.raise_for_status()
        laps = r.json()
        for i, lap in enumerate(laps, 1):
            dist = safe_round(lap.get("distance"), divisor=1000, decimals=2)
            move = format_duration(lap.get("moving_time", 0), style="compact")
            pace = format_pace(lap.get("moving_time"), dist)
            hr = safe_int(lap.get("average_heartrate"))
            max_hr = safe_int(lap.get("max_heartrate"))
            cadence = safe_int_scaled(lap.get("average_cadence"), multiplier=2)
            elev_s = f"{safe_round(lap.get('total_elevation_gain'), decimals=1, default=0):+}m"
            lap_text += f"{i:>2}: {dist:.2f} km | Time {move:<5} | Pace {pace:<8} | HR {hr} | Max {max_hr} | Elev {elev_s} | Cadence {cadence}\n"

    # 7) Privacy warnings
    privacy_warning = ""
    if dist_data and dist_data[0] > 30:
        privacy_warning += "\n⚠️ Missing early HR data — likely due to start location privacy settings.\n"
    if dist_data and distance_km - dist_data[-1] / 1000 > 0.1:
        privacy_warning += "\n⚠️ Missing end HR data — likely due to end location privacy settings.\n"
    if privacy_warning:
        split_text += privacy_warning

    # 8) Compose summary + call coach
    summary = (
        f"🏃‍♂️ Workout: {name}\n📍 Start: {start_time}\n📏 Distance: {distance_km} km\n"
        f"⏱️ Moving Time: {moving} min | Elapsed: {elapsed} min\n"
        f"❤️ Avg HR: {avg_hr} bpm | Max HR: {max_hr} bpm\n🔥 Calories: {calories}\n"
        f"🌡️ Temp: {temp}°C | Cadence: {cadence} spm\n⛰️ Elev Gain: {elev} m\n\n"
        f"{'='*40}\n📊 Splits:\n{split_text}\n{'='*40}\n🟧 {lap_text}"
    )

    chat_response = call_chat_completion(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert marathon coach. Analyze the workout below, "
                    "comment on pacing strategy, heart rate drift, aerobic vs threshold distribution, "
                    "and give feedback on execution and improvement tips. Be clear and detailed."
                )
            },
            {"role": "user", "content": summary}
        ]
    )
    feedback = chat_response["choices"][0]["message"]["content"]

    timestamp = datetime.now().strfti
