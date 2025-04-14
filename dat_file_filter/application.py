from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, Type

from .metadata import Edition, Metadata
from .parse import DatFile


def default_metadata_filter(metadata: Metadata) -> bool:
    return (
        not metadata.variation.edition.prerelease
        and not metadata.variation.edition.demo
    )


class TreePrinter:
    @dataclass
    class Context:
        printer: TreePrinter
        nest: bool

        def __enter__(self) -> TreePrinter.Context:
            if self.nest:
                self.printer.level += 1
            if self.nest or not self.printer.lines:
                self.printer.lines.append([f"{'  ' * self.printer.level}-"])
            return self  # or whatever you need in the 'as' variable

        def __exit__(
            self,
            exc_type: Type[BaseException] | None,
            exc_value: BaseException | None,
            TracebackType: None,
        ) -> None:
            if self.nest:
                self.printer.level -= 1

    def __init__(self) -> None:
        self.lines: list[list[str]] = []
        self.level = 0

    def child(self, nest: bool) -> Context:
        return TreePrinter.Context(self, nest)

    def append(self, value: str) -> None:
        if not self.lines:
            self.lines.append([])
        if value:
            self.lines[-1].append(value)

    def print(self) -> None:
        for line in self.lines:
            print(" ".join(line))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Process a .dat file.")
    parser.add_argument(
        "-b",
        "--best-versions",
        action="store_true",
        help="Print best version of every game.",
    )
    parser.add_argument(
        "-g",
        "--game-tag-sets",
        action="store_true",
        help="Print games with multiple tag sets.",
    )
    parser.add_argument(
        "-u",
        "--unhandled-tags",
        action="store_true",
        help="Print all unhandled tags",
    )
    parser.add_argument(
        "-e",
        "--editions",
        action="store_true",
        help="Print all custom editions.",
    )
    parser.add_argument(
        "-c", "--categories", action="store_true", help="Print all categories."
    )
    parser.add_argument(
        "-f",
        "--filter-metadata",
        action="store_true",
        default=False,
        help="Filter out undesirable ROMs (demos, prereleases, bad dumps...)",
    )
    parser.add_argument(
        "dat_file_path", type=str, help="Path to the .dat file"
    )
    args = parser.parse_args(args=argv)

    dat_content = DatFile(
        args.dat_file_path,
        metadata_filter=default_metadata_filter
        if args.filter_metadata
        else None,
    )
    if args.best_versions:
        print("Variations:")
        # rom_count = 0
        for title, game in dat_content.title_to_games.items():
            print(title)
            english_version = game.english_version()
            if english_version:
                print(f"- {english_version}")
            else:
                print(f"- [NO-ENGLISH] {game.versions[0]}")
    if args.game_tag_sets:
        print("Game Tag Sets:")
        # rom_count = 0
        for title, game in dat_content.title_to_games.items():
            printer = TreePrinter()
            printer.append(title)
            game_variations = game.variations()
            for (
                variation,
                localization_tags_title_metadata,
            ) in game_variations.items():
                with printer.child(len(game_variations) > 1):
                    printer.append(
                        f"{variation}" if variation else "[No-Variation]"
                    )
                    for (
                        localization,
                        tags_title_metadata,
                    ) in localization_tags_title_metadata.items():
                        with printer.child(
                            len(localization_tags_title_metadata) > 1
                        ):
                            printer.append(
                                str(localization)
                                if localization
                                else "[No-Localization]"
                            )
                            for (
                                tags,
                                title_metadata,
                            ) in tags_title_metadata.items():
                                with printer.child(
                                    len(tags_title_metadata) > 1
                                ):
                                    printer.append(
                                        f"{tags}" if tags else "[No-Tags]"
                                    )

                                    show_titles = any(
                                        title != name
                                        for name in title_metadata.keys()
                                    )
                                    for (
                                        name,
                                        metadata,
                                    ) in title_metadata.items():
                                        if show_titles:
                                            with printer.child(
                                                len(title_metadata) > 1
                                            ):
                                                printer.append(name)
            printer.print()
    if args.editions or args.unhandled_tags or args.categories:
        editions: set[Edition] = set()
        unhandled_tags: dict[str, list[Metadata]] = {}
        categories: set[str] = set()
        for stem, metadata in dat_content.stem_to_metadata.items():
            if args.editions:
                if metadata.variation.edition:
                    editions.add(metadata.variation.edition)
            if args.unhandled_tags and metadata.unhandled_tags:
                if metadata.unhandled_tags:
                    unhandled_tags.setdefault(
                        str(sorted(set(metadata.unhandled_tags.values))),
                        [],  # full group
                    ).append(metadata)
            if args.categories and metadata.category:
                categories.add(metadata.category)
            # if metadata.
        if editions:
            print("Editions:")
            for edition in sorted(editions):
                print(f"- {edition}")
            print()
        if unhandled_tags:
            print("Unhandled Tags:")
            for tag, metadata_list in unhandled_tags.items():
                print(f"- {tag}")
                for metadata in metadata_list:
                    print(f"  - {metadata.stem}")
            print()
        if categories:
            print("Categories:")
            for category in sorted(categories):
                print(f"- {category}")
            print()

    return 0


# for diagnostics
def generate_reports(rom_root: Path) -> None:
    all_tags: set[str] = set()
    print("gathering metadata...")
    with open("metadata.txt", "w") as metadata_file:
        for path in rom_root.rglob("*"):
            if path.is_dir():
                continue
            try:
                metadata = Metadata.from_stem(path.stem)
                all_tags.update(metadata.unhandled_tags.values)
                metadata_file.write(str(metadata) + "\n")
            except ValueError as e:
                print(f"Error with file: {path})")
                print(f"- {e}")
    print("writing tags...")
    with open("tags.txt", "w") as tags_file:
        for tag in all_tags:
            tags_file.write(tag + "\n")
    print("done!")
