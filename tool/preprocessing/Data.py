from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import numpy as np
from typing import Optional, Tuple

@dataclass
class DataConfig:
    timestamp_col: Optional[str] = None
    acc_cols: Optional[Tuple[str, str, str]] = None
    mag_cols1: Optional[Tuple[str, str, str]] = None
    mag_cols2: Optional[Tuple[str, str, str]] = None
    lat_col: Optional[str] = None
    lon_col: Optional[str] = None
    alt_col: Optional[str] = None
    heading_col: Optional[str] = 'Heading [Deg]'
    track_id_col: Optional[str] = 'Track ID'
    line_id_col: Optional[str] = 'Line ID'
    yaw_col: Optional[str] = 'Yaw [deg]'
    facing_col: Optional[str] = 'Facing'
    track_facing_col: Optional[str] = 'Track facing'
    sensor_id_col: Optional[str] = None
    total_field_col: Optional[str] = None
    total_field_anomaly_col: Optional[str] = 'Total field anomaly [nT]'
    residual_field_col: Optional[str] = None
    gps_time_col: Optional[str] = None
    gps_date_col: Optional[str] = None
    utc_timestamp_col: Optional[str] = "UTC Timestamp [ms]" #in ms!!!

class Data:
    DEFAULT_CONFIG = DataConfig()
    DEFAULT_DELIMITER = ','

    def __init__(self, df: pd.DataFrame, filepath: Optional[str] = None, delimiter: Optional[str] = None, config: Optional[DataConfig] = None):
        self.df = df
        self.filepath = filepath
        self.delimiter = delimiter or self.DEFAULT_DELIMITER
        self.config = config or self.DEFAULT_CONFIG
        self.date = None
        self.set_date()

    @classmethod
    def from_file(cls, filepath: str, delimiter: Optional[str] = None, config: Optional[DataConfig] = None):
        delimiter = delimiter or cls.DEFAULT_DELIMITER
        config = config or cls.DEFAULT_CONFIG
        df = pd.read_csv(filepath, delimiter=delimiter)
        return cls(df, filepath=filepath, delimiter=delimiter, config=config)

    @classmethod
    def from_empty(cls, filepath: Optional[str] = None, delimiter: Optional[str] = None, config: Optional[DataConfig] = None):
        config = config or cls.DEFAULT_CONFIG
        delimiter = delimiter or cls.DEFAULT_DELIMITER

        columns = [
            config.utc_timestamp_col,
            config.timestamp_col,
            config.track_id_col, config.track_facing_col,
            config.sensor_id_col,
            config.line_id_col,
            config.lat_col, config.lon_col, config.alt_col,
            config.total_field_col,
            config.residual_field_col,
            config.gps_time_col,
            config.gps_date_col
        ]

        for group in [config.mag_cols1, config.mag_cols2, config.acc_cols]:
            if group:
                columns.extend(group)

        columns.extend([
            config.heading_col, config.yaw_col, config.facing_col])

        columns = list(filter(None, columns))

        empty_df = pd.DataFrame(columns=columns)
        return cls(empty_df, filepath=filepath, delimiter=delimiter, config=config)


    def set_date(self, date: Optional[datetime] = None):
        gps_date_col = self.config.gps_date_col
        if gps_date_col in self.df.columns and self.df[gps_date_col].notna().any():
            d = self.df[gps_date_col].iloc[0]
            if pd.notna(d):
                self.date = d
                return

        elif date:
            self.add_column(self.config.gps_date_col, date)
            self.date = date

    def add_column(self, col_name: str, values=None, index: Optional[int] = None):
        if values is None:
            self.df.insert(index if index is not None else len(self.df.columns), col_name, np.nan)
        else:
            self.df[col_name] = values

    def save(self, new_filepath: Optional[str] = None, new_delimiter: Optional[str] = None):
        path = new_filepath or self.filepath
        delim = new_delimiter or self.delimiter
        self.df.to_csv(path, sep=delim, index=False)

    def num_tracks(self):
        if self.config.track_id_col in self.df.columns:
            return int(self.df[self.config.track_id_col].nunique())
        return 0

    def column_freq(self, column_name):
        n = 1000
        part = self.df[:n]
        df = part.dropna(subset=column_name).reset_index(drop=True)
        ts_part = df[self.config.timestamp_col] / 1000 #convert to seconds
        intervals = ts_part.diff().dropna()
        estimated_interval_mode = intervals.median()
        frequency_hz_mode = round(1 / estimated_interval_mode)
        return frequency_hz_mode

    def gen_line_id(self):
        track_id = self.df[self.config.track_id_col]
        sensor_id = self.df[self.config.sensor_id_col]

        self.df[self.config.line_id_col] = track_id * 2 + (sensor_id == 2).astype(int)


