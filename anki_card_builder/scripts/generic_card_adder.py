import collections.abc
import dataclasses
import enum
import pathlib
import re
import time

from scripts.shared import CATEGORY_TO_FORMAT, AnkiCard, CardCategory, ColorCode


class _Preposition(enum.StrEnum):
    AN = "AN"
    AUF = "AUF"
    AUS = "AUS"
    BEI = "BEI"
    DURCH = "DURCH"
    FUER = "FÜR"
    GEGEN = "GEGEN"
    MIT = "MIT"
    NACH = "NACH"
    OHNE = "OHNE"
    UM = "UM"
    UNTER = "UNTER"
    UEBER = "ÜBER"
    VON = "VON"
    VOR = "VOR"
    ZU = "ZU"


class _Artikel(enum.StrEnum):
    DER = "der"
    DIE = "die"
    DAS = "das"


class _AuxiliaryVerbChoice(enum.StrEnum):
    HAT = "HAT"
    IST = "IST"
    BOTH = "HAT / IST"


class _GrammaticalCase(enum.StrEnum):
    """Case as a SLOT inside `X + Y + Z`; alternation within a slot uses `/`."""

    AKKUSATIV = "AKKUSATIV"
    DATIV = "DATIV"
    BOTH = "AKKUSATIV / DATIV"


class _GrammaticalCaseSection(enum.StrEnum):
    """Case as the WHOLE back; alternation across a whole section uses `|`."""

    AKKUSATIV = "AKKUSATIV"
    DATIV = "DATIV"
    BOTH = "AKKUSATIV | DATIV"


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class _Person:
    pronoun: str
    reflexive_pronoun: str


_PERSONS_BY_CONJUGATION_TOKEN: dict[str, tuple[_Person, ...]] = {
    "ICH_DU_ES": (
        _Person(pronoun="ich", reflexive_pronoun="mich"),
        _Person(pronoun="du", reflexive_pronoun="dich"),
        _Person(pronoun="er/sie/es", reflexive_pronoun="sich"),
    ),
    "WIR_IHR_SIE": (
        _Person(pronoun="wir", reflexive_pronoun="uns"),
        _Person(pronoun="ihr", reflexive_pronoun="euch"),
        _Person(pronoun="Sie/sie", reflexive_pronoun="sich"),
    ),
}


def _select_card_category() -> CardCategory:
    categories = list(CATEGORY_TO_FORMAT)
    print("> Choose a category:")
    for i, category in enumerate(categories):
        print(f"\t* `{i}` for category=`{category}`")
    while True:
        try:
            category_index: int = int(input("> Enter a category code: "))
            if 0 <= category_index < len(categories):
                selected_category = categories[category_index]
                print(f"[INFO] {selected_category=}.")
                return selected_category
            else:
                print("> Given category code is not valid! Try again..")
        except ValueError:
            print("> Please enter a valid integer!")


def _enter_from_options(an_enum: type[enum.StrEnum]) -> str:
    options_str = ", ".join([f"`{x}`" for x in an_enum])
    input_str = f"Enter an option ({options_str})"
    input_str_with_err = f"Wrong option entered! {input_str}"
    while True:
        output = input(f"\t> {input_str}:")
        if output.lower() in an_enum:
            return an_enum(output.lower())

        if output.upper() in an_enum:
            return an_enum(output.upper())
        input_str = input_str_with_err


def _prompt_alphabetic_word(
    *, prompt: str, normalize: collections.abc.Callable[[str], str]
) -> str | None:
    word = normalize(input(f"   > {prompt}: "))
    return word if word.isalpha() else None


def _prompt_conjugations(*, persons: tuple[_Person, ...]) -> str | None:
    conjugations = [
        input(
            f'   > Enter a conjugation for "{person.pronoun}" '
            f"(add ` {person.reflexive_pronoun}` at the end if reflexive): "
        ).lower()
        for person in persons
    ]
    for person, conjugation in zip(persons, conjugations, strict=True):
        word = conjugation.replace(f" {person.reflexive_pronoun}", "")
        if word.count(" ") > 1 or not word.replace(" ", "").isalpha():
            return None
    return "<br>".join(
        f"{person.pronoun} {conjugation}"
        for person, conjugation in zip(persons, conjugations, strict=True)
    )


