TIMEOUT = 30
RETRY_ATTEMPTS = 3

# Reference data only — NOT used to validate user input.
#
# The API accepts several spellings for the same language (``en-tw``,
# ``en-twi`` and ``eng-twi`` all translate to Twi), so rejecting or warning on
# codes absent from these sets produced false positives on valid calls. The
# API is the authority on what it accepts; these lists exist for documentation
# and for callers who want to offer a picker.

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
# Unverified: /asr/v1/languages returns 404, so this list has no live source
# and may drift. Treat as indicative, not authoritative.
SUPPORTED_ASR_LANGUAGES: frozenset[str] = frozenset(
    {
        "ada",  # Adangme
        "en_gh",  # African English
        "atw",  # Akuapem Twi
        "tw",  # Asante Twi
        "dga",  # Dagaare
        "dag",  # Dagbani
        "ee",  # Ewe
        "fat",  # Fante
        "fra",  # French
        "gaa",  # Ga
        "gon",  # Gonja
        "gur",  # Gurene
        "ha",  # Hausa
        "ig",  # Igbo
        "kas",  # Kasem
        "ki",  # Kikuyu
        "kon_k",  # Konkomba (Likoonli)
        "kon_l",  # Konkomba (Likpakpaanl)
        "kri",  # Krio
        "kus",  # Kusaal
        "luo",  # Luo
        "mam",  # Mampruli
        "men",  # Mende
        "mer",  # Meru/Kimeru
        "nzi",  # Nzema
        "pid",  # Pidgin
        "sn",  # Shona
        "sw",  # Swahili
        "tem",  # Temne
        "wal",  # Wali
        "wo",  # Wolof
        "yo",  # Yoruba
    }
)

# Languages supported for TTS.
# Unverified: /tts/v1/languages returns 403, so this list has no live source
# and may drift. Treat as indicative, not authoritative.
# Note: TTS language codes differ from ASR codes for the same language.
SUPPORTED_TTS_LANGUAGES: frozenset[str] = frozenset(
    {
        "ada",  # Adangme
        "atw",  # Akuapem Twi
        "twi",  # Asante Twi
        "dag",  # Dagbani
        "dga",  # Dagaare
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
        "xon",  # Konkomba (Likpakpaanl)
        "lxn",  # Konkomba (Likoonli)
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
SUPPORTED_TTS_SPEAKERS: frozenset[str] = frozenset({"male_low", "male_high", "female"})
