import dataclasses
import enum
import pathlib
import re
import time

from scripts.shared import AnkiCard, CardCategory, ColorCode


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


@dataclasses.dataclass(frozen=True, kw_only=True)
class _CardCategoryWithFormat:
    category: CardCategory
    format: str  # TODO: Can change


class _Logger:
    @staticmethod
    def info(*args: str) -> None:
        print("[INFO] ", *args)

    @staticmethod
    def warning(*args: str) -> None:
        print("[WARN] ", *args)

    @staticmethod
    def error(*args: str) -> None:
        print("[ERROR] ", *args)

    @staticmethod
    def entry(s: str) -> None:
        input("> " + s)


LOGGER = _Logger()

_CATEGORY_WITH_FORMATS: list[_CardCategoryWithFormat] = [
    _CardCategoryWithFormat(
        category=CardCategory.ARTIKEL_PLURAL,
        format="{NOUN_SINGULAR};{ARTIKEL} {NOUN_SINGULAR}, {OPTIONAL_PLURAL}",
    ),
    _CardCategoryWithFormat(
        category=CardCategory.AKKUSATIVFORM,
        format="{STR_GERMAN_1};{STR_GERMAN_2}",
    ),
    _CardCategoryWithFormat(
        category=CardCategory.IMPERATIV_DU_FORM,
        format="{VERB_PRESENT};{STR_GERMAN}",
    ),
    _CardCategoryWithFormat(
        category=CardCategory.IMPERATIV_IHR_FORM,
        format="{VERB_PRESENT};{STR_GERMAN}",
    ),
    _CardCategoryWithFormat(
        category=CardCategory.IMPERATIV_SIE_FORM,
        format="{VERB_PRESENT};{STR_GERMAN}",
    ),
    _CardCategoryWithFormat(
        category=CardCategory.DATIVFORM,
        format="{STR_GERMAN_1};{STR_GERMAN_2}",
    ),
    _CardCategoryWithFormat(
        category=CardCategory.HAT_IST_PERFEKT,
        format="{VERB_PRESENT};{HAT_IST} + {VERB_PERFEKT}",
    ),
    _CardCategoryWithFormat(
        category=CardCategory.PRAETERITUM_HAT_IST_PERFEKT,
        format="{VERB_PRESENT};{VERB_PRÄTERITUM}, {HAT_IST} + {VERB_PERFEKT}",
    ),
    _CardCategoryWithFormat(
        category=CardCategory.DEU_TO_ENG_ARTIKEL_PLURAL,
        format="{NOUN_SINGULAR};{STR_ENGLISH}, {ARTIKEL} {NOUN_SINGULAR}, {OPTIONAL_PLURAL}",
    ),
    _CardCategoryWithFormat(
        category=CardCategory.DEU_TO_ENG,
        format="{STR_GERMAN};{STR_ENGLISH}",
    ),
    _CardCategoryWithFormat(
        category=CardCategory.KOMPARATIV_SUPERLATIV,
        format="{ADJEKTIV};{ADJEKTIV_KOMPARATIV}, am {ADJEKTIV_SUPERLATIV}",
    ),
    _CardCategoryWithFormat(
        category=CardCategory.KONJUGATION_ICH_DU_ES,
        format="{VERB_PRESENT};{ICH_DU_ES}",
    ),
    _CardCategoryWithFormat(
        category=CardCategory.KONJUGATION_WIR_IHR_SIE,
        format="{VERB_PRESENT};{WIR_IHR_SIE}",
    ),
    _CardCategoryWithFormat(
        category=CardCategory.PRAEPOSITION_AKK_DATIV,
        format="{VERB_PRESENT};{VERB_PRESENT} + {PREPOSITION} + {AKK_DAT}",
    ),
    _CardCategoryWithFormat(
        category=CardCategory.DAS_GEGENTEIL_VON,
        format="{STR_GERMAN_1};{STR_GERMAN_2}",
    ),
    _CardCategoryWithFormat(
        category=CardCategory.PRAEPOSITION_REKTION,
        format="{STR_GERMAN};{AKK_DAT_SECTION}",
    ),
    _CardCategoryWithFormat(
        category=CardCategory.QUIZFRAGE,
        format="{STR_ANY_1};{STR_ANY_2}",
    ),
]


def _select_card_category() -> _CardCategoryWithFormat:
    print("> Choose a category:")
    for i, category_with_format in enumerate(_CATEGORY_WITH_FORMATS):
        print(f"\t* `{i}` for category=`{category_with_format.category}`")
    while True:
        try:
            category_index: int = int(input("> Enter a category code: "))
            if 0 <= category_index < len(_CATEGORY_WITH_FORMATS):
                selected_category = _CATEGORY_WITH_FORMATS[category_index]
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