def _resolve_token(token: str) -> str | None:
    """
    Prompt the user to resolve various token types into their string outputs.
    Returns the trimmed output or None if the input was invalid/empty.
    """
    match token:
        case "":  # empty token → no action
            return None

        case "ICH_DU_ES" | "WIR_IHR_SIE":
            return _prompt_conjugations(persons=_PERSONS_BY_CONJUGATION_TOKEN[token])

        case "ADJEKTIV":
            return _prompt_alphabetic_word(
                prompt="Enter an adjective", normalize=str.lower
            )

        case "ADJEKTIV_KOMPARATIV":
            return _prompt_alphabetic_word(
                prompt="Enter a comparative adjective", normalize=str.lower
            )

        case "ADJEKTIV_SUPERLATIV":
            return _prompt_alphabetic_word(
                prompt='Enter a superlativ adjective (without "am")',
                normalize=str.lower,
            )

        case t if t.startswith("STR_GERMAN"):
            return input("   > Enter a German text: ")

        case t if t.startswith("STR_ENGLISH"):
            return input("   > Enter an English text: ")

        case t if t.startswith("STR_ANY"):
            return input("   > Enter any text: ")

        case "NOUN_SINGULAR":
            return _prompt_alphabetic_word(
                prompt="Enter a singular noun", normalize=str.title
            )

        case t if t.startswith("VERB_"):
            form = t.split("VERB_")[1].lower()
            assert form in ("present", "perfekt", "präteritum")
            verb = input(
                f"   > Enter a verb in {form} form (add `sich ` at the beginning if reflexive): "
            ).lower()
            cleaned = verb.replace("*", "").replace("sich ", "").replace(" ", "")
            if not cleaned.isalpha():
                return None
            return verb

        case "ARTIKEL":
            return _enter_from_options(_Artikel)

        case "HAT_IST":
            return _enter_from_options(_AuxiliaryVerbChoice)

        case "AKK_DAT":
            return _enter_from_options(_GrammaticalCase)

        case "AKK_DAT_SECTION":
            return _enter_from_options(_GrammaticalCaseSection)

        case "PREPOSITION":
            return _enter_from_options(_Preposition)

        case "OPTIONAL_PLURAL":
            sel = input("   > Does this word have a plural form? (Y/n): ").lower()
            if sel == "n":
                return "NO PLURAL"
            plural = _prompt_alphabetic_word(
                prompt="Enter a plural noun without artikel", normalize=str.title
            )
            return None if plural is None else f"die {plural}"

        case _:  # fallback for any other token
            raise ValueError(f"Wrong `{token=}`")


def _build_new_card() -> AnkiCard:
    category = _select_card_category()
    fmt = CATEGORY_TO_FORMAT[category].template
    tokens: list[str] = re.findall(r"{(?P<token>.*?)}", fmt)

    argument_pairs: dict[str, str] = {}
    for i, token in enumerate(tokens):
        token_colored = ColorCode.block(ColorCode.FORE_RED, text=token)
        fmt_colored = ColorCode.block(
            ColorCode.BACK_YELLOW, ColorCode.FORE_BLACK, text=fmt
        )
        print(f"[INFO] Token #{i} <{token_colored}> in the pattern <{fmt_colored}>:")
        while True:
            if output := _resolve_token(token):
                break
            print(f"[WARN] `{output=}` is invalid, please try again!")
        argument_pairs[token] = output

    # TODO: Workaround
    front_without_category, back = fmt.format(**argument_pairs).split(";")
    return AnkiCard(front=f"{category}: {front_without_category}", back=back)


def _check_initial_file_content(filepath: pathlib.Path) -> None:
    if not filepath.exists():
        return

    with filepath.open(mode="r", encoding="utf-8") as fp:
        lines = fp.readlines()
    if not lines:
        file_content_str = ColorCode.block(ColorCode.FORE_MAGENTA, text="<EMPTY>")
        print(f"[INFO] INITIAL FILE CONTENT: {file_content_str}")
        return
    non_empty_lines = [
        f"[{str(i).zfill(2)}] {ln.rstrip()}" for i, ln in enumerate(lines) if ln.strip()
    ]
    file_content_str = ColorCode.block(
        ColorCode.FORE_MAGENTA, text="\n".join(non_empty_lines)
    )
    print(f"[INFO] INITIAL FILE CONTENT:\n{file_content_str}")
    selection = input("> Do you want to erase the file content? (y/N)?:")
    if selection.lower() == "y":
        filepath.write_text("", encoding="utf-8")
        print("[INFO] File content deleted!")
        time.sleep(1.5)


def anki_deutsch_adder(filepath: pathlib.Path):
    _check_initial_file_content(filepath=filepath)
    while True:
        try:
            with open(filepath, "a+", encoding="utf-8") as fp:
                new_card: AnkiCard = _build_new_card()
                print(f"[INFO] `{new_card.to_colored_str=}`")
                fp.write(new_card.to_str + "\n")
        except KeyboardInterrupt as e:
            print(f"\n> Got: {e}, exiting..")
            break

        with open(filepath, "r", encoding="utf-8") as fp:
            print(f"> CURRENT FILE CONTENT:{ColorCode.FORE_YELLOW}", end="")
            for line in fp:
                print("\n  > " + line[:-1], end="")
            print(ColorCode.STYLE_RESET_ALL)


if __name__ == "__main__":
    anki_deutsch_adder(filepath=pathlib.Path("output/new_anki_cards.csv"))
