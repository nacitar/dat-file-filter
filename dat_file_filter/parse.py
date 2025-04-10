from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from typing import Callable

from .metadata import Localization, Metadata, Tags, Variation


def get_child_text(element: ET.Element, name: str) -> str:
    child = element.find(name)
    return child.text or "" if child is not None else ""


# TODO:
# - skip bad dumps


@dataclass
class Game:
    versions: list[Metadata]

    def variations(
        self,
    ) -> dict[Variation, dict[Localization, dict[Tags, Metadata]]]:
        variation_lookup: dict[
            Variation, dict[Localization, dict[Tags, Metadata]]
        ] = {}
        for metadata in self.versions:
            tags_to_metadata = variation_lookup.setdefault(
                metadata.variation, {}
            ).setdefault(metadata.localization, {})

            if metadata.unhandled_tags in tags_to_metadata:
                raise ValueError(
                    f"Multiple game roms with same sorting: {metadata.stem}"
                )
            tags_to_metadata[metadata.unhandled_tags] = metadata
        return variation_lookup

    # TODO: cache?
    def english_version(self) -> Metadata | None:
        best_metadata: list[Metadata] = []
        best_priority: int = 0

        for metadata in self.versions:
            priority = metadata.localization.english_priority()
            if not priority:
                continue
            if not best_metadata or priority < best_priority:
                best_metadata = [metadata]
                best_priority = priority
            elif priority == best_priority:
                best_metadata.append(metadata)
        best_metadata = sorted(
            best_metadata, key=lambda metadata: metadata.variation
        )
        if best_metadata:
            # if len(best_metadata) > 1:
            #     for metadata in best_metadata:
            #         print(
            #             f"{metadata.localization.english_priority()}"
            #             f" {metadata}"  # {metadata.stem}"
            #         )
            #     raise ValueError(f"Multiple of priority: {priority}")
            return best_metadata[0]
        return None


class DatFile:
    def __init__(
        self,
        path: Path | str,
        *,
        metadata_filter: Callable[[Metadata], bool] | None = None,
    ):
        self.name = ""
        self.stem_to_metadata: dict[str, Metadata] = {}
        id_to_metadata: dict[str, Metadata] = {}
        original_id_to_clones: dict[str, set[str]] = {}

        tree = ET.parse(path)
        root = tree.getroot()
        for child in root:
            if child.tag == "header":
                self.name = get_child_text(child, "name")
            elif child.tag == "game":
                stem = child.attrib["name"]
                description = get_child_text(child, "description")
                if description and stem != description:
                    raise ValueError(
                        "ERROR: description mismatch:"
                        f' "{stem}" != "{description}"'
                    )
                category = get_child_text(child, "category")
                if stem in self.stem_to_metadata:
                    raise ValueError(f"Duplicate stem: {stem}")
                id = child.attrib.get("id", "")
                cloneofid = child.attrib.get("cloneofid", "")
                metadata = Metadata.from_stem(
                    stem, category=category, id=id, cloneofid=cloneofid
                )
                if metadata_filter and not metadata_filter(metadata):
                    # print(f"filtering: {metadata.edition}")
                    continue
                self.stem_to_metadata[stem] = metadata

                if id:
                    if id in id_to_metadata:
                        raise ValueError(f"Duplicate id: {id}")
                    id_to_metadata[id] = metadata
                    if cloneofid:
                        original_id_to_clones.setdefault(cloneofid, set()).add(
                            id
                        )
                elif cloneofid:
                    raise ValueError(
                        f'"{stem}" has no id, but has cloneofid {cloneofid}'
                    )
        # NOTE: same game might have multiple names
        # group game versions
        title_to_stems: dict[str, set[str]] = {}
        # groups using clone ids
        for id, clones in original_id_to_clones.items():
            stems: set[str] = set()
            for metadata in chain(
                [id_to_metadata[id]] if id in id_to_metadata else [],
                (id_to_metadata[cloneid] for cloneid in clones),
            ):
                stems.add(metadata.stem)
                title_to_stems[metadata.variation.title] = stems
        # groups using the title
        for stem, metadata in self.stem_to_metadata.items():
            stems = title_to_stems.setdefault(metadata.variation.title, set())
            stems.add(stem)

        self.title_to_games: dict[str, Game] = {}

        processed_titles: set[str] = set()
        # Game objects for each game, grouped by the english title if available
        for title, stems in title_to_stems.items():
            if title in processed_titles:
                continue
            game = Game(
                versions=[self.stem_to_metadata[stem] for stem in stems]
            )
            english_version = game.english_version()
            self.title_to_games[
                english_version.variation.title if english_version else title
            ] = game
            processed_titles |= set(
                metadata.variation.title for metadata in game.versions
            )
