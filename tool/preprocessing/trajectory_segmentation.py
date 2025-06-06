import numpy as np
from geographiclib.geodesic import Geodesic

def compute_geodesic_heading(lat1, lon1, lat2, lon2):
    """Computes the geodesic azimuth (more accurate, WGS84 ellipsoid)."""
    g = Geodesic.WGS84.Inverse(lat1, lon1, lat2, lon2)
    return g['azi1'] % 360

def planar_heading(x1, y1, x2, y2):
    """Computes azimuth in degrees using projected (planar) coordinates."""
    return (np.degrees(np.arctan2(x2 - x1, y2 - y1)) + 360) % 360

def heading_diff(h1, h2):
    """Returns the smallest angular difference between two headings."""
    return min(abs(h1 - h2), 360 - abs(h1 - h2))


def calculate_heading(df, start, end, lat_col='lat', lon_col='lon'):
    if end - start < 1:
        raise ValueError("End index must be greater than start index by at least 1.")
    h_ref = compute_geodesic_heading(df.iloc[start][lat_col], df.iloc[start][lon_col],
                            df.iloc[start+1][lat_col], df.iloc[start+1][lon_col])
    h_curr = compute_geodesic_heading(df.iloc[end][lat_col], df.iloc[end][lon_col],
                             df.iloc[end+1][lat_col], df.iloc[end+1][lon_col])
    return h_ref, h_curr

def segment_by_heading_incremental(df, lat_col, lon_col, max_angle_diff=50, min_segment_len=10):
    """
    Performs trajectory segmentation using an incremental greedy approach.
    Extends the segment one point at a time until the heading constraint is violated.
    """
    n = len(df)

    track_ids = np.full(n, np.nan)
    headings = np.full(n, np.nan)

    i = 0
    track = 0
    while i < n-1:
        j = i + 1
        while j < n-1:
            h_ref, h_curr = calculate_heading(df, i, j, lat_col, lon_col)
            if i == j - 1:
                headings[i] = h_ref
            headings[j] = h_curr
            hd = heading_diff(h_ref, h_curr)

            if hd > max_angle_diff:
                break

            j += 1
        if check_len_segment(df[lat_col].iloc[i], df[lon_col].iloc[i],
                             df[lat_col].iloc[j], df[lon_col].iloc[j],
                             min_segment_len):
            track_ids[i:j] = track
            track += 1
        i = j
    return track_ids, headings

def check_len_segment(lat1, lon1, lat2, lon2, min_len):
    geo = Geodesic.WGS84.Inverse(lat1, lon1, lat2, lon2)
    dist = geo['s12'] # in meters
    if dist >= min_len:
        return True
    return False

#
# def segment_by_heading_doubling(df, max_angle_diff=10, lat_col='lat', lon_col='lon'):
#     """
#     Performs trajectory segmentation using the double-and-search method.
#     Combines exponential search with binary search for efficient segment boundary detection.
#     """
#     n = len(df)
#     track_ids = np.zeros(n, dtype=int)
#     i = 0
#     track = 0
#     while i < n - 1:
#         a = 1
#         while i + a < n and test_heading_simple(df, i, i + a, max_angle_diff, lat_col, lon_col):
#             a *= 2
#         lo = i + a // 2
#         hi = min(i + a, n - 1)
#         while lo <= hi:
#             mid = (lo + hi) // 2
#             if test_heading_simple(df, i, mid, max_angle_diff, lat_col, lon_col):
#                 lo = mid + 1
#             else:
#                 hi = mid - 1
#         j = hi
#         track_ids[i:j + 1] = track
#         i = j + 1 #CHECK!!!!
#         track += 1
#     if i == n - 1:
#         track_ids[i] = track
#     df['track_id'] = track_ids
#     return df
