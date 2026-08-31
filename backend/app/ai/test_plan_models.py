from dataclasses import dataclass, field
from typing import Literal

TestPlanCategory = Literal[
    "happy",
    "validation",
    "edge",
    "auth",
    "errors",
]


@dataclass(frozen=True)
class TestPlanItem:
    __test__ = False

    category: TestPlanCategory
    description: str
    grounded_facts: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.description.strip():
            raise ValueError("Test plan item description cannot be empty.")

        if not self.grounded_facts:
            raise ValueError("Test plan item must contain at least one grounded fact.")


@dataclass(frozen=True)
class TestPlan:
    __test__ = False

    endpoint: str
    items: list[TestPlanItem]

    def __post_init__(self) -> None:
        if not self.endpoint.strip():
            raise ValueError("Test plan endpoint cannot be empty.")

        if not self.items:
            raise ValueError("Test plan must contain at least one item.")
