import math
import sys
import warnings
from datetime import datetime
from typing import TYPE_CHECKING, Any, ClassVar, Literal

from cognite.client import data_modeling as dm
from pydantic import Field, field_serializer, field_validator, model_validator
from pydantic.main import IncEx
from pydantic_core.core_schema import ValidationInfo

from cognite.neat.issues import MultiValueError
from cognite.neat.issues.warnings import (
    PrincipleMatchingSpaceAndVersionWarning,
    PrincipleSolutionBuildsOnEnterpriseWarning,
)
from cognite.neat.rules.models._base import (
    BaseMetadata,
    BaseRules,
    DataModelType,
    ExtensionCategory,
    RoleTypes,
    SchemaCompleteness,
    SheetEntity,
    SheetList,
)
from cognite.neat.rules.models._types import (
    ExternalIdType,
    PropertyType,
    StrListType,
    VersionType,
)
from cognite.neat.rules.models.data_types import DataType
from cognite.neat.rules.models.entities import (
    ClassEntity,
    ContainerEntity,
    ContainerEntityList,
    DMSUnknownEntity,
    ReferenceEntity,
    URLEntity,
    ViewEntity,
    ViewEntityList,
    ViewPropertyEntity,
)
from cognite.neat.rules.models.wrapped_entities import HasDataFilter, NodeTypeFilter, RawFilter

from ._schema import DMSSchema

if TYPE_CHECKING:
    pass

if sys.version_info >= (3, 11):
    pass
else:
    pass

_DEFAULT_VERSION = "1"


