import argparse
from pathlib import Path
from typing import Sequence

from .metadata import Metadata
from .parse import DatFile


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Process a .dat file.")
    parser.add_argument(
        "-u",
        "--unhandled-tags",
        action="store_true",
        help="Print all unhandled tags",
    )
    parser.add_argument(
        "-g",
        "--game-tag-sets",
        action="store_true",
        help="Print games with multiple tag sets.",
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
    if args.editions or args.unhandled_tags:
        editions: set[str] = set()
        unhandled_tags: set[str] = set()
        if args.editions or args.unhandled_tags:
            for stem, metadata in dat_content.stem_to_metadata.items():
                if args.editions:
                    if metadata.edition:
                        editions.add(str(metadata.edition))
                if args.unhandled_tags:
                    if metadata.tags:
                        unhandled_tags.add(
                            str(sorted(set(metadata.tags)))
                        )  # NOTE: full group
                # if metadata.
            if editions:
                print("Editions:")
                for entry in editions:
                    print(f"- {entry}")
                print()
            if unhandled_tags:
                print("Unhandled Tags:")
                for tag in unhandled_tags:
                    print(f"- {tag}")
                print()
    if args.game_tag_sets:
        print("Game Tag Sets:")
        # TODO: group even further by discs
        game_tag_sets = {
            title: sorted(
                set(
                    str(sorted(set(version.tags)))
                    for version in game.versions
                    if version.tags
                )
            )
            for title, game in dat_content.title_to_games.items()
        }

        for title, tag_set in game_tag_sets.items():
            if len(tag_set) > 1:
                print(title)
                for tags in tag_set:
                    print(f"- {tags}")

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
