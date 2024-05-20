#!/usr/bin/env python3

from __future__ import annotations

import re
from dataclasses import dataclass, field
from itertools import chain
from pathlib import Path
from re import Pattern
from typing import ClassVar

from enum import Enum, auto, unique

# import datetime
# _DATE_PATTERN = re.compile(
#    r"(?P<year>\d{4})([-.](?P<month>\d{1,2}|XX)([-.](?P<day>\d{1,2}|XX))?)?", re.IGNORECASE
# )
#
#
# def parse_date(value: str) -> datetime.date|None:
#    match = _DATE_PATTERN.fullmatch(value)
#    if not match:
#        return None
#
#    month, day = (
#        int(group) if group and group.lower() != "xx" else 1
#        for group in (match.group("month"), match.group("day"))
#    )
#    return datetime.date(int(match.group("year")), month, day)
# _VERSION_PATTERN = re.compile(r"(v|Ver|Version |r|Rev )?(?P<version>\.?(\d|[a-f][^\s]*\d).*)", re.IGNORECASE)

_EARLY_ROMAN_NUMERALS = [
    "I",
    "II",
    "III",
    "IV",
    "V",
    "VI",
    "VII",
    "VIII",
    "IX",
    "X",
]
_EARLY_ROMAN_NUMERALS.extend([f"X{value}" for value in _EARLY_ROMAN_NUMERALS])


_DISC_PATTERN = re.compile(
    rf"Dis[ck] (?P<disc>\d+|[A-Z]|{'|'.join(_EARLY_ROMAN_NUMERALS)})"
)


@unique
class Language(Enum):
    ENGLISH = "En"
    AMERICAN_ENGLISH = "En-US"
    BRITISH_ENGLISH = "En-GB"
    FRENCH = "Fr"
    CANADIAN_FRENCH = "Fr-CA"
    GERMAN = "De"
    SPANISH = "Es"
    LATIN_AMERICAN_SPANISH = "Es-XL"
    ITALIAN = "It"
    DUTCH = "Nl"
    SWEDISH = "Sv"
    DANISH = "Da"
    JAPANESE = "Ja"
    NORWEGIAN = "No"
    FINNISH = "Fi"
    KOREAN = "Ko"
    RUSSIAN = "Ru"
    POLISH = "Pl"
    PORTUGESE = "Pt"
    BRAZILIAN_PORTUGESE = "Pt-BR"
    TURKISH = "Tr"
    ARABIC = "Ar"
    CHINESE = "Zh"
    SIMPLIFIED_CHINESE = "Zh-Hans"
    TRADITIONAL_CHINESE = "Zh-Hant"
    CZECH = "Cs"
    HINDI = "Hi"
    GREEK = "El"
    CATALAN = "Ca"
    CROATIAN = "Hr"
    HUNGARIAN = "Hu"


@unique
class Region(Enum):
    USA = "USA"
    EUROPE = "Europe"
    KOREA = "Korea"
    ASIA = "Asia"
    AUSTRALIA = "Australia"
    TAIWAN = "Taiwan"
    BRAZIL = "Brazil"
    PORTUGAL = "Portugal"
    FRANCH = "France"
    SPAIN = "Spain"
    BELGIUM = "Belgium"
    NETHERLANDS = "Netherlands"
    CANADA = "Canada"
    GERMANY = "Germany"
    HONG_KONG = "Hong Kong"
    NEW_ZEALAND = "New Zealand"
    JAPAN = "Japan"
    SWEDEN = "Sweden"
    FINLAND = "Finland"


