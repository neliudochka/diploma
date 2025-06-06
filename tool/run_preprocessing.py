import argparse
import glob
import logging
import os

import yaml

from preprocessing.main import preprocess
from mddConverter.main import convert_mdd_to_csv


def process_single_file(
    mdd_filepath=None,
    src_filepath=None,
    result_filepath=None,
    delimiter=",",
    systeminfo_filepath=None,
    datetime=None,
    gnss=None
):
    if mdd_filepath:
        logger.info("Decoding MDD to CSV started")
        if src_filepath:
            logger.warning("MDD path provided. Ignoring SRC path.")
        src_filepath = convert_mdd_to_csv(mdd_filepath, save_OF=True)
        logger.info(f"Decoding MDD to CSV finished. CSV saved to {src_filepath}\n")

    if not src_filepath:
        logger.error("No source CSV file specified. Cannot proceed.")
        return

    logger.info("Preprocessing started")
    preprocess(src_filepath, delimiter, systeminfo_filepath, result_filepath, datetime, gnss)
    logger.info("Preprocessing finished")


def main():
    parser = argparse.ArgumentParser(
        description="Run preprocessing"
    )

    parser.add_argument("-c", "--config", type=str, default="config.yaml", help="Path to YAML config file")
    parser.add_argument("-m", "--mdd", type=str, help="Path to MDD file")
    parser.add_argument("--src", type=str, help="Path to source CSV file")
    parser.add_argument("-d", "--delimiter", type=str, help="Delimiter used in the source CSV")
    parser.add_argument("-o", "--output", type=str, help="Path to save the result CSV")
    parser.add_argument("--systeminfo_filepath", type=str, help="Path to the systeminfo TXT file (magnetometer configuration file)")
    parser.add_argument("-t", "--datetime", type=str, help="Date string in format YYYYMMDD_HHMMSS.S")
    parser.add_argument("--gnss", type=str, help="Use external GNSS")
    parser.add_argument("--mdd_dir", type=str, help="Path to directory with MDD files")

    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    delim = args.delimiter or config["delimiter"]
    systeminfo_filepath = args.systeminfo_filepath or config["systeminfo_filepath"]
    datetime = args.datetime or config["datetime"]
    gnss = args.gnss or config["gnss"]

    if args.mdd_dir:
        full_path = os.path.abspath(args.mdd_dir)
        print(full_path)
        mdd_files = glob.glob(os.path.join(args.mdd_dir, "*.mdd"))
        logger.info(f"Found {len(mdd_files)} MDD files in directory '{args.mdd_dir}'")

        for mdd_filepath in mdd_files:
            logger.info(f"Processing file: {mdd_filepath}")

            process_single_file(
                mdd_filepath=mdd_filepath,
                result_filepath=None,
                delimiter=delim,
                systeminfo_filepath=systeminfo_filepath,
                datetime=datetime,
                gnss=gnss
            )

    else:
        mdd_filepath = args.mdd or config["mdd"]
        src_filepath = args.src or config["src"]
        result_filepath = args.output or config["output"]

        process_single_file(
            mdd_filepath=mdd_filepath,
            src_filepath=src_filepath,
            result_filepath=result_filepath,
            delimiter=delim,
            systeminfo_filepath=systeminfo_filepath,
            datetime=datetime,
            gnss=gnss
        )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    main()
