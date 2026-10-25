from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from datetime import time
from abc import ABC, abstractmethod


class EvaluationMethod(ABC):
    @abstractmethod
    def score(self, offer, priority_type=None, dataset=None, qualifier=None) -> float:
        pass


class Comparative(EvaluationMethod):
    def score(self, offer, priority_type=None, dataset=None, qualifier=None) -> float:
        modifier = 1.0;
        if qualifier:
            match qualifier.operator:
                case QualifierOperator.LESS_THAN:
                    if offer == qualifier.value:
                        modifier = .75
                    elif offer < qualifier.value:
                        modifier = .5
                case QualifierOperator.MORE_THAN:
                    if offer == qualifier.value:
                        modifier = .75
                    elif offer > qualifier.value:
                        modifier = .5
                case _:
                    pass

        minimum, maximum = self.determine_min_max(dataset)

        if maximum == minimum:
            return 1.0

        normalized = (offer - minimum) / (maximum - minimum)
        #Customer rating is the exception to lower value is better so it needs to be calculated 
        #Slightly different
        if priority_type is PriorityType.CUSTOMER_RATING:
            return normalized * modifier
        
        return (1 - normalized) * modifier

    def determine_min_max(self,dataset):
        if not dataset:
            raise ValueError("Cannot score against an empty dataset.")

        return min(dataset),max(dataset)
                


class Binary(EvaluationMethod):
    def score(self, offer, priority_type, dataset=None, qualifier=None) -> float:
        modifier = 1.0;
        if qualifier:
            match qualifier.operator:
                case QualifierOperator.EARLIER_THAN:
                    if not (isinstance(offer, time) and isinstance(qualifier.value, time)):
                        raise TypeError("To evaluate this priority, Both inputs must be datetime.time objects.")
                    if offer == qualifier.value:
                        modifier = .75
                    elif offer > qualifier.value:
                        modifier = 0
                case QualifierOperator.LATER_THAN:
                    if not (isinstance(offer, time) and isinstance(qualifier.value, time)):
                        raise TypeError("To evaluate this priority, Both inputs must be datetime.time objects.")
                    if offer == qualifier.value:
                        modifier = .75
                    elif offer < qualifier.value:
                        modifier = .0
            return modifier
        match priority_type:
            case PriorityType.FLEXIBLE:
                match offer:
                    case 0:
                        return 0
                    case 1: 
                        return .6
                    case 2: 
                        return .4
                    case 3:
                        return 1
            case _:
                return 1.0


class PriorityType(Enum):
    LOWER_PRICE = "trip_price", Comparative, "lower_price"
    FEWER_TRANSFERS = "transfers", Comparative, "fewer_transfers"
    DURATION = "duration", Comparative, "duration"
    ENVIRONMENTAL_IMPACT = "environmental_impact", Comparative, "environmental_impact"

    CUSTOMER_RATING = "customer_rating", Comparative, "customer_rating"
    
    DEPARTURE_BEFORE = "departure_time", Binary, "departure_before"
    DEPARTURE_AFTER = "departure_time", Binary, "departure_after"
    ARRIVAL_BEFORE = "arrival_time", Binary, "arrival_before"
    ARRIVAL_AFTER = "arrival_time", Binary, "arrival_after"
    FLEXIBLE = "flexible", Binary, "flexible"

    def __init__(self, field_name, evaluator_class, key):
        self.field_name = field_name
        self.evaluator_class = evaluator_class
        self.key = key

class QualifierOperator(Enum):
    LESS_THAN = "less_than"
    MORE_THAN = "more_than"

    EARLIER_THAN = "earlier_than"
    LATER_THAN = "later_than"

@dataclass
class Qualifier:
    operator: QualifierOperator
    value: Any


class MissingQualifierForTimeframe(ValueError):
    pass


@dataclass
class Priority:
    priority_type: PriorityType
    weight: int
    qualifier: Qualifier | None = None

    def __init__(self, priority_type, weight, qualifier = None):
        self.priority_type = priority_type
        self.weight = weight
        self.qualifier = qualifier

        if priority_type in (PriorityType.DEPARTURE_BEFORE, PriorityType.DEPARTURE_AFTER, PriorityType.ARRIVAL_BEFORE, PriorityType.ARRIVAL_AFTER):
            if qualifier is None:
                raise MissingQualifierForTimeframe(f"Priority type: {priority_type} requires context of a Qualifier to adequately evaluate Trip quality")

    def score(self, offer, dataset=None):
        field_name = self.priority_type.field_name
        evaluator = self.priority_type.evaluator_class()

        if field_name == PriorityType.FLEXIBLE.field_name:
            flexibility = int(offer.refundable) + 2 * int(offer.changes_allowed)
            value = flexibility
            return evaluator.score(
                value,
                self.priority_type,
                qualifier=self.qualifier,
            ) * self.weight
        else:
            value = getattr(offer,field_name)
            if dataset:
                dataset_values = [
                    item_value
                    for item in dataset
                    if (item_value := getattr(item, field_name)) is not None
                ]
                if value is None or not dataset_values:
                    return 0.0
                return evaluator.score(
                    value,
                    self.priority_type,
                    dataset=dataset_values,
                    qualifier=self.qualifier,
                ) * self.weight
            else:
                return evaluator.score(
                    value,
                    self.priority_type,
                    qualifier=self.qualifier,
                ) * self.weight
        
