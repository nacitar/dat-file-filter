from __future__ import annotations

import datetime
import re
from dataclasses import KW_ONLY, dataclass, field
from enum import StrEnum, unique
from pathlib import Path
from re import Match, Pattern
from typing import Callable, ClassVar

from .stem_info import StemInfo


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
    ISRAEL = "Israel"
    IRELAND = "Ireland"
    SCANDINAVIA = "Scandinavia"
    LATIN_AMERICA = "Latin America"
    TAIWAN = "Taiwan"
    BRAZIL = "Brazil"
    PORTUGAL = "Portugal"
    FRANCH = "France"
    GREECE = "Greece"
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
    early: str = ""
    debug: bool = False
    date: Date = field(default_factory=lambda: Date(None))
    alternate: int = 0
    wii: bool = False
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
            or self.early
            or self.debug
            or self.date
            or self.alternate
            or self.wii
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
        if self.early:
            output.append(f"[{self.early}]")
        if self.debug:
            output.append("[Debug]")
        if self.date:
            output.append(f"({self.date})")
        if self.alternate:
            if self.alternate > 1:
                output.append(f"(Alt {self.alternate})")
            else:
                output.append("(Alt)")
        if self.wii:
            output.append("(Wii)")
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
            return f"({", ".join(output)})"
        return ""


@dataclass(frozen=True, eq=True, order=True)
class Variation:
    edition: Edition = field(default_factory=Edition)
    disc: Disc = field(default_factory=Disc)

    def __bool__(self) -> bool:
        return bool(self.edition or self.disc)

    def __str__(self) -> str:
        output: list[str] = []
        if self.edition:
            output.append(str(self.edition))
        if self.disc:
            output.append(str(self.disc))
        if output:
            return " ".join(output)
        return "<Release>"


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
            if Region.EUROPE in self.regions:
                return 9
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
        return "<Unlocalized>"


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
        return "<Untagged>"


# TODO: maybe make a new class that lets you have a list of TagMatchers
# in order to independently process things, perhaps with different extractors
@dataclass
class TagMatcher:
    parser: Callable[[str], str]
    value: str = ""
    _: KW_ONLY
    allow_duplicates: bool = False

    def __call__(self, tag: str) -> bool:
        if value := self.parser(tag):
            if self.value:
                if not self.allow_duplicates:
                    raise ValueError(f'Multiple "{tag}" equivalent tags')
                elif value != self.value:
                    raise ValueError(
                        f'Multiple "{tag}" equivalent tags (allowed), but'
                        " conflicting values encountered:"
                        f' "{self.value}" != "{value}"'
                    )
            self.value = value
            return True
        return False

    def __bool__(self) -> bool:
        return bool(self.value)

    def __str__(self) -> str:
        return self.value

    def __int__(self) -> int:
        return int(self.value or 0)


def FULL_TAG_EXTRACTOR(match: Match[str]) -> str:
    return match.string


@dataclass
class PatternParser:
    pattern: re.Pattern[str]
    extractor: Callable[[Match[str]], str] = FULL_TAG_EXTRACTOR

    def matcher(self, *, allow_duplicates: bool = False) -> TagMatcher:
        return TagMatcher(self, allow_duplicates=allow_duplicates)

    @classmethod
    def from_tags(
        cls,
        tags: list[str],
        extractor: Callable[[Match[str]], str] = FULL_TAG_EXTRACTOR,
        *,
        case_sensitive: bool = False,
    ) -> PatternParser:
        return cls(
            re.compile(
                "|".join(re.escape(tag) for tag in tags),
                0 if case_sensitive else re.IGNORECASE,
            ),
            extractor,
        )

    def __call__(self, tag: str) -> str:
        if match := self.pattern.fullmatch(tag):
            return self.extractor(match)
        return ""


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
_ROMAN_OR_JAPANESE_NUMBERS = (
    "|".join(_EARLY_ROMAN_NUMERALS)
    + "|"
    + "|".join(
        [
            re.escape(item)
            for sublist in _EARLY_JAPANESE_NUMBERS
            for item in sublist
        ]
    )
)


def disc_number_to_int(number: str) -> str:
    if number.isdigit():
        return number
    try:
        # check before alpha due to single-character roman numerals
        # must be uppercase already to be a roman numeral
        return str(_EARLY_ROMAN_NUMERALS.index(number) + 1)
    except ValueError:
        pass
    number = number.lower()
    if len(number) == 1 and number.isalpha():
        return str(ord(number.lower()) - ord("a"))
    for index in range(len(_EARLY_JAPANESE_NUMBERS)):
        if number in _EARLY_JAPANESE_NUMBERS[index]:
            return str(index + 1)
    return ""


