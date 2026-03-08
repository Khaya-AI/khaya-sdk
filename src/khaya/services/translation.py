import httpx

from khaya.constants import SUPPORTED_LANGUAGE_PAIRS
from khaya.exceptions import TranslationError
from khaya.models import TranslationResult
from khaya.services.base_api import BaseApi
from khaya.utils import check_authentication, warn_if_unknown


def _parse_language_pair(language_pair: str) -> tuple[str, str]:
    parts = language_pair.split("-", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return parts[0], ""


class TranslationService:
    def __init__(self, http_client: BaseApi) -> None:
        self.http_client = http_client
        self.endpoint = http_client.config.endpoints["translation"]

    @check_authentication
    def translate(self, text: str, language_pair: str = "en-tw") -> TranslationResult:
        """Translate text from one language to another.

        Args:
            text: The text to translate.
            language_pair: The language pair (e.g. ``"en-tw"``).

        Returns:
            TranslationResult with the translated text and language codes.

        Raises:
            TranslationError: If text or language_pair are empty.
            AuthenticationError: If no API key is configured.
            APIError: On HTTP errors from the API.
        """
        if not text or not language_pair:
            raise TranslationError("Text and language pair are required", 400)
        warn_if_unknown(language_pair, SUPPORTED_LANGUAGE_PAIRS, "language pair")
        source, target = _parse_language_pair(language_pair)
        response: httpx.Response = self.http_client.request(
            "POST", self.endpoint, json={"in": text, "lang": language_pair}
        )
        return TranslationResult(
            text=response.json(), source_language=source, target_language=target
        )

    @check_authentication
    async def atranslate(
        self, text: str, language_pair: str = "en-tw"
    ) -> TranslationResult:
        """Async version of translate."""
        if not text or not language_pair:
            raise TranslationError("Text and language pair are required", 400)
        warn_if_unknown(language_pair, SUPPORTED_LANGUAGE_PAIRS, "language pair")
        source, target = _parse_language_pair(language_pair)
        response: httpx.Response = await self.http_client.arequest(
            "POST", self.endpoint, json={"in": text, "lang": language_pair}
        )
        return TranslationResult(
            text=response.json(), source_language=source, target_language=target
        )
