import datetime


def date_range_str(start: datetime.date, end: datetime.date):
    date_fmt = "%-d %b %Y"
    if not start and not end:
        return ""

    if start == end or (bool(start) ^ bool(end)):
        return (start or end).strftime(date_fmt)

    if end < start:
        start, end = end, start

    same_year = start.year == end.year
    same_month = start.month == end.month

    if same_year and same_month:
        return "{start_day}-{end_day} {month} {year}".format(
            month=start.strftime("%b"),
            start_day=start.day,
            end_day=end.day,
            year=start.year,
        )

    if same_year:
        return "{start_day} {start_month} - {end_day} {end_month} {year}".format(
            start_month=start.strftime("%b"),
            start_day=start.day,
            end_month=end.strftime("%b"),
            end_day=end.day,
            year=start.year,
        )

    return "{start_date} to {end_date}".format(
        start_date=start.strftime(date_fmt),
        end_date=end.strftime(date_fmt),
    )
