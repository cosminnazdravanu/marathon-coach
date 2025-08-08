from datetime import datetime

def safe_round(value, divisor=1, default="N/A", multiplier=1, decimals=2):
    try:
        return round((value * multiplier) / divisor, decimals)
    except (TypeError, ZeroDivisionError):
        return default

def safe_int(value, default="N/A"):
    try:
        return int(round(value))
    except (TypeError, ValueError):
        return default

def safe_str(value, default="N/A"):
    return str(value) if value is not None else default

def safe_int_scaled(value, multiplier=1, default="N/A"):
    try:
        return int(round(value * multiplier))
    except (TypeError, ValueError):
        return default
    
def format_date(date_str, fmt="%a, %d %b %Y – %H:%M", default="N/A"):
    """
    Converts an ISO 8601 date string (like '2025-07-27T08:34:12Z')
    into a human-readable format like 'Sun, 27 Jul 2025 – 11:34'.
    Adjust `fmt` as needed for different formats.
    """
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime(fmt)
    except (TypeError, ValueError):
        return default
    
def format_pace(time_seconds, distance_km, default="N/A"):
    """
    Returns a formatted pace string (min:sec per km) given total time in seconds and distance in km.
    Example: 295 sec / 1 km → "4:55/km"
    """
    try:
        if not distance_km or distance_km <= 0:
            return default
        pace = time_seconds / distance_km
        mins = int(pace // 60)
        secs = int(pace % 60)
        return f"{mins}:{secs:02d}/km"
    except (TypeError, ZeroDivisionError):
        return default
    
def format_duration(seconds, style="colon", default="N/A"):
    """
    Converts seconds into formatted duration.
    
    style="colon"   -> "H:MM:SS" (or "MM:SS" if < 1 hour)
    style="long"    -> "1h 05m 22s"
    style="compact" -> "MM:SS" always
    """
    try:
        seconds = int(seconds)
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)

        if style == "long":
            parts = []
            if hours > 0:
                parts.append(f"{hours}h")
            if minutes > 0 or hours > 0:
                parts.append(f"{minutes}m")
            parts.append(f"{secs}s")
            return " ".join(parts)
        
        elif style == "compact":
            total_minutes = seconds // 60
            return f"{total_minutes}:{secs:02d}"
        
        # Default: colon style (race-style)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"

    except (TypeError, ValueError):
        return default