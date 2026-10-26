import math
from ..registry import metric
from ..types import MetricResult


@metric("jerk_rms_mps3", "flight", "m/s^3")
def jerk_rms(context):
    samples = context["samples"]
    if len(samples) < 3:
        return MetricResult(None, "m/s^3", "undefined", "At least three velocity samples required")
    accelerations = []
    for a, b in zip(samples, samples[1:]):
        accelerations.append(((a.time + b.time) / 2,
                              tuple((y-x)/(b.time-a.time) for x, y in zip(a.velocity, b.velocity))))
    integral, duration = 0.0, 0.0
    for (ta, aa), (tb, ab) in zip(accelerations, accelerations[1:]):
        dt = tb - ta
        integral += sum(((y-x)/dt)**2 for x, y in zip(aa, ab)) * dt
        duration += dt
    return MetricResult(math.sqrt(integral / duration), "m/s^3",
                        note="Velocity differences; midpoint acceleration times; derivative-support weighting")
