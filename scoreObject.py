from dataclasses import dataclass, field
from priority import Priority


@dataclass
class PriorityScore:
    priority: Priority
    score: float


@dataclass
class Score:
    score_value: float = 0.0
    priority_scores: list[PriorityScore] = field(default_factory=list)
