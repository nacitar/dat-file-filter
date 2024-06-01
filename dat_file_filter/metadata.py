from __future__ import annotations

import datetime
import re
from dataclasses import dataclass, field
from enum import Enum, unique
from pathlib import Path
from re import Pattern
from typing import ClassVar

from .stem_info import StemInfo

_DATE_PATTERN = re.compile(
    r"(?P<year>\d{4})([-.](?P<month>\d{1,2}|XX)([-.](?P<day>\d{1,2}|XX))?)?",
    re.IGNORECASE,
)


@dataclass
class Edition:
    version: str = ""
    revision: str = ""
    prerelease: str = ""
    demo: str = ""
    date: datetime.date | None = None

    def __bool__(self) -> bool:
        return bool(
            self.version
            or self.revision
            or self.prerelease
            or self.demo
            or self.date
        )

    def __str__(self) -> str:
        output: list[str] = []
        if self.version:
            output.append(f"v{self.version}")
        if self.revision:
            output.append(f"r{self.revision}")
        if self.prerelease:
            output.append(f"[{self.prerelease}]")
        if self.demo:
            output.append(f"[{self.demo}]")
        if self.date:
            output.append(f"({self.date})")
        return " ".join(output)


def parse_date(value: str) -> datetime.date | None:
    match = _DATE_PATTERN.fullmatch(value)
    if not match:
        return None

    month, day = (
        int(group) if group and group.lower() != "xx" else 1
        for group in (match.group("month"), match.group("day"))
    )
    return datetime.date(int(match.group("year")), month, day)


_VERSION_PATTERN = re.compile(
    (
        r"((?P<prefix>v|Ver|Version |r|Rev )(?P<value>[a-f0-9.]+))"
        r"|(?P<version>\.?(\d|[a-f]\d[^\s]*\d)[^\s]*)"
        # r"(?P<version>\.?(\d|[a-f]\d[^\s]*\d)[^\s]*)"
        # r"(?P<version>[a-f0-9.]+)"
    ),
    re.IGNORECASE,
)

_PRERELEASE_PATTERN = re.compile(
    (
        r"(?P<name>alpha|beta|([^\s]+ )?promo|(possible )?proto(type)?)"
        r"( (?P<iteration>\d+))?"
    ),
    re.IGNORECASE,
)
_DEMO_PATTERN = re.compile(
    (
        r"(?P<name>(tech )?demo|sample|(?P<trial>([^\s]+ )+)?trial)"
        r"( ((?P<iteration>\d+)|edition|version))?"
    ),
    re.IGNORECASE,
)

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
    rf"[Dd]is[ck] (?P<disc>\d+|[A-Z]|{'|'.join(_EARLY_ROMAN_NUMERALS)})"
)

_ALTERNATE_PATTERN = re.compile(r"alt( (?P<index>\d+))?", re.IGNORECASE)

_EARLY_JAPANESE_NUMBERS: list[list[str]] = [
    ["ichi"],
    ["ni"],
    ["san"],
    ["shi", "yon"],
    ["go"],
    ["roku"],
    ["shichi", "nana"],
    ["hachi"],
    ["kyū", "ku", "kyu"],
    ["jū", "ju"],
]
_JAPANESE_NUMBER_PATTERN = re.compile(
    r"([^\s]+ )?([Dd]is[ck] )?(?P<disc>"
    + "|".join(
        [
            re.escape(item)
            for sublist in _EARLY_JAPANESE_NUMBERS
            for item in sublist
        ]
    )
    + r")",
    re.IGNORECASE,
)
_DISC_NAME_PATTERN = re.compile(
    r"cd (?P<name1>.+)|(?P<name2>.+) dis[ck]", re.IGNORECASE
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
    UNITED_KINGDOM = "UK"
    AUSTRIA = "Austria"
    DENMARK = "Denmark"
    NORWAY = "Norway"
    EUROPE = "Europe"
    KOREA = "Korea"
    ASIA = "Asia"
    AUSTRALIA = "Australia"
    CHINA = "China"
    ITALY = "Italy"
    SCANDINAVIA = "Scandinavia"
    LATIN_AMERICA = "Latin America"
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
    POLAND = "Poland"
    WORLD = "World"
    RUSSIA = "Russia"


@dataclass
class Metadata:
    stem: str
    title: str
    tags: list[str] = field(default_factory=list)
    regions: set[Region] = field(default_factory=set)
    languages: set[Language] = field(default_factory=set)
    disc: int | None = None
    disc_name: str = ""
    edition: Edition = field(default_factory=Edition)
    unlicensed: bool = False
    bad_dump: bool = False
    alternate: int = 0
    category: str | None = None

    _TAG_COMMA_RE: ClassVar[Pattern[str]] = re.compile(r" *[,\+] *")

    _LANGUAGE_LOOKUP: ClassVar[dict[str, Language]] = {
        member.value: member for member in Language
    }
    _REGION_LOOKUP: ClassVar[dict[str, Region]] = {
        member.value: member for member in Region
    }

    @staticmethod
    def from_stem(stem: str, *, category: str | None = None) -> Metadata:
        stem_info = StemInfo.from_stem(stem)

        languages: set[Language] = set()
        regions: set[Region] = set()
        date: datetime.date | None = None
        disc: int | None = None
        disc_name: str = ""
        japanese_number: int | None = None
        version: str | None = None
        revision: str | None = None
        prerelease: str = ""
        demo: str = ""
        unlicensed = False
        alternate: int = 0
        bad_dump = False
        tags: list[str] = []
        for tag in stem_info.tags:
            lower_tag = tag.lower()
            ###################################################
            if _DEMO_PATTERN.fullmatch(tag):
                if demo:
                    raise ValueError(f"Parsed multiple demo tags: {stem}")
                demo = tag  # NOTE: match has groups we aren't using
            elif lower_tag in ["unl", "unlicensed"]:
                if unlicensed:
                    raise ValueError(f"Parsed multiple unl tags: {stem}")
                unlicensed = True
            elif lower_tag in ["b"]:
                if bad_dump:
                    raise ValueError(f"Parsed multiple b tags: {stem}")
                bad_dump = True
            elif alternate_match := _ALTERNATE_PATTERN.fullmatch(tag):
                if alternate:
                    raise ValueError(f"Parsed multible alt tags: {stem}")
                alternate = int(alternate_match.group("index") or 1)
            elif disc_name_match := _DISC_NAME_PATTERN.fullmatch(tag):
                if disc_name:
                    raise ValueError(f"Parsed multiple disc names: {stem}")
                disc_name = disc_name_match.group(
                    "name1"
                ) or disc_name_match.group("name2")
            elif parsed_date := parse_date(tag):
                if date is not None:
                    raise ValueError(f"Parsed multiple dates: {stem}")
                date = parsed_date
            elif version_match := _VERSION_PATTERN.fullmatch(tag):
                if (version_match.group("prefix") or "")[:1].lower() == "r":
                    if revision is not None:
                        raise ValueError(f"Parsed multiple revisions: {stem}")
                    revision = version_match.group("value")
                else:
                    if version is not None:
                        raise ValueError(f"Parsed multiple versions: {stem}")
                    version = version_match.group(
                        "version"
                    ) or version_match.group("value")
            elif _PRERELEASE_PATTERN.fullmatch(tag):
                # NOTE: not using the groups (for now)
                if prerelease:
                    raise ValueError(
                        f"Parsed multiple prerelease tags: {stem}"
                    )
                prerelease = tag
            ###################################################
            elif disc_match := _DISC_PATTERN.fullmatch(tag):
                if disc is not None:
                    raise ValueError(f"Parsed multiple discs: {stem}")
                disc_str = disc_match.group("disc")
                try:
                    disc = _EARLY_ROMAN_NUMERALS.index(disc_str) + 1
                except ValueError:
                    try:
                        disc = int(disc_str)
                    except ValueError:
                        disc = ord(disc_str.lower()) - ord("a")
            elif japanese_number_match := _JAPANESE_NUMBER_PATTERN.fullmatch(
                tag
            ):
                if japanese_number is not None:
                    raise ValueError(f"Parsed multiple jp numbers: {stem}")
                parsed_disc = japanese_number_match.group("disc").lower()
                for index in range(len(_EARLY_JAPANESE_NUMBERS)):
                    if parsed_disc in _EARLY_JAPANESE_NUMBERS[index]:
                        japanese_number = index + 1
                        break
                if japanese_number is None:
                    raise AssertionError(
                        "number regex and number list mismatched."
                    )
            elif language := Metadata._LANGUAGE_LOOKUP.get(tag):
                languages.add(language)
            elif region := Metadata._REGION_LOOKUP.get(tag):
                regions.add(region)
            else:
                if not tag:
                    import pdb

                    pdb.set_trace()
                tags.append(tag)
        if (
            disc is not None
            and japanese_number is not None
            and disc != japanese_number
        ):
            raise ValueError(f"Got different disc index and jp number: {stem}")

        return Metadata(
            stem=stem,
            title=stem_info.title,
            tags=tags,
            regions=regions,
            languages=languages,
            disc=disc or japanese_number or 0,
            disc_name=disc_name,
            edition=Edition(
                version=version or "",
                revision=revision or "",
                date=date,
                prerelease=prerelease,
                demo=demo,
            ),
            unlicensed=unlicensed,
            bad_dump=bad_dump,
            alternate=alternate,
            category=category,  # just forwarded, not determined
        )

    @staticmethod
    def from_path(path: Path, *, category: str | None = None) -> Metadata:
        return Metadata.from_stem(path.stem, category=category)

    def __str__(self) -> str:
        return f"{repr(self.title)}, {repr(self.tags)}"
