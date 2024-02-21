import filecmp
from pathlib import Path

from cognite.neat.config import copy_examples_to_directory
from cognite.neat.constants import EXAMPLE_GRAPHS, EXAMPLE_RULES, EXAMPLE_WORKFLOWS
from cognite.neat.rules.models.rules import Rules


def test_load_excel(transformation_rules: Rules):
    assert transformation_rules


def test_copy_examples_to_directory(tmp_path: Path):
    target_path = tmp_path / "data"
    copy_examples_to_directory(target_path)

    rapport = filecmp.dircmp(target_path / "rules", EXAMPLE_RULES)
    assert not rapport.diff_files

    rapport = filecmp.dircmp(target_path / "source-graphs", EXAMPLE_GRAPHS)
    assert not rapport.diff_files

    rapport = filecmp.dircmp(target_path / "workflows", EXAMPLE_WORKFLOWS)
    assert not rapport.diff_files