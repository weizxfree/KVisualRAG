from datetime import datetime, timezone, timedelta


def beijing_time_now():
    # 创建一个表示 UTC+8 的时区对象
    beijing_tz = timezone(timedelta(hours=8))

    # 获取当前的北京时间
    time_now = datetime.now(beijing_tz)
    return time_now
