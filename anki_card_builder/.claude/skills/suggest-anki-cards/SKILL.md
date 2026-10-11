---
name: suggest-anki-cards
description: Suggest Anki card categories for German words and print the chosen cards as rows to paste into Google Sheets.
disable-model-invocation: true
argument-hint: <German word> [more words...]
---

# Suggest Anki Cards

Words: $ARGUMENTS

1. Run `.venv/bin/python -m scripts.suggest_anki_cards_cli list` for the categories, their card formats with an example card each, and the translation separator. Never work from memory.
2. For each word, suggest only the categories whose example shows it fits, up to 4. Ask with one multi-select `AskUserQuestion` question per word.
3. Draft one card per selected category, shaped like its example and writing German nouns with their definite article unless the card tests it. For an English translation:
   - Use the shortest common equivalent that translates back to this German word, not to a near-synonym. If the meaning depends on context, use the fewest that cover the common senses.
   - Start verbs with `to`, and mark `[adj]`, `[adv]` or `[pl]` on the German word and every translation, e.g. `witzig [adj]` → `witty [adj]`.
   - If a translation is still unclear, add the fewest suffix tags (such as `[noun]`) and/or `(e.g. …)` usage examples that make it fully clear on the card, without repeating the translation.
   - Justify each word's translation once, before the code block, in one short sentence with 1–2 translated example sentences.
4. Pipe the drafts to `.venv/bin/python -m scripts.suggest_anki_cards_cli build` (see `--help` for the input), fix any card it rejects, and print its output unchanged in one code block. Do not write any files.
5. Copy that same output to the clipboard, keeping the tabs.
