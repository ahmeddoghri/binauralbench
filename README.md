# binauralbench

**A spatial-audio separation benchmark that checks whether the instrument stayed where you put it.**

binauralbench is a compact, inspectable implementation inspired by [The 2025 study of spatial-information loss in binaural music source separation.](https://arxiv.org/abs/2507.00155).
It turns the paper's core idea into a deterministic benchmark that runs on a laptop with Python's standard library.

## Run it

```bash
python binauralbench.py
python -m unittest discover -s tests -v
```

The benchmark writes its result to stdout. Audio projects also write playable WAV files to `demo/`.

## What is tested

The test compares the research-inspired method with a deliberately legible baseline and requires
`ild_error_reduction_pct >= 70`. The data generator is seeded, so the number in this README,
CI, and the portfolio case study can be reproduced.

## Scope

This is an educational research reproduction on controlled synthetic data. It is not a clinical,
diagnostic, production genomics, copyright-authentication, or safety-critical system. The point is
to make one mechanism measurable without hiding it behind a checkpoint or API.

## Research basis

- [The 2025 study of spatial-information loss in binaural music source separation.](https://arxiv.org/abs/2507.00155)
- Original implementation and benchmark in this repository are MIT licensed.

## License

MIT

## Reproduced result

| Metric | Value |
|---|---:|
| `target_ild_db` | **8.2** |
| `naive_ild_db` | **0.0** |
| `linked_ild_db` | **8.06** |
| `ild_error_reduction_pct` | **98.3** |
