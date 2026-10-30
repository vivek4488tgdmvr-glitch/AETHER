from pydantic import BaseModel, Field
from typing import Literal

class AnalyzeRequest(BaseModel):
    repo_id: str = Field(min_length=8, max_length=80)
    task: str = Field(min_length=5, max_length=4000)
    focus_files: list[str] = Field(default_factory=list, max_length=100)

class PatchRequest(BaseModel):
    repo_id: str = Field(min_length=8, max_length=80)
    task: str = Field(min_length=5, max_length=4000)
    finding_ids: list[str] = Field(default_factory=list, max_length=30)

class ApplyPatchRequest(BaseModel):
    repo_id: str = Field(min_length=8, max_length=80)
    patch: str = Field(min_length=10, max_length=100000)

class TestRequest(BaseModel):
    repo_id: str = Field(min_length=8, max_length=80)
    command: Literal["pytest", "unittest", "auto"] = "auto"