DISC_NUMBER_PARSER = PatternParser(
    re.compile(
        r"cd (?P<name1>.+)|(?P<name2>.+)-hen|"  # -hen is Jp for "chapter"
        r"((?P<name3>.+) )?dis[ck]( (?P<number1>\d+|[A-Z]|"
        + _ROMAN_OR_JAPANESE_NUMBERS
        + rf"))?|(?P<number2>{_ROMAN_OR_JAPANESE_NUMBERS})",
        re.IGNORECASE,
    ),
    lambda match: disc_number_to_int(
        match.group("number1") or match.group("number2") or ""
    ),
)
DISC_NAME_PARSER = PatternParser(
    DISC_NUMBER_PARSER.pattern,
    lambda match: (
        match.group("name1")
        or match.group("name2")
        or match.group("name3")
        or ""
    ),
)
DEMO_PARSER = PatternParser(
    re.compile(
        r"(?P<name>(tech )?demo|(playable game )?preview( edition by .+)?"
        r"|.+ previews"  # Square Soft on PlayStation Previews
        r"|(taikenban )?sample( rom)?|(?P<trial>([^\s]+ )+)?trial)"
        r"( ((?P<iteration>\d+)|edition|version))?",
        re.IGNORECASE,
    )  # not using groups
)

EARLY_PARSER = PatternParser.from_tags(["early", "earlier"])
ARCADE_PARSER = PatternParser.from_tags(["arcade"])
WII_PARSER = PatternParser.from_tags(["wii"])
SWITCH_PARSER = PatternParser.from_tags(["switch", "switch online"])
STEAM_PARSER = PatternParser.from_tags(["steam"])
VIRTUAL_CONSOLE_PARSER = PatternParser.from_tags(["virtual console"])
CLASSIC_MINI_PARSER = PatternParser.from_tags(["classic mini"])
NINTENDO_POWER_PARSER = PatternParser.from_tags(["np"])
UNLICENSED_PARSER = PatternParser.from_tags(["unl", "unlicensed"])
BAD_DUMP_PARSER = PatternParser.from_tags(["b"])
DEBUG_PARSER = PatternParser.from_tags(["debug"])
ALTERNATE_PARSER = PatternParser(
    re.compile(r"alt( (?P<index>\d+))?", re.IGNORECASE),
    lambda match: match.group("index") or "1",
)
PRERELEASE_PARSER = PatternParser(
    re.compile(
        r"(?P<name>alpha|beta|([^\s]+ )?promo|(possible )?proto(type)?)"
        r"( (?P<iteration>\d+))?",
        re.IGNORECASE,
    )  # TODO: groups?
)
DATE_PARSER = PatternParser(
    re.compile(
        r"(?P<year>\d{4})"
        r"([-.](?P<month>\d{1,2}|XX)"
        r"([-.](?P<day>\d{1,2}|XX))?)?",
        re.IGNORECASE,
    ),
    lambda match: datetime.date(
        int(match.group("year")),
        int(m) if (m := match.group("month")).lower() != "xx" else 1,
        int(d) if (d := match.group("day")).lower() != "xx" else 1,
    ).isoformat(),
)
REVISION_PARSER = PatternParser(
    re.compile(r"((Rev|Revision) |r)(?P<revision>[a-f0-9.]+)", re.IGNORECASE),
    lambda match: match.group("revision"),
)

VERSION_PARSER = PatternParser(
    re.compile(
        r"((?P<prefix>v|Ver|Version )(?P<value>[a-f0-9.]+))"
        r"|(?P<version>\.?(\d|[a-f]\d[^\s]*\d)[^\s]*)",
        re.IGNORECASE,
    ),
    lambda match: (
        match.group("value")
        if match.group("prefix")
        else match.group("version")
    ),
)


@dataclass(frozen=True, eq=True, order=True)
class Entity:
    variation: Variation = field(default_factory=Variation)
    unhandled_tags: Tags = field(default_factory=Tags)

    def __bool__(self) -> bool:
        return bool(self.variation or self.unhandled_tags)

    def __str__(self) -> str:
        output: list[str] = []
        output.append(str(self.variation))
        if self.unhandled_tags:
            output.append(str(self.unhandled_tags))
        return " ".join(output)


@dataclass(frozen=True, eq=True, order=True)
class Unit:
    title: str = ""
    entity: Entity = field(default_factory=Entity)
    localization: Localization = field(default_factory=Localization)

    def __bool__(self) -> bool:
        return bool(self.title or self.entity or self.localization)

    def __str__(self) -> str:
        output: list[str] = []
        if self.title:
            output.append(self.title)
        if self.entity:
            output.append(str(self.entity))
        if self.localization:
            output.append(str(self.localization))
        return " ".join(output)


