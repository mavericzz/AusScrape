from __future__ import annotations

import math

from src.handicap.weights import lbs_per_length


def sectional_upgrade_lbs(
    horse_fsp: float,
    par_fsp: float,
    *,
    lbs_per_fsp_point: float = 0.35,
    cap_lbs: float = 6.0,
) -> float:
    raw = (float(horse_fsp) - float(par_fsp)) * lbs_per_fsp_point
    return max(-cap_lbs, min(cap_lbs, raw))


def late_split_upgrade_lbs(
    horse_l400_s: float | None,
    field_l400_s: float | None,
    distance_m: float,
) -> float:
    if horse_l400_s is None or field_l400_s is None:
        return 0.0
    if horse_l400_s <= 0 or field_l400_s <= 0:
        return 0.0
    delta_s = field_l400_s - horse_l400_s
    lengths = delta_s / 0.2
    return max(-4.0, min(4.0, lengths * lbs_per_length(distance_m) * 0.35))


def early_speed_score(early_speed: float | None, late_speed: float | None) -> float:
    if early_speed is None:
        return 0.0
    late = late_speed if late_speed is not None else early_speed
    return float(early_speed) - float(late)


def softmax(xs: list[float], temperature: float = 4.0) -> list[float]:
    if not xs:
        return []
    t = max(0.4, float(temperature))
    shifted = [(x - max(xs)) / t for x in xs]
    exps = [math.exp(v) for v in shifted]
    total = sum(exps) or 1.0
    return [e / total for e in exps]
