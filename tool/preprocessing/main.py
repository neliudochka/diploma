import logging
import pandas as pd

from .external_gnss import merge_gnss_into_data
from .frequency import reduce_frequency, increase_frequency
from .handle_date_time import add_utc_timestamps
from .interpolation import interpolate_for_lines
from .magnetic_calibration import apply_magnetometer_calibration
from .magnetic_field import add_total_field, add_residual_field
from .sensors_offset import add_sensor_positions_by_heading
from .trajectory_segmentation import segment_by_heading_incremental
from .Data import DataOwn, DataFinal, DataExternalGNSS
from .attitude_determination import calculate_yaws, get_facing_points, get_facing_tracks

def preprocess(data_filepath, delim, systeminfo_filepath, result_filepath, datetime, external_gnss_filepath=None):
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)

    logger = logging.getLogger(__name__)

    logger.info(f"Step 0: Downloading data from {data_filepath}")
    data = DataOwn.from_file(data_filepath, delimiter=delim)
    logger.debug(f"\n{data.df}\n")

    if systeminfo_filepath is not None:
        logger.info(f"Step 1: Calibrating magnetometer sensors with {systeminfo_filepath}")
        apply_magnetometer_calibration(systeminfo_filepath, data)
        logger.debug(f"\n{data.df}\n")

    logger.info(f"Step 2: Adding date and UTC timestamps")
    add_utc_timestamps(data, datetime)
    logger.debug(f"\n{data.df}\n")

    if external_gnss_filepath is not None:
        logger.info(f"Step 2.5: Overriding with external gnss: {external_gnss_filepath}")
        external_data = DataExternalGNSS.from_file(external_gnss_filepath)
        merge_gnss_into_data(data, external_data, max_diff_ms=8)
        logger.debug(f"\n{data.df}\n")

    logger.info(f"Step 3: Reducing frequency if frequency of gnss data and timestamps are different")
    timestamp_freq = data.column_freq(data.config.timestamp_col)
    gnss_freq = data.column_freq(data.config.lat_col)
    df_original = None
    if gnss_freq < timestamp_freq:
        df_original = data.df.copy()
        data.df = reduce_frequency(data)
        logger.debug(f"\n{data.df}\n")

    logger.info(f"Step 4: Extracting tracks. Calculating headings")
    track_ids, headings = segment_by_heading_incremental(data.df,
                                          data.config.lat_col,
                                          data.config.lon_col,
                                          max_angle_diff=30,
                                          min_segment_len=10)
    data.add_column(data.config.track_id_col, track_ids)
    data.add_column(data.config.heading_col, headings)
    data.df = data.df.dropna(subset=[data.config.track_id_col]).reset_index(drop=True)
    logger.debug(f"\n{data.df}\n")

    logger.info(f"Step 5: Calculating orientations (yaws)")
    yaws = calculate_yaws(data)
    data.add_column(data.config.yaw_col, yaws)
    logger.debug(f"\n{data.df}\n")

    logger.info(f"Step 6: Adding facing direction based on heading and yaw")
    facings = get_facing_points(data.df[data.config.heading_col], data.df[data.config.yaw_col])
    data.add_column(data.config.facing_col, facings)
    ft = get_facing_tracks(data)
    data.add_column(data.config.track_facing_col, ft)
    logger.debug(f"\n{data.df}\n")

    logger.info(f"Step 7: Calculating the coordinates of the magnetometer sensors side tracks. Adding line_id")
    data_final = DataFinal.from_empty()
    add_sensor_positions_by_heading(data, data_final)
    data_final.gen_line_id()
    logger.debug(f"\n{data_final.df}\n")

    logger.info(f"Step 8: Increasing frequency, if it was reduced in step 3")
    if df_original is not None:
        increase_frequency(data_final, df_original, data.config)
        logger.debug(f"\n{data_final.df}\n")

    logger.info(f"Step 9: Interpolating GNSS data (latitude, longitude, altitude)")
    data_final.df = interpolate_for_lines(data_final)
    logger.debug(f"\n{data_final.df}\n")

    logger.info(f"Step 10: Calculating total field")
    add_total_field(data_final)
    logger.debug(f"\n{data_final.df}\n")

    logger.info(f"Step 11: Calculating residual field")
    add_residual_field(data_final)
    logger.debug(f"\n{data_final.df}\n")

    if result_filepath is None:
        result_filepath = str(data_filepath).split(".")[0] + "_prep" + ".csv"

    if external_gnss_filepath is not None:
        result_filepath = str(result_filepath).split(".")[0] + "_eg" + ".csv" #ex = external_gnss

    logger.info(f"Step 12: Saving the results to {result_filepath}")
    data_final.save(new_filepath=result_filepath, new_delimiter=';')

