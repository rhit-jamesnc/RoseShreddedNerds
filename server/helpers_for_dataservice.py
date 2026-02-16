from datetime import datetime, timedelta, timezone, date

# Storing the date and time format in ISO 8601 format with 'Z' suffix for UTC time
ISO_Z = "%Y-%m-%dT%H:%M:%SZ"

# This method find the current time in UTC and formats it in the ISO_Z format
def now_iso():
    """UTC timestamp e.g: 2023-10-05T14:48:00Z"""
    return datetime.now(timezone.utc).replace(microsecond=0).strftime(ISO_Z)

# This method takes any ISO_Z formatted datetime string and converts it into python datetime object
def parse_iso_z(time_string):
    """Parse ISO 8601 'Z' formatted string to datetime object"""
    return datetime.strptime(time_string, ISO_Z).replace(tzinfo=timezone.utc)

# This method also takes any date string and converts it into python date object
def parse_date(date_string):
    """Parse date string in YYYY-MM-DD format to date object"""
    return datetime.strptime(date_string, "%Y-%m-%d").date()

# The Epley Formula
def epley_1rm(weight_kg, reps):
    """1RM = W * (1 + reps/30), rounded to 2 decimal places"""
    return round(float(weight_kg) * (1.0 + float(reps) / 30.0), 2)

def iso_week_of(day):
    """Return ISO Week string like '2025-W44' for a date"""
    # Can be very use useful for weekly score report, scheduling and weekly stats
    year, week, _ = day.isocalendar()
    return f"{year}-W{week:02d}"

def iso_week_boundary(week_string):
    """
    Given 'YYYY-Www', it gives (this_week_monday_date, next_week_monday_date)
    Example: '2025-W44' it gives (2025-10-27, 2025-11-03)
    """

    year, week = week_string.split("-W")
    year, week = int(year), int(week)

    # The method isocalendar(year, week, weekday) return the date for that ISO calendar combination
    # weekday=1 means date for Monday of that week
    start_date = date.fromisocalendar(year, week, 1)
    end_date = start_date + timedelta(days=7)

    return start_date, end_date

