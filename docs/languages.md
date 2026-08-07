# Languages

Reference data for all three services, generated from the API's own catalogues
and pinned by a test so it cannot drift from `khaya.constants`.

These lists are **not** a whitelist. The SDK sends whatever code you pass and
lets the API decide — see [why](internals.md#service-layer).

## Language codes: legacy and ISO 639-3

The API accepts two generations of code, and several spellings resolve to the
same language: `en-tw`, `en-twi` and `eng-twi` all translate to Twi.

The API warns about the older forms, and the SDK surfaces those warnings on
`TranscriptionResult.warnings` (and logs them at `WARNING`):

```json
{"text": "Me ho yɛ.",
 "warnings": ["Language code 'tw' is a legacy code. Please update to 'twi'
   (ISO 639-3) when possible to ensure compatibility in the event of a full
   migration."]}
```

Both forms work today. **Prefer the ISO 639-3 codes in the tables below** —
they are what the API reports and what a future migration will keep.

Note that ASR and TTS use different codes for some languages: Konkomba
(Likpakpaanl) is `xon_likpakpaanl` for ASR and `xon` for TTS.

## Translation pairs

Format: `"<source>-<target>"`. All pairs are bidirectional with English as the
pivot.

| Pair | Direction |
|------|-----------|
| `dag-en` | Dagbani → English |
| `en-dag` | English → Dagbani |
| `ee-en` | Ewe → English |
| `en-ee` | English → Ewe |
| `en-fat` | English → Fante |
| `fat-en` | Fante → English |
| `en-gaa` | English → Ga |
| `gaa-en` | Ga → English |
| `en-gur` | English → Gurune |
| `gur-en` | Gurune → English |
| `en-ki` | English → Kikuyu |
| `ki-en` | Kikuyu → English |
| `en-mer` | English → Kimeru |
| `mer-en` | Kimeru → English |
| `en-kus` | English → Kusaal |
| `kus-en` | Kusaal → English |
| `en-luo` | English → Luo |
| `luo-en` | Luo → English |
| `en-tw` | English → Twi |
| `tw-en` | Twi → English |
| `en-yo` | English → Yoruba |
| `yo-en` | Yoruba → English |

## ASR languages

| Code | Language |
|------|----------|
| `eng` | African English |
| `fra` | African French |
| `atw` | Akuapem Twi |
| `bwu` | Buli |
| `dga` | Dagaare |
| `dag` | Dagbani |
| `ada` | Dangme |
| `ewe` | Ewe |
| `fat` | Fante |
| `gaa` | Ga |
| `gjn` | Gonja |
| `gur` | Gurene |
| `hau` | Hausa |
| `ibo` | Igbo |
| `xsm` | Kasem |
| `kik` | Kikuyu |
| `kin` | Kinyarwanda |
| `xon_likoonli` | Konkomba-Likoonli |
| `xon_likpakpaanl` | Konkomba-Likpakpaanl |
| `kri` | Krio |
| `kus` | Kusaal |
| `luo` | Luo |
| `maw` | Mampruli |
| `men` | Mende |
| `mer` | Meru |
| `pcm` | Naija Pidgin |
| `nzi` | Nzema |
| `sna` | Shona |
| `swa` | Swahili |
| `tem` | Temne |
| `twi` | Twi |
| `wlx` | Wali |
| `wol` | Wolof |
| `yor` | Yoruba |

## TTS languages

| Code | Language |
|------|----------|
| `atw` | Akuapem Twi |
| `twi` | Asante Twi |
| `dga` | Dagaare |
| `dag` | Dagbani |
| `ada` | Dangme |
| `eng` | English |
| `ewe` | Ewe |
| `fat` | Fante |
| `fra` | French |
| `gaa` | Ga |
| `gjn` | Gonja |
| `gur` | Gurene |
| `hau` | Hausa |
| `ibo` | Igbo |
| `xsm` | Kasem |
| `kik` | Kikuyu |
| `lxn` | Konkomba (Likoonli) |
| `xon` | Konkomba (Likpakpaanl) |
| `kri` | Krio |
| `kus` | Kusaal |
| `luo` | Luo |
| `maw` | Mampruli |
| `men` | Mende |
| `mer` | Meru/Kimeru |
| `nzi` | Nzema |
| `pcm` | Pidgin |
| `sna` | Shona |
| `swa` | Swahili |
| `tem` | Temne |
| `wlx` | Wali |
| `wol` | Wolof |
| `yor` | Yoruba |

## TTS speakers

All languages share one multilingual speaker pool. Unlike language codes, this
set **is** validated by the SDK — the API silently falls back to its default
voice rather than erroring on a typo.

| Speaker | Description |
|---------|-------------|
| `male_low` | Male, lower pitch |
| `male_high` | Male, higher pitch |
| `female` | Female |
