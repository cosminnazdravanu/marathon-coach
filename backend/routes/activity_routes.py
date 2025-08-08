import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import secrets
from fastapi import HTTPException
from fastapi import Request, APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from openai import OpenAI
import requests
from collections import defaultdict
from datetime import datetime

from backend.services.token_manager import get_access_token, save_tokens
from backend.utils.utils import *
from backend.config import DEBUG_GPT
from backend.utils.hr_plot import save_hr_plot_plotly
from backend.services.strava_api import get_last_20_activities

router = APIRouter()

TEMPLATES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates"))
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Main route
@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    user_id = request.session.get("user_id")
    valid_token = False
    athlete = None
    activities_list = []

    if user_id:
        access_token = get_access_token(user_id)
        if access_token:
            valid_token = True
            headers = {"Authorization": f"Bearer {access_token}"}
            athlete_response = requests.get("https://www.strava.com/api/v3/athlete", headers=headers)
            if athlete_response.status_code == 200:
                athlete = athlete_response.json()
            activities_list = get_last_20_activities(user_id)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "valid_token": valid_token,
        "athlete": athlete,
        "activities_list": activities_list
    })

# Connect to Strava (authorize URL)
@router.get("/connect_strava")
def connect_strava(request: Request):
    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state
    return RedirectResponse(
        url=(
            f"https://www.strava.com/oauth/authorize"
            f"?client_id={os.getenv('STRAVA_CLIENT_ID')}"
            f"&response_type=code"
            f"&redirect_uri={os.getenv('STRAVA_REDIRECT_URI')}"
            f"&approval_prompt=auto&scope=activity:read"
            f"&state={state}"
        )
    )

# Disconnect from Strava (clear tokens + session)
@router.post("/disconnect_strava")
def disconnect_strava(request: Request):
    # You may want to delete from the DB too, for now we just clear memory
    request.session.clear()
    print("👋 User disconnected from Strava.")
    return RedirectResponse(url="/", status_code=303)

# Callback after Strava auth
@router.get("/strava_callback")
def strava_callback(request: Request, code: str | None = None, state: str | None = None):
    if not code:
        return HTMLResponse("Authorization failed", status_code=400)

    saved = request.session.get("oauth_state")
    if not state or not saved or state != saved:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    # one-time use
    request.session.pop("oauth_state", None)

    token_url = "https://www.strava.com/api/v3/oauth/token"
    payload = {
        "client_id": os.getenv("STRAVA_CLIENT_ID"),
        "client_secret": os.getenv("STRAVA_CLIENT_SECRET"),
        "code": code,
        "grant_type": "authorization_code"
    }

    response = requests.post(token_url, data=payload)
    if response.status_code != 200:
        return HTMLResponse(f"Token exchange failed: {response.text}", status_code=400)

    tokens = response.json()
    user_id = str(tokens["athlete"]["id"])

    save_tokens(user_id, tokens)
    request.session["user_id"] = user_id

    return RedirectResponse(url="/activity_feedback")

@router.get("/activity_feedback", response_class=HTMLResponse)
async def activity_feedback(request: Request, activity_id: str = None):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/connect_strava")

    access_token = get_access_token(user_id)
    if not access_token:
        return RedirectResponse("/connect_strava")

    headers = {"Authorization": f"Bearer {access_token}"}

    # Step 1: Get latest activity if none specified
    if not activity_id:
        activities = requests.get(
            "https://www.strava.com/api/v3/athlete/activities",
            headers=headers
        ).json()
        if not activities:
            return HTMLResponse("No activities found", status_code=200)
        latest_activity = activities[0]
        activity_id = latest_activity["id"]

    # Step 2: Detailed activity
    activity_url = f"https://www.strava.com/api/v3/activities/{activity_id}"
    activity = requests.get(activity_url, headers=headers).json()

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

    # Step 3: HR Stream
    stream_url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams"
    params = {"keys": "heartrate,distance", "key_by_type": True}
    streams = requests.get(stream_url, headers=headers, params=params).json()
    hr_data = streams.get("heartrate", {}).get("data", [])
    dist_data = streams.get("distance", {}).get("data", [])

    if hr_data and dist_data:
        save_hr_plot_plotly(dist_data, hr_data, distance_km)

    # Step 4: HR split map
    split_hr_map = defaultdict(list)
    for dist, hr in zip(dist_data, hr_data):
        split_index = int(dist // 1000)
        split_hr_map[split_index].append(hr)

    split_max_hrs = {}
    for i in range(1, len(splits) + 1):
        split_max_hr = max(split_hr_map.get(i - 1, []), default="N/A")
        split_max_hrs[i] = split_max_hr

    # Step 5: Format splits
    split_text = ""
    for i, split in enumerate(splits, 1):
        pace = format_pace(1000, split.get("average_speed", 0))
        move_sec = split.get("moving_time", 0)
        move_str = f"{move_sec//60:.0f}:{move_sec%60:02.0f}"
        hr = safe_int(split.get("average_heartrate"))
        max_hr = split_max_hrs.get(i, "N/A")
        elev = f"{safe_round(split.get('elevation_difference', 0), decimals=1):+}m"
        dist_km = split.get("distance", 0) / 1000
        split_text += f"{i:>2}: {dist_km:.2f} km | {pace:<8} | {move_str:<8} | HR {hr:<3} | Max HR {max_hr:<3} | Elev {elev}\n"

    # Step 6: Custom laps
    lap_text = "Custom Laps:\n"
    laps = requests.get(f"https://www.strava.com/api/v3/activities/{activity_id}/laps", headers=headers).json()
    for i, lap in enumerate(laps, 1):
        dist = safe_round(lap.get("distance"), divisor=1000, decimals=2)
        move = format_duration(lap.get("moving_time", 0), style="compact")
        pace = format_pace(lap.get("moving_time"), dist)
        hr = safe_int(lap.get("average_heartrate"))
        max_hr = safe_int(lap.get("max_heartrate"))
        cadence = safe_int_scaled(lap.get("average_cadence"), multiplier=2)
        elev = f"{safe_round(lap.get('total_elevation_gain'), decimals=1, default=0):+}m"
        lap_text += f"{i:>2}: {dist:.2f} km | Time {move:<5} | Pace {pace:<8} | HR {hr} | Max {max_hr} | Elev {elev} | Cadence {cadence}\n"

    # Step 7: Privacy warnings
    privacy_warning = ""
    if dist_data and dist_data[0] > 30:
        privacy_warning += (
            "\n⚠️ Missing early HR data — likely due to start location privacy settings.\n"
        )
    if dist_data and distance_km - dist_data[-1] / 1000 > 0.1:
        privacy_warning += (
            "\n⚠️ Missing end HR data — likely due to end location privacy settings.\n"
        )

    if privacy_warning:
        split_text += privacy_warning

    # Step 8: Compose summary
    summary = (
        f"🏃‍♂️ Workout: {name}\n📍 Start: {start_time}\n📏 Distance: {distance_km} km\n"
        f"⏱️ Moving Time: {moving} min | Elapsed: {elapsed} min\n"
        f"❤️ Avg HR: {avg_hr} bpm | Max HR: {max_hr} bpm\n🔥 Calories: {calories}\n"
        f"🌡️ Temp: {temp}°C | Cadence: {cadence} spm\n⛰️ Elev Gain: {elev} m\n\n"
        f"{'='*40}\n📊 Splits:\n{split_text}\n{'='*40}\n🟧 {lap_text}"
    )

    if DEBUG_GPT:
        feedback = "[ChatGPT not called – debug mode ON]"
    else:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        chat_response = client.chat.completions.create(
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
        feedback = chat_response.choices[0].message.content
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S") #used to add a dummy query param to force bypass browser cache for HR PLOT load

    chart_html = f'<iframe src="/static/hr_plot.html?v={timestamp}" width="100%" height="400" style="border:none;"></iframe>'
    return HTMLResponse(content=f"<pre>{summary}</pre>{chart_html}<br><br>💬 AI Coach Feedback:<br><pre>{feedback}</pre>")
