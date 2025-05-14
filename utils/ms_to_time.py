from datetime import datetime
import pytz

def ms_to_time(ms, timezone='Europe/Moscow', as_duration=False):
    try:
        ms = int(ms)
    except (ValueError, TypeError):
        raise ValueError("Некорректное значение миллисекунд")

    if as_duration:
        total_seconds = abs(ms) // 1000
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"
    else:
        try:
            tz = pytz.timezone(timezone)
            dt = datetime.fromtimestamp(ms / 1000, tz)
            return dt.strftime('%H:%M')
        except OverflowError:
            return "Дата вне диапазона"
