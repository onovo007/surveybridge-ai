"""Typed normalized records retain the entire original API record."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SourceRecord(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    raw: dict[str, Any]
    source_url: str
    retrieved_utc: str
    source_response_hash: str
    source_record_hash: str


class Country(SourceRecord):
    id: str
    name: str


class Survey(SourceRecord):
    id: str
    country_id: str
    year: int | None
    year_label: str | None = None
    survey_type: str | None = None
    fieldwork_start: str | None = None
    fieldwork_end: str | None = None


class Indicator(SourceRecord):
    id: str
    label: str
    definition: str | None
    denominator: str | None
    unit: str | None


class Observation(SourceRecord):
    source_row_id: str
    source_country_id: str
    source_country_name: str
    source_survey_id: str
    survey_year: int | None
    survey_year_label: str | None
    survey_type: str | None
    indicator_id: str
    indicator_label: str
    value: float | None
    unit: str | None
    lower_ci: float | None
    upper_ci: float | None
    breakdown_type: str | None
    breakdown_value: str | None
    characteristic_id: str | None
    by_variable_id: str | None
    by_variable_label: str | None
    region_id: str | None
    is_total: bool | None
    is_preferred: bool | None
    definition: str | None
    denominator: str | None
    denominator_weighted: float | None
    denominator_unweighted: float | None
    precision: int | None
    warnings: list[str] = Field(default_factory=list)


class ComparabilityFinding(BaseModel):
    severity: Literal["info", "caution", "block"]
    affected_keys: list[str]
    attribute: str
    explanation: str
    evidence: list[str]
    recommendation: str


class ProvenanceManifest(BaseModel):
    release_version: str
    git_sha: str | None
    project_id: str
    query_filters: dict[str, Any]
    source_endpoints: list[str]
    fetch_dates: list[str]
    raw_response_hashes: list[str]
    source_row_ids: list[str]
    output_checksums: dict[str, str]
    warnings: list[str]
    transformation_history: list[str]
    citation: str


class Result(BaseModel):
    status: Literal["ok", "error", "blocked"] = "ok"
    data: Any = None
    warnings: list[str] = Field(default_factory=list)
    source: list[dict[str, Any]] = Field(default_factory=list)
    truncated: bool = False
    pagination: dict[str, Any] = Field(default_factory=dict)
