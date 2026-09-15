"""Versioned input contracts. No payload can assign its tenant, plane or trust domain."""
from datetime import datetime, timezone
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Identifier = Annotated[str, Field(min_length=1, max_length=160, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]*$")]
Digest = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
Revision = Annotated[str, Field(pattern=r"^[a-f0-9]{40}$")]
Plane = Literal['operational', 'public_intelligence', 'historical', 'lab']
Action = Literal['runtime_observed', 'repository_ref_observed', 'protected_action',
                 'shared_state_read', 'shared_state_write', 'report_observed']

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)

class Event(Strict):
    schema_version: Literal[1] = 1
    event_id: Identifier
    event_time: datetime
    time_uncertainty_ms: Annotated[int, Field(ge=0, le=300000)]
    action: Action
    actor: Identifier
    workload: Identifier
    resource: Identifier
    outcome: Literal['success', 'denied', 'failure', 'unknown']
    authorization: Literal['allowed', 'denied', 'unknown']
    artifact_digest: Digest | None = None
    revision: Revision | None = None
    # A safe source receipt identifier, not an arbitrary URL or executable text.
    receipt_id: Identifier

    @field_validator('schema_version', mode='before')
    @classmethod
    def version(cls,value):
        if type(value) is not int:raise ValueError('Integer schema version required')
        return value

    @field_validator('event_time', mode='before')
    @classmethod
    def time(cls, value):
        if isinstance(value, str):
            try: value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError: raise ValueError('ISO-8601 timestamp required') from None
        if not isinstance(value, datetime) or value.tzinfo is None:
            raise ValueError('Explicit timezone required')
        return value.astimezone(timezone.utc)

    @model_validator(mode='after')
    def shape(self):
        if self.action == 'repository_ref_observed' and self.revision is None:
            raise ValueError('Repository observations require a revision')
        if self.action in ('shared_state_read', 'shared_state_write') and self.artifact_digest is None:
            raise ValueError('Shared state observations require an artifact digest')
        return self

class Enrollment(Strict):
    source_id: Identifier
    plane: Plane
    trust_domain: Identifier
    kind: Literal['repository', 'shared_service', 'runtime', 'public_report']
    resources: Annotated[list[Identifier], Field(min_length=1, max_length=64)]
    workloads: Annotated[dict[Identifier, Identifier], Field(min_length=1, max_length=64)]
    expected_revisions: dict[Identifier, Revision] = Field(default_factory=dict)
    max_silence_seconds: Annotated[int, Field(ge=5, le=86400)] = 300

    @model_validator(mode='after')
    def scope(self):
        if len(set(self.resources)) != len(self.resources): raise ValueError('Duplicate resource')
        if not set(self.expected_revisions).issubset(self.resources): raise ValueError('Ref outside source scope')
        if self.kind != 'repository' and self.expected_revisions: raise ValueError('Only repository sources can pin refs')
        if self.kind == 'public_report' and self.plane == 'operational': raise ValueError('Public reports are not operational telemetry')
        return self

class Checkpoint(Strict):
    cursor: Identifier
    complete: bool
    # Complete means collector-reported completion of its defined scope, not independent proof.

class Review(Strict):
    decision: Literal['investigating', 'dismissed', 'closed']
    reason: Literal['needs_original_evidence', 'authorized_change', 'benign_explanation', 'recovery_verified']
    evidence_event_ids: Annotated[list[Digest], Field(min_length=1, max_length=32)]
