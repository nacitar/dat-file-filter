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
        r"(?P<name>alpha|beta|(possible )?proto(type)?)"
        r"( (?P<iteration>\d+))?"
    ),
    re.IGNORECASE,
)
_DEMO_PATTERN = re.compile(
    (r"(?P<name>demo|sample)" r"( (?P<iteration>\d+))?"), re.IGNORECASE
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
    AUSTRIA = "Austria"
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
    WORLD = "World"


@dataclass
class Metadata:
    stem: str
    title: str
    tags: list[str] = field(default_factory=list)
    regions: set[Region] = field(default_factory=set)
    languages: set[Language] = field(default_factory=set)
    disc: int | None = None
    edition: Edition = field(default_factory=Edition)
    unlicensed: bool = False
    bad_dump: bool = False
    alternate: bool = False
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
        version: str | None = None
        revision: str | None = None
        prerelease: str = ""
        demo: str = ""
        unlicensed = False
        alternate = False
        bad_dump = False
        tags: list[str] = []
        for tag in stem_info.tags:
            lower_tag = tag.lower()
            ###################################################
            if _DEMO_PATTERN.fullmatch(tag):
                if demo:
                    raise ValueError(f"Parsed multiple demo tags: {stem}")
                demo = tag
            elif lower_tag in ["unl", "unlicensed"]:
                if unlicensed:
                    raise ValueError(f"Parsed multiple unl tags: {stem}")
                unlicensed = True
            elif lower_tag in ["b"]:
                if bad_dump:
                    raise ValueError(f"Parsed multiple b tags: {stem}")
                bad_dump = True
            elif lower_tag in ["alt"]:
                if alternate:
                    raise ValueError(f"Parsed multible alt tags: {stem}")
                alternate = True
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
            else:
                language_results: list[Language] | None = []
                region_results: list[Region] | None = []
                tag_tokens = Metadata._TAG_COMMA_RE.split(tag)
                for token in tag_tokens:
                    if language_results is not None:
                        if language := Metadata._LANGUAGE_LOOKUP.get(
                            token, None
                        ):
                            language_results.append(language)
                        else:
                            language_results = None
                    if region_results is not None:
                        if region := Metadata._REGION_LOOKUP.get(token, None):
                            region_results.append(region)
                        else:
                            region_results = None
                    if language_results is None and region_results is None:
                        break  # no need to check further
                if language_results:
                    languages.update(language_results)
                elif region_results:
                    regions.update(region_results)
                else:
                    tags.append(tag)
        return Metadata(
            stem=stem,
            title=stem_info.title,
            tags=tags,
            regions=regions,
            languages=languages,
            disc=disc,
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
