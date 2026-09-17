"""In-memory project store.

Deliberately not a database. Projects live for the length of a planning session
and nothing here needs to survive a restart. Adding persistence would mean
migrations, connection handling and a deployment dependency, for no capability
this product actually needs.

Bounded so a long-running demo cannot grow without limit.
"""

import uuid
from collections import OrderedDict

from ..api.schemas import BathroomBrief, PlanResponse

MAX_PROJECTS = 200


class ProjectStore:
    def __init__(self, max_projects: int = MAX_PROJECTS) -> None:
        self._projects: OrderedDict[str, PlanResponse] = OrderedDict()
        self._max = max_projects

    def new_id(self) -> str:
        return uuid.uuid4().hex[:12]

    def save(self, plan: PlanResponse) -> PlanResponse:
        self._projects[plan.project_id] = plan
        self._projects.move_to_end(plan.project_id)
        while len(self._projects) > self._max:
            self._projects.popitem(last=False)
        return plan

    def get(self, project_id: str) -> PlanResponse | None:
        plan = self._projects.get(project_id)
        if plan is not None:
            self._projects.move_to_end(project_id)
        return plan

    def brief_for(self, project_id: str) -> BathroomBrief | None:
        plan = self.get(project_id)
        return plan.brief if plan else None

    def clear(self) -> None:
        self._projects.clear()

    def __len__(self) -> int:
        return len(self._projects)


store = ProjectStore()
