from datetime import datetime, time, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .Data import DataAsc


def get_date_and_time_by_filepath(filepath_str):
    date_str = Path(filepath_str).stem.split('_')[0]
    time_str = Path(filepath_str).stem.split('_')[1]
    # print(date_str)
    return datetime.strptime(date_str, "%Y%m%d").date(), datetime.strptime(time_str, "%H%M%S").time()

def get_date_and_time_by_str(datetime_str):
    date_str, time_str = datetime_str.split('_')
    return get_date_by_str(date_str), get_time_by_str(time_str)

def get_date_by_str(date_str):
    return datetime.strptime(date_str, "%Y%m%d").date()

def get_time_by_str(time_str):
    if time_str is not str:
        time_str = str(time_str)
    return datetime.strptime(time_str, "%H%M%S.%f").time()


def get_timestamp_utc(date, t=None):
    if t is None:
        dt = datetime.combine(date, time.min)
    else:
        dt = datetime.combine(date, t)

    dt = dt.replace(tzinfo=timezone.utc)
    return round_to_step(int(dt.timestamp() * 1000))

def round_to_step(value, step=200):
    return round(value / step) * step

def add_utc_timestamps(data, datetime=None):
    if datetime:
        date, time = get_date_and_time_by_str(datetime)
    else:
        date, time = get_date_and_time_by_filepath(data.filepath)

    if data.date is None:
        data.set_date(date)

    # check for gps_time because it has better time values
    first_valid_index = 0
    gps_time_col = data.config.gps_time_col
    timestamp_col = data.config.timestamp_col
    if gps_time_col in data.df.columns and data.df[gps_time_col].notna().any():
        valid_mask = data.df[gps_time_col].notna() & (data.df[gps_time_col] != 0)
        valid_values = data.df[gps_time_col][valid_mask]
        first_valid_index = valid_values.index[0]
        first_valid_time = valid_values.iloc[0]
        first_tmst = get_timestamp_utc(date, get_time_by_str(first_valid_time))

    elif isinstance(data, DataAsc):
        day_timestamps = data.df[timestamp_col]
        timestamps = get_timestamp_utc(date) + day_timestamps
        data.add_column(data.config.utc_timestamp_col, timestamps)
        return

    timestamps = [None] * len(data.df)
    timestamps[first_valid_index] = first_tmst

    # Розрахунок вперед
    for i in range(first_valid_index, len(data.df) - 1):
        delta = data.df[timestamp_col].iloc[i + 1] - data.df[timestamp_col].iloc[i]
        timestamps[i + 1] = timestamps[i] + delta

    # Розрахунок назад
    for i in range(first_valid_index, 0, -1):
        delta = data.df[timestamp_col].iloc[i] - data.df[timestamp_col].iloc[i - 1]
        timestamps[i - 1] = timestamps[i] - delta
    data.add_column(data.config.utc_timestamp_col, timestamps)

# date = get_date("part.csv")
# print(date)