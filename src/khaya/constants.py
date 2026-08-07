TIMEOUT = 30
RETRY_ATTEMPTS = 3

# Reference data only — NOT used to validate language input.
#
# The API accepts several spellings for the same language (``en-tw``,
# ``en-twi`` and ``eng-twi`` all translate to Twi), so rejecting or warning on
# codes absent from these sets produced false positives on valid calls. The
# API is the authority on what it accepts; these lists exist for documentation
# and for callers who want to offer a picker.
#
# SUPPORTED_TTS_SPEAKERS is the exception — see its note below.
#
# The Khaya API is versioned per service, and the SDK currently calls v1 of
# each. Newer versions exist (translation v2, ASR v2 and v3, TTS v2) and offer
# richer responses; the language catalogues below are taken from whichever
# version publishes one, then checked against the v1 endpoint the SDK calls.

# Translation language pairs (source-target).
# Verified against the /v1/languages endpoint. Note that endpoint reports
# three-letter codes (twi, ewe, yor, kik) for several languages listed here
# with two-letter codes; both forms are accepted by /v1/translate.
SUPPORTED_LANGUAGE_PAIRS: frozenset[str] = frozenset(
    {
        "en-tw",  # English → Twi
        "tw-en",  # Twi → English
        "en-ee",  # English → Ewe
        "ee-en",  # Ewe → English
        "en-gaa",  # English → Ga
        "gaa-en",  # Ga → English
        "en-fat",  # English → Fante
        "fat-en",  # Fante → English
        "en-yo",  # English → Yoruba
        "yo-en",  # Yoruba → English
        "en-dag",  # English → Dagbani
        "dag-en",  # Dagbani → English
        "en-ki",  # English → Kikuyu
        "ki-en",  # Kikuyu → English
        "en-gur",  # English → Gurune
        "gur-en",  # Gurune → English
        "en-luo",  # English → Luo
        "luo-en",  # Luo → English
        "en-mer",  # English → Kimeru
        "mer-en",  # Kimeru → English
        "en-kus",  # English → Kusaal
        "kus-en",  # Kusaal → English
    }
)

# Languages supported for ASR.
# Verified against GET /asr/v3/languages (34 entries). The SDK calls the v1
# transcribe endpoint, which accepts every one of these codes — checked by
# posting a sample .wav for each.
#
# These are ISO 639-3. An earlier revision of this list carried legacy
# spellings, nine of which the API rejects outright: en_gh, gon, kas, kon_k,
# kon_l, mam, pid, wal, wo. Their replacements are below.
SUPPORTED_ASR_LANGUAGES: frozenset[str] = frozenset(
    {
        "eng",  # African English (was en_gh)
        "fra",  # African French
        "atw",  # Akuapem Twi
        "bwu",  # Buli
        "dga",  # Dagaare
        "dag",  # Dagbani
        "ada",  # Dangme
        "ewe",  # Ewe
        "fat",  # Fante
        "gaa",  # Ga
        "gjn",  # Gonja (was gon)
        "gur",  # Gurene
        "hau",  # Hausa
        "ibo",  # Igbo
        "xsm",  # Kasem (was kas)
        "kik",  # Kikuyu
        "kin",  # Kinyarwanda
        "xon_likoonli",  # Konkomba-Likoonli (was kon_k)
        "xon_likpakpaanl",  # Konkomba-Likpakpaanl (was kon_l)
        "kri",  # Krio
        "kus",  # Kusaal
        "luo",  # Luo
        "maw",  # Mampruli (was mam)
        "men",  # Mende
        "mer",  # Meru
        "pcm",  # Naija Pidgin (was pid)
        "nzi",  # Nzema
        "sna",  # Shona
        "swa",  # Swahili
        "tem",  # Temne
        "twi",  # Twi
        "wlx",  # Wali (was wal)
        "wol",  # Wolof (was wo)
        "yor",  # Yoruba
    }
)

# Languages supported for TTS.
# Verified against GET /tts/v2/languages (32 entries); /tts/v1/languages
# returns the same set.
# Note: TTS language codes differ from ASR codes for some languages —
# Konkomba is lxn/xon here but xon_likoonli/xon_likpakpaanl for ASR.
SUPPORTED_TTS_LANGUAGES: frozenset[str] = frozenset(
    {
        "atw",  # Akuapem Twi
        "twi",  # Asante Twi
        "dga",  # Dagaare
        "dag",  # Dagbani
        "ada",  # Dangme
        "eng",  # English
        "ewe",  # Ewe
        "fat",  # Fante
        "fra",  # French
        "gaa",  # Ga
        "gjn",  # Gonja
        "gur",  # Gurene
        "hau",  # Hausa
        "ibo",  # Igbo
        "xsm",  # Kasem
        "kik",  # Kikuyu
        "lxn",  # Konkomba (Likoonli)
        "xon",  # Konkomba (Likpakpaanl)
        "kri",  # Krio
        "kus",  # Kusaal
        "luo",  # Luo
        "maw",  # Mampruli
        "men",  # Mende
        "mer",  # Meru/Kimeru
        "nzi",  # Nzema
        "pcm",  # Pidgin
        "sna",  # Shona
        "swa",  # Swahili
        "tem",  # Temne
        "wlx",  # Wali
        "wol",  # Wolof
        "yor",  # Yoruba
    }
)

# Available TTS speakers.
# Source: /tts/v1/speakers endpoint.
#
# Unlike the language lists, this one IS enforced (see khaya.services.tts).
# The set is small and closed, and the API silently falls back to its default
# voice for an unrecognised value instead of returning an error — so a typo
# would otherwise produce the wrong voice with no signal at all.
SUPPORTED_TTS_SPEAKERS: frozenset[str] = frozenset({"male_low", "male_high", "female"})
