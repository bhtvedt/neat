from typing import Any

import pandas as pd
import pytest

from cognite.neat._client.data_classes.schema import DMSSchema
from cognite.neat._rules.importers import ExcelImporter
from cognite.neat._rules.models import DMSRules, InformationInputRules, InformationRules
from cognite.neat._rules.models.dms import DMSInputRules
from cognite.neat._utils.spreadsheet import read_individual_sheet
from tests.config import DATA_FOLDER, DOC_RULES
from tests.data import COGNITE_CORE_ZIP


@pytest.fixture(scope="session")
def alice_spreadsheet() -> dict[str, dict[str, Any]]:
    filepath = DOC_RULES / "cdf-dms-architect-alice.xlsx"
    excel_file = pd.ExcelFile(filepath)
    return {
        "Metadata": dict(pd.read_excel(excel_file, "Metadata", header=None).values),
        "Properties": read_individual_sheet(excel_file, "Properties", False, ["View Property"]),
        "Views": read_individual_sheet(excel_file, "Views", False, ["View"]),
        "Containers": read_individual_sheet(excel_file, "Containers", False, ["Container"]),
    }


@pytest.fixture(scope="session")
def alice_rules(alice_spreadsheet: dict[str, dict[str, Any]]) -> DMSRules:
    return DMSInputRules.load(alice_spreadsheet).as_verified_rules()


@pytest.fixture(scope="session")
def david_spreadsheet() -> dict[str, dict[str, Any]]:
    filepath = DOC_RULES / "information-architect-david.xlsx"
    excel_file = pd.ExcelFile(filepath)
    return {
        "Metadata": dict(pd.read_excel(excel_file, "Metadata", header=None).values),
        "Properties": read_individual_sheet(excel_file, "Properties", expected_headers=["Property"]),
        "Classes": read_individual_sheet(excel_file, "Classes", expected_headers=["Class"]),
    }


@pytest.fixture(scope="session")
def david_rules(david_spreadsheet: dict[str, dict[str, Any]]) -> InformationRules:
    return InformationRules.model_validate(InformationInputRules.load(david_spreadsheet).dump())


@pytest.fixture(scope="session")
def asset_spreadsheet() -> dict[str, dict[str, Any]]:
    filepath = DATA_FOLDER / "asset-architect-test.xlsx"
    excel_file = pd.ExcelFile(filepath)
    return {
        "Metadata": dict(pd.read_excel(excel_file, "Metadata", header=None).values),
        "Properties": read_individual_sheet(excel_file, "Properties", expected_headers=["Property"]),
        "Classes": read_individual_sheet(excel_file, "Classes", expected_headers=["Class"]),
    }


@pytest.fixture(scope="session")
def jimbo_spreadsheet() -> dict[str, dict[str, Any]]:
    filepath = DOC_RULES / "asset-architect-jimbo.xlsx"
    excel_file = pd.ExcelFile(filepath)
    return {
        "Metadata": dict(pd.read_excel(excel_file, "Metadata", header=None).values),
        "Properties": read_individual_sheet(excel_file, "Properties", expected_headers=["Property"]),
        "Classes": read_individual_sheet(excel_file, "Classes", expected_headers=["Class"]),
        "Prefixes": read_individual_sheet(excel_file, "Prefixes", expected_headers=["Prefix"]),
    }


@pytest.fixture(scope="session")
def jon_spreadsheet() -> dict[str, dict[str, Any]]:
    filepath = DOC_RULES / "expert-wind-energy-jon.xlsx"
    excel_file = pd.ExcelFile(filepath)
    return {
        "Metadata": dict(pd.read_excel(excel_file, "Metadata", header=None).values),
        "Properties": read_individual_sheet(excel_file, "Properties", expected_headers=["Property"]),
    }


@pytest.fixture(scope="session")
def emma_spreadsheet() -> dict[str, dict[str, Any]]:
    filepath = DOC_RULES / "expert-grid-emma.xlsx"
    excel_file = pd.ExcelFile(filepath)
    return {
        "Metadata": dict(pd.read_excel(excel_file, "Metadata", header=None).values),
        "Properties": read_individual_sheet(excel_file, "Properties", expected_headers=["Property"]),
        "Classes": read_individual_sheet(excel_file, "Classes", expected_headers=["Class"]),
    }


@pytest.fixture(scope="session")
def olav_rules() -> InformationRules:
    return ExcelImporter(DOC_RULES / "information-analytics-olav.xlsx").to_rules().rules.as_verified_rules()


@pytest.fixture(scope="session")
def olav_dms_rules() -> DMSRules:
    return ExcelImporter(DOC_RULES / "dms-analytics-olav.xlsx").to_rules().rules.as_verified_rules()


@pytest.fixture(scope="session")
def svein_harald_information_rules() -> InformationRules:
    return ExcelImporter(DOC_RULES / "information-addition-svein-harald.xlsx").to_rules().rules.as_verified_rules()


@pytest.fixture(scope="session")
def svein_harald_dms_rules() -> DMSRules:
    return ExcelImporter(DOC_RULES / "dms-addition-svein-harald.xlsx").to_rules().rules.as_verified_rules()


@pytest.fixture(scope="session")
def olav_rebuild_dms_rules() -> DMSRules:
    return ExcelImporter(DOC_RULES / "dms-rebuild-olav.xlsx").to_rules().rules.as_verified_rules()


@pytest.fixture(scope="session")
def cognite_core_schema() -> DMSSchema:
    return DMSSchema.from_zip(COGNITE_CORE_ZIP)
