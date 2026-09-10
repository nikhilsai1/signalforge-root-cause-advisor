from datetime import datetime, timedelta

FLOOD_WINDOW = timedelta(minutes=10)
FLOOD_THRESHOLD = 10  # ISA-18.2: >10 alarms in a 10-minute window is a flood


def _parse(alarm: dict) -> datetime:
    return datetime.fromisoformat(alarm["timestamp"])


def detect_flood(alarms: list[dict]) -> dict:
    """ISA-18.2 alarm flood detection.

    Given timestamped alarms, find the first 10-minute window containing more
    than FLOOD_THRESHOLD alarms. The root alarm is the earliest-occurring
    alarm in that window; the rest are suppressed/clustered alarms.

    Returns {is_flood, root_alarm, suppressed}.
    """
    if not alarms:
        return {"is_flood": False, "root_alarm": None, "suppressed": []}

    sorted_alarms = sorted(alarms, key=_parse)

    for i, start_alarm in enumerate(sorted_alarms):
        window_start = _parse(start_alarm)
        window = [
            a for a in sorted_alarms[i:]
            if _parse(a) - window_start <= FLOOD_WINDOW
        ]
        if len(window) > FLOOD_THRESHOLD:
            root_alarm = window[0]
            suppressed = window[1:]
            return {"is_flood": True, "root_alarm": root_alarm, "suppressed": suppressed}

    return {"is_flood": False, "root_alarm": None, "suppressed": []}