@dataclass(frozen=True, eq=True, order=True)
class Metadata:
    unit: Unit = field(default_factory=Unit)
    unlicensed: bool = False
    bad_dump: bool = False
    category: str | None = None
    stem: str = ""
    id: str = ""
    cloneofid: str = ""

    _TAG_COMMA_RE: ClassVar[Pattern[str]] = re.compile(r" *[,\+] *")

    _LANGUAGE_LOOKUP: ClassVar[dict[str, Language]] = {
        member.value: member for member in Language
    }
    _REGION_LOOKUP: ClassVar[dict[str, Region]] = {
        member.value: member for member in Region
    }

    @staticmethod
    def from_stem(
        stem: str,
        *,
        category: str | None = None,
        id: str = "",
        cloneofid: str = "",
    ) -> Metadata:
        stem_info = StemInfo.from_stem(stem)
        languages: set[Language] = set()
        regions: set[Region] = set()
        unhandled_tag_values: list[str] = []
        # If any top-level entry matches, processing concludes for a given tag.
        # For entries that are lists, all of the matchers will be tried even
        # even if an earlier member of the list matches, but subsequent
        # top-level entries won't be processed.This allows multiple matchers
        # to match a given tag, provided they are grouped together in a list.
        TAG_MATCHERS: list[
            Callable[[str], bool] | list[Callable[[str], bool]]
        ] = [
            [
                disc_name_matcher := DISC_NAME_PARSER.matcher(),
                disc_number_matcher := DISC_NUMBER_PARSER.matcher(
                    allow_duplicates=True
                ),
            ],
            demo_matcher := DEMO_PARSER.matcher(),
            early_matcher := EARLY_PARSER.matcher(),
            debug_matcher := DEBUG_PARSER.matcher(),
            arcade_matcher := ARCADE_PARSER.matcher(),
            wii_matcher := WII_PARSER.matcher(),
            switch_matcher := SWITCH_PARSER.matcher(),
            steam_matcher := STEAM_PARSER.matcher(),
            virtual_console_matcher := VIRTUAL_CONSOLE_PARSER.matcher(),
            classic_mini_matcher := CLASSIC_MINI_PARSER.matcher(),
            nintendo_power_matcher := NINTENDO_POWER_PARSER.matcher(),
            unlicensed_matcher := UNLICENSED_PARSER.matcher(),
            bad_dump_matcher := BAD_DUMP_PARSER.matcher(),
            alternate_matcher := ALTERNATE_PARSER.matcher(),
            date_matcher := DATE_PARSER.matcher(),
            prerelease_matcher := PRERELEASE_PARSER.matcher(),
            revision_matcher := REVISION_PARSER.matcher(),
            version_matcher := VERSION_PARSER.matcher(),
        ]
        for tag in stem_info.tags:
            matched = False
            for matcher_group in TAG_MATCHERS:
                if not isinstance(matcher_group, list):
                    matcher_group = [matcher_group]
                for matcher in matcher_group:
                    if matcher(tag):
                        matched = True
                if matched:
                    break
            if matched:
                continue
            elif language := Metadata._LANGUAGE_LOOKUP.get(tag):
                languages.add(language)
            elif region := Metadata._REGION_LOOKUP.get(tag):
                regions.add(region)
            else:
                if not tag:
                    raise RuntimeError("Received blank tag; debug things!")
                unhandled_tag_values.append(tag)

        return Metadata(
            unit=Unit(
                title=stem_info.title,
                entity=Entity(
                    variation=Variation(
                        edition=Edition(
                            arcade=bool(arcade_matcher),
                            version=str(version_matcher),
                            revision=str(revision_matcher),
                            date=Date(
                                datetime.date.fromisoformat(str(date_matcher))
                                if date_matcher
                                else None
                            ),
                            prerelease=str(prerelease_matcher),
                            demo=str(demo_matcher),
                            early=str(early_matcher),
                            debug=bool(debug_matcher),
                            alternate=int(alternate_matcher),
                            wii=bool(wii_matcher),
                            switch=bool(switch_matcher),
                            steam=bool(steam_matcher),
                            virtual_console=bool(virtual_console_matcher),
                            classic_mini=bool(classic_mini_matcher),
                            nintendo_power=bool(nintendo_power_matcher),
                        ),
                        disc=Disc(
                            name=str(disc_name_matcher),
                            number=int(disc_number_matcher),
                        ),
                    ),
                    unhandled_tags=Tags(
                        values=frozenset(unhandled_tag_values)
                    ),
                ),
                localization=Localization(
                    regions=frozenset(regions), languages=frozenset(languages)
                ),
            ),
            stem=stem,
            unlicensed=bool(unlicensed_matcher),
            bad_dump=bool(bad_dump_matcher),
            category=category,  # just forwarded, not determined
        )

    @staticmethod
    def from_path(
        path: Path,
        *,
        category: str | None = None,
        id: str = "",
        cloneofid: str = "",
    ) -> Metadata:
        return Metadata.from_stem(
            path.stem, category=category, id=id, cloneofid=cloneofid
        )

    def __str__(self) -> str:
        return str(self.unit)
