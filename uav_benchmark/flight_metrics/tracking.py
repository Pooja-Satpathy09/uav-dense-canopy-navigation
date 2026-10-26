import math
from ..registry import metric
from ..types import MetricResult


@metric("speed_rmse_mps", "flight", "m/s")
def speed_rmse(context):
    if context["duration"] == 0:
        return MetricResult(None, "m/s", "undefined", "Zero duration")
    samples = context["samples"]
    target = context["config"].target_speed_mps
    integral = sum((math.sqrt(sum(v*v for v in b.velocity)) - target)**2 * (b.time-a.time)
                   for a, b in zip(samples, samples[1:]))
    return MetricResult(math.sqrt(integral / context["duration"]), "m/s",
                        note="Right-endpoint time weighting; constant commanded speed magnitude")
