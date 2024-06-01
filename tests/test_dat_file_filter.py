from dat_file_filter import __version__
from dat_file_filter.stem_info import StemInfo


def test_version() -> None:
    assert __version__ == "0.1.0"


def test_stem_info() -> None:
    # basic parsing + space preservation mid-tag
    assert StemInfo.from_stem("Some Game (En,Fr,Sp) (Jp, Ko, Ch)") == StemInfo(
        "Some Game", tags=["En", "Fr", "Sp", "Jp", "Ko", "Ch"]
    )
    # tags act as word separators
    assert StemInfo.from_stem("hello(there)!") == StemInfo(
        "hello !", tags=["there"]
    )
    # punctuation not separated from words
    assert StemInfo.from_stem("hello?") == StemInfo("hello?", tags=[])
    # multiple tag types, outer whitespace trimming
    assert StemInfo.from_stem("(what)open[who]") == StemInfo(
        "open", tags=["what", "who"]
    )
    # tagless
    assert StemInfo.from_stem("I ate a panda") == StemInfo("I ate a panda")
    # outer whitespace and leading/trailing tags
    assert StemInfo.from_stem("(howdy) I ate a panda (partner)") == StemInfo(
        "I ate a panda", tags=["howdy", "partner"]
    )
    # inner whitespace and leading/trailing tags
    assert StemInfo.from_stem(
        "(howdy) I           ate a panda(partner)"
    ) == StemInfo("I ate a panda", tags=["howdy", "partner"])
    # varied spacing around tags, trailing whitespace
    assert StemInfo.from_stem(
        "(howdy) I ate a panda(partner)dude ()  "
    ) == StemInfo("I ate a panda dude", tags=["howdy", "partner"])
    # underscores as spaces
    assert StemInfo.from_stem(
        "____(howdy) ___I__ ate a _panda(partner)dude ()  "
    ) == StemInfo("I ate a panda dude", tags=["howdy", "partner"])