class RomMetadata:
    _OPEN_TO_CLOSE: dict[str, str] = {
        "[": "]",
        "(": ")",
    }
    _TOKEN_RE: Pattern[str] = re.compile(
        r" *((?P<open>O)|(?P<close>C)) *| +".replace(r" ", r"[\s_]")
        # uses negative lookahead to exclude the kaomoji "(^^;"
        .replace(r"O", r"\[|\((?!\^\^;)").replace(r"C", r"[)\]]")
    )
    _TAG_COMMA_RE: Pattern[str] = re.compile(r" *[,\+] *")

    _LANGUAGE_LOOKUP: dict[str, Language] = {
        member.value: member for member in Language
    }
    _REGION_LOOKUP: dict[str, Region] = {
        member.value: member for member in Region
    }

    def __init__(self,
        stem: str,
        *,
        category: str = "",
        id: int | None = None,
        cloneofid: int | None = None,
    ) -> None:
        title_parts: list[str] = []
        tag_parts: list[str] = []
        tags: list[str] = []
        last_end = 0
        in_open_tag: str | None = None
        # versions: set[str] = set()
        languages: set[Language] = set()
        regions: set[Region] = set()
        disc: int | None = None

        for match in chain(RomMetadata._TOKEN_RE.finditer(stem), [None]):
            start = match.start() if match else len(stem)
            if start != last_end:
                segment = stem[last_end:start]
                parts = tag_parts if in_open_tag else title_parts
                parts.append(segment)
            if match:
                if symbol := match.group("open"):
                    if in_open_tag:
                        raise ValueError(f"nested groups: {stem}")
                    in_open_tag = symbol
                elif symbol := match.group("close"):
                    if not in_open_tag:
                        raise ValueError(f"group closed but none open: {stem}")
                    if symbol != RomMetadata._OPEN_TO_CLOSE[in_open_tag]:
                        raise ValueError(f"mismatched close tag: {stem}")
                    in_open_tag = None
                    if tag_parts:
                        tag = " ".join(tag_parts)
                        ###################################################
                        if disc_match := _DISC_PATTERN.fullmatch(tag):
                            if disc is not None:
                                raise ValueError(
                                    f"Parsed multiple discs: {stem}"
                                )
                            disc_str = disc_match.group("disc")
                            try:
                                disc = (
                                    _EARLY_ROMAN_NUMERALS.index(disc_str) + 1
                                )
                            except ValueError:
                                try:
                                    disc = int(disc_str)
                                except ValueError:
                                    disc = ord(disc_str.lower()) - ord("a")
                        else:
                            language_results: list[Language] | None = []
                            region_results: list[Region] | None = []
                            tag_tokens = RomMetadata._TAG_COMMA_RE.split(tag)
                            for token in tag_tokens:
                                if language_results is not None:
                                    if language := RomMetadata._LANGUAGE_LOOKUP.get(
                                        token, None
                                    ):
                                        language_results.append(language)
                                    else:
                                        language_results = None
                                if region_results is not None:
                                    if region := RomMetadata._REGION_LOOKUP.get(
                                        token, None
                                    ):
                                        region_results.append(region)
                                    else:
                                        region_results = None
                                if (
                                    language_results is None
                                    and region_results is None
                                ):
                                    break  # no need to check further
                            if language_results:
                                languages.update(language_results)
                            elif region_results:
                                regions.update(region_results)
                            else:
                                # normal tag, or part of the title
                                tags.append(tag)
                        ###################################################
                        tag_parts = []
                last_end = match.end()
            elif in_open_tag:
                raise ValueError(f"unterminated group: {stem}")
        self.stem = stem
        self.title=" ".join(title_parts)
        self.tags=tags
        self.languages=languages
        self.regions=regions
        self.disc=disc
        # not detected, just set
        self.category=category
        self.id=id
        self.cloneofid=cloneofid

    def __str__(self) -> str:
        return f"{repr(self.title)}, {repr(self.tags)}"


def run_tests() -> None:
    test_values = [
        "Some Game (En,Fr,Sp) (Jp, Ko, Ch)",
        "hello(there)!",
        "hello?",
        "(what)open[who]",
        "I ate a panda",
        "(howdy) I ate a panda (howdy)",
        "(howdy) I           ate a panda(howdy)",
        "(howdy) I ate a panda(howdy)a ()  ",
        "____(howdy) ___I__ ate a _panda(howdy)a ()  ",
    ]

    for value in test_values:
        print(RomMetadata(value))


def main_gen(rom_root: Path) -> None:
    all_tags = set()
    print("gathering metadata...")
    with open("metadata.txt", "w") as metadata_file:
        for path in rom_root.rglob("*"):
            if path.is_dir():
                continue
            try:
                metadata = RomMetadata(path.stem)
                all_tags.update(metadata.tags)
                if metadata.title == "Sony":
                    import pdb

                    pdb.set_trace()
                metadata_file.write(str(metadata) + "\n")
            except ValueError as e:
                print(f"Error with file: {path})")
                print(f"- {e}")
    print("writing tags...")
    with open("tags.txt", "w") as tags_file:
        for tag in all_tags:
            tags_file.write(tag + "\n")
    print("done!")


def main() -> None:
    print("begin!")


if __name__ == "__main__":
    main()
