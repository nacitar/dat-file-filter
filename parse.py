#!/usr/bin/env python3

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Sequence

from rom_management import RomMetadata
from pathlib import Path


def get_child_text(element: ET.Element, name: str) -> str:
    child = element.find(name)
    return child.text or "" if child is not None else ""


def get_int_attribute(element: ET.Element, name: str) -> int | None:
    value = element.attrib.get(name)
    if value is not None:
        return int(value)
    return None


class DatFile:
    def __init__(self, path: Path | str):
        self.games: dict[str, list[RomMetadata]]

        self.name = ""
        self.stem_to_metadata: dict[str, RomMetadata] = {}
        self.id_to_metadata: dict[int, RomMetadata] = {}
        self.clone_to_original: dict[int, int] = {}
        self.original_to_clones: dict[int, set[int]] = {}

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
                        f'ERROR: description mismatch: "{stem}" != "{description}"'
                    )
                category = get_child_text(child, "category")
                if stem in self.stem_to_metadata:
                    raise ValueError(f"Duplicate stem: {stem}")
                id = get_int_attribute(child, "id")
                cloneofid = get_int_attribute(child, "cloneofid")
                metadata = RomMetadata(
                    stem,
                    category=category,
                    id=id,
                    cloneofid=cloneofid,
                )
                self.stem_to_metadata[stem] = metadata

                if id is not None:
                    if id in self.id_to_metadata:
                        raise ValueError(f"Duplicate id: {id}")
                    self.id_to_metadata[id] = metadata
                    if cloneofid is not None:
                        self.clone_to_original[id] = cloneofid
                        self.original_to_clones.setdefault(
                            cloneofid, set()
                        ).add(id)
                elif cloneofid is not None:
                    raise ValueError(
                        f'"{stem}" has no id, but has cloneofid {cloneofid}'
                    )
                ######################
                # metadata = RomMetadata.from_stem(name)
                # print(str(metadata))
        #

    # for testing
    def print_largest(self) -> None:
        largest: int | None = None
        largest_id: int | None = None
        for id in self.id_to_metadata:
            if id in self.clone_to_original:
                orig = self.clone_to_original[id]
                if orig in self.clone_to_original:
                    other = self.clone_to_original[orig]
                    raise ValueError(
                        f"Indirect reference: {id} => {orig} => {other}"
                    )
                else:
                    clones = self.original_to_clones[orig]
                    if largest is None or len(clones) > largest:
                        largest = len(clones)
                        largest_id = orig
        if largest_id is not None:
            metadata = self.id_to_metadata[largest_id]
            print(f"LARGEST: {metadata.title} == {largest}")
            for id in self.original_to_clones[largest_id]:
                print(f"- {self.id_to_metadata[id].title}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Process a .dat file.")
    parser.add_argument(
        "dat_file_path", type=str, help="The path to the .dat file"
    )
    args = parser.parse_args(args=argv)

    # dat_content = parse_dat_file(args.dat_file_path)
    # print(dat_content)
    dat_content = DatFile(args.dat_file_path)
    dat_content.print_largest()

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
