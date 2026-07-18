from typing import Protocol

from .client import MytharCompiler
from .models import MytharISF


class MytharImportSink(Protocol):
    def save_mythar_artifact(self, project_id: int, source: str, isf: MytharISF) -> int: ...


class MytharImporter:
    def __init__(self, compiler: MytharCompiler, sink: MytharImportSink):
        self.compiler = compiler
        self.sink = sink

    def import_source(self, project_id: int, source: str) -> tuple[int, MytharISF]:
        isf = self.compiler.compile_to_isf(source)
        source_id = self.sink.save_mythar_artifact(project_id, source, isf)
        return source_id, isf

