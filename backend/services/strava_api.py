import requests
import datetime
from dotenv import load_dotenv
from backend.services.token_manager import get_access_token
from backend.utils.utils import safe_round, safe_str, safe_int

load_dotenv()

def get_last_20_activities(user_id):
    access_token = get_access_token(user_id)
    if not access_token:
        print(f"⚠️ No access token found for user {user_id}.")
        return []

    url = "https://www.strava.com/api/v3/athlete/activities"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "per_page": 20,
        "page": 1
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print(f"❌ Strava API error: {response.status_code}, {response.text}")
        return []

    raw_activities = response.json()
    activities = []

    for act in raw_activities:
        distance_km = safe_round(act.get("distance"), divisor=1000)
        moving_time_seconds = act.get("moving_time")
        moving_time = str(datetime.timedelta(seconds=moving_time_seconds)) if moving_time_seconds else "N/A"
        pace_sec_per_km = moving_time_seconds / (distance_km or 1) if moving_time_seconds and distance_km != "N/A" else 0
        pace_min = int(pace_sec_per_km // 60)
        pace_sec = int(pace_sec_per_km % 60)
        avg_pace = f"{pace_min}:{pace_sec:02d}/km" if pace_sec_per_km > 0 else "N/A"

        activities.append({
            "id": act['id'],
            "date": safe_str(act.get("start_date_local")).split("T")[0],
            "name": safe_str(act.get("name")),
            "length_km": distance_km,
            "duration": moving_time,
            "avg_pace": avg_pace,
            "avg_hr": safe_int(act.get("average_heartrate"))
        })

    return activities
