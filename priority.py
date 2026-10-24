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
        return (1 - ((offer-minimum) / (maximum - minimum)))*modifier

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


class PriorityType(Enum):
    LOWER_PRICE = "trip_price", Comparative
    FEWER_TRANSFERS = "transfers", Comparative
    DURATION = "duration", Comparative

    DEPARTURE_BEFORE = "departure_time", Binary
    DEPARTURE_AFTER = "departure_time", Binary

    ARRIVAL_BEFORE = "arrival_time", Binary
    ARRIVAL_AFTER = "arrival_time", Binary

    CUSTOMER_RATING = "customer_rating", Comparative
    FLEXIBLE = "flexible", Binary
    ENVIRONMENTAL_IMPACT = "environmental_impact", Binary

    def __init__(self, field_name, evaluator_class):
        self.field_name = field_name
        self.evaluator_class = evaluator_class

class QualifierOperator(Enum):
    LESS_THAN = "less_than"
    MORE_THAN = "more_than"

    EARLIER_THAN = "earlier_than"
    LATER_THAN = "later_than"

@dataclass
class Qualifier:
    operator: QualifierOperator
    value: Any

@dataclass
class Priority:
    priority_type: PriorityType
    weight: int
    qualifier: Qualifier | None = None

    def set_qualifier(rule, limit):
        qualifier = Qualifier(rule,limit)
        self.qualifier = qualifier

    def score(self, offer, dataset=None):
        field_name = self.priority_type.field_name
        evaluator = self.priority_type.evaluator_class()

        if field_name == PriorityType.FLEXIBLE.field_name:
            flexibility = int(offer.refundable) + 2 * int(offer.changes_allowed)
            value = flexibility
            return evaluator.score(value, self.priority_type, self.qualifier) * self.weight
        else:
            value = getattr(offer,field_name)
            if dataset:
                dataset_values = [getattr(item,field_name) for item in dataset]
                return evaluator.score(value, self.priority_type,  dataset_values, self.qualifier) * self.weight
            else:
                return evaluator.score(value, self.priority_type, self.qualifier) * self.weight
        

