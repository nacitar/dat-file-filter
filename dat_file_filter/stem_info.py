from __future__ import annotations

from dataclasses import dataclass, field
from itertools import chain
from pathlib import Path
from re import Pattern, compile
from typing import ClassVar


@dataclass
class StemInfo:
    title: str
    tags: list[str] = field(default_factory=list)

    _OPEN_TO_CLOSE: ClassVar[dict[str, str]] = {"[": "]", "(": ")"}
    _TOKEN_RE: ClassVar[Pattern[str]] = compile(
        r" *((?P<open>O)|(?P<close>C)) *| +".replace(r" ", r"[\s_]")
        # uses negative lookahead to exclude the kaomoji "(^^;"
        .replace(r"O", r"\[|\((?!\^\^;)").replace(r"C", r"[)\]]")
    )
    _TAG_COMMA_RE: ClassVar[Pattern[str]] = compile(r" *[,\+] *")

    @staticmethod
    def from_stem(stem: str) -> StemInfo:
        last_end = 0
        in_open_tag: str | None = None
        title_parts: list[str] = []
        tag_parts: list[str] = []
        tags: list[str] = []
        for match in chain(StemInfo._TOKEN_RE.finditer(stem), [None]):
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
                    if symbol != StemInfo._OPEN_TO_CLOSE[in_open_tag]:
                        raise ValueError(f"mismatched close tag: {stem}")
                    in_open_tag = None
                    if tag_parts:
                        # tags.append(" ".join(tag_parts))
                        full_tag = " ".join(tag_parts)
                        for tag in StemInfo._TAG_COMMA_RE.split(full_tag):
                            if tag:
                                tags.append(tag)
                        tag_parts = []
                last_end = match.end()
            elif in_open_tag:
                raise ValueError(f"unterminated group: {stem}")
        return StemInfo(title=" ".join(title_parts), tags=tags)

    @staticmethod
    def from_path(path: Path) -> StemInfo:
        return StemInfo.from_stem(path.stem)
