from dataclasses import dataclass


@dataclass(frozen=True)
class MetricSpec:
    name: str
    scope: str
    unit: str
    function: object


REGISTRY = {}


def metric(name, scope, unit):
    def register(function):
        if name in REGISTRY:
            raise ValueError(f"Duplicate metric identifier: {name}")
        REGISTRY[name] = MetricSpec(name, scope, unit, function)
        return function
    return register
