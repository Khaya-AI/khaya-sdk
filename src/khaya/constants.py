TIMEOUT = 30
RETRY_ATTEMPTS = 3

# Supported translation language pairs (source-target).
SUPPORTED_LANGUAGE_PAIRS: frozenset[str] = frozenset(
    {
        "en-tw",  # English → Twi
        "tw-en",  # Twi → English
        "en-ee",  # English → Ewe
        "ee-en",  # Ewe → English
        "en-gaa",  # English → Ga
        "gaa-en",  # Ga → English
        "en-dag",  # English → Dagbani
        "dag-en",  # Dagbani → English
        "en-dga",  # English → Dagaare
        "dga-en",  # Dagaare → English
        "en-fat",  # English → Fante
        "fat-en",  # Fante → English
        "en-gur",  # English → Gurene
        "gur-en",  # Gurene → English
        "en-nzi",  # English → Nzema
        "nzi-en",  # Nzema → English
        "en-kpo",  # English → Ghanaian Pidgin
        "kpo-en",  # Ghanaian Pidgin → English
        "en-yo",   # English → Yoruba
        "yo-en",   # Yoruba → English
        "en-ki",   # English → Kikuyu
        "ki-en",   # Kikuyu → English
    }
)

# Languages supported for ASR.
SUPPORTED_ASR_LANGUAGES: frozenset[str] = frozenset(
    {"tw", "gaa", "dag", "ee", "dga", "fat", "gur", "nzi", "kpo", "yo"}
)

# Languages supported for TTS.
SUPPORTED_TTS_LANGUAGES: frozenset[str] = frozenset(
    {"tw", "gaa", "dag", "ee", "yo"}
)
