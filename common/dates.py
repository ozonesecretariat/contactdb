import datetime


def date_range_str(start: datetime.datetime, end: datetime.datetime):
    date_fmt = "%-d %b %Y"
    if not start and not end:
        return ""

    if not start or not end:
        # One date is missing, assume a single-day event
        start = end = start or end

    start, end = start.date(), end.date()
    if start == end:
        return start.strftime(date_fmt)

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
