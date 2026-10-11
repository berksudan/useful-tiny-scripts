import dataclasses
import enum
import functools
import typing

import pydantic


class CardCategory(enum.StrEnum):
    ABKUERZUNG = "ABKÜRZUNG"
    ADJEKTIVDEKLINATION_AKK = "ADJEKTIVDEKLINATION ⋀ AKKUSATIV"
    ADJEKTIVDEKLINATION_DATIV = "ADJEKTIVDEKLINATION ⋀ DATIV"
    ADJEKTIVDEKLINATION_NOMINATIV_BESTIMMT = "ADJEKTIVDEKLINATION ⋀ NOMINATIV"
    AKKUSATIVFORM = "AKKUSATIVFORM"
    ARTIKEL_PLURAL = "ARTIKEL ⋀ PLURAL"
    AUF_DEUTSCH = "AUF DEUTSCH"
    DAS_GEGENTEIL_VON = "DAS GEGENTEIL VON"
    DATIVFORM = "DATIVFORM"
    DEU_TO_ENG = "DEU → ENG"
    DEU_TO_ENG_ARTIKEL_PLURAL = "DEU → ENG ⋀ ARTIKEL ⋀ PLURAL"
    ENG_TO_DEU = "ENG → DEU"
    GENITIV_TRANSFORMATION = "GENITIV TRANSFORMATION"
    HAT_IST_PERFEKT = "HAT/IST + PERFEKT"
    IMPERATIV_DU_FORM = "IMPERATIV DU-FORM"
    IMPERATIV_IHR_FORM = "IMPERATIV IHR-FORM"
    IMPERATIV_SIE_FORM = "IMPERATIV SIE-FORM"
    KOMPARATIV_SUPERLATIV = "KOMPARATIV ⋀ SUPERLATIV"
    KONJUGATION_ICH_DU_ES = "KONJUGATION (ICH/DU/ES)"
    KONJUGATION_WIR_IHR_SIE = "KONJUGATION (WIR/IHR/SIE)"
    LOKALE_PRAEPOSITION_BEDEUTUNG = "LOKALE PRÄPOSITION BEDEUTUNG"
    PRAEPOSITION_AKK_DATIV = "PRÄPOSITION ⋀ AKKUSATIV/DATIV"
    PRAEPOSITION_REKTION = "PRÄPOSITION REKTION"
    PRAETERITUM_HAT_IST_PERFEKT = "PRÄTERITUM ⋀ HAT/IST + PERFEKT"
    QUIZFRAGE = "QUIZFRAGE"
    REFLEXIVPRONOMEN_DATIV = "REFLEXIVPRONOMEN ⋀ DATIV"
    SUFFIX_ARTIKEL_MIT_AUSNAHMEN = "SUFFIX-ARTIKEL (MIT AUSNAHMEN)"
    TEMPORALE_PRAEPOSITION_BEDEUTUNG = "TEMPORALE PRÄPOSITION BEDEUTUNG"


TRANSLATION_SEPARATOR = " | "


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class CardFormat:
    template: str
    example: str


