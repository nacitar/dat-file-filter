import argparse
from pathlib import Path
from typing import Sequence

from .metadata import Metadata
from .parse import DatFile


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Process a .dat file.")
    parser.add_argument(
        "-t", "--tags", action="store_true", help="Print all unhandled tags"
    )
    parser.add_argument(
        "-e",
        "--editions",
        action="store_true",
        help="Print all custom editions.",
    )
    parser.add_argument(
        "dat_file_path", type=str, help="Path to the .dat file"
    )
    args = parser.parse_args(args=argv)

    dat_content = DatFile(args.dat_file_path)
    if args.editions or args.tags:
        editions: set[str] = set()
        tags: set[str] = set()
        for stem, metadata in dat_content.stem_to_metadata.items():
            if args.editions:
                if metadata.edition:
                    editions.add(str(metadata.edition))
            if args.tags:
                if metadata.tags:
                    tags.add(str(metadata.tags))  # NOTE: full group
        if editions:
            print("Editions:")
            for entry in editions:
                print(f"- {entry}")
            print()
        if tags:
            print("Tags:")
            for entry in tags:
                print(f"- {entry}")
            print()

    return 0


# for diagnostics
def generate_reports(rom_root: Path) -> None:
    all_tags = set()
    print("gathering metadata...")
    with open("metadata.txt", "w") as metadata_file:
        for path in rom_root.rglob("*"):
            if path.is_dir():
                continue
            try:
                metadata = Metadata.from_stem(path.stem)
                all_tags.update(metadata.tags)
                metadata_file.write(str(metadata) + "\n")
            except ValueError as e:
                print(f"Error with file: {path})")
                print(f"- {e}")
    print("writing tags...")
    with open("tags.txt", "w") as tags_file:
        for tag in all_tags:
            tags_file.write(tag + "\n")
    print("done!")
