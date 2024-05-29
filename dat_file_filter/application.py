import argparse
from typing import Sequence

from .parse import DatFile


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Process a .dat file.")
    parser.add_argument(
        "dat_file_path", type=str, help="The path to the .dat file"
    )
    args = parser.parse_args(args=argv)

    # dat_content = parse_dat_file(args.dat_file_path)
    # print(dat_content)
    dat_content = DatFile(args.dat_file_path)
    print(dat_content)

    return 0
