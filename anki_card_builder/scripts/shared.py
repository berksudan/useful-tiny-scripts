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
