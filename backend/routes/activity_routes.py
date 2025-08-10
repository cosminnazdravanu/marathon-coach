# backend/routes/activity_routes.py

from fastapi import Request, APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import os
import httpx
import secrets
import logging
import math

from collections import defaultdict
from datetime import datetime, timezone
from html import escape

from backend.deps.auth import get_current_user
from backend.services.token_manager import get_access_token, save_tokens, delete_tokens
from backend.services.identity_manager import link_strava_identity, unlink_strava_identity
from backend.utils.utils import (
    safe_str, safe_round, safe_int, safe_int_scaled,
    format_date, format_duration, format_pace, to_float, to_int, to_int_scaled
)
from backend.utils.hr_plot import save_hr_plot_plotly
from backend.services.gpt_helper import call_chat_completion
from urllib.parse import urlencode, parse_qs, quote
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from zoneinfo import ZoneInfo  # Python 3.9+
from pathlib import Path
from time import time

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
BACKEND_ORIGIN = os.getenv("BACKEND_ORIGIN", "http://localhost:8000")
REDIRECT_URI = f"{BACKEND_ORIGIN}/strava_callback"

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

SER = URLSafeTimedSerializer(os.getenv("SECRET_KEY"), salt="strava-oauth")

try:
    TZ = ZoneInfo("Europe/Bucharest")
except Exception:
    TZ = datetime.now().astimezone().tzinfo or timezone.utc

timestamp = datetime.now(TZ).isoformat(timespec="seconds")

def ensure_csrf(request: Request) -> str:
    token = request.session.get("csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf"] = token
    return token

# --- CSRF helper (matches your /auth/* approach) ---
async def require_csrf(request: Request):
    sess = request.session.get("csrf")
    if not sess:
        raise HTTPException(status_code=403, detail="CSRF check failed (no session token)")

    # 1) Header path
    hdr = request.headers.get("X-CSRF-Token")
    if hdr and hdr == sess:
        return

    # 2) Body path
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        ctype = (request.headers.get("content-type") or "").lower()

        # a) application/x-www-form-urlencoded → parse manually (no deps)
        if ctype.startswith("application/x-www-form-urlencoded"):
            body = (await request.body()).decode(errors="ignore")
            token = parse_qs(body).get("csrf_token", [None])[0]
            if token == sess:
                return

        # b) multipart/form-data → only try if python-multipart is really present
        if "multipart/form-data" in ctype:
            try:
                import multipart  # type: ignore
            except Exception:
                raise HTTPException(status_code=403, detail="CSRF check failed (multipart parser missing)")
            form = await request.form()  # safe now
            token = form.get("csrf_token")
            if token == sess:
                return

    raise HTTPException(status_code=403, detail="CSRF check failed")

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    # If NOT logged in → send to login SPA (same as you already do elsewhere if desired)
    # return RedirectResponse("/login?next=/", status_code=303)

    local_user_id = request.session.get("user_id")
    valid_token = False
    athlete = None
    activities_list = []

    if local_user_id:
        access_token = get_access_token(str(local_user_id))
        if access_token:
            headers = {"Authorization": f"Bearer {access_token}"}
            try:
                r = httpx.get(
                    "https://www.strava.com/api/v3/athlete",
                    headers=headers,
                    timeout=10.0,
                )
                if r.status_code == 200:
                    athlete = r.json()
                    valid_token = True
                    # only fetch activities if the token actually works
                    from backend.services.strava_api import get_last_20_activities
                    activities_list = get_last_20_activities(str(local_user_id))
                elif r.status_code in (401, 403):
                    # token was invalidated at Strava (e.g., deauthorize in another session)
                    logger.warning(
                        "Strava %s on /athlete for user %s → wiping tokens",
                        r.status_code, local_user_id
                    )
                    delete_tokens(str(local_user_id))
                    valid_token = False
                    athlete = None
                    activities_list = []
                else:
                    logger.warning(
                        "Strava unexpected %s on /athlete: %s",
                        r.status_code, r.text
                    )
            except httpx.HTTPError as e:
                logger.warning("Strava API error on /athlete: %s", e)

    csrf = ensure_csrf(request)
    logged_in = bool(local_user_id)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "valid_token": valid_token,   # will be False after a 401/403
        "athlete": athlete,
        "activities_list": activities_list,
        "csrf": csrf,
        "logged_in": logged_in,
    })

