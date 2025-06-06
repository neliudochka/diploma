import pandas as pd
from geographiclib.geodesic import Geodesic
from .Data import build_column_rename_map

DIST_CENTER_SENSOR = 0.5

def compute_sensor_angles(heading):
    left = (heading - 90) % 360
    right = (heading + 90) % 360
    return left, right

def compute_sensor_angles_with_facing(heading, facing):
    left, right = compute_sensor_angles(heading)
    if facing == 1:
        return left, right
    elif facing == -1:
        return right, left
    else:
        raise ValueError(f"Facing must be 1 or -1, got: {facing}")

def compute_sensor_positions(angles, facings, lats, lons, use_facing=False):
    s1_coords, s2_coords = [], []
    for i in range(len(angles)):
        if use_facing:
            s1_angle, s2_angle = compute_sensor_angles_with_facing(angles[i], facings[i])
        else:
            s1_angle, s2_angle = compute_sensor_angles(angles[i])

        s1_pos = Geodesic.WGS84.Direct(lats[i], lons[i], s1_angle, DIST_CENTER_SENSOR)
        s2_pos = Geodesic.WGS84.Direct(lats[i], lons[i], s2_angle, DIST_CENTER_SENSOR)

        s1_coords.append([s1_pos["lat2"], s1_pos["lon2"]])
        s2_coords.append([s2_pos["lat2"], s2_pos["lon2"]])

    return s1_coords, s2_coords

def add_sensor_positions(data, data_final, angle_col_name, use_facing):
    for track_id in range(data.num_tracks()):
        config = data.config
        chunk = data.df[data.df[data.config.track_id_col] == track_id]
        if chunk.empty:
            continue

        lats = chunk[data.config.lat_col].to_numpy()
        lons = chunk[data.config.lon_col].to_numpy()
        angles = chunk[angle_col_name].to_numpy()

        facings = None

        if use_facing:
            facings = chunk[data.config.track_facing_col].to_numpy()

        if use_facing and (len(facings) == 0 or facings[0] == 0):
            continue

        s1_coords, s2_coords = compute_sensor_positions(angles, facings, lats, lons, use_facing)
        if s1_coords and s2_coords:
            append_sensor_coords_to_data(data_final, s1_coords, s2_coords, chunk, config)

def append_sensor_coords_to_data(d, sc1, sc2, chunk, config):
    rename_map = build_column_rename_map(config, d.config)
    renamed_chunk = chunk.rename(columns=rename_map)

    # Перший сенсор
    df1 = renamed_chunk.copy()
    df1[d.config.lat_col] = [lat for lat, _ in sc1]
    df1[d.config.lon_col] = [lon for _, lon in sc1]
    df1[d.config.sensor_id_col] = 1

    # Другий сенсор
    df2 = renamed_chunk.copy()
    df2[d.config.lat_col] = [lat for lat, _ in sc2]
    df2[d.config.lon_col] = [lon for _, lon in sc2]
    df2[d.config.sensor_id_col] = 2

    # Об'єднуємо
    rows_df = pd.concat([df1, df2], ignore_index=True)
    common_cols = d.df.columns.intersection(rows_df.columns)

    d.df = pd.concat([d.df if not d.df.empty else None,
                      rows_df[common_cols]], ignore_index=True)


def translate_360_to_signed(angle):
    return angle if angle <= 180 else angle - 360

def translate_signed_to_360(angle):
    return angle if angle >= 0 else angle + 360

def add_sensor_positions_by_yaw(source_data, target_data):
    add_sensor_positions(
    source_data, target_data,
    angle_col_name=source_data.config.yaw_col,
    use_facing=False)

def add_sensor_positions_by_heading(source_data, target_data):
    add_sensor_positions(
        source_data, target_data,
        angle_col_name=source_data.config.heading_col,
        use_facing=True)

# pd.set_option('display.max_columns', None)
# pd.set_option('display.width', None)
#
# data = DataOwn.from_file("no_interp.csv")
# data_final = DataFinal.from_empty()
# add_sensor_positions_by_heading(data, data_final)
# data_final.save(new_filepath="final.csv")
