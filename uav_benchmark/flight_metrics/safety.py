import math
from ..registry import metric
from ..types import MetricResult


@metric("min_obstacle_clearance_m", "flight", "m")
def minimum_clearance(context):
    value = context["obstacle_clearance"]
    if math.isinf(value):
        return MetricResult(None, "m", "unbounded", "Scene has no obstacles")
    return MetricResult(value, "m", note="Minimum on recorded piecewise-linear path")
