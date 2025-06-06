from collections import defaultdict
from collections.abc import Iterable
from typing import cast

from cognite.client import data_modeling as dm
from cognite.client.data_classes.data_modeling.instances import Instance

from cognite.neat._constants import DEFAULT_NAMESPACE
from cognite.neat._graph.extractors import DMSExtractor
from tests.data import car


class TestDMSExtractor:
    def test_extract_instances(self) -> None:
        total_instances_pair_by_view: dict[dm.ViewId, tuple[int | None, list[Instance]]] = defaultdict(lambda: (0, []))
        for instance in instance_apply_to_read(car.INSTANCES):
            if isinstance(instance, dm.Node):
                view_id = next(iter(instance.properties.keys()))
            else:
                # Hardcoded for this test - all edges belong to this view
                view_id = dm.ViewId("sp_example_car", "Car", "v1")
            total_instances, instances = total_instances_pair_by_view[view_id]
            instances.append(instance)
            total_instances_pair_by_view[view_id] = total_instances + 1, instances

        extractor = DMSExtractor(
            total_instances_pair_by_view,
            overwrite_namespace=DEFAULT_NAMESPACE,
        )
        expected_triples = set(car.TRIPLES)

        triples = set(extractor.extract())

        missing_triples = expected_triples - triples
        assert len(missing_triples) == 0
        extra_triples = triples - expected_triples
        assert len(extra_triples) == 0


def instance_apply_to_read(instances: Iterable[dm.NodeApply | dm.EdgeApply]) -> Iterable[Instance]:
    for instance in instances:
        if isinstance(instance, dm.NodeApply):
            yield dm.Node(
                space=instance.space,
                external_id=instance.external_id,
                type=instance.type,
                last_updated_time=0,
                created_time=0,
                version=instance.existing_version,
                deleted_time=None,
                properties={cast(dm.ViewId, source.source): source.properties for source in instance.sources or []},
            )
        elif isinstance(instance, dm.EdgeApply):
            yield dm.Edge(
                space=instance.space,
                external_id=instance.external_id,
                type=instance.type,
                start_node=instance.start_node,
                end_node=instance.end_node,
                last_updated_time=0,
                created_time=0,
                version=instance.existing_version,
                deleted_time=None,
                properties={cast(dm.ViewId, source.source): source.properties for source in instance.sources or []},
            )
        else:
            raise NotImplementedError(f'Unknown instance type "{type(instance)}"')
