import math
from ..registry import metric
from ..types import MetricResult


@metric("path_excess_factor", "flight", "1")
def path_excess(context):
    d0 = context["initial_distance"]
    if d0 == 0:
        return MetricResult(None, "1", "undefined", "Initial goal distance is zero")
    note = "Straight-line reference; incomplete flights can have negative values"
    return MetricResult(context["path_length"] / d0 - 1, "1", note=note)


@metric("average_speed_mps", "flight", "m/s")
def average_speed(context):
    if context["duration"] == 0:
        return MetricResult(None, "m/s", "undefined", "Zero duration")
    return MetricResult(context["path_length"] / context["duration"], "m/s")


@metric("relative_end_distance", "flight", "1")
def relative_end_distance(context):
    if context["initial_distance"] == 0:
        return MetricResult(None, "1", "undefined", "Initial goal distance is zero")
    return MetricResult(context["final_distance"] / context["initial_distance"], "1")
