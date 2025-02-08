from __future__ import annotations

import datetime
import re
from dataclasses import dataclass, field
from enum import StrEnum, unique
from pathlib import Path
from re import Match, Pattern
from typing import Callable, ClassVar, Generic, Sequence, TypeVar

from .stem_info import StemInfo

T = TypeVar("T", bound=object)  # T is non-none


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


def tag_list_pattern(
    tags: Sequence[str], *, case_insensitive: bool = True
) -> Pattern[str]:
    return re.compile(
        "|".join(re.escape(tag) for tag in tags),
        re.IGNORECASE if case_insensitive else 0,
    )


@dataclass
class BaseTagMatcher(Generic[T]):
    pattern: re.Pattern[str]
    extractor: Callable[[Match[str]], T]
    value: T = field(init=False)

    def __post_init__(self) -> None:
        """Initialize value safely in subclasses."""
        if not hasattr(self, "value"):
            raise NotImplementedError(
                "Subclasses must define a default value for 'value'."
            )

    def __call__(self, tag: str) -> bool:
        if match := self.pattern.fullmatch(tag):
            if self.value:
                raise ValueError(f"Processed multiple '{tag}' equivalent tags")
            self.value = self.extractor(match)
            return True
        return False

    def __bool__(self) -> bool:
        return bool(self.value)

class TagPresenceMatcher:
    def __init__(
        self,
        tag_names: list[str],
        *,
        case_sensitive: bool = False,
        allow_multiple: bool = False,
    ):
        self.case_sensitive = case_sensitive
        self.allow_multiple = allow_multiple
        self.tag_names = {
            tag.lower() if not self.case_sensitive else tag
            for tag in tag_names
            if tag  # Filters out empty strings
        }
        if not self.tag_names:
            raise ValueError("No non-empty tag names specified.")
        self.clear()

    def clear(self) -> None:
        self.present = False

    def __call__(self, tag: str) -> bool:
        if tag in self.tag_names:
            if not self.allow_multiple and self.present:
                raise ValueError(
                    f"Processed multiple tags from list: {self.tag_names}"
                )
            self.present = True
            return True
        return False

    def __bool__(self) -> bool:
        return self.present


@dataclass
class StrTagMatcher(BaseTagMatcher[str]):
    extractor: Callable[[Match[str]], str] = lambda match: match.string
    value: str = ""


@dataclass
class IntTagMatcher(BaseTagMatcher[int]):
    extractor: Callable[[Match[str]], int] = lambda match: int(match.string)
    value: int = 0


@dataclass
class DateTagMatcher(BaseTagMatcher[Date]):
    pattern: re.Pattern[str] = re.compile(
        (
            r"(?P<year>\d{4})"
            r"([-.](?P<month>\d{1,2}|XX)"
            r"([-.](?P<day>\d{1,2}|XX))?)?"
        ),
        re.IGNORECASE,
    )

    extractor: Callable[[Match[str]], Date] = lambda match: Date(
        datetime.date(
            int(match.group("year")),
            int(m) if (m := match.group("month")).lower() != "xx" else 1,
            int(d) if (d := match.group("day")).lower() != "xx" else 1,
        )
    )
    value: Date = Date(None)


# TODO: combine disk name/number formats
# <name> disc <number>
# <cd> <name>
# <name> disc
# TODO: allow matching from lists of tags without regex
def parse_disc_number(number_str: str) -> int:
    number = 0
    try:
        number = _EARLY_ROMAN_NUMERALS.index(number_str) + 1
    except ValueError:
        try:
            number = int(number_str)
        except ValueError:
            if len(number_str) == 1 and number_str.isalpha():
                number = ord(number_str.lower()) - ord("a")
            else:
                for index in range(len(_EARLY_JAPANESE_NUMBERS)):
                    if number_str in _EARLY_JAPANESE_NUMBERS[index]:
                        number = index + 1
                        break
    return number


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
        disc_number: int | None = None
        japanese_number: int | None = None
        version: str | None = None
        revision: str | None = None
        unhandled_tag_values: list[str] = []

        TAG_MATCHERS: list[Callable[[str], bool]] = [
            # disc_number_matcher := IntTagMatcher(_DISC_PATTERN,
            demo_matcher := StrTagMatcher(_DEMO_PATTERN),
            arcade_matcher := TagPresenceMatcher(["arcade"]),
            switch_matcher := TagPresenceMatcher(["switch", "switch online"]),
            steam_matcher := TagPresenceMatcher(["steam"]),
            virtual_console_matcher := TagPresenceMatcher(["virtual console"]),
            classic_mini_matcher := TagPresenceMatcher(["classic mini"]),
            nintendo_power_matcher := TagPresenceMatcher(["np"]),
            unlicensed_matcher := TagPresenceMatcher(["unl", "unlicensed"]),
            bad_dump_matcher := TagPresenceMatcher(["b"]),
            alternate_matcher := IntTagMatcher(
                _ALTERNATE_PATTERN,
                lambda match: int(match.group("index") or 1),
            ),
            disc_name_matcher := StrTagMatcher(
                _DISC_NAME_PATTERN,
                lambda match: match.group("name1") or match.group("name2"),
            ),
            date_matcher := DateTagMatcher(),
            prerelease_matcher := StrTagMatcher(_PRERELEASE_PATTERN),  # group?
        ]
        matched = False
        for tag in stem_info.tags:
            ###################################################
            for matcher in TAG_MATCHERS:
                if matcher(tag):
                    matched = True
                    break
            ###################################################
            if matched:
                continue
            if version_match := _VERSION_PATTERN.fullmatch(tag):
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
                unhandled_tag_values.append(tag)
        if (
            disc_number is not None
            and japanese_number is not None
            and disc_number != japanese_number
        ):
            raise ValueError(f"Got different disc index and jp number: {stem}")

        return Metadata(
            stem=stem,
            unhandled_tags=Tags(values=frozenset(unhandled_tag_values)),
            localization=Localization(
                regions=frozenset(regions), languages=frozenset(languages)
            ),
            variation=Variation(
                title=stem_info.title,
                edition=Edition(
                    arcade=bool(arcade_matcher),
                    version=version or "",
                    revision=revision or "",
                    date=date_matcher.value,
                    prerelease=prerelease_matcher.value,
                    demo=demo_matcher.value,
                    alternate=alternate_matcher.value,
                    switch=bool(switch_matcher),
                    steam=bool(steam_matcher),
                    virtual_console=bool(virtual_console_matcher),
                    classic_mini=bool(classic_mini_matcher),
                    nintendo_power=bool(nintendo_power_matcher),
                ),
                disc=Disc(name=disc_name_matcher.value, number=disc_number),
            ),
            unlicensed=bool(unlicensed_matcher),
            bad_dump=bool(bad_dump_matcher),
            category=category,  # just forwarded, not determined
        )

    @staticmethod
    def from_path(path: Path, *, category: str | None = None) -> Metadata:
        return Metadata.from_stem(path.stem, category=category)

    def __str__(self) -> str:
        return f"{repr(self.variation.title)}, {repr(self.unhandled_tags)}"
