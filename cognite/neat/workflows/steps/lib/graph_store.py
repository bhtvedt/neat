import logging
from pathlib import Path
from typing import ClassVar, cast

from cognite.neat.constants import PREFIXES
from cognite.neat.graph.stores import NeatGraphStore, RdfStoreType, drop_graph_store
from cognite.neat.workflows._exceptions import StepNotInitialized
from cognite.neat.workflows.model import FlowMessage
from cognite.neat.workflows.steps.data_contracts import RulesData, SolutionGraph, SourceGraph
from cognite.neat.workflows.steps.step_model import Configurable, Step

__all__ = ["ConfigureDefaultGraphStores", "ResetGraphStores", "ConfigureGraphStore"]

CATEGORY = __name__.split(".")[-1].replace("_", " ").title()


class ConfigureDefaultGraphStores(Step):
    """
    This step initializes the source and solution graph stores
    """

    description = "This step initializes the source and solution graph stores."
    category = CATEGORY
    configurables: ClassVar[list[Configurable]] = [
        Configurable(
            name="source_rdf_store.type",
            value=RdfStoreType.OXIGRAPH,
            label="Data store type for source graph. Supported: oxigraph, memory,file, graphdb, sparql. ",
            options=["oxigraph", "memory", "file", "graphdb", "sparql"],
        ),
        Configurable(
            name="solution_rdf_store.type",
            value=RdfStoreType.OXIGRAPH,
            label="Data store type for solutioin graph. Supported: oxigraph, memory,file, graphdb, sparql",
            options=["oxigraph", "memory", "file", "graphdb", "sparql"],
        ),
        Configurable(
            name="source_rdf_store.disk_store_dir",
            value="source-graph-store",
            label="Local directory for source graph store",
        ),
        Configurable(
            name="source_rdf_store.query_url",
            value="",
            label="Sparql query endpoint.Only for sparql and graphdb store type",
        ),
        Configurable(
            name="source_rdf_store.update_url",
            value="",
            label="Sparql update endpoint.Only for sparql and graphdb store type",
        ),
        Configurable(
            name="solution_rdf_store.query_url",
            value="",
            label="Sparql query endpoint.Only for sparql and graphdb store type",
        ),
        Configurable(
            name="solution_rdf_store.update_url",
            value="",
            label="Sparql update endpoint.Only for sparql and graphdb store type",
        ),
        Configurable(
            name="solution_rdf_store.disk_store_dir",
            value="solution-graph-store",
            label="Local directory for solution graph store",
        ),
        Configurable(
            name="stores_to_configure",
            value="all",
            label="Defines which stores to configure",
            options=["all", "source", "solution"],
        ),
        Configurable(name="solution_rdf_store.api_root_url", value="", label="Root url for graphdb or sparql endpoint"),
    ]

    def run(self, rules_data: RulesData) -> (FlowMessage, SourceGraph, SolutionGraph):  # type: ignore[override, syntax]
        if self.configs is None or self.data_store_path is None:
            raise StepNotInitialized(type(self).__name__)
        logging.info("Initializing source graph")
        stores_to_configure = self.configs["stores_to_configure"]
        source_store_dir = self.configs["source_rdf_store.disk_store_dir"]
        source_store_dir = Path(self.data_store_path) / Path(source_store_dir) if source_store_dir else None
        source_store_type = self.configs["source_rdf_store.type"]
        if stores_to_configure in ["all", "source"]:
            if source_store_type == RdfStoreType.OXIGRAPH and "SourceGraph" in self.flow_context:
                return FlowMessage(output_text="Stores already configured")

            source_graph = NeatGraphStore(
                prefixes=rules_data.rules.prefixes, base_prefix="neat", namespace=PREFIXES["neat"]
            )
            source_graph.init_graph(
                source_store_type,
                self.configs["source_rdf_store.query_url"],
                self.configs["source_rdf_store.update_url"],
                "neat-tnt",
                internal_storage_dir=source_store_dir,
            )
            if stores_to_configure == "source":
                return FlowMessage(output_text="Source graph store configured successfully"), SourceGraph(
                    graph=source_graph
                )

        if stores_to_configure in ["all", "solution"]:
            solution_store_dir = self.configs["solution_rdf_store.disk_store_dir"]
            solution_store_dir = self.data_store_path / Path(solution_store_dir) if solution_store_dir else None
            solution_store_type = self.configs["solution_rdf_store.type"]

            if solution_store_type == RdfStoreType.OXIGRAPH and "SolutionGraph" in self.flow_context:
                return FlowMessage(output_text="Stores already configured")
            solution_graph = NeatGraphStore(
                prefixes=rules_data.rules.prefixes, base_prefix="neat", namespace=PREFIXES["neat"]
            )

            solution_graph.init_graph(
                solution_store_type,
                self.configs["solution_rdf_store.query_url"],
                self.configs["solution_rdf_store.update_url"],
                "tnt-solution",
                internal_storage_dir=solution_store_dir,
            )

            solution_graph.graph_db_rest_url = self.configs["solution_rdf_store.api_root_url"]
            if stores_to_configure == "solution":
                return FlowMessage(output_text="Solution graph store configured successfully"), SolutionGraph(
                    graph=solution_graph
                )

        return (
            FlowMessage(output_text="All graph stores configured successfully"),
            SourceGraph(graph=source_graph),
            SolutionGraph(graph=solution_graph),
        )


