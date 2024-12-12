import argparse
from pathlib import Path
from typing import Callable, Sequence

from .metadata import Edition, Metadata
from .parse import DatFile


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Process a .dat file.")
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
        "-b",
        "--best-versions",
        action="store_true",
        help="Print best version of every game.",
    )
    parser.add_argument(
        "dat_file_path", type=str, help="Path to the .dat file"
    )
    args = parser.parse_args(args=argv)

    metadata_filter: Callable[[Metadata], bool] = lambda metadata: (
        not metadata.edition.prerelease and not metadata.edition.demo
    )
    dat_content = DatFile(args.dat_file_path, metadata_filter=metadata_filter)
    if args.best_versions:
        print("Best Versions:")
        for title, game in dat_content.title_to_games.items():
            best_version = game.english_version()
            if best_version:
                print(f"- {best_version}")

    if args.game_tag_sets:
        print("Game Tag Sets:")
        game_tag_sets: dict[
            str, dict[Edition, dict[str, dict[str, set[str]]]]
        ] = {}

        for title, game in dat_content.title_to_games.items():
            for metadata in game.versions:
                tags = sorted(metadata.tags)
                game_tag_sets.setdefault(title, {}).setdefault(
                    metadata.edition, {}
                ).setdefault(
                    " ".join(
                        sorted(
                            f"[{region.value}]" for region in metadata.regions
                        )
                    ),
                    {},
                ).setdefault(
                    " ".join(
                        sorted(
                            f"[{language.value}]"
                            for language in metadata.languages
                        )
                    ),
                    set(),
                ).add(
                    str(tags) if tags else ""
                )
        for title, edition_to_region in game_tag_sets.items():
            lines = [[title]]
            indent = 0

            def add_prefix() -> None:
                if not lines[-1]:
                    lines[-1].append(f"{'  ' * indent}-")

            for edition, region_to_language in edition_to_region.items():
                if len(edition_to_region) > 1:
                    indent += 1
                    lines.append([])
                    add_prefix()
                lines[-1].append(str(edition) or "[No-Edition]")
                for region, language_to_tag_set in region_to_language.items():
                    if len(region_to_language) > 1:
                        indent += 1
                        lines.append([])
                        add_prefix()
                    lines[-1].append(str(region) or "[No-Region]")
                    for language, tag_set in language_to_tag_set.items():
                        if len(language_to_tag_set) > 1:
                            indent += 1
                            lines.append([])
                            add_prefix()
                        lines[-1].append(language or "[No-Language]")
                        for tag_string in tag_set:
                            if len(tag_set) > 1:
                                indent += 1
                                lines.append([])
                                add_prefix()
                            lines[-1].append(tag_string or "[No-Tags]")
                            if len(tag_set) > 1:
                                indent -= 1
                        if len(language_to_tag_set) > 1:
                            indent -= 1
                    if len(region_to_language) > 1:
                        indent -= 1
                if len(edition_to_region) > 1:
                    indent -= 1
            for line in lines:
                print(" ".join(line))
        print()
    if args.editions or args.unhandled_tags or args.categories:
        editions: set[Edition] = set()
        unhandled_tags: dict[str, list[Metadata]] = {}
        categories: set[str] = set()
        for stem, metadata in dat_content.stem_to_metadata.items():
            if args.editions:
                if metadata.edition:
                    editions.add(metadata.edition)
            if args.unhandled_tags and metadata.tags:
                unhandled_tags.setdefault(
                    str(sorted(set(metadata.tags))), []  # full group
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
