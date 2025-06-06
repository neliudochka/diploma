import numpy as np
import pandas as pd
from ahrs.utils import WMM
from geographiclib.geodesic import Geodesic
from geopy import Point


def total_field(B1, B2, B3):
    return np.round(np.sqrt(B1**2+B2**2+B3**2), 2)

def total_field_anomaly(tf, date, lat_series, lon_series, alt_series):
    trend = []
    for lat, lon, alt in zip(lat_series, lon_series, alt_series):
        alt = 0 if pd.isna(alt) else alt
        wmm = WMM(date=date, latitude=lat, longitude=lon, height=alt)
        trend.append(total_field(wmm.X, wmm.Y, wmm.Z))

    return np.array(tf) - np.array(trend)

def calculate_residual(tf_series: pd.Series, window_size: int):
    N = len(tf_series)
    trend = []

    half = window_size // 2

    start_window_mean = tf_series.iloc[0:window_size].mean()
    trend.extend([start_window_mean] * half)

    for i in range(half, N - half):
        window = tf_series.iloc[i - half: i + half + 1]
        trend.append(window.median())

    end_window_mean = tf_series.iloc[-window_size:].median()
    trend.extend([end_window_mean] * (N - len(trend)))

    residual = tf_series - pd.Series(trend, index=tf_series.index)
    return residual.round(2), pd.Series(trend, index=tf_series.index).round(2)


def velocity(time_series, lat_series, lon_series):
    vels = []
    for i in range(len(time_series)-1):
        t1 = time_series[i]
        lat1 = lat_series[i]
        lon1 = lon_series[i]
        p1 = Point(lat1, lon1)

        t2 = time_series[i+1]
        lat2 = lat_series[i+1]
        lon2 = lon_series[i+1]
        p2 = Point(lat2, lon2)

        dist = Geodesic.WGS84.Inverse(p1.latitude, p1.longitude, p2.latitude, p2.longitude)['s12']
        vel = dist / (t2-t1)
        vels.append(vel)

    return pd.Series(vels).mean()  # meter / ms

def velocity_data(data, n_elements):
    time_col = data.config.utc_timestamp_col
    lat_col = data.config.lat_col
    lon_col = data.config.lon_col
    line_id_col = data.config.line_id_col

    v = []
    for i in range(data.num_tracks()):
        df = data.df[data.df[line_id_col] == i]
        # decided to calculate velocity by the beginning of the track
        if n_elements < len(df):
            n_elements = len(df)
        df = df[:n_elements].reset_index(drop=True)
        # n = len(df)
        # df = df[int(n/2-n_elements/2):int(n/2+n_elements/2)].reset_index(drop=True)
        # df = df.reset_index(drop=True)
        v.append(velocity(df[time_col], df[lat_col], df[lon_col]))  # meter / ms

    if len(v) == 0:
        raise ValueError("No valid tracks with enough data points to compute velocity.")

    return pd.Series(v).mean()
    
def calculate_window_size(data, s = 15, n_elements=12000):
    v = velocity_data(data, n_elements)  # m / ms
    t_delta = s / v  # ms
    time_period = (1/data.column_freq(data.config.timestamp_col))*1000
    return int(np.ceil(t_delta/time_period))

def add_total_field(data):
    tf_col = data.config.total_field_col
    bx_col, by_col, bz_col = data.config.mag_cols1
    data.df[tf_col] = total_field(
        data.df[bx_col],
        data.df[by_col],
        data.df[bz_col],
    )

def add_residual_field(data):
    s_id = data.config.sensor_id_col
    tf_col = data.config.total_field_col
    resid_col = data.config.residual_field_col

    window_size = calculate_window_size(data)
    df1 = data.df[data.df[s_id] == 1][tf_col]
    df2 = data.df[data.df[s_id] == 2][tf_col]

    residual1, _ = calculate_residual(df1, window_size)
    residual2, _ = calculate_residual(df2, window_size)

    mask1 = data.df[s_id] == 1
    mask2 = data.df[s_id] == 2

    data.df.loc[mask1, resid_col] = residual1
    data.df.loc[mask2, resid_col] = residual2


# file_path = 'final.csv'
# data = DataFinal.from_file(file_path)
# add_residual_field(data)

# data.save(file_path+'_TF.csv')