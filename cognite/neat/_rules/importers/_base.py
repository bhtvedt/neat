from abc import ABC, abstractmethod
from contextlib import suppress
from datetime import datetime
from typing import TYPE_CHECKING, Any, Generic

from rdflib import URIRef

from cognite.neat._constants import DEFAULT_NAMESPACE
from cognite.neat._rules._shared import ReadRules, T_InputRules
from cognite.neat._utils.auxiliary import class_html_doc

if TYPE_CHECKING:
    from cognite.neat._store._provenance import Agent as ProvenanceAgent


class BaseImporter(ABC, Generic[T_InputRules]):
    """
    BaseImporter class which all importers inherit from.
    """

    @abstractmethod
    def to_rules(self) -> ReadRules[T_InputRules]:
        """Creates `Rules` object from the data for target role."""
        raise NotImplementedError()

    def _default_metadata(self) -> dict[str, Any]:
        created_time = self._get_current_time()
        return {
            "schema": "partial",
            "space": "neat",
            "external_id": "NeatImportedDataModel",
            "version": "0.1.0",
            "name": "Neat Imported Data Model",
            "created": created_time,
            "updated": created_time,
            "creator": self._get_username(),
            "description": f"Imported using {type(self).__name__}",
        }

    @classmethod
    def _repr_html_(cls) -> str:
        return class_html_doc(cls)

    @classmethod
    def _get_username(cls) -> str:
        with suppress(KeyError, ImportError):
            import getpass

            return getpass.getuser()
        return "UNKNOWN"

    @classmethod
    def _get_current_time(cls) -> str:
        return datetime.now().replace(microsecond=0).isoformat()

    @property
    def agent(self) -> "ProvenanceAgent":
        """Provenance agent for the importer."""
        from cognite.neat._store._provenance import Agent as ProvenanceAgent

        return ProvenanceAgent(id_=DEFAULT_NAMESPACE[f"agent/{type(self).__name__}"])

    @property
    def description(self) -> str:
        return "MISSING DESCRIPTION"

    @property
    def source_uri(self) -> URIRef:
        return DEFAULT_NAMESPACE["UNKNOWN"]
