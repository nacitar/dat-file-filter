import argparse
from pathlib import Path
from typing import Sequence

from .metadata import Edition, Metadata
from .parse import DatFile


def default_metadata_filter(metadata: Metadata) -> bool:
    return (
        not metadata.variation.edition.prerelease
        and not metadata.variation.edition.demo
    )


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

        # TODO: fix so we don't process the same games by a different title
        # the game_id stuff doesn't work, perhaps by not looping over titles,
        # or even preventing multiple titles from entering the list.
        processed_games: set[int] = set()
        for title, game in dat_content.title_to_games.items():
            game_id = id(game)
            if title == "Legend of Zelda, The - A Link to the Past":
                print(f"LTTP: {game_id}")
            elif title == "Zelda no Densetsu - Kamigami no Triforce":
                print(f"LTTP J: {game_id}")
            if game_id in processed_games:
                continue
            processed_games.add(game_id)
            print(title)
            for (
                variation,
                localization_tags_metadata,
            ) in game.variations().items():
                print(f"- {variation}")
                for (
                    localization,
                    tags_metadata,
                ) in localization_tags_metadata.items():
                    print(f"  - {localization}")
                    for tags, metadata in tags_metadata.items():
                        print(f"    - {tags}: {metadata.stem}")
                        # rom_count += 1
        # if rom_count > 3:
        #        import pdb
        #    pdb.set_trace()

    if args.game_tag_sets:
        print("Game Tag Sets:")
        # title, Edition, regions, languages, tags
        game_tag_sets: dict[
            str, dict[Edition, dict[str, dict[str, set[str]]]]
        ] = {}

        for title, game in dat_content.title_to_games.items():
            for metadata in game.versions:
                tag_values = sorted(metadata.unhandled_tags.values)
                game_tag_sets.setdefault(title, {}).setdefault(
                    metadata.variation.edition, {}
                ).setdefault(
                    " ".join(
                        sorted(
                            f"[{region.value}]"
                            for region in metadata.localization.regions
                        )
                    ),
                    {},
                ).setdefault(
                    " ".join(
                        sorted(
                            f"[{language.value}]"
                            for language in metadata.localization.languages
                        )
                    ),
                    set(),
                ).add(
                    str(tag_values) if tag_values else ""
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
