from __future__ import annotations

import datetime
import re
from dataclasses import dataclass, field
from enum import StrEnum, unique
from pathlib import Path
from re import Pattern
from typing import ClassVar

from .stem_info import StemInfo

_DATE_PATTERN = re.compile(
    r"(?P<year>\d{4})([-.](?P<month>\d{1,2}|XX)([-.](?P<day>\d{1,2}|XX))?)?",
    re.IGNORECASE,
)


@dataclass(frozen=True, eq=True)
class Date:
    date: datetime.date | None = None

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Date):
            return NotImplemented
        # Treat None as less than any date
        return (self.date is None, self.date) < (
            other.date is None,
            other.date,
        )

    def __bool__(self) -> bool:
        return bool(self.date)

    def __str__(self) -> str:
        return str(self.date) if self.date else ""


def parse_date(value: str) -> Date | None:
    match = _DATE_PATTERN.fullmatch(value)
    if not match:
        return None

    month, day = (
        int(group) if group and group.lower() != "xx" else 1
        for group in (match.group("month"), match.group("day"))
    )
    return Date(datetime.date(int(match.group("year")), month, day))


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
class Language(StrEnum):
    AMERICAN_ENGLISH = "En-US"
    ENGLISH = "En"
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
class Region(StrEnum):
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


@dataclass(frozen=True, eq=True, order=True)
class Edition:
    arcade: bool = False
    version: str = ""
    revision: str = ""
    prerelease: str = ""
    demo: str = ""
    date: Date = field(default_factory=lambda: Date(None))
    alternate: int = 0
    switch: bool = False
    steam: bool = False
    virtual_console: bool = False
    classic_mini: bool = False
    nintendo_power: bool = False  # updated versions for certain Japanese games

    def __bool__(self) -> bool:
        return bool(
            self.arcade
            or self.version
            or self.revision
            or self.prerelease
            or self.demo
            or self.date
            or self.alternate
            or self.switch
            or self.steam
            or self.virtual_console
            or self.classic_mini
            or self.nintendo_power
        )

    def __str__(self) -> str:
        output: list[str] = []
        if self.arcade:
            output.append("(Arcade)")
        if self.version:
            output.append(f"v{self.version}")
        if self.revision:
            if not self.revision[0].isdigit():
                output.append(f"Rev {self.revision}")
            else:
                output.append(f"r{self.revision}")
        if self.prerelease:
            output.append(f"[{self.prerelease}]")
        if self.demo:
            output.append(f"[{self.demo}]")
        if self.date:
            output.append(f"({self.date})")
        if self.alternate:
            if self.alternate > 1:
                output.append(f"(Alt {self.alternate})")
            else:
                output.append("(Alt)")
        if self.switch:
            output.append("(Switch)")
        if self.steam:
            output.append("(Steam)")
        if self.virtual_console:
            output.append("(Virtual Console)")
        if self.classic_mini:
            output.append("(Classic Mini)")
        if self.nintendo_power:
            output.append("(Nintendo Power)")
        return " ".join(output)


@dataclass(frozen=True, eq=True, order=True)
class Disc:
    name: str = ""
    number: int | None = None

    def __bool__(self) -> bool:
        return bool(self.name or self.number)

    def __str__(self) -> str:
        output: list[str] = []
        if self.name:
            output.append(self.name)
        if self.number:
            output.append(f"Disc {self.number}")
        if output:
            if len(output) == 1:
                return output[0]
            return f"({", ".join(output)})"
        return ""


@dataclass(frozen=True, eq=True, order=True)
class Variation:
    title: str = ""
    edition: Edition = field(default_factory=Edition)
    disc: Disc = field(default_factory=Disc)

    def __bool__(self) -> bool:
        return bool(self.title or self.edition or self.disc)

    def __str__(self) -> str:
        output: list[str] = []
        if self.title:
            output.append(self.title)
        if self.edition:
            output.append(str(self.edition))
        if self.disc:
            output.append(str(self.disc))
        return " ".join(output)


@dataclass(frozen=True, eq=True, order=True)
class Localization:
    _sort_key: tuple[int, tuple[Region, ...], tuple[Language, ...]] = field(
        init=False, compare=True, repr=False
    )
    regions: frozenset[Region] = field(
        default_factory=frozenset, compare=False
    )
    languages: frozenset[Language] = field(
        default_factory=frozenset, compare=False
    )

    def __post_init__(self) -> None:
        sort_key: tuple[int, tuple[Region, ...], tuple[Language, ...]] = (
            self.english_priority(),
            tuple(sorted(self.regions)),
            tuple(sorted(self.languages)),
        )
        # because frozen=True
        object.__setattr__(self, "_sort_key", sort_key)

    def __bool__(self) -> bool:
        return bool(self.regions or self.languages)

    def english_priority(self) -> int:
        is_american_english = Language.AMERICAN_ENGLISH in self.languages
        is_english = Language.ENGLISH in self.languages
        is_british_english = Language.BRITISH_ENGLISH in self.languages
        any_english = is_american_english or is_english or is_british_english
        not_only_nonenglish = not self.languages or any_english
        if Region.USA in self.regions and not_only_nonenglish:
            return 1
        if is_american_english:
            return 2
        if is_english:
            return 3
        if is_british_english:
            return 4
        if not_only_nonenglish:
            if Region.CANADA in self.regions:
                return 5
            if Region.UNITED_KINGDOM in self.regions:
                return 6
            if Region.AUSTRALIA in self.regions:
                return 7
            if Region.NEW_ZEALAND in self.regions:
                return 8
        return 0

    def __str__(self) -> str:
        output: list[str] = []
        if self.regions:
            output.append(
                "["
                + ", ".join(sorted(region.value for region in self.regions))
                + "]"
            )
        if self.languages:
            output.append(
                "["
                + ", ".join(
                    sorted(language.value for language in self.languages)
                )
                + "]"
            )
        if output:
            return " ".join(output)
        return "Unlocalized"