def resolve_token(token: str) -> str | None:
    """
    Prompt the user to resolve various token types into their string outputs.
    Returns the trimmed output or None if the input was invalid/empty.
    """
    match token:
        case "":  # empty token → no action
            return None

        case "ICH_DU_ES":
            ich = input(
                '   > Enter a conjugation for "ich" (add ` mich` at the end if reflexive): '
            ).lower()
            du = input(
                '   > Enter a conjugation for "du" (add ` dich` at the end if reflexive): '
            ).lower()
            er_sie_es = input(
                '   > Enter a conjugation for "er/sie/es" (add ` sich` at the end if reflexive): '
            ).lower()

            # Validate that each cleaned word is single‑ or two‑part and alphabetic
            for word in (
                ich.replace(" mich", ""),
                du.replace(" dich", ""),
                er_sie_es.replace(" sich", ""),
            ):
                if word.count(" ") > 1 or not word.replace(" ", "").isalpha():
                    return None

            return f"ich {ich}<br>du {du}<br>er/sie/es {er_sie_es}"

        case "WIR_IHR_SIE":
            wir = input(
                '   > Enter a conjugation for "wir" (add ` uns` at the end if reflexive): '
            ).lower()
            ihr = input(
                '   > Enter a conjugation for "ihr" (add ` euch` at the end if reflexive): '
            ).lower()
            sie_sie = input(
                '   > Enter a conjugation for "Sie/sie" (add ` sich` at the end if reflexive): '
            ).lower()

            for word in (
                wir.replace(" uns", ""),
                ihr.replace(" euch", ""),
                sie_sie.replace(" sich", ""),
            ):
                if word.count(" ") > 1 or not word.replace(" ", "").isalpha():
                    return None

            return f"wir {wir}<br>ihr {ihr}<br>Sie/sie {sie_sie}"

        case "ADJEKTIV":
            adj = input("   > Enter an adjective: ").lower()
            if not adj.isalpha():
                return None
            return adj

        case "ADJEKTIV_KOMPARATIV":
            comp = input("   > Enter a comparative adjective: ").lower()
            if not comp.isalpha():
                return None
            return comp

        case "ADJEKTIV_SUPERLATIV":
            superl = input('   > Enter a superlativ adjective (without "am"): ').lower()
            if not superl.isalpha():
                return None
            return superl

        case t if t.startswith("STR_GERMAN"):
            return input("   > Enter a German text: ")

        case t if t.startswith("STR_ENGLISH"):
            return input("   > Enter an English text: ")

        case t if t.startswith("STR_ANY"):
            return input("   > Enter any text: ")

        case "NOUN_SINGULAR":
            noun = input("   > Enter a singular noun: ").title()
            if not noun.isalpha():
                return None
            return noun

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
            else:
                pl = input("   > Enter a plural noun without artikel: ").title()
                if not pl.isalpha():
                    return None
                return f"die {pl}"

        case _:  # fallback for any other token
            raise ValueError(f"Wrong `{token=}`")


def _build_new_card() -> AnkiCard:
    category_with_format: _CardCategoryWithFormat = _select_card_category()
    category, fmt = category_with_format.category, category_with_format.format
    tokens: list[str] = re.findall(r"{(?P<token>.*?)}", fmt)

    argument_pairs: dict[str, str] = {}
    for i, token in enumerate(tokens):
        token_colored = ColorCode.block(ColorCode.FORE_RED, text=token)
        fmt_colored = ColorCode.block(
            ColorCode.BACK_YELLOW, ColorCode.FORE_BLACK, text=fmt
        )
        LOGGER.info(f"Token #{i} <{token_colored}> in the pattern <{fmt_colored}>:")
        while True:
            if output := resolve_token(token):
                break
            LOGGER.warning(f"`{output=}` is invalid, please try again!")
        argument_pairs[token] = output

    # TODO: Workaround
    front_without_category, back = fmt.format(**argument_pairs).split(";")
    front = f"{category}: {front_without_category}"
    return AnkiCard.parse_iterable([front, back])


def _check_initial_file_content(filepath: pathlib.Path) -> None:
    if not filepath.exists():
        return

    with filepath.open(mode="r", encoding="utf-8") as fp:
        lines = fp.readlines()
    if not lines:
        file_content_str = ColorCode.block(ColorCode.FORE_MAGENTA, text="<EMPTY>")
        print(f"[INFO] INITIAL FILE CONTENT: {file_content_str}")
        return
    # TODO:tt
    non_empty_lines = [
        f"[{str(i).zfill(2)}] {ln.rstrip()}" for i, ln in enumerate(lines) if ln.strip()
    ]
    file_content_str = ColorCode.block(
        ColorCode.FORE_MAGENTA, text="\n".join(non_empty_lines)
    )
    print(f"[INFO] INITIAL FILE CONTENT:\n{file_content_str}")
    selection = input("> Do you want to erase the file content? (y/N)?:")
    if selection.lower() == "y":
        with open(filepath, "a+", encoding="utf-8") as fp:
            fp.truncate(0)
            LOGGER.info("File content deleted!")
            time.sleep(1.5)


def anki_deutsch_adder(filepath: pathlib.Path):
    _check_initial_file_content(filepath=filepath)
    while True:
        try:
            with open(filepath, "a+", encoding="utf-8") as fp:
                new_card: AnkiCard = _build_new_card()
                LOGGER.info(f"`{new_card.to_colored_str=}`")
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