@router.get("/login")
def login_redirect(next: str | None = None):
    # Your SPA doesn’t define a separate /login route; the login form is a component.
    # So send users to the SPA root and include ?next=... so the client can bounce back.
    target = f"{FRONTEND_ORIGIN}/" + (f"?next={quote(next)}" if next else "")
    return RedirectResponse(target, status_code=303)

# --- Start STRAVA OAuth ---
@router.get("/connect_strava")
def connect_strava(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        # change this to your real login route (and optionally add ?next=/connect_strava)
        return RedirectResponse("/login?next=/connect_strava", status_code=303)

    state = SER.dumps({"u": user_id, "n": secrets.token_urlsafe(8)})
    params = {
        "client_id": os.getenv("STRAVA_CLIENT_ID"),
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "approval_prompt": "auto",
        "scope": "read,activity:read",
        "state": state,
    }
    return RedirectResponse("https://www.strava.com/oauth/authorize?" + urlencode(params))

# --- Callback (no login required here) ---
@router.get("/strava_callback")
def strava_callback(code: str, state: str):
    # 1) Verify state
    try:
        data = SER.loads(state, max_age=600)  # 10 minutes
    except SignatureExpired:
        raise HTTPException(400, "OAuth state expired")
    except BadSignature:
        raise HTTPException(400, "Invalid OAuth state")

    user_id = data["u"]

    # 2) Exchange code → tokens
    token_url = "https://www.strava.com/api/v3/oauth/token"
    payload = {
        "client_id": os.getenv("STRAVA_CLIENT_ID"),
        "client_secret": os.getenv("STRAVA_CLIENT_SECRET"),
        "code": code,
        "grant_type": "authorization_code",
    }
    try:
        res = httpx.post(token_url, data=payload, timeout=20.0)
        res.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error("Strava token exchange failed: %s %s", e.response.status_code, e.response.text)
        raise HTTPException(502, f"Token exchange failed ({e.response.status_code})")
    except httpx.HTTPError as e:
        logger.error("HTTP error talking to Strava: %s", e)
        raise HTTPException(502, "Network error contacting Strava")

    tokens = res.json()
    if not tokens.get("access_token"):
        logger.error("Unexpected token payload: %s", tokens)
        raise HTTPException(502, "Token exchange succeeded but no access_token in response")

    # 3) Save + link
    save_tokens(str(user_id), tokens)
    try:
        link_strava_identity(user_id, tokens)
    except Exception as e:
        logger.warning("Identity link warning: %s", e)

    return RedirectResponse(url="/activity_feedback")

@router.post("/disconnect_strava")
async def disconnect_strava(request: Request):
    await require_csrf(request)
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login?next=/", status_code=303)

    # Revoke on Strava (optional, if you want consent next time)
    access_token = get_access_token(str(user_id))
    if access_token:
        try:
            # Strava deauth; pass the athlete token
            await httpx.AsyncClient().post(
                "https://www.strava.com/oauth/deauthorize",
                data={"access_token": access_token}, timeout=10.0
            )
        except httpx.HTTPError as e:
            logger.warning("Strava deauthorize failed: %s", e)

    delete_tokens(str(user_id))
    try:
        unlink_strava_identity(int(user_id))
    except Exception as e:
        logger.warning("unlink warning: %s", e)

    return RedirectResponse("/", status_code=303)

@router.get("/activity_feedback", response_class=HTMLResponse)
async def activity_feedback(request: Request, activity_id: str | None = None):
    user_id = request.session.get("user_id")
    if not user_id:
        # preserve deep link back to this page
        nxt = "/activity_feedback"
        if activity_id:
            from urllib.parse import urlencode
            nxt = f"/activity_feedback?{urlencode({'activity_id': str(activity_id)})}"
        return RedirectResponse(f"/login?next={nxt}", status_code=303)

    local_user_id = str(user_id)
    access_token = get_access_token(local_user_id)
    if not access_token:
        return RedirectResponse("/connect_strava", status_code=303)

    headers = {"Authorization": f"Bearer {access_token}"}

    async def get_json(url: str, *, params: dict | None = None):
        """Fetch JSON from Strava; if 401, ask user to reconnect (or refresh here if you have a refresher)."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(url, headers=headers, params=params)
            if r.status_code == 401:
                # If you have a refresh flow, do it here then retry once.
                # tokens = await refresh_tokens_for_user(local_user_id)  # if implemented
                # headers["Authorization"] = f"Bearer {tokens['access_token']}"
                # r = await client.get(url, headers=headers, params=params)
                return RedirectResponse("/connect_strava")
            r.raise_for_status()
            return r.json()

    # 1) Latest activity if none specified
    if not activity_id:
        activities = await get_json("https://www.strava.com/api/v3/athlete/activities")
        if isinstance(activities, RedirectResponse):  # bubbled reconnection
            return activities
        if not activities:
            return HTMLResponse("No activities found", status_code=200)
        latest_activity = activities[0]
        activity_id = latest_activity["id"]

    # 2) Detailed activity
    activity_url = f"https://www.strava.com/api/v3/activities/{activity_id}"
    activity = await get_json(activity_url)
    if isinstance(activity, RedirectResponse):
        return activity

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
    cadence = safe_int(safe_round(activity.get("average_cadence"), multiplier=2, decimals=0))  # strides→steps
    splits = activity.get("splits_metric", []) or []

    # 3) HR Stream
    streams = await get_json(
        f"https://www.strava.com/api/v3/activities/{activity_id}/streams",
        params={"keys": "heartrate,distance", "key_by_type": True},
    )
    if isinstance(streams, RedirectResponse):
        return streams
    hr_data = (streams.get("heartrate") or {}).get("data", []) or []
    dist_data = (streams.get("distance") or {}).get("data", []) or []

    # Optional plot (use existing helper)
    hr_plot_html = ""
    if hr_data and dist_data:
        try:
            plot_result = save_hr_plot_plotly(dist_data, hr_data, distance_km)
            # Support common return styles from your helper:
            if isinstance(plot_result, str):
                pr = plot_result.strip()
                if pr.startswith("<"):  # helper returned inline HTML
                    hr_plot_html = pr
                elif pr.lower().endswith((".html", ".htm")):  # path to an HTML file
                    hr_plot_html = f"<iframe src='{pr}' style='width:100%;height:380px;border:0'></iframe>"
                elif pr.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".svg")):  # image path
                    hr_plot_html = f"<img src='{pr}' alt='Heart rate plot' style='max-width:100%;height:auto'/>"
            # If helper returns None, nothing to embed (keeps page clean)
        except Exception as e:
            logger.warning("HR plot render failed: %s", e)
        static_path = Path(__file__).parent / "static" / "hr_plot.html"
        if not hr_plot_html and static_path.exists():
            hr_plot_html = "<iframe src='/static/hr_plot.html' style='width:100%;height:380px;border:0'></iframe>"

    # 4) HR split map
    split_hr_map: dict[int, list[int]] = defaultdict(list)
    for dist, hr in zip(dist_data, hr_data):
        split_index = int(dist // 1000)
        split_hr_map[split_index].append(hr)

    split_max_hrs: dict[int, int | str] = {}
    for i in range(1, len(splits) + 1):
        split_max_hr = max(split_hr_map.get(i - 1, []), default="N/A")
        split_max_hrs[i] = split_max_hr

    # 5) Format splits
    split_text = ""
    for i, split in enumerate(splits, 1):
        move_sec = to_int(split.get("moving_time"))
        dist_km  = to_float(split.get("distance")) / 1000.0
        pace     = format_pace(move_sec, dist_km) if move_sec and dist_km else "N/A"

        # labels (safe_* for display)
        dist_km_s = safe_round(split.get("distance"), divisor=1000, decimals=2)
        move_str  = format_duration(move_sec, style="compact")
        hr        = safe_int(split.get("average_heartrate"))
        max_hr_s  = split_max_hrs.get(i, "N/A")
        elev_s    = f"{safe_round(split.get('elevation_difference', 0), decimals=1):+}m"

        split_text += (
            f"{i:>2}: {dist_km_s:.2f} km | {pace:<8} | {move_str:<8} | "
            f"HR {hr:<3} | Max HR {max_hr_s:<3} | Elev {elev_s}\n"
        )

    # 6) Custom laps
    lap_text = "Custom Laps:\n"
    laps = await get_json(f"https://www.strava.com/api/v3/activities/{activity_id}/laps")
    if isinstance(laps, RedirectResponse):
        return laps
    for i, lap in enumerate(laps or [], 1):
        move_sec = to_int(lap.get("moving_time"))
        dist_km  = to_float(lap.get("distance")) / 1000.0
        pace     = format_pace(move_sec, dist_km) if dist_km else "N/A"

        # labels
        dist     = safe_round(lap.get("distance"), divisor=1000, decimals=2)
        move     = format_duration(move_sec, style="compact")
        hr_lap   = safe_int(lap.get("average_heartrate"))
        max_hr   = safe_int(lap.get("max_heartrate"))
        cad_lap  = to_int_scaled(lap.get("average_cadence"), multiplier=2)  # numeric
        elev_s   = f"{safe_round(lap.get('total_elevation_gain'), decimals=1, default=0):+}m"

        lap_text += (
            f"{i:>2}: {dist:.2f} km | Time {move:<5} | Pace {pace:<8} | "
            f"HR {hr_lap} | Max {max_hr} | Elev {elev_s} | Cadence {cad_lap}\n"
        )

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
        f"⏱️ Moving Time: {moving} | Elapsed: {elapsed}\n"
        f"❤️ Avg HR: {avg_hr} bpm | Max HR: {max_hr} bpm\n🔥 Calories: {calories}\n"
        f"🌡️ Temp: {temp}°C | Cadence: {cadence} spm\n⛰️ Elev Gain: {elev} m\n\n"
        f"{'='*40}\n📊 Splits:\n{split_text}\n{'='*40}\n🟧 {lap_text}"
    )

    # Make sure this call can't kill the page
    try:
        chat_response = call_chat_completion(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content":
                    "You are an expert marathon coach. Analyze the workout below, "
                    "comment on pacing strategy, heart rate drift, aerobic vs threshold distribution, "
                    "and give feedback on execution and improvement tips. Be clear and detailed."
                },
                {"role": "user", "content": summary},
            ],
        )
    except Exception as e:
        chat_response = f"(Coach analysis temporarily unavailable: {e})"

    # 9) RETURN actual HTML so the page renders
    html = f"""
    <!doctype html>
    <meta charset="utf-8">
    <title>Activity Feedback</title>
    <style>
    body {{ font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial; padding: 16px; }}
    pre {{ white-space: pre-wrap; background:#f7f7f7; padding:12px; border-radius:8px; }}
    .grid {{ display:grid; gap:16px; grid-template-columns: 1fr; max-width: 1000px; }}
    h1, h2 {{ margin: 0 0 8px; }}
    </style>
    <div class="grid">
    <div>
        <h1>Activity Feedback</h1>
        <pre>{escape(summary)}</pre>
    </div>
        <div>
        <h2>Heart Rate Plot</h2>
        {hr_plot_html or "<p>No HR data available.</p>"}
    </div>
    <div>
        <h2>Coach Notes</h2>
        <pre>{escape(str(chat_response))}</pre>
    </div>
    </div>
    """
    return HTMLResponse(html)