TIMEOUT = 30
RETRY_ATTEMPTS = 3

# Reference data for documentation and pickers — not used to validate input.
# The API accepts several spellings per language (en-tw, en-twi, eng-twi all
# mean Twi), so a whitelist rejects valid calls. SUPPORTED_TTS_SPEAKERS is the
# one exception; see its note below.
#
# The SDK calls v1 of each service. These lists come from whichever version
# publishes a catalogue, then checked against v1.

# Translation pairs, source-target. From /v1/languages, which reports
# three-letter codes; /v1/translate accepts both forms.
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

# ASR languages, ISO 639-3, from /asr/v3/languages. The v1 endpoint the SDK
# calls accepts all of them. An earlier revision used legacy spellings, nine
# of which the API rejects; replacements are marked below.
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

# TTS languages, from /tts/v2/languages (/tts/v1/languages returns the same).
# Some codes differ from ASR: Konkomba is lxn/xon here, xon_* for ASR.
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

# From /tts/v1/speakers. Unlike the language lists this one IS enforced (see
# khaya.services.tts): the set is closed, and the API silently falls back to
# its default voice rather than erroring on a typo.
SUPPORTED_TTS_SPEAKERS: frozenset[str] = frozenset({"male_low", "male_high", "female"})
