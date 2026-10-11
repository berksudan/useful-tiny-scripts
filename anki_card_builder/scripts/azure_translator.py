import collections.abc
import decimal
import json
import os
import urllib.request

import pydantic
from pydantic.alias_generators import to_camel

_DICTIONARY_LOOKUP_URL = "https://api.cognitive.microsofttranslator.com/dictionary/lookup?api-version=3.0&from=de&to=en"


class BackTranslation(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=True, alias_generator=to_camel)
    display_text: str
    frequency_count: int


class DictionaryTranslation(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=True, alias_generator=to_camel)
    display_target: str
    pos_tag: str
    confidence: decimal.Decimal
    back_translations: tuple[BackTranslation, ...]


class _DictionaryLookupResult(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=True)
    translations: tuple[DictionaryTranslation, ...]


def fetch_dictionary_translations(
    *, german_words: collections.abc.Collection[str]
) -> dict[str, tuple[DictionaryTranslation, ...]]:
    unique_german_words = list(dict.fromkeys(german_words))
    request = urllib.request.Request(
        _DICTIONARY_LOOKUP_URL,
        data=json.dumps([{"Text": word} for word in unique_german_words]).encode(),
        headers={
            "Ocp-Apim-Subscription-Key": os.environ["AZURE_TRANSLATOR_KEY"],
            "Ocp-Apim-Subscription-Region": os.environ["AZURE_TRANSLATOR_REGION"],
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request) as response:
        results = pydantic.TypeAdapter(
            tuple[_DictionaryLookupResult, ...]
        ).validate_json(response.read())
    return {
        word: result.translations
        for word, result in zip(unique_german_words, results, strict=True)
    }
