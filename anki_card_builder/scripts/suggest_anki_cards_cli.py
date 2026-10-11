import argparse
import collections.abc
import enum
import string
import typing

import pydantic

from scripts.azure_translator import fetch_dictionary_translations
from scripts.shared import (
    CATEGORY_TO_FORMAT,
    TRANSLATION_SEPARATOR,
    AnkiCard,
    CardCategory,
)


class _Command(enum.Enum):
    LIST = "list"
    BUILD = "build"
    LOOKUP = "lookup"


class _DraftCard(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")
    category: CardCategory
    front: str
    back: str


def _print_suggestible_categories() -> None:
    print(f"Translation separator: {TRANSLATION_SEPARATOR!r}")
    for category, card_format in CATEGORY_TO_FORMAT.items():
        if category is not CardCategory.ENG_TO_DEU:
            print(f"{category}\t{card_format.template}\te.g. {card_format.example}")


def _validate_back_separators(*, draft: _DraftCard) -> None:
    _, back_template = CATEGORY_TO_FORMAT[draft.category].template.split(";")
    separators = [
        literal
        for literal, _field, _spec, _conversion in string.Formatter().parse(
            back_template
        )
        if literal.strip()
    ]
    for separator in separators:
        if draft.back.count(separator) != back_template.count(separator):
            raise ValueError("separator count mismatch", separator, draft.back)


def _print_validated_rows(*, drafts_json: str) -> None:
    drafts = pydantic.TypeAdapter(list[_DraftCard]).validate_json(drafts_json)
    for draft in drafts:
        _validate_back_separators(draft=draft)
        card = AnkiCard(front=f"{draft.category}: {draft.front}", back=draft.back)
        print(f"{card.category}\t{card.front_without_category}\t{card.back}")


def _print_translation_suggestions(
    *, german_words: collections.abc.Collection[str]
) -> None:
    translations_by_word = fetch_dictionary_translations(german_words=german_words)
    for word, translations in translations_by_word.items():
        for translation in translations:
            back_translations = ", ".join(
                f"{back.display_text} ({back.frequency_count})"
                for back in translation.back_translations
            )
            print(
                f"{word}\t{translation.display_target}\t{translation.pos_tag}"
                f"\t{translation.confidence}\t{back_translations}"
            )


def _dispatch_command_from_cli() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "`list`: print the translation separator and the suggestible "
            "categories with their `front;back` format and an example card. "
            '`build JSON`: take a JSON list of {"category", "front", "back"}, '
            "shaped like each category's example, validate each card and print it "
            "as a tab-separated Google Sheets row. "
            "`lookup WORD...`: print Azure dictionary translations per German word "
            "with part of speech, confidence and back-translations (needs the "
            "variables from `.env`)."
        )
    )
    parser.add_argument("command", choices=[command.value for command in _Command])
    parser.add_argument("inputs", nargs="*")
    arguments = parser.parse_args()
    match _Command(arguments.command):
        case _Command.LIST:
            _print_suggestible_categories()
        case _Command.BUILD:
            (drafts_json,) = arguments.inputs
            _print_validated_rows(drafts_json=drafts_json)
        case _Command.LOOKUP:
            _print_translation_suggestions(german_words=arguments.inputs)
        case unreachable:
            typing.assert_never(unreachable)


if __name__ == "__main__":
    _dispatch_command_from_cli()