CATEGORY_TO_FORMAT: dict[CardCategory, CardFormat] = {
    CardCategory.ARTIKEL_PLURAL: CardFormat(
        template="{NOUN_SINGULAR};{ARTIKEL} {NOUN_SINGULAR}, {OPTIONAL_PLURAL}",
        example="Brot;das Brot, die Brote",
    ),
    CardCategory.AKKUSATIVFORM: CardFormat(
        template="{STR_GERMAN_1};{STR_GERMAN_2}", example="ich;mich"
    ),
    CardCategory.IMPERATIV_DU_FORM: CardFormat(
        template="{VERB_PRESENT};{STR_GERMAN}", example="helfen;hilf"
    ),
    CardCategory.IMPERATIV_IHR_FORM: CardFormat(
        template="{VERB_PRESENT};{STR_GERMAN}", example="helfen;helft"
    ),
    CardCategory.IMPERATIV_SIE_FORM: CardFormat(
        template="{VERB_PRESENT};{STR_GERMAN}", example="helfen;helfen Sie"
    ),
    CardCategory.DATIVFORM: CardFormat(
        template="{STR_GERMAN_1};{STR_GERMAN_2}", example="ich;mir"
    ),
    CardCategory.HAT_IST_PERFEKT: CardFormat(
        template="{VERB_PRESENT};{HAT_IST} + {VERB_PERFEKT}",
        example="ab*holen;HAT + abgeholt",
    ),
    CardCategory.PRAETERITUM_HAT_IST_PERFEKT: CardFormat(
        template="{VERB_PRESENT};{VERB_PRÄTERITUM}, {HAT_IST} + {VERB_PERFEKT}",
        example="spielen;spielte, HAT + gespielt",
    ),
    CardCategory.DEU_TO_ENG_ARTIKEL_PLURAL: CardFormat(
        template="{NOUN_SINGULAR};{STR_ENGLISH}, {ARTIKEL} {NOUN_SINGULAR}, {OPTIONAL_PLURAL}",
        example="Daumen;thumb, der Daumen, die Daumen",
    ),
    CardCategory.DEU_TO_ENG: CardFormat(
        template="{STR_GERMAN};{STR_ENGLISH}", example="die Jura;law"
    ),
    CardCategory.KOMPARATIV_SUPERLATIV: CardFormat(
        template="{ADJEKTIV};{ADJEKTIV_KOMPARATIV}, am {ADJEKTIV_SUPERLATIV}",
        example="teuer;teurer, am teuersten",
    ),
    CardCategory.KONJUGATION_ICH_DU_ES: CardFormat(
        template="{VERB_PRESENT};{ICH_DU_ES}",
        example="mitnehmen;ich nehme mit<br>du nimmst mit<br>er/sie/es nimmt mit",
    ),
    CardCategory.KONJUGATION_WIR_IHR_SIE: CardFormat(
        template="{VERB_PRESENT};{WIR_IHR_SIE}",
        example="mitnehmen;wir nehmen mit<br>ihr nehmt mit<br>Sie/sie nehmen mit",
    ),
    CardCategory.PRAEPOSITION_AKK_DATIV: CardFormat(
        template="{VERB_PRESENT};{VERB_PRESENT} + {PREPOSITION} + {AKK_DAT}",
        example="sich interessieren;sich interessieren + FÜR + AKKUSATIV",
    ),
    CardCategory.DAS_GEGENTEIL_VON: CardFormat(
        template="{STR_GERMAN_1};{STR_GERMAN_2}", example="schwierig;einfach | leicht"
    ),
    CardCategory.PRAEPOSITION_REKTION: CardFormat(
        template="{STR_GERMAN};{AKK_DAT_SECTION}", example="bis;AKKUSATIV"
    ),
    CardCategory.QUIZFRAGE: CardFormat(
        template="{STR_ANY_1};{STR_ANY_2}",
        example="helfen + DATIV or helfen + AKKUSATIV?;helfen + DATIV",
    ),
}


class ColorCode(enum.StrEnum):
    BACK_CYAN = "\x1b[46m"
    BACK_YELLOW = "\x1b[43m"
    FORE_BLACK = "\x1b[30m"
    FORE_MAGENTA = "\x1b[35m"
    FORE_RED = "\x1b[31m"
    FORE_YELLOW = "\x1b[33m"
    STYLE_RESET_ALL = "\x1b[0m"

    @classmethod
    def block(cls, *codes: typing.Self, text: str) -> str:
        concatenated_codes = "".join(code.value for code in codes)
        return f"{concatenated_codes}{text}{cls.STYLE_RESET_ALL}"


class AnkiCard(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=True)
    front: str = pydantic.Field(..., pattern=r"^\S[^:]*: [^:]*\S$")
    back: str = pydantic.Field(..., pattern=r"^\S.*\S$")

    @functools.cached_property
    def to_str(self) -> str:
        return f"{self.front};{self.back}"

    @functools.cached_property
    def to_colored_str(self) -> str:
        return ColorCode.block(
            ColorCode.BACK_CYAN, ColorCode.FORE_BLACK, text=self.to_str
        )

    @functools.cached_property
    def _split_front(self) -> list[str]:
        return self.front.split(": ")

    @functools.cached_property
    def category(self) -> CardCategory:
        card_category_str, _ = self._split_front
        return CardCategory(card_category_str)

    @functools.cached_property
    def front_without_category(self) -> str:
        _, front_without_category = self._split_front
        return front_without_category
