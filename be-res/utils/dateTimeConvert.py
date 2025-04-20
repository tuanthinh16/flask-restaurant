from datetime import datetime

def datetime_to_number(dt: datetime) -> int:
    return int(dt.strftime('%Y%m%d%H%M%S'))

def number_to_datetime(num: int) -> datetime:
    return datetime.strptime(str(num), '%Y%m%d%H%M%S')
