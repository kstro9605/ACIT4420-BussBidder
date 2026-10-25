from dataclasses import dataclass, field
from priority import PriorityType, Priority

@dataclass
class Hierarchy:
    priorities: dict[PriorityType, Priority] = field(default_factory=dict)

    @property
    def total_weight(self) -> float:
        return sum(p.weight for p in self.priorities.values())

    def score(self, payload):
        return_map = []
        for trip in payload:
            score = 0
            for priority in self.priorities.values():
                current_priority_score = priority.score(trip, payload)
                score = score + current_priority_score
            return_map.append((round(score,2), trip))
        return_map.sort(key=lambda item: item[0], reverse=True)
        return return_map
            

    def add_priority(self, priority: Priority) -> None:
        if priority.priority_type in self.priorities:
            raise ValueError(
                f"Priority '{priority.priority_type}' already exists."
            )

        if priority.weight < 0:
            raise ValueError("Weight cannot be negative.")

        if self.total_weight + priority.weight > 100:
            raise ValueError(
                "Total hierarchy weight cannot exceed 100."
            )

        self.priorities[priority.priority_type] = priority

    def remove_priority(self, name: str) -> None:
        del self.priorities[name]

    def get_priority(self, name: PriorityType) -> Priority:
        return self.priorities[name]

    def create_priorities(self, priority_details):
        total_weight = sum(item["priority_weight"] for item in priority_details)
        if total_weight > 100:
            raise OverWeightPrioritiesError("Attempted to create a priority Hierarchy with an overall weight greater that 100 points")
        
        desired_priorities = {}
        for priority_protoype in priority_details:
            priority_type = priority_protoype["priority_type"]
            priority_weight = priority_protoype["priority_weight"]

            priority_key = priority_type
            if priority_key in desired_priorities:
                raise InvalidPriorityBundleException("Bundle of Priorities passed to Hierarchy is invalid and contain duplicate types of priorities")

            if "priority_qualifier" in priority_protoype:
                priority_qualifier = priority_protoype["priority_qualifier"]
                priority = Priority(priority_type, priority_weight, priority_qualifier)
            else:
                priority = Priority(priority_type, priority_weight)
            desired_priorities[priority_key] = priority

        self.priorities = desired_priorities

class OverWeightPrioritiesError(Exception):
    pass
class InvalidPriorityBundleException(Exception):
    pass