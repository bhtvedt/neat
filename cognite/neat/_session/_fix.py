from cognite.neat._issues._base import IssueList
from cognite.neat._rules.transformers import IMFRuleMapper, ToCompliantEntities
from cognite.neat._utils.affix import Affix

from ._state import SessionState
from .exceptions import session_class_wrapper


@session_class_wrapper
class FixAPI:
    """Apply variety of fix methods to data model and isntances"""

    def __init__(self, state: SessionState, verbose: bool) -> None:
        self._state = state
        self._verbose = verbose
        self.data_model = DataModelFixAPI(state, verbose)


@session_class_wrapper
class DataModelFixAPI:
    def __init__(self, state: SessionState, verbose: bool) -> None:
        self._state = state
        self._verbose = verbose

    def cdf_compliant_external_ids(self, _prefix: str = "prefix", _suffix: str = "suffix") -> IssueList:
        """Convert (information/logical) data model component external ids to CDF compliant entities."""

        return self._state.rule_transform(ToCompliantEntities(Affix(prefix=_prefix, suffix=_suffix)))

    def map_imf_rules(self) -> IssueList:
        return self._state.rule_transform(IMFRuleMapper())
