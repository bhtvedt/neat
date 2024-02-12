from datetime import datetime
from typing import ClassVar

from rdflib import Namespace

from .base import Prefix, RoleTypes, RuleModel
from .domain_rules import DomainMetadata


class InformationArchitectMetadata(DomainMetadata):
    role: ClassVar[RoleTypes] = RoleTypes.information_architect
    prefix: Prefix
    namespace: Namespace
    version: str
    contributor: str | list[str]
    created: datetime
    updated: datetime

    @classmethod
    def from_domain_expert_metadata(
        cls,
        metadata: DomainMetadata,
        prefix: str | None = None,
        namespace: Namespace | None = None,
        version: str | None = None,
        contributor: str | list[str] | None = None,
        created: datetime | None = None,
        updated: datetime | None = None,
    ):
        metadata_as_dict = metadata.model_dump()
        metadata_as_dict["prefix"] = prefix or "neat"
        metadata_as_dict["namespace"] = namespace or Namespace("http://purl.org/cognite/neat#")
        metadata_as_dict["version"] = version or "0.1.0"
        metadata_as_dict["contributor"] = contributor or "Cognite"
        metadata_as_dict["created"] = created or datetime.utcnow()
        metadata_as_dict["updated"] = updated or datetime.utcnow()
        return cls(**metadata_as_dict)


class InformationArchitectRules(RuleModel):
    metadata: InformationArchitectMetadata