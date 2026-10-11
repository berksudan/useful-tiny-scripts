import collections
import csv
import dataclasses
import enum
import pathlib
import pprint
import re
import typing

from scripts.shared import TRANSLATION_SEPARATOR, AnkiCard, CardCategory

_INPUT_FILE_DELIMITER = "\t"
_INPUT_FILEPATH = pathlib.Path("input_deck/Deutsche Übung.txt")
_OUTPUT_FILE_DELIMITER = ";"
_OUTPUT_FILEPATH = pathlib.Path("output/upserted_translations.csv")


class _MetadataTag(enum.StrEnum):
    SEPARATOR = "#separator:"
    HTML = "#html:"
    TAGS_COLUMN = "#tags column:"


@dataclasses.dataclass(frozen=True, kw_only=True)
class _TranslationPair:
    deu: str
    eng: str


def _fetch_cards(*, raw_rows: list[list[str]]) -> list[AnkiCard]:
    ignored_row_count = 0
    anki_cards: list[AnkiCard] = []
    html_char_pattern: re.Pattern[str] = re.compile(r"&\w+;")
    for row in raw_rows:
        if not row[-1]:
            row.pop()
        if any(html_char_pattern.search(row_part) for row_part in row):
            raise ValueError(f"[ERROR] HTML character found in `{row=}`")
        row_first_part, *_ = row
        if any(row_first_part.startswith(pref) for pref in _MetadataTag):
            print(f"[WARN] Skipping metadata {row=}")
            ignored_row_count += 1
            continue
        try:
            front, back = row
            anki_card = AnkiCard(front=front, back=back)
        except ValueError as err:
            raise ValueError(f"[ERROR] Validation error in `{row=}`") from err

        anki_cards.append(anki_card)

    print(f"[INFO] Ignored `{ignored_row_count}` rows.")
    print(f"[INFO] Collected `{len(anki_cards)}` cards.")
    anki_card_categories: list[CardCategory] = [ac.category for ac in anki_cards]
    print(f"[INFO] Collected `{len(set(anki_card_categories))}` categories.")
    return anki_cards


def _split_strict(s: str, *, delimiter: str) -> typing.Generator[str]:
    for part in s.split(delimiter):
        if part != part.strip():
            raise ValueError(f"String=`{part}` has leading or trailing whitespace")
        yield part


def _fetch_deu_to_eng_pairs(*, cards: list[AnkiCard]) -> list[_TranslationPair]:
    deu_to_eng_pairs: list[_TranslationPair] = []
    for card in cards:
        match card.category:
            case CardCategory.DEU_TO_ENG:
                deu_word: str = card.front_without_category
                for eng_word in _split_strict(
                    card.back, delimiter=TRANSLATION_SEPARATOR
                ):
                    pair = _TranslationPair(deu=deu_word, eng=eng_word)
                    deu_to_eng_pairs.append(pair)
            case CardCategory.DEU_TO_ENG_ARTIKEL_PLURAL:
                eng_words_part, deu_word, _ = _split_strict(card.back, delimiter=", ")
                for eng_word in _split_strict(
                    eng_words_part, delimiter=TRANSLATION_SEPARATOR
                ):
                    pair = _TranslationPair(deu=deu_word, eng=eng_word)
                    deu_to_eng_pairs.append(pair)
    return deu_to_eng_pairs


def _fetch_eng_to_deu_pairs(*, cards: list[AnkiCard]) -> list[_TranslationPair]:
    eng_to_deu_pairs: list[_TranslationPair] = []
    for card in cards:
        match card.category:
            case CardCategory.ENG_TO_DEU:
                eng_word: str = card.front_without_category
                for deu_word in _split_strict(
                    card.back, delimiter=TRANSLATION_SEPARATOR
                ):
                    pair = _TranslationPair(deu=deu_word, eng=eng_word)
                    eng_to_deu_pairs.append(pair)
    return eng_to_deu_pairs


def _group_pairs_by_eng_word(
    *,
    pairs: list[_TranslationPair],
) -> dict[str, list[_TranslationPair]]:
    pairs_by_eng: dict[str, list[_TranslationPair]] = collections.defaultdict(list)
    for pair in pairs:
        pairs_by_eng[pair.eng].append(pair)
    return pairs_by_eng


def _write_upserted_translation_pairs(
    *,
    output_file_delimiter: str,
    output_filepath: pathlib.Path,
    deu_to_eng_pairs: list[_TranslationPair],
    eng_to_deu_pairs: list[_TranslationPair],
) -> None:
    unique_deu_to_eng_pairs: list[_TranslationPair] = sorted(
        set(deu_to_eng_pairs).difference(eng_to_deu_pairs), key=lambda x: x.eng
    )

    unique_deu_to_eng_pairs_by_eng: dict[str, list[_TranslationPair]] = (
        _group_pairs_by_eng_word(pairs=unique_deu_to_eng_pairs)
    )

    eng_to_eng_deu_pairs: dict[str, list[_TranslationPair]] = _group_pairs_by_eng_word(
        pairs=eng_to_deu_pairs
    )

    if not unique_deu_to_eng_pairs_by_eng:
        print("[INFO] No unique deu_to_eng_pairs found, translations are up-to-date.")
        return

    with output_filepath.open("w", encoding="utf-8") as fp:
        for eng_word, deu_eng_pairs in unique_deu_to_eng_pairs_by_eng.items():
            all_pairs_per_eng_word = deu_eng_pairs + eng_to_eng_deu_pairs.get(
                eng_word, []
            )
            deu_words = TRANSLATION_SEPARATOR.join(
                sorted({pair.deu for pair in all_pairs_per_eng_word})
            )
            fp.write(
                f"{CardCategory.ENG_TO_DEU}: {eng_word}{output_file_delimiter}{deu_words}\n"
            )


def run_deu_to_eng_card_adder() -> None:
    with _INPUT_FILEPATH.open("r", encoding="utf-8") as fp:
        raw_rows = list(csv.reader(fp, delimiter=_INPUT_FILE_DELIMITER))

    anki_cards: list[AnkiCard] = _fetch_cards(raw_rows=raw_rows)
    deu_to_eng_pairs: list[_TranslationPair] = _fetch_deu_to_eng_pairs(cards=anki_cards)
    eng_to_deu_pairs: list[_TranslationPair] = _fetch_eng_to_deu_pairs(cards=anki_cards)

    if eng_to_deu_pairs_unique := set(eng_to_deu_pairs).difference(deu_to_eng_pairs):
        formatted = pprint.pformat(eng_to_deu_pairs_unique)
        raise ValueError(
            f"There are ENG to DEU but not DEU to ENG translations:\n{formatted}"
        )

    _write_upserted_translation_pairs(
        output_file_delimiter=_OUTPUT_FILE_DELIMITER,
        output_filepath=_OUTPUT_FILEPATH,
        deu_to_eng_pairs=deu_to_eng_pairs,
        eng_to_deu_pairs=eng_to_deu_pairs,
    )


if __name__ == "__main__":
    run_deu_to_eng_card_adder()
