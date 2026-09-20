"""In-memory project store.

Deliberately not a database. Projects live for the length of a planning session
and nothing here needs to survive a restart. Adding persistence would mean
migrations, connection handling and a deployment dependency, for no capability
this product actually needs.

Bounded so a long-running demo cannot grow without limit.
"""

from collections import OrderedDict
from typing import Any
import uuid

from ..api.schemas import BathroomBrief, PlanResponse
from ..designpulse.models import (
    DesignState,
    VersionHistory,
    create_design_state_from_candidate,
)

MAX_PROJECTS = 200


class ProjectStore:
    def __init__(self, max_projects: int = MAX_PROJECTS) -> None:
        self._projects: OrderedDict[str, PlanResponse] = OrderedDict()
        self._histories: dict[str, VersionHistory] = {}
        self._last_impacts: dict[str, Any] = {}
        self._vision_evidence: dict[str, Any] = {}
        self._max = max_projects

    def new_id(self) -> str:
        return uuid.uuid4().hex[:12]

    def save(self, plan: PlanResponse) -> PlanResponse:
        self._projects[plan.project_id] = plan
        self._projects.move_to_end(plan.project_id)

        # Automatically initialize a V1 DesignState if candidates exist and history is empty
        if plan.candidates and plan.project_id not in self._histories:
            history = VersionHistory(project_id=plan.project_id)
            vision = self._vision_evidence.get(plan.project_id)
            v1_state = create_design_state_from_candidate(
                candidate=plan.candidates[0],
                brief=plan.brief,
                project_id=plan.project_id,
                version_id="v1",
                version_number=1,
                vision_analysis=vision,
            )
            history.add_version(v1_state)
            self._histories[plan.project_id] = history

        while len(self._projects) > self._max:
            evicted_id, _ = self._projects.popitem(last=False)
            self._histories.pop(evicted_id, None)
            self._last_impacts.pop(evicted_id, None)
            self._vision_evidence.pop(evicted_id, None)
        return plan

    def get(self, project_id: str) -> PlanResponse | None:
        plan = self._projects.get(project_id)
        if plan is not None:
            self._projects.move_to_end(project_id)
        return plan

    def brief_for(self, project_id: str) -> BathroomBrief | None:
        plan = self.get(project_id)
        return plan.brief if plan else None

    def get_history(self, project_id: str) -> VersionHistory | None:
        return self._histories.get(project_id)

    def save_design_state(self, state: DesignState, set_active: bool = True) -> DesignState:
        project_id = state.project_id
        history = self._histories.get(project_id)
        if history is None:
            history = VersionHistory(project_id=project_id)
            self._histories[project_id] = history
        history.add_version(state, set_active=set_active)
        return state

    def get_design_state(self, project_id: str, version_id: str | None = None) -> DesignState | None:
        history = self.get_history(project_id)
        if not history or not history.versions:
            # Fallback: if plan exists in store, lazily initialize V1
            plan = self._projects.get(project_id)
            if plan and plan.candidates:
                history = VersionHistory(project_id=plan.project_id)
                v1_state = create_design_state_from_candidate(
                    candidate=plan.candidates[0],
                    brief=plan.brief,
                    project_id=plan.project_id,
                    version_id="v1",
                    version_number=1,
                )
                history.add_version(v1_state)
                self._histories[plan.project_id] = history
            else:
                return None
        if version_id:
            return history.get_version(version_id)
        return history.get_active()

    def set_last_impact(self, project_id: str, report: Any) -> None:
        self._last_impacts[project_id] = report

    def get_last_impact(self, project_id: str) -> Any | None:
        return self._last_impacts.get(project_id)

    def set_vision_evidence(self, project_id: str, evidence: Any) -> None:
        self._vision_evidence[project_id] = evidence

    def get_vision_evidence(self, project_id: str) -> Any | None:
        return self._vision_evidence.get(project_id)

    def clear(self) -> None:
        self._projects.clear()
        self._histories.clear()
        self._last_impacts.clear()
        self._vision_evidence.clear()

    def __len__(self) -> int:
        return len(self._projects)


store = ProjectStore()

