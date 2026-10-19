# Exceptions

All exceptions inherit from `APIError` and expose `message` and `status_code` attributes.

```
APIError
├── AuthenticationError
├── InsufficientCreditsError
├── RateLimitError
├── TranslationError
├── TTSGenerationError
└── ASRTranscriptionError
```

::: khaya.exceptions.APIError

::: khaya.exceptions.AuthenticationError

::: khaya.exceptions.InsufficientCreditsError

::: khaya.exceptions.RateLimitError

::: khaya.exceptions.TranslationError

::: khaya.exceptions.TTSGenerationError

::: khaya.exceptions.ASRTranscriptionError
