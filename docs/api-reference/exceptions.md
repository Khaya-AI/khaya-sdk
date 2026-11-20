# Exceptions

All exceptions inherit from `APIError` and expose `message`, `status_code`, `code`, `details` and `activity_id` attributes.

```
APIError
├── AuthenticationError
├── InsufficientCreditsError
├── PayloadTooLargeError
├── UnsupportedMediaTypeError
├── RateLimitError
├── ServerError
├── TranslationError
├── TTSGenerationError
└── ASRTranscriptionError
```

::: khaya.exceptions.APIError

::: khaya.exceptions.AuthenticationError

::: khaya.exceptions.InsufficientCreditsError

::: khaya.exceptions.PayloadTooLargeError

::: khaya.exceptions.UnsupportedMediaTypeError

::: khaya.exceptions.RateLimitError

::: khaya.exceptions.ServerError

::: khaya.exceptions.TranslationError

::: khaya.exceptions.TTSGenerationError

::: khaya.exceptions.ASRTranscriptionError