@dataclass(frozen=True, eq=True, order=True)
class Tags:
    _sort_key: tuple[str, ...] = field(init=False, compare=True, repr=False)
    values: frozenset[str] = field(default_factory=frozenset, compare=False)

    def __post_init__(self) -> None:
        sort_key: tuple[str, ...] = tuple(sorted(self.values))
        # because frozen=True
        object.__setattr__(self, "_sort_key", sort_key)

    def __bool__(self) -> bool:
        return bool(self.values)

    def __str__(self) -> str:
        if self.values:
            return " ".join(f"[{value}]" for value in self.values)
        return "Untagged"


@dataclass
class Metadata:
    stem: str
    variation: Variation = field(default_factory=Variation)
    unhandled_tags: Tags = field(default_factory=Tags)
    localization: Localization = field(default_factory=Localization)
    unlicensed: bool = False
    bad_dump: bool = False
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
        date = Date(None)
        disc_number: int | None = None
        disc_name: str = ""
        japanese_number: int | None = None
        version: str | None = None
        revision: str | None = None
        prerelease: str = ""
        arcade: bool = False
        switch: bool = False
        steam: bool = False
        virtual_console: bool = False
        classic_mini: bool = False
        nintendo_power: bool = False
        demo: str = ""
        unlicensed = False
        alternate: int = 0
        bad_dump = False
        unhandles_tag_values: list[str] = []
        for tag in stem_info.tags:
            lower_tag = tag.lower()
            ###################################################
            if _DEMO_PATTERN.fullmatch(tag):
                if demo:
                    raise ValueError(f"Parsed multiple demo tags: {stem}")
                demo = tag  # NOTE: match has groups we aren't using
            elif lower_tag in ["arcade"]:
                if arcade:
                    raise ValueError(f"Parsed multiple arcade tags: {stem}")
                arcade = True
            elif lower_tag in ["switch", "switch online"]:
                if switch:
                    raise ValueError(f"Parsed multiple switch tags: {stem}")
                switch = True
            elif lower_tag in ["steam"]:
                if steam:
                    raise ValueError(f"Parsed multiple steam tags: {stem}")
                steam = True
            elif lower_tag in ["virtual console"]:
                if virtual_console:
                    raise ValueError(
                        f"Parsed multiple virtual console tags: {stem}"
                    )
                virtual_console = True
            elif lower_tag in ["classic mini"]:
                if classic_mini:
                    raise ValueError(
                        f"Parsed multiple classic mini tags: {stem}"
                    )
                classic_mini = True
            elif lower_tag in ["np"]:
                if nintendo_power:
                    raise ValueError(f"Parsed multiple np tags: {stem}")
                nintendo_power = True
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
                if date:
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
                if disc_number is not None:
                    raise ValueError(f"Parsed multiple discs: {stem}")
                disc_str = disc_match.group("disc")
                try:
                    disc_number = _EARLY_ROMAN_NUMERALS.index(disc_str) + 1
                except ValueError:
                    try:
                        disc_number = int(disc_str)
                    except ValueError:
                        disc_number = ord(disc_str.lower()) - ord("a")
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
                    raise RuntimeError("Received blank tag; debug things!")
                unhandles_tag_values.append(tag)
        if (
            disc_number is not None
            and japanese_number is not None
            and disc_number != japanese_number
        ):
            raise ValueError(f"Got different disc index and jp number: {stem}")

        return Metadata(
            stem=stem,
            unhandled_tags=Tags(values=frozenset(unhandles_tag_values)),
            localization=Localization(
                regions=frozenset(regions), languages=frozenset(languages)
            ),
            variation=Variation(
                title=stem_info.title,
                edition=Edition(
                    arcade=arcade,
                    version=version or "",
                    revision=revision or "",
                    date=date,
                    prerelease=prerelease,
                    demo=demo,
                    alternate=alternate,
                    switch=switch,
                    steam=steam,
                    virtual_console=virtual_console,
                    classic_mini=classic_mini,
                    nintendo_power=nintendo_power,
                ),
                disc=Disc(name=disc_name, number=disc_number),
            ),
            unlicensed=unlicensed,
            bad_dump=bad_dump,
            category=category,  # just forwarded, not determined
        )

    @staticmethod
    def from_path(path: Path, *, category: str | None = None) -> Metadata:
        return Metadata.from_stem(path.stem, category=category)

    def __str__(self) -> str:
        return f"{repr(self.variation.title)}, {repr(self.unhandled_tags)}"
