import inspect
import warnings
from functools import wraps

from khaya.exceptions import AuthenticationError


def warn_if_unknown(value: str, supported: frozenset[str], label: str) -> None:
    """Emit a UserWarning if *value* is not in *supported*."""
    if value and value not in supported:
        warnings.warn(
            f"Unknown {label} {value!r}. Supported values: {sorted(supported)}",
            UserWarning,
            stacklevel=3,
        )


def check_authentication(func):
    """Decorator that raises AuthenticationError if no API key is configured.

    Works with both synchronous and asynchronous service methods.
    """
    if inspect.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            if not self.http_client.config.api_key:
                raise AuthenticationError("API key is required", 401)
            return await func(self, *args, **kwargs)

        return async_wrapper

    @wraps(func)
    def sync_wrapper(self, *args, **kwargs):
        if not self.http_client.config.api_key:
            raise AuthenticationError("API key is required", 401)
        return func(self, *args, **kwargs)

    return sync_wrapper
