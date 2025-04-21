from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, Type

from .metadata import Edition, Metadata
from .parse import DatFile
from .term_style import TermStyle


def default_metadata_filter(metadata: Metadata) -> bool:
    return (
        not metadata.entity.edition.prerelease
        and not metadata.entity.edition.demo
        and not metadata.entity.edition.early
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
        "--color",
        choices=("auto", "always", "never"),
        default="auto",
        help=(
            "Control colorized output: "
            "'auto' (default), 'always', or 'never'."
        ),
    )
    parser.add_argument(
        "-b",
        "--best-versions",
        action="store_true",
        help="Print best version of every game.",
    )
    parser.add_argument(
        "-m",
        "--missing-entities",
        action="store_true",
        help=(
            "Only valid with --best-versions; lists entities with no English"
            " ROM available; can reveal release differences such as special"
            " editions or if one region is single-disc and others are not."
        ),
    )
    parser.add_argument(
        "-r",
        "--report",
        action="store_true",
        help="Print a hierarchy report of all ROMs for a given game.",
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
    if args.missing_entities and not args.best_versions:
        parser.print_help(sys.stderr)
        print("", file=sys.stderr)
        print(
            "ERROR: --missing-entities is only valid with -b", file=sys.stderr
        )
        return 1
    TermStyle.set_enabled(
        args.color == "always"
        or (args.color == "auto" and sys.stdout.isatty())
    )

    dat_content = DatFile(
        args.dat_file_path,
        metadata_filter=default_metadata_filter
        if args.filter_metadata
        else None,
    )
    if args.best_versions:
        print("Best Versions:")
        for title, game in dat_content.title_to_games.items():
            missing_entities = set(game.entity_to_metadata.keys())
            entity_metadata = game.english_entities()

            if entity_metadata:
                print(title)
                for metadata in entity_metadata:
                    print(f"- {metadata}")
                    missing_entities.remove(metadata.entity)
                if args.missing_entities:
                    for entity in missing_entities:
                        print(
                            f"{TermStyle.YELLOW}- [NO-ENGLISH]: {entity}"
                            f"{TermStyle.RESET}"
                        )
            elif args.missing_entities:
                print(
                    f"{TermStyle.YELLOW}[NO-ENGLISH]: {title}"
                    f"{TermStyle.RESET}"
                )
            # TODO: else? should I show missing entities for things with NO
            # english versions whatsoever?  Want to keep some other things?

    if args.report:
        print("Hierarchy:")
        # rom_count = 0
        for title, game in dat_content.title_to_games.items():
            printer = TreePrinter()
            printer.append(title)
            game_hierarchy = game.hierarchy()
            for (
                edition,
                version_tags_disc_localization_title_meta,
            ) in game_hierarchy.items():
                with printer.child(len(game_hierarchy) > 1):
                    printer.append(str(edition))
                    for (
                        version,
                        tags_disc_localization_title_meta,
                    ) in version_tags_disc_localization_title_meta.items():
                        with printer.child(
                            len(version_tags_disc_localization_title_meta) > 1
                        ):
                            printer.append(str(version))
                            for (
                                tags,
                                disc_localization_title_meta,
                            ) in tags_disc_localization_title_meta.items():
                                with printer.child(
                                    len(tags_disc_localization_title_meta) > 1
                                ):
                                    printer.append(str(tags))
                                    for (
                                        disc,
                                        localization_title_meta,
                                    ) in disc_localization_title_meta.items():
                                        with printer.child(
                                            len(disc_localization_title_meta)
                                            > 1
                                        ):
                                            printer.append(str(disc))

                                            for (
                                                localization,
                                                title_meta,
                                            ) in (
                                                localization_title_meta.items()
                                            ):
                                                with printer.child(
                                                    len(
                                                        localization_title_meta
                                                    )
                                                    > 1
                                                ):
                                                    printer.append(
                                                        str(localization)
                                                    )
                                                    show_titles = False
                                                    for (
                                                        name
                                                    ) in title_meta.keys():
                                                        if title != name:
                                                            show_titles = True
                                                            break
                                                    if show_titles:
                                                        for (
                                                            name,
                                                            metadata,
                                                        ) in (
                                                            title_meta.items()
                                                        ):
                                                            with printer.child(
                                                                len(title_meta)
                                                                > 1
                                                            ):
                                                                printer.append(
                                                                    name
                                                                )
            printer.print()
    if args.editions or args.unhandled_tags or args.categories:
        editions: set[Edition] = set()
        unhandled_tags: dict[str, list[Metadata]] = {}
        categories: set[str] = set()
        for stem, metadata in dat_content.stem_to_metadata.items():
            if args.editions:
                if metadata.entity.edition:
                    editions.add(metadata.entity.edition)
            if args.unhandled_tags and metadata.entity.unhandled_tags:
                if metadata.entity.unhandled_tags:
                    unhandled_tags.setdefault(
                        str(
                            sorted(set(metadata.entity.unhandled_tags.values))
                        ),
                        [],  # full group
                    ).append(metadata)
            if args.categories and metadata.category:
                categories.add(metadata.category)
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
                all_tags.update(metadata.entity.unhandled_tags.values)
                metadata_file.write(str(metadata) + "\n")
            except ValueError as e:
                print(f"Error with file: {path})")
                print(f"- {e}")
    print("writing tags...")
    with open("tags.txt", "w") as tags_file:
        for tag in all_tags:
            tags_file.write(tag + "\n")
    print("done!")