class DMSMetadata(BaseMetadata):
    role: ClassVar[RoleTypes] = RoleTypes.dms
    data_model_type: DataModelType = Field(DataModelType.enterprise, alias="dataModelType")
    schema_: SchemaCompleteness = Field(alias="schema")
    extension: ExtensionCategory = ExtensionCategory.addition
    space: ExternalIdType
    name: str | None = Field(
        None,
        description="Human readable name of the data model",
        min_length=1,
        max_length=255,
    )
    description: str | None = Field(None, min_length=1, max_length=1024)
    external_id: ExternalIdType = Field(alias="externalId")
    version: VersionType
    creator: StrListType
    created: datetime = Field(
        description=("Date of the data model creation"),
    )
    updated: datetime = Field(
        description=("Date of the data model update"),
    )

    @field_validator("*", mode="before")
    def strip_string(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_serializer("schema_", "extension", "data_model_type", when_used="always")
    @staticmethod
    def as_string(value: SchemaCompleteness | ExtensionCategory | DataModelType) -> str:
        return str(value)

    @field_validator("schema_", mode="plain")
    def as_enum_schema(cls, value: str) -> SchemaCompleteness:
        return SchemaCompleteness(value)

    @field_validator("extension", mode="plain")
    def as_enum_extension(cls, value: str) -> ExtensionCategory:
        return ExtensionCategory(value)

    @field_validator("data_model_type", mode="plain")
    def as_enum_model_type(cls, value: str) -> DataModelType:
        return DataModelType(value)

    @field_validator("description", mode="before")
    def nan_as_none(cls, value):
        if isinstance(value, float) and math.isnan(value):
            return None
        return value

    def as_space(self) -> dm.SpaceApply:
        return dm.SpaceApply(
            space=self.space,
        )

    def as_data_model_id(self) -> dm.DataModelId:
        return dm.DataModelId(space=self.space, external_id=self.external_id, version=self.version)

    def as_data_model(self) -> dm.DataModelApply:
        suffix = f"Creator: {', '.join(self.creator)}"
        if self.description:
            description = f"{self.description} Creator: {', '.join(self.creator)}"
        else:
            description = suffix

        return dm.DataModelApply(
            space=self.space,
            external_id=self.external_id,
            name=self.name or None,
            version=self.version or "missing",
            description=description,
            views=[],
        )

    def as_identifier(self) -> str:
        return repr(self.as_data_model_id())

    def get_prefix(self) -> str:
        return self.space


class DMSProperty(SheetEntity):
    view: ViewEntity = Field(alias="View")
    view_property: str = Field(alias="View Property")
    name: str | None = Field(alias="Name", default=None)
    description: str | None = Field(alias="Description", default=None)
    connection: Literal["direct", "edge", "reverse"] | None = Field(None, alias="Connection")
    value_type: DataType | ViewPropertyEntity | ViewEntity | DMSUnknownEntity = Field(alias="Value Type")
    nullable: bool | None = Field(default=None, alias="Nullable")
    immutable: bool | None = Field(default=None, alias="Immutable")
    is_list: bool | None = Field(default=None, alias="Is List")
    default: str | int | dict | None = Field(None, alias="Default")
    reference: URLEntity | ReferenceEntity | None = Field(default=None, alias="Reference", union_mode="left_to_right")
    container: ContainerEntity | None = Field(None, alias="Container")
    container_property: str | None = Field(None, alias="Container Property")
    index: StrListType | None = Field(None, alias="Index")
    constraint: StrListType | None = Field(None, alias="Constraint")
    class_: ClassEntity = Field(alias="Class (linage)")
    property_: PropertyType = Field(alias="Property (linage)")

    @field_validator("nullable")
    def direct_relation_must_be_nullable(cls, value: Any, info: ValidationInfo) -> None:
        if info.data.get("connection") == "direct" and value is False:
            raise ValueError("Direct relation must be nullable")
        return value

    @field_validator("value_type", mode="after")
    def connections_value_type(
        cls, value: ViewPropertyEntity | ViewEntity | DMSUnknownEntity, info: ValidationInfo
    ) -> DataType | ViewPropertyEntity | ViewEntity | DMSUnknownEntity:
        if (connection := info.data.get("connection")) is None:
            return value
        if connection == "direct" and not isinstance(value, ViewEntity | DMSUnknownEntity):
            raise ValueError(f"Direct relation must have a value type that points to a view, got {value}")
        elif connection == "edge" and not isinstance(value, ViewEntity):
            raise ValueError(f"Edge connection must have a value type that points to a view, got {value}")
        elif connection == "reverse" and not isinstance(value, ViewPropertyEntity | ViewEntity):
            raise ValueError(
                f"Reverse connection must have a value type that points to a view or view property, got {value}"
            )
        return value

    @field_serializer("value_type", when_used="always")
    @staticmethod
    def as_dms_type(value_type: DataType | ViewPropertyEntity | ViewEntity) -> str:
        if isinstance(value_type, DataType):
            return value_type.dms._type
        else:
            return str(value_type)


class DMSContainer(SheetEntity):
    container: ContainerEntity = Field(alias="Container")
    name: str | None = Field(alias="Name", default=None)
    description: str | None = Field(alias="Description", default=None)
    reference: URLEntity | ReferenceEntity | None = Field(alias="Reference", default=None, union_mode="left_to_right")
    constraint: ContainerEntityList | None = Field(None, alias="Constraint")
    class_: ClassEntity = Field(alias="Class (linage)")

    def as_container(self) -> dm.ContainerApply:
        container_id = self.container.as_id()
        constraints: dict[str, dm.Constraint] = {}
        for constraint in self.constraint or []:
            requires = dm.RequiresConstraint(constraint.as_id())
            constraints[f"{constraint.space}_{constraint.external_id}"] = requires

        return dm.ContainerApply(
            space=container_id.space,
            external_id=container_id.external_id,
            name=self.name or None,
            description=self.description,
            constraints=constraints or None,
            properties={},
        )


class DMSView(SheetEntity):
    view: ViewEntity = Field(alias="View")
    name: str | None = Field(alias="Name", default=None)
    description: str | None = Field(alias="Description", default=None)
    implements: ViewEntityList | None = Field(None, alias="Implements")
    reference: URLEntity | ReferenceEntity | None = Field(alias="Reference", default=None, union_mode="left_to_right")
    filter_: HasDataFilter | NodeTypeFilter | RawFilter | None = Field(None, alias="Filter")
    in_model: bool = Field(True, alias="In Model")
    class_: ClassEntity = Field(alias="Class (linage)")

    def as_view(self) -> dm.ViewApply:
        view_id = self.view.as_id()
        implements = [parent.as_id() for parent in self.implements or []] or None
        if implements is None and isinstance(self.reference, ReferenceEntity):
            # Fallback to the reference if no implements are provided
            parent = self.reference.as_view_id()
            if (parent.space, parent.external_id) != (view_id.space, view_id.external_id):
                implements = [parent]

        return dm.ViewApply(
            space=view_id.space,
            external_id=view_id.external_id,
            version=view_id.version or _DEFAULT_VERSION,
            name=self.name or None,
            description=self.description,
            implements=implements,
            properties={},
        )


class DMSRules(BaseRules):
    metadata: DMSMetadata = Field(alias="Metadata")
    properties: SheetList[DMSProperty] = Field(alias="Properties")
    views: SheetList[DMSView] = Field(alias="Views")
    containers: SheetList[DMSContainer] | None = Field(None, alias="Containers")
    last: "DMSRules | None" = Field(None, alias="Last", description="The previous version of the data model")
    reference: "DMSRules | None" = Field(None, alias="Reference")

    @field_validator("reference")
    def check_reference_of_reference(cls, value: "DMSRules | None", info: ValidationInfo) -> "DMSRules | None":
        if value is None:
            return None
        if value.reference is not None:
            raise ValueError("Reference rules cannot have a reference")
        if value.metadata.data_model_type == DataModelType.solution and (metadata := info.data.get("metadata")):
            warnings.warn(
                PrincipleSolutionBuildsOnEnterpriseWarning(
                    f"The solution model {metadata.as_data_model_id()} is referencing another "
                    f"solution model {value.metadata.as_data_model_id()}",
                ),
                stacklevel=2,
            )
        return value

    @field_validator("views")
    def matching_version_and_space(cls, value: SheetList[DMSView], info: ValidationInfo) -> SheetList[DMSView]:
        if not (metadata := info.data.get("metadata")):
            return value
        model_version = metadata.version
        if different_version := [view.view.as_id() for view in value if view.view.version != model_version]:
            for view_id in different_version:
                warnings.warn(
                    PrincipleMatchingSpaceAndVersionWarning(
                        f"The view {view_id!r} has a different version than the data model version, {model_version}",
                    ),
                    stacklevel=2,
                )
        if different_space := [view.view.as_id() for view in value if view.view.space != metadata.space]:
            for view_id in different_space:
                warnings.warn(
                    PrincipleMatchingSpaceAndVersionWarning(
                        f"The view {view_id!r} is in a different space than the data model space, {metadata.space}",
                    ),
                    stacklevel=2,
                )
        return value

    @model_validator(mode="after")
    def post_validation(self) -> "DMSRules":
        from ._validation import DMSPostValidation

        issue_list = DMSPostValidation(self).validate()
        if issue_list.warnings:
            issue_list.trigger_warnings()
        if issue_list.has_errors:
            raise MultiValueError(issue_list.errors)
        return self

    def dump(
        self,
        mode: Literal["python", "json"] = "python",
        by_alias: bool = False,
        exclude: IncEx = None,
        exclude_none: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        as_reference: bool = False,
    ) -> dict[str, Any]:
        from ._serializer import _DMSRulesSerializer

        dumped = self.model_dump(
            mode=mode,
            by_alias=by_alias,
            exclude=exclude,
            exclude_none=exclude_none,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
        )
        space, version = self.metadata.space, self.metadata.version
        serializer = _DMSRulesSerializer(by_alias, space, version)
        clean = serializer.clean(dumped, as_reference)
        last = "Last" if by_alias else "last"
        if last_dump := clean.get(last):
            clean[last] = serializer.clean(last_dump, False)
        reference = "Reference" if by_alias else "reference"
        if self.reference and (ref_dump := clean.get(reference)):
            space, version = self.reference.metadata.space, self.reference.metadata.version
            clean[reference] = _DMSRulesSerializer(by_alias, space, version).clean(ref_dump, True)
        return clean

    def as_schema(self, include_pipeline: bool = False, instance_space: str | None = None) -> DMSSchema:
        from ._exporter import _DMSExporter

        return _DMSExporter(self, include_pipeline, instance_space).to_schema()
