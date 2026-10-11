import argparse
import enum
import string
import sys
import typing

import pydantic

from scripts.shared import (
    CATEGORY_TO_FORMAT,
    TRANSLATION_SEPARATOR,
    AnkiCard,
    CardCategory,
)


class _Command(enum.Enum):
    LIST = "list"
    BUILD = "build"


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


def _print_validated_rows() -> None:
    drafts = pydantic.TypeAdapter(list[_DraftCard]).validate_json(sys.stdin.read())
    for draft in drafts:
        _validate_back_separators(draft=draft)
        card = AnkiCard(front=f"{draft.category}: {draft.front}", back=draft.back)
        print(f"{card.category}\t{card.front_without_category}\t{card.back}")


def _dispatch_command_from_cli() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "`list`: print the translation separator and the suggestible "
            "categories with their `front;back` format and an example card. "
            '`build`: read a JSON list of {"category", "front", "back"} from stdin, '
            "shaped like each category's example, validate each card and print it "
            "as a tab-separated Google Sheets row."
        )
    )
    parser.add_argument("command", choices=[command.value for command in _Command])
    match _Command(parser.parse_args().command):
        case _Command.LIST:
            _print_suggestible_categories()
        case _Command.BUILD:
            _print_validated_rows()
        case unreachable:
            typing.assert_never(unreachable)


if __name__ == "__main__":
    _dispatch_command_from_cli()
