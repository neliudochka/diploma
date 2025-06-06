from datetime import datetime

import numpy as np
import math

import pandas as pd
from ahrs.utils import WMM
from numpy.ma.core import arctan2
from pandas import Series

# in a global frame
def calculate_yaws(data):
    yaws = []

    for i, row in data.df.iterrows():
        Bx1, By1 = row[data.config.mag_cols1[0]], row[data.config.mag_cols1[1]]
        if not pd.isna(data.date):
            d = data.date
        else:
            d = datetime.now()
        yaw = calculate_yaw(Bx1, By1, d, row[data.config.lat_col], row[data.config.lon_col])
        yaws.append(yaw)

    return yaws

def calculate_yaw(Bx, By, date, lat, lon):
    B_body_angle = math.degrees(math.atan2(By, Bx)) % 360
    B_ref_angle = get_B_reference(date, lat, lon)
    return (B_ref_angle - B_body_angle) % 360


def get_B_reference(date, lat, lon, h=0.0):
    wmm = WMM(date=date, latitude=lat, longitude=lon, height=h)
    B_r_x = wmm.X
    B_r_y = wmm.Y
    return np.degrees(arctan2(B_r_y, B_r_x)) % 360

def get_facing_points(headings, yaws, max_deviation=30):
    res = []
    for i in range(len(headings)):
        res.append(get_facing_point(headings[i], yaws[i], max_deviation))

    return res

def get_facing_point(heading_angle, yaw_angle, max_deviation):
    """
    :param heading_angle:
    :param yaw_angle:
    :param max_deviation:
    :return:
    1  - facing forward
    -1 - facing backward
    0  - neither
    """
    if heading_angle > yaw_angle:
        A = yaw_angle
        B = heading_angle
    else:
        A = heading_angle
        B = yaw_angle

    first_segment = B-A
    second_segment = (360-B) + A

    if first_segment <= max_deviation or second_segment <= max_deviation:
        return 1

    if abs(first_segment-180) <= max_deviation or abs(second_segment-180) <= max_deviation:
        return -1

    return 0

def get_facing_tracks(data):
    fts = []
    for t_n in range(data.num_tracks()):
        df_by_t = data.df[data.df[data.config.track_id_col] == t_n].reset_index(drop=True)
        track_facings = get_facing_points(df_by_t[data.config.heading_col], df_by_t[data.config.yaw_col])
        fts.extend([get_facing_track(track_facings)]*len(df_by_t))
    return fts

def get_facing_track(facings):
    counts = Series(facings).value_counts(normalize=True)
    # check the most popular
    if counts.iloc[0] > 0.9:
        return int(counts.index[0])
    else:
        return 0  # або 0, якщо не впевнений

# file_path='part.csv'
# data = DataOwn.from_file(file_path, delimiter=',')
# df = data.df[364:400].reset_index(drop=True)
# facings = calculate_is_facing_direction_val(df[data.heading_col], df[data.yaw_col])
# print(facings)
