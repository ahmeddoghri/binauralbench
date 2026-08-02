"""Stress-test binauralbench's linked-gain claim across many randomized
pan/frequency/noise configurations.

This is not a bug fix -- binauralbench.py's mechanism and published
numbers are correct and reproduce exactly. naive_ild_db is mathematically
guaranteed to be exactly 0.0 for any input (naive_L and naive_R are the
literal same array, avg_gain*target, so their ILD is 0 by algebra) --
that's disclosed honestly in the README, not a hidden rigged baseline.
This checks whether the *linked method's* error-reduction claim survives
randomized configurations rather than the one seed the benchmark ships
with.
"""
import json
import math
import random
import statistics as st

from adversarial import HOLDOUT_SEEDS, RATE, TUNING_SEEDS, random_config
from binauralbench import estimate_gain, ild


def run_config(seed):
    cfg = random_config(seed)
    rng = random.Random(seed * 7919 + 1)
    target = [math.sin(2 * math.pi * cfg["target_freq"] * t / RATE) for t in range(RATE)]
    interferer = [math.sin(2 * math.pi * cfg["interferer_freq"] * t / RATE + 0.4) for t in range(RATE)]
    mix_L = [cfg["gL"] * t + cfg["hL"] * i + rng.gauss(0, cfg["noise_std"]) for t, i in zip(target, interferer)]
    mix_R = [cfg["gR"] * t + cfg["hR"] * i + rng.gauss(0, cfg["noise_std"]) for t, i in zip(target, interferer)]

    gL_hat = estimate_gain(mix_L, target)
    gR_hat = estimate_gain(mix_R, target)
    avg_gain = (gL_hat + gR_hat) / 2
    naive_L = [avg_gain * x for x in target]
    naive_R = [avg_gain * x for x in target]
    linked_L = [gL_hat * x for x in target]
    linked_R = [gR_hat * x for x in target]

    target_ild = ild([cfg["gL"] * x for x in target], [cfg["gR"] * x for x in target])
    naive_ild = ild(naive_L, naive_R)
    linked_ild = ild(linked_L, linked_R)
    e1 = abs(naive_ild - target_ild)
    e2 = abs(linked_ild - target_ild)
    return {
        "target_ild_db": round(target_ild, 2),
        "naive_ild_db": round(naive_ild, 2),
        "linked_ild_db": round(linked_ild, 2),
        "ild_error_reduction_pct": round(100 * (1 - e2 / max(e1, 1e-9)), 1),
    }


def summarize(seeds):
    results = [run_config(seed) for seed in seeds]
    naive_all_zero = all(r["naive_ild_db"] == 0.0 for r in results)
    reductions = [r["ild_error_reduction_pct"] for r in results]
    return {
        "n": len(seeds),
        "naive_ild_always_exactly_zero": naive_all_zero,
        "mean_reduction_pct": round(st.mean(reductions), 1),
        "min_reduction_pct": min(reductions),
    }


def main():
    print("binauralbench eval_v2: linked-gain generalization across randomized configurations")
    for label, seeds in (("tuning", TUNING_SEEDS), ("holdout", HOLDOUT_SEEDS)):
        print(f"\n{label} ({len(seeds)} seeds, randomized pans/frequencies/noise):")
        print(json.dumps(summarize(seeds), indent=2))


if __name__ == "__main__":
    main()
