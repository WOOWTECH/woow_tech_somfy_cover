"""zh-Hant translations stay complete (commercial acceptance INFRA-HA-009-3).

The 'Add integration' dialog showed English to zh-Hant users because no
zh-Hant file existed. Each zh-Hant file must mirror the keys of its English
counterpart and translate every leaf whose English text contains a word.

Run: python -m pytest tests  (stdlib + pytest only)
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

TRANSLATIONS = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "woow_tech_somfy_cover"
    / "translations"
)
ENGLISH_WORD = re.compile(r"[A-Za-z]{3,}")
CJK = re.compile(r"[㐀-鿿]")


def _leaves(node: object, prefix: str = "") -> dict[str, str]:
    if isinstance(node, dict):
        out: dict[str, str] = {}
        for key, value in node.items():
            out.update(_leaves(value, f"{prefix}{key}."))
        return out
    return {prefix[:-1]: node} if isinstance(node, str) else {}


def _load(name: str) -> dict[str, str]:
    return _leaves(json.loads((TRANSLATIONS / name).read_text(encoding="utf-8")))


@pytest.mark.parametrize("stem", [""])
def test_zh_hant_mirrors_english_keys(stem: str) -> None:
    english = _load(f"{stem}en.json")
    chinese = _load(f"{stem}zh-Hant.json")
    assert set(chinese) == set(english)


@pytest.mark.parametrize("stem", [""])
def test_zh_hant_translates_every_english_sentence(stem: str) -> None:
    english = _load(f"{stem}en.json")
    chinese = _load(f"{stem}zh-Hant.json")
    untranslated = sorted(
        key
        for key, text in english.items()
        if ENGLISH_WORD.search(re.sub(r"\{\w+\}", "", text))
        and not CJK.search(chinese.get(key, ""))
    )
    assert not untranslated


@pytest.mark.parametrize("stem", [""])
def test_zh_hant_keeps_every_placeholder(stem: str) -> None:
    english = _load(f"{stem}en.json")
    chinese = _load(f"{stem}zh-Hant.json")
    for key, text in english.items():
        assert set(re.findall(r"\{\w+\}", chinese.get(key, ""))) == set(
            re.findall(r"\{\w+\}", text)
        ), key
