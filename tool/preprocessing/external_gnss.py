import numpy as np
import pandas as pd

def find_nearest(external_ts: float, main_ts_series: pd.Series, max_diff_ms= None):
    if pd.isna(external_ts):
        return None

    diffs = np.abs(main_ts_series.values - external_ts)
    min_idx = diffs.argmin()

    if max_diff_ms is not None and diffs[min_idx] > max_diff_ms:
        return None

    return main_ts_series.index[min_idx]


def merge_gnss_into_data(main_data, external_data, max_diff_ms = None):
    main_df = main_data.df
    external_df = external_data.df

    main_ts_col = main_data.config.utc_timestamp_col
    external_ts_col = external_data.config.utc_timestamp_col

    main_lat_col = main_data.config.lat_col
    main_lon_col = main_data.config.lon_col
    main_alt_col = main_data.config.alt_col
    main_gps_time_col = main_data.config.gps_time_col


    main_df[main_lat_col] = np.nan
    main_df[main_lon_col] = np.nan
    main_df[main_alt_col] = np.nan
    main_df[main_gps_time_col] = np.nan

    ext_lat_col = external_data.config.lat_col
    ext_lon_col = external_data.config.lon_col
    ext_alt_col = external_data.config.alt_col

    main_ts = main_df[main_ts_col].values
    last_main_idx = 0

    for ext_idx, row in external_df.iterrows():
        ts = row[external_ts_col]
        if pd.isna(ts):
            continue


        while last_main_idx + 1 < len(main_ts) and main_ts[last_main_idx + 1] < ts:
            last_main_idx += 1

        candidates = [last_main_idx]
        if last_main_idx + 1 < len(main_ts):
            candidates.append(last_main_idx + 1)

        best_idx = min(candidates, key=lambda i: abs(main_ts[i] - ts))
        time_diff = abs(main_ts[best_idx] - ts)

        if max_diff_ms is not None and time_diff > max_diff_ms:
            continue


        if not pd.isna(row.get(ext_lat_col, np.nan)):
            main_df.at[best_idx, main_lat_col] = row[ext_lat_col]
        if not pd.isna(row.get(ext_lon_col, np.nan)):
            main_df.at[best_idx, main_lon_col] = row[ext_lon_col]
        if not pd.isna(row.get(ext_alt_col, np.nan)):
            main_df.at[best_idx, main_alt_col] = row[ext_alt_col]

    main_data.df = main_df

# main_data = DataOwn.from_file("../utc.csv")
# external_data = DataExternalGNSS.from_file("../rtk.csv")
# print(external_data.df)
#
# merge_gnss_into_data(main_data, external_data, max_diff_ms=30)
# updated_data.save("merged.csv")
