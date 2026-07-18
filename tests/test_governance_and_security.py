from pathlib import Path

import pytest

from research_os.constitution.runtime import ConstitutionalRuntime, WorkflowRequest
from research_os.domain.errors import ValidationError
from research_os.security import Workspace


def test_workspace_confines_paths(tmp_path):
    workspace = Workspace(tmp_path)
    assert workspace.resolve("reports/final.md") == (tmp_path / "reports/final.md").resolve()
    with pytest.raises(ValueError):
        workspace.resolve("../secret.txt")
    with pytest.raises(ValueError):
        workspace.resolve(str(Path(tmp_path.anchor) / "absolute.txt"))


def test_constitutional_runtime_enforces_model_and_budget():
    runtime = ConstitutionalRuntime()
    valid = WorkflowRequest(1, "What does the evidence support?", "openai", "gpt-5.6", 2_000)
    assert runtime.authorize(valid) is valid

    with pytest.raises(ValidationError):
        runtime.authorize(WorkflowRequest(1, "Question", "unapproved", "gpt-5.6", 2_000))
    with pytest.raises(ValidationError):
        runtime.authorize(WorkflowRequest(1, "Question", "openai", "unapproved-model", 2_000))
    with pytest.raises(ValidationError):
        runtime.authorize(WorkflowRequest(1, "Question", "openai", "gpt-5.6", 100_000))