class DataOwn(Data):
    DEFAULT_CONFIG = DataConfig(
        timestamp_col='Timestamp [ms]',
        acc_cols=(' AccX [g]', ' AccY [g]', ' AccZ [g]'),
        mag_cols1=(' B1x [nT]', ' B1y [nT]', ' B1z [nT]'),
        mag_cols2=(' B2x [nT]', ' B2y [nT]', ' B2z [nT]'),
        lat_col=' Latitude [Decimal Degrees]',
        lon_col=' Longitude [Decimal Degrees]',
        alt_col=' Altitude [m]',
        gps_time_col = ' GPSTime',
        gps_date_col = ' GPSDate'
    )
    DEFAULT_DELIMITER = ';'

class DataFinal(Data):
    DEFAULT_CONFIG = DataConfig(
        timestamp_col='Timestamp [ms]',
        track_id_col='Track ID',
        sensor_id_col='Sensor ID',
        line_id_col='Line ID',
        lat_col='Latitude [Decimal Degrees]',
        lon_col='Longitude [Decimal Degrees]',
        alt_col='Altitude [m]',
        mag_cols1=('Mag-X [nT]', 'Mag-Y [nT]', 'Mag-Z [nT]'),
        total_field_col='Total field [nT]',
        total_field_anomaly_col='Total field anomaly [nT]',
        residual_field_col='Residual field [nT]',
        heading_col=None,
        yaw_col=None,
        track_facing_col='Track facing',
        facing_col=None,
        acc_cols=('AccX [g]', 'AccY [g]', 'AccZ [g]')
    )
    DEFAULT_DELIMITER = ';'


class DataAsc(Data):
    DEFAULT_CONFIG = DataConfig(
        timestamp_col='Timestamp [ms]',
        track_id_col='Track ID',
        sensor_id_col='Sensor ID',
        lat_col='Latitude [°]',
        lon_col='Longitude [°]',
        mag_cols1=('Mag-X [nT]', 'Mag-Y [nT]', 'Mag-Z [nT]'),
        total_field_col='Total field [nT]',
        heading_col='Heading [Deg]',
        yaw_col='Yaw [deg]',
        facing_col='Facing',
        track_facing_col='Track facing',
        acc_cols=('AccX [g]', 'AccY [g]', 'AccZ [g]'),
        alt_col='Altitude [m]',
    )
    DEFAULT_DELIMITER = '\t'

class DataExternalGNSS(Data):
    DEFAULT_CONFIG = DataConfig(
        utc_timestamp_col='timestamp',
        track_id_col=None,
        sensor_id_col=None,
        lat_col='latitude',
        lon_col='longitude',
        mag_cols1=None,
        total_field_col=None,
        heading_col=None,
        yaw_col=None,
        facing_col=None,
        track_facing_col=None,
        acc_cols=None,
        alt_col=None,
        gps_time_col='GPS Time'
    )
    DEFAULT_DELIMITER = ','

def build_column_rename_map(src_config, dest_config):
    rename_map = {}
    for attr in dir(src_config):
        if attr.startswith('__'):
            continue
        if hasattr(dest_config, attr):
            src = getattr(src_config, attr)
            dst = getattr(dest_config, attr)
            if isinstance(src, (list, tuple)) and isinstance(dst, (list, tuple)):
                if len(src) == len(dst):
                    rename_map.update(dict(zip(src, dst)))
            elif isinstance(src, str) and isinstance(dst, str):
                rename_map[src] = dst

    return rename_map

