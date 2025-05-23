from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from functools import cached_property
from itertools import chain
from pathlib import Path
from typing import Callable

from .metadata import (
    Disc,
    Edition,
    Entity,
    Localization,
    Metadata,
    Tags,
    Version,
)


def get_child_text(element: ET.Element, name: str) -> str:
    child = element.find(name)
    return child.text or "" if child is not None else ""


@dataclass
class Game:
    versions: list[Metadata]

    def __post_init__(self) -> None:
        self.versions = sorted(self.versions)

    @cached_property
    def entity_to_metadata(self) -> dict[Entity, list[Metadata]]:
        entity_to_metadata: dict[Entity, list[Metadata]] = {}
        for metadata in self.versions:
            entity_to_metadata.setdefault(metadata.entity, []).append(metadata)
        return entity_to_metadata

    def hierarchy(
        self,
    ) -> dict[
        Edition,
        dict[
            Version,
            dict[Tags, dict[Disc, dict[Localization, dict[str, Metadata]]]],
        ],
    ]:
        lookup: dict[
            Edition,
            dict[
                Version,
                dict[
                    Tags, dict[Disc, dict[Localization, dict[str, Metadata]]]
                ],
            ],
        ] = {}
        for metadata in self.versions:
            title_to_metadata = (
                lookup.setdefault(metadata.entity.edition, {})
                .setdefault(metadata.entity.version, {})
                .setdefault(metadata.entity.unhandled_tags, {})
                .setdefault(metadata.entity.disc, {})
                .setdefault(metadata.localization, {})
            )
            if metadata.title in title_to_metadata:
                raise ValueError(
                    f"Multiple game roms with same sorting: {metadata.stem}"
                )
            title_to_metadata[metadata.title] = metadata
        return lookup

    def english_entities(self) -> list[Metadata]:
        best_versions: list[Metadata] = []
        for entity, versions in self.entity_to_metadata.items():
            metadata = Game.english_version(versions)
            if metadata is not None:
                best_versions.append(metadata)
        return best_versions

    @cached_property
    def english_title(self) -> str:
        # this will get the "best" english version of all units
        # which isn't great, but works to assume a title.
        english_version = Game.english_version(self.versions)
        return english_version.title if english_version else ""

    @staticmethod
    def english_version(versions: list[Metadata]) -> Metadata | None:
        best_metadata: list[Metadata] = []
        best_priority: int = 0

        for metadata in versions:
            priority = metadata.localization.english_priority()
            if not priority:
                continue
            if not best_metadata or priority < best_priority:
                best_metadata = [metadata]
                best_priority = priority
            elif priority == best_priority:
                best_metadata.append(metadata)
        best_metadata = sorted(
            best_metadata, key=lambda metadata: metadata.entity
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
                    # print(f"filtering: {metadata.variation.edition}")
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
                title_to_stems[metadata.title] = stems
        # groups using the title
        for stem, metadata in self.stem_to_metadata.items():
            stems = title_to_stems.setdefault(metadata.title, set())
            stems.add(stem)

        # sorting this inherently sorts title_to_games below
        title_to_stems = dict(
            sorted(title_to_stems.items(), key=lambda item: item[0].casefold())
        )
        self.title_to_games: dict[str, Game] = {}

        processed_titles: set[str] = set()
        # Game objects for each game, grouped by the english title if available
        for title, stems in title_to_stems.items():
            if title in processed_titles:
                continue
            game = Game(
                versions=[self.stem_to_metadata[stem] for stem in stems]
            )
            english_title = game.english_title or title
            self.title_to_games[english_title] = game
            processed_titles |= set(
                metadata.title for metadata in game.versions
            )
