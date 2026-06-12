TIMEOUT = 30
RETRY_ATTEMPTS = 3

# Supported translation language pairs (source-target).
# Source: /v1/languages endpoint — pivot language is English.
SUPPORTED_LANGUAGE_PAIRS: frozenset[str] = frozenset(
    {
        "en-tw",   # English → Twi
        "tw-en",   # Twi → English
        "en-ee",   # English → Ewe
        "ee-en",   # Ewe → English
        "en-gaa",  # English → Ga
        "gaa-en",  # Ga → English
        "en-fat",  # English → Fante
        "fat-en",  # Fante → English
        "en-yo",   # English → Yoruba
        "yo-en",   # Yoruba → English
        "en-dag",  # English → Dagbani
        "dag-en",  # Dagbani → English
        "en-ki",   # English → Kikuyu
        "ki-en",   # Kikuyu → English
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
# Source: /asr/v1/languages endpoint.
SUPPORTED_ASR_LANGUAGES: frozenset[str] = frozenset(
    {
        "ada",    # Dangme
        "en_gh",  # African English
        "atw",    # Akuapem Twi
        "tw",     # Asante Twi
        "dga",    # Dagaare
        "dag",    # Dagbani
        "ee",     # Ewe
        "fat",    # Fante
        "fra",    # French
        "gaa",    # Ga
        "gon",    # Gonja
        "gur",    # Gurene
        "ha",     # Hausa
        "ig",     # Igbo
        "kas",    # Kasem
        "ki",     # Kikuyu
        "kon_k",  # Konkomba (Likoonli)
        "kon_l",  # Konkomba (Likpakpaanl)
        "kri",    # Krio
        "kus",    # Kusaal
        "luo",    # Luo
        "mam",    # Mampruli
        "men",    # Mende
        "mer",    # Meru/Kimeru
        "nzi",    # Nzema
        "pid",    # Pidgin
        "sn",     # Shona
        "sw",     # Swahili
        "tem",    # Temne
        "wal",    # Wali
        "wo",     # Wolof
        "yo",     # Yoruba
    }
)

# Languages supported for TTS.
# Source: /tts/v1/languages endpoint.
# Note: TTS language codes differ from ASR codes for the same language.
SUPPORTED_TTS_LANGUAGES: frozenset[str] = frozenset(
    {
        "ada",  # Dangme
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
SUPPORTED_TTS_SPEAKERS: frozenset[str] = frozenset(
    {"male_low", "male_high", "female"}
)