class ResetGraphStores(Step):
    """
    This step resets graph stores to their initial state (clears all data)
    """

    description = "This step resets graph stores to their initial state (clears all data)."
    category = CATEGORY

    def run(self) -> FlowMessage:  # type: ignore[override, syntax]
        if self.configs is None or self.data_store_path is None:
            raise StepNotInitialized(type(self).__name__)
        source_store_type = self.configs["source_rdf_store.type"]
        solution_store_type = self.configs["solution_rdf_store.type"]
        if source_store_type == RdfStoreType.OXIGRAPH and solution_store_type == RdfStoreType.OXIGRAPH:
            if "SourceGraph" not in self.flow_context or "SolutionGraph" not in self.flow_context:
                source_store_dir = (
                    Path(self.data_store_path) / Path(value)
                    if (value := self.configs["source_rdf_store.disk_store_dir"])
                    else None
                )
                solution_store_dir = (
                    self.data_store_path / Path(value)
                    if (value := self.configs["solution_rdf_store.disk_store_dir"])
                    else None
                )
                if solution_store_dir:
                    drop_graph_store(None, source_store_dir, force=True)
                if solution_store_dir:
                    drop_graph_store(None, solution_store_dir, force=True)
            else:
                if "SourceGraph" in self.flow_context:
                    cast(SourceGraph, self.flow_context["SourceGraph"]).graph.drop()
                if "SolutionGraph" in self.flow_context:
                    cast(SolutionGraph, self.flow_context["SolutionGraph"]).graph.drop()
        return FlowMessage(output_text="Stores Reset")


class ConfigureGraphStore(Step):
    """
    This step initializes source and solution graph store
    """

    description = "This step initializes the source and solution graph stores."
    category = CATEGORY
    configurables: ClassVar[list[Configurable]] = [
        Configurable(
            name="graph_name",
            value="source",
            label="Name of the data store. Supported: solution, source ",
            options=["source", "solution"],
        ),
        Configurable(
            name="store_type",
            value=RdfStoreType.OXIGRAPH,
            label="Data store type for source graph. Supported: oxigraph, memory,file, graphdb, sparql. ",
            options=["oxigraph", "memory", "file", "graphdb", "sparql"],
        ),
        Configurable(
            name="disk_store_dir",
            value="source-graph-store",
            label="Local directory that is used as local graph store.Only for oxigraph, file store types",
        ),
        Configurable(
            name="sparql_query_url", value="", label="Query url for sparql endpoint.Only for sparql store type"
        ),
        Configurable(
            name="sparql_update_url", value="", label="Update url for sparql endpoint.Only for sparql store type"
        ),
        Configurable(
            name="db_server_api_root_url", value="", label="Root url for graphdb or sparql endpoint.Only for graphdb"
        ),
        Configurable(
            name="init_procedure",
            value="reset",
            label="Operations to be performed on the graph store as part of init and configuration process. \
              Supported options : reset, clear, none",
            options=["reset", "none"],
        ),
    ]

    def run(  # type: ignore[override]
        self, rules_data: RulesData
    ) -> (FlowMessage, SourceGraph | SolutionGraph):  # type: ignore[syntax]
        if self.configs is None or self.data_store_path is None:
            raise StepNotInitialized(type(self).__name__)
        logging.info("Initializing graph")
        store_dir = self.data_store_path / Path(value) if (value := self.configs["disk_store_dir"]) else None
        store_type = self.configs["store_type"]
        graph_name_mapping = {"source": "SourceGraph", "solution": "SolutionGraph"}

        graph_name = graph_name_mapping[self.configs["graph_name"]]

        if self.configs["init_procedure"] == "reset":
            self.reset_store(store_type, graph_name, store_dir)

        if store_type == RdfStoreType.OXIGRAPH and graph_name in self.flow_context:
            # OXIGRAPH doesn't like to be initialized twice without a good reason
            return FlowMessage(output_text="Stores already configured")

        graph_store = NeatGraphStore(prefixes=rules_data.rules.prefixes, base_prefix="neat", namespace=PREFIXES["neat"])
        graph_store.init_graph(
            store_type,
            self.configs["sparql_query_url"],
            self.configs["sparql_update_url"],
            "neat-tnt",
            internal_storage_dir=store_dir,
        )

        return (
            FlowMessage(output_text="Graph store configured successfully"),
            SourceGraph(graph=graph_store) if graph_name == "SourceGraph" else SolutionGraph(graph=graph_store),
        )

    def reset_store(self, store_type: str, graph_name: str, data_store_dir: Path | None):
        if store_type == RdfStoreType.OXIGRAPH:
            if graph_name not in self.flow_context:
                if data_store_dir:
                    drop_graph_store(None, data_store_dir, force=True)
            else:
                cast(SourceGraph | SolutionGraph, self.flow_context[graph_name]).graph.drop()
        return