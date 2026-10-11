---
name: suggest-anki-cards
description: Suggest Anki card categories for German words and print the chosen cards as rows to paste into Google Sheets.
disable-model-invocation: true
argument-hint: <German word> [more words...]
---

# Suggest Anki Cards

Words: $ARGUMENTS

1. Run `.venv/bin/python -m scripts.suggest_anki_cards_cli list` for the categories, their card formats and the translation separator. Never work from memory.
2. For each word, suggest up to 4 fitting categories from that list. Ask with one multi-select `AskUserQuestion` question per word.
3. Draft one card per selected category, following its format. For an English translation:
   - Use the single best one. If the meaning depends on context, use the fewest that cover the common senses.
   - Each one must point clearly back to the German word.
   - Start verbs with `to`, and mark `[adj]`, `[adv]` or `[pl]` on the German word and every translation, e.g. `witzig [adj]` → `witty [adj]`.
   - Justify it in one short sentence with 1–2 example sentences, outside the code block.
4. Pipe the drafts to `.venv/bin/python -m scripts.suggest_anki_cards_cli build` (see `--help` for the input), fix any card it rejects, and print its output unchanged in one code block. Do not write any files.
