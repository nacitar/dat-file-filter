#!/usr/bin/env python3

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Sequence

from rom_management import Metadata
from pathlib import Path
from itertools import chain


def get_child_text(element: ET.Element, name: str) -> str:
    child = element.find(name)
    return child.text or "" if child is not None else ""


def get_int_attribute(element: ET.Element, name: str) -> int | None:
    value = element.attrib.get(name)
    return int(value) if value is not None else None


# TODO: add methods to determine english version, or whatever else is relevant
@dataclass
class Game:
    stem_to_metadata: dict[str, Metadata] = field(default_factory=dict)


class DatFile:
    def __init__(self, path: Path | str):
        self.name = ""
        self.stem_to_metadata: dict[str, Metadata] = {}
        id_to_metadata: dict[int, Metadata] = {}
        original_to_clones: dict[int, set[int]] = {}

        tree = ET.parse(path)
        root = tree.getroot()
        for child in root:
            if child.tag == "header":
                self.name = get_child_text(child, "name")
            elif child.tag == "game":
                stem = child.attrib["name"]
                description = get_child_text(child, "description")
                if description and stem != description:
                    print(
                        "ERROR: description mismatch:"
                        f' "{stem}" != "{description}"'
                    )
                category = get_child_text(child, "category")
                if stem in self.stem_to_metadata:
                    raise ValueError(f"Duplicate stem: {stem}")
                id = get_int_attribute(child, "id")
                cloneofid = get_int_attribute(child, "cloneofid")
                metadata = Metadata(
                    stem,
                    category=category,
                    id=id,
                    cloneofid=cloneofid,
                )
                self.stem_to_metadata[stem] = metadata

                if id is not None:
                    if id in id_to_metadata:
                        raise ValueError(f"Duplicate id: {id}")
                    id_to_metadata[id] = metadata
                    if cloneofid is not None:
                        original_to_clones.setdefault(cloneofid, set()).add(id)
                elif cloneofid is not None:
                    raise ValueError(
                        f'"{stem}" has no id, but has cloneofid {cloneofid}'
                    )
        # group game versions
        self.title_to_game: dict[
            str, Game
        ] = {}  # NOTE: same game might have multiple names
        # groups using the datfile's clone ids
        for id, clones in original_to_clones.items():
            game = Game()
            for metadata in chain(
                [id_to_metadata[id]] if id in id_to_metadata else [],
                (id_to_metadata[cloneid] for cloneid in clones),
            ):
                game.stem_to_metadata[metadata.stem] = metadata
                self.title_to_game[metadata.title] = game
        # groups using the title
        for stem, metadata in self.stem_to_metadata.items():
            game = self.title_to_game.setdefault(metadata.title, Game())
            if stem not in game.stem_to_metadata:
                game.stem_to_metadata[stem] = metadata


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Process a .dat file.")
    parser.add_argument(
        "dat_file_path", type=str, help="The path to the .dat file"
    )
    args = parser.parse_args(args=argv)

    # dat_content = parse_dat_file(args.dat_file_path)
    # print(dat_content)
    dat_content = DatFile(args.dat_file_path)

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
