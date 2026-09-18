"""AU pounds-per-length scale and last-run weight adjustments."""

from __future__ import annotations

FURLONG_M = 201.168


def distance_furlongs(distance_m: float) -> float:
    return float(distance_m) / FURLONG_M


def lbs_per_length(distance_m: float) -> float:
    f = distance_furlongs(distance_m)
    if f <= 5.25:
        return 3.0
    if f <= 6.25:
        return 2.5
    if f <= 7.25:
        return 2.25
    if f <= 8.5:
        return 2.0
    if f <= 10.5:
        return 1.75
    if f <= 13.0:
        return 1.5
    return 1.25


def kg_to_lbs(kg: float) -> float:
    return round(float(kg) * 2.20462, 2)


def weight_swing_lbs(last_carried_lbs: float, today_lbs: float) -> float:
    return float(last_carried_lbs) - float(today_lbs)


def performance_figure(
    last_or: float,
    beaten_lengths: float,
    distance_m: float,
    last_carried_lbs: float,
    today_lbs: float,
) -> float:
    beaten = max(0.0, float(beaten_lengths))
    return (
        float(last_or)
        - beaten * lbs_per_length(distance_m)
        + weight_swing_lbs(last_carried_lbs, today_lbs)
    )
