from typing import Protocol

import httpx
from pydantic import ValidationError as PydanticValidationError

from research_os.domain.errors import ExternalServiceError, ValidationError

from .models import MytharISF


class MytharCompiler(Protocol):
    def compile_to_isf(self, source: str) -> MytharISF: ...


class MytharCompilerClient:
    def __init__(
        self,
        base_url: str,
        token: str | None = None,
        timeout: float = 15.0,
        transport: httpx.BaseTransport | None = None,
    ):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"), headers=headers, timeout=timeout, transport=transport
        )

    def compile_to_isf(self, source: str) -> MytharISF:
        if not source.strip():
            raise ValidationError("Mythar source is required")
        try:
            response = self._client.post("/v2/compile", params={"format": "isf"}, json={"source": source})
            response.raise_for_status()
            return MytharISF.model_validate(response.json())
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 400:
                raise ValidationError("Mythar compiler rejected the source") from exc
            raise ExternalServiceError(f"Mythar compiler returned HTTP {exc.response.status_code}") from exc
        except (httpx.RequestError, PydanticValidationError, ValueError) as exc:
            raise ExternalServiceError("Mythar compiler returned an invalid or unavailable response") from exc

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()

