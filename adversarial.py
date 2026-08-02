"""Adversarial configurations for the linked-gain generalization check.

binauralbench.py's naive_ild_db is not actually a variable measurement --
naive_L and naive_R are both computed as `avg_gain * target`, the same
array, so ild(naive_L, naive_R) is mathematically guaranteed to equal
exactly 0.0 for any seed, any pan, any interferer (confirmed directly
across 30 seeds). That's disclosed honestly in the README's mechanism
description (it's not a hidden oracle read), but it means naive_ild_db
itself isn't the part worth stress-testing -- the linked method's
error-reduction claim is.

TUNING_SEEDS / HOLDOUT_SEEDS each map to a randomized configuration
(different target/interferer frequencies, pan gains, noise level) via
random_config(), rejecting near-centered pans (|target_ild| < 2 dB) where
relative-error metrics are inherently noisy regardless of method quality.

TUNING_SEEDS: used to characterize the linked method's generalization.
HOLDOUT_SEEDS: disjoint, evaluated exactly once after characterization.
"""
import math
import random

RATE = 8000
MIN_TARGET_ILD_DB = 2.0


def random_config(seed: int):
    rng = random.Random(seed)
    while True:
        gL = rng.uniform(0.05, 1.0)
        gR = rng.uniform(0.05, 1.0)
        est_ild = 10 * math.log10((gL ** 2) / (gR ** 2))
        if abs(est_ild) >= MIN_TARGET_ILD_DB:
            break
    return {
        "target_freq": rng.uniform(150, 500),
        "interferer_freq": rng.uniform(600, 1200),
        "gL": gL,
        "gR": gR,
        "hL": rng.uniform(0.1, 0.6),
        "hR": rng.uniform(0.4, 1.0),
        "noise_std": rng.uniform(0.05, 0.4),
    }


TUNING_SEEDS = list(range(1, 41))
HOLDOUT_SEEDS = list(range(1000, 1030))
