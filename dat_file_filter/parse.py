from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from typing import Callable

from .metadata import Metadata


def get_child_text(element: ET.Element, name: str) -> str:
    child = element.find(name)
    return child.text or "" if child is not None else ""


# def get_int_attribute(element: ET.Element, name: str) -> int | None:
#    value = element.attrib.get(name)
#    return int(value) if value is not None else None


# TODO: figure out how to differentiate editions of the game w/r to the english
# version.  You'll have an english version of each variation, and I suppose
# they should all be provided.
@dataclass
class Game:
    versions: list[Metadata]

    def english_version(self) -> Metadata | None:
        priorities: set[int] = set()
        best_metadata: Metadata | None = None
        best_priority: int = 0

        for metadata in self.versions:
            priority = metadata.english_priority()
            if not priority:
                continue
            if not best_metadata or priority < best_priority:
                best_metadata = metadata
                best_priority = priority
            if priority in priorities:
                for metadata in self.versions:
                    print(f"{metadata.english_priority()} {metadata}")
                import pdb

                pdb.set_trace()
                raise ValueError(f"Multiple versions of priority: {priority}")
            priorities.add(priority)
        return best_metadata


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
                metadata = Metadata.from_stem(stem, category=category)
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
        self.title_to_stems: dict[str, set[str]] = {}
        # groups using clone ids
        for id, clones in original_id_to_clones.items():
            stems: set[str] = set()
            for metadata in chain(
                [id_to_metadata[id]] if id in id_to_metadata else [],
                (id_to_metadata[cloneid] for cloneid in clones),
            ):
                stems.add(metadata.stem)
                self.title_to_stems[metadata.title] = stems
        # groups using the title
        for stem, metadata in self.stem_to_metadata.items():
            stems = self.title_to_stems.setdefault(metadata.title, set())
            stems.add(stem)

        self.title_to_games: dict[str, Game] = {}

        for title, stems in self.title_to_stems.items():
            # TODO: determine the best version while filtering here
            # which will involve parsing of version numbers/dates
            # and sorting based upon them, grabbing the first/last
            self.title_to_games[title] = Game(
                versions=[self.stem_to_metadata[stem] for stem in stems]
            )
