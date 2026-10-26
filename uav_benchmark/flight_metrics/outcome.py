from ..registry import metric
from ..types import MetricResult


@metric("goal_success", "flight", "1")
def goal_success(context):
    return MetricResult(int(context["termination"] == "goal_reached"), "1")


@metric("collision", "flight", "1")
def collision(context):
    return MetricResult(int(context["termination"] == "collision"), "1")
