from typing import Any, Protocol

from .models import AdapterExecutionResult, ExecutionEnvelope, RuntimeAdapterDescriptor


class RuntimeAdapter(Protocol):
    @property
    def descriptor(self) -> RuntimeAdapterDescriptor: ...

    def execute(self, envelope: ExecutionEnvelope, payload: Any) -> AdapterExecutionResult: ...

