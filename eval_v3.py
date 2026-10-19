"""Sweep the non-oracle separator (binauralbench_v2) across randomized scenes.

Same tuning and holdout configurations as eval_v2, plus a hard split written
for this check: target and interferer closer in frequency and the interferer
louder, so the estimated mask leaks and the linked output's ILD can drift.

    python eval_v3.py
"""
import json
import random
import statistics as st

from adversarial import HOLDOUT_SEEDS, TUNING_SEEDS, random_config
from binauralbench_v2 import run

HARD_SEEDS = list(range(500, 530))


def hard_config(seed):
    rng = random.Random(seed)
    cfg = random_config(seed)
    cfg["target_freq"] = rng.uniform(380, 470)
    cfg["interferer_freq"] = rng.uniform(560, 680)
    cfg["hL"], cfg["hR"] = rng.uniform(0.6, 1.2), rng.uniform(0.6, 1.2)
    return cfg


def scene(seed, cfg):
    return run(seed=seed * 7919 + 1, f_target=cfg["target_freq"], f_interf=cfg["interferer_freq"],
               g=(cfg["gL"], cfg["gR"]), h=(cfg["hL"], cfg["hR"]), noise=cfg["noise_std"])


def summarize(seeds, make):
    rows = [scene(s, make(s)) for s in seeds]
    out = {"n": len(rows)}
    for name in ("mono", "per_ear", "linked"):
        errs = [r[name]["ild_error_db"] for r in rows]
        out[name] = {
            "mean_ild_error_db": round(st.mean(errs), 2),
            "max_ild_error_db": round(max(errs), 2),
            "mean_sdr_db": round(st.mean(r[name]["sdr_db"] for r in rows), 2),
        }
    out["mean_target_abs_ild_db"] = round(st.mean(abs(r["target_ild_db"]) for r in rows), 2)
    return out


def build_report():
    return {
        "tuning": summarize(TUNING_SEEDS, random_config),
        "holdout": summarize(HOLDOUT_SEEDS, random_config),
        "hard": summarize(HARD_SEEDS, hard_config),
    }


if __name__ == "__main__":
    print("binauralbench eval_v3: a separator that never sees the clean target")
    print(json.dumps(build_report(), indent=2))
