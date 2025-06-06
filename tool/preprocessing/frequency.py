import pandas as pd
from .Data import build_column_rename_map


def reduce_frequency(data):
    data.df.dropna(subset=[data.config.lat_col, data.config.lon_col]).reset_index(drop=True)
    return data.df.dropna(subset=[data.config.lat_col, data.config.lon_col]).reset_index(drop=True)

def increase_frequency(data_final, df_original, config_original):
    rename_map = build_column_rename_map(config_original, data_final.config)
    renamed_chunk = df_original.rename(columns=rename_map)

    expected_columns = list(rename_map.values())
    renamed_chunk = renamed_chunk[[col for col in expected_columns if col in renamed_chunk.columns]]

    fill_data_with_original(data_final, renamed_chunk)


def fill_data_with_original(data_final, original_df):
    line_col = data_final.config.line_id_col
    timestamp_col = data_final.config.timestamp_col

    # print(data_final.num_tracks())
    new_rows = []
    for i in range(data_final.num_tracks() * 2):
        df_part = data_final.df[data_final.df[line_col] == i]

        if df_part.empty:
            # print(f"Skipping Line ID = {i}, because no data is available for it")
            continue


        first_ts = df_part[timestamp_col].iloc[0]
        last_ts = df_part[timestamp_col].iloc[-1]

        original_part = original_df[
            (original_df[timestamp_col] >= first_ts) &
            (original_df[timestamp_col] <= last_ts)
            ]

        existing_ts = set(df_part[timestamp_col])
        original_part_missing = original_part[~original_part[timestamp_col].isin(existing_ts)]

        original_part_missing = original_part_missing.copy()

        if line_col not in original_part_missing.columns:
            original_part_missing[line_col] = i

        original_part_missing[data_final.config.sensor_id_col] = (
            df_part[data_final.config.sensor_id_col].iloc[0])
        original_part_missing[data_final.config.track_id_col] = (
            df_part[data_final.config.track_id_col].iloc[0])
        original_part_missing[data_final.config.track_facing_col] = (
            df_part[data_final.config.track_facing_col].iloc[0])

        new_rows.append(original_part_missing)

    if new_rows:
        new_data = pd.concat(new_rows, ignore_index=True)
        data_final.df = pd.concat([data_final.df, new_data], ignore_index=True)
        data_final.df = data_final.df.sort_values(by=[line_col, timestamp_col]).reset_index(drop=True)
