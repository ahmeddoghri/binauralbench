"""Spatial-cue preservation with a separator that never sees the clean target.

binauralbench.py estimates each ear's gain by projecting the mixture onto the
clean target waveform, then renders gain * clean target. Neither of its two
methods separates anything: both are handed the answer, so the benchmark
measures least-squares gain recovery from an oracle reference, and the naive
baseline's 0.00 dB ILD is guaranteed by construction.

Here the separator only gets the two-channel mixture:

1. Estimate the two source frequencies from the mixture's own average power
   spectrum (the two strongest peaks) and put the crossover between them.
2. Build one time-frequency mask from that crossover with an STFT.
3. Render the target three ways that real pipelines actually use:
     mono      separate the mid channel (L+R)/2 and play it in both ears
     per_ear   mask each ear, then loudness-normalize each ear to a common
               level, as a separator that solves each ear independently does
     linked    apply the same mask to each ear's own spectrum and keep the
               channel energies as they are

Scored on the error between each output's ILD and the true target ILD, and on
SDR against the true target image in each ear.

    python binauralbench_v2.py
"""
import cmath
import json
import math
import random

RATE = 8000
N_FFT = 256
HOP = 128


def ild(left, right):
    l = sum(x * x for x in left) + 1e-9
    r = sum(x * x for x in right) + 1e-9
    return 10 * math.log10(l / r)


def sdr(est, ref):
    num = sum(r * r for r in ref) + 1e-12
    den = sum((e - r) ** 2 for e, r in zip(est, ref)) + 1e-12
    return 10 * math.log10(num / den)


def fft(x):
    n = len(x)
    if n == 1:
        return [complex(x[0])]
    even, odd = fft(x[0::2]), fft(x[1::2])
    out = [0j] * n
    for k in range(n // 2):
        t = cmath.exp(-2j * math.pi * k / n) * odd[k]
        out[k] = even[k] + t
        out[k + n // 2] = even[k] - t
    return out


def ifft(X):
    n = len(X)
    conj = fft([v.conjugate() for v in X])
    return [v.conjugate() / n for v in conj]


WINDOW = [0.5 - 0.5 * math.cos(2 * math.pi * i / N_FFT) for i in range(N_FFT)]


def stft(x):
    pad = [0.0] * N_FFT + list(x) + [0.0] * N_FFT
    return [fft([pad[s + i] * WINDOW[i] for i in range(N_FFT)]) for s in range(0, len(pad) - N_FFT + 1, HOP)]


def istft(frames, length):
    out = [0.0] * (length + 3 * N_FFT)
    norm = [0.0] * len(out)
    for f, X in enumerate(frames):
        s = f * HOP
        y = ifft(X)
        for i in range(N_FFT):
            out[s + i] += y[i].real * WINDOW[i]
            norm[s + i] += WINDOW[i] ** 2
    return [out[N_FFT + i] / norm[N_FFT + i] if norm[N_FFT + i] > 1e-9 else 0.0 for i in range(length)]


def bin_hz(k):
    return k * RATE / N_FFT


def estimate_crossover(spec_l, spec_r):
    """Midpoint between the two strongest spectral peaks of the mixture."""
    half = N_FFT // 2
    power = [0.0] * half
    for spec in (spec_l, spec_r):
        for X in spec:
            for k in range(half):
                power[k] += abs(X[k]) ** 2
    peaks = [k for k in range(1, half - 1) if power[k] >= power[k - 1] and power[k] >= power[k + 1]]
    top = sorted(sorted(peaks, key=lambda k: -power[k])[:2])
    if len(top) < 2:
        return bin_hz(half // 2), []
    return (bin_hz(top[0]) + bin_hz(top[1])) / 2, [bin_hz(k) for k in top]


def mask_for(crossover_hz):
    # The target is the lower of the two sources. A short raised-cosine
    # transition keeps the mask from ringing.
    width = RATE / N_FFT * 2
    m = []
    for k in range(N_FFT):
        f = bin_hz(min(k, N_FFT - k))
        if f <= crossover_hz - width:
            m.append(1.0)
        elif f >= crossover_hz + width:
            m.append(0.0)
        else:
            m.append(0.5 + 0.5 * math.cos(math.pi * (f - (crossover_hz - width)) / (2 * width)))
    return m


def apply(spec, m):
    return [[X[k] * m[k] for k in range(N_FFT)] for X in spec]


def make_mixture(seed, f_target, f_interf, g, h, noise):
    rng = random.Random(seed)
    target = [math.sin(2 * math.pi * f_target * t / RATE) for t in range(RATE)]
    interferer = [math.sin(2 * math.pi * f_interf * t / RATE + 0.4) for t in range(RATE)]
    gL, gR = g
    hL, hR = h
    mix_l = [gL * a + hL * b + rng.gauss(0, noise) for a, b in zip(target, interferer)]
    mix_r = [gR * a + hR * b + rng.gauss(0, noise) for a, b in zip(target, interferer)]
    return mix_l, mix_r, [gL * a for a in target], [gR * a for a in target]


def run(seed=43, f_target=330.0, f_interf=770.0, g=(0.9, 0.35), h=(0.3, 0.9), noise=0.02):
    mix_l, mix_r, ref_l, ref_r = make_mixture(seed, f_target, f_interf, g, h, noise)
    spec_l, spec_r = stft(mix_l), stft(mix_r)
    crossover, peaks = estimate_crossover(spec_l, spec_r)
    m = mask_for(crossover)

    linked_l = istft(apply(spec_l, m), RATE)
    linked_r = istft(apply(spec_r, m), RATE)

    mid = istft(apply(stft([(a + b) / 2 for a, b in zip(mix_l, mix_r)]), m), RATE)
    mono_l = mono_r = mid

    # Each ear separated on its own, then normalized to a common output level.
    level = math.sqrt((sum(x * x for x in linked_l) + sum(x * x for x in linked_r)) / 2 / RATE)
    def normalize(x):
        rms = math.sqrt(sum(v * v for v in x) / len(x)) + 1e-12
        return [v * level / rms for v in x]
    per_l, per_r = normalize(linked_l), normalize(linked_r)

    true_ild = ild(ref_l, ref_r)
    out = {"target_ild_db": round(true_ild, 2), "crossover_hz": round(crossover, 1),
           "estimated_peaks_hz": [round(p, 1) for p in peaks]}
    for name, (l, r) in (("mono", (mono_l, mono_r)), ("per_ear", (per_l, per_r)), ("linked", (linked_l, linked_r))):
        out[name] = {
            "ild_db": round(ild(l, r), 2),
            "ild_error_db": round(abs(ild(l, r) - true_ild), 2),
            "sdr_db": round((sdr(l, ref_l) + sdr(r, ref_r)) / 2, 2),
        }
    return out


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
