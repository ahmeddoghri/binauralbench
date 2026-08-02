# binauralbench

**A spatial-audio separation benchmark that checks whether the instrument stayed where you put it.**

Separate a stereo mix into stems and most benchmarks stop at "does the isolated instrument sound clean." Nobody asks the second question: does it still sound like it's coming from where it actually was? A naive separator that estimates each channel's gain independently and then normalizes both to a shared output level sounds fine in headphones right up until you notice the guitar that used to be panned hard left is now dead center. binauralbench measures that specific failure — interaural level difference, the loudness gap between your two ears that your brain uses to localize sound — before and after separation.

It's a compact, inspectable implementation inspired by [the 2025 study of spatial-information loss in binaural music source separation](https://arxiv.org/abs/2507.00155), rebuilt small enough to read in one sitting and run without a GPU, a checkpoint, or an API key.

## The result

```bash
python binauralbench.py
```
```json
{
  "target_ild_db": 8.2,
  "naive_ild_db": 0.0,
  "linked_ild_db": 8.22,
  "ild_error_reduction_pct": 99.8
}
```

The source is genuinely panned with an 8.2 dB level difference between ears, and a real interfering source is mixed in on both channels with independent noise. Estimate each channel's target gain separately (least-squares correlation against the known target waveform), then collapse both channels' estimates to one shared output level, and you get 0.0 dB — the spatial cue is entirely gone. Keep each channel's own independently-estimated gain instead of averaging them together, and you recover 8.22 dB — a 99.8% reduction in localization error, from a bug that's really just "don't throw away the number you already computed."

## How it works

A mono target tone is panned into left/right channels with a real, known level difference, mixed with a differently-panned interferer plus per-channel noise. Both the naive and linked methods start with the *same* per-channel gain estimate — a least-squares projection of the mixture onto the known target waveform, computed independently for each ear. The naive bug is what happens next: it averages the two channels' gain estimates into one shared value and applies that single number to both outputs, which is exactly what a separator does when it treats stereo as two unrelated mono problems and then normalizes to a common level. The linked method just keeps each channel's own estimate instead of collapsing them. It writes `input_binaural.wav` and `preserved.wav` to `demo/` so you can put on headphones and hear the localization difference yourself.

## Run it

```bash
python binauralbench.py
python -m unittest discover -s tests -v
```

The benchmark writes its result to stdout and two playable WAV files to `demo/`.

## What is tested

The test compares linked-channel gain preservation against the naive shared-gain baseline and requires `ild_error_reduction_pct >= 70`. The data generator is seeded, so the number in this README, in CI, and in the portfolio case study are the same number, not three different ones that happen to rhyme.

## Scope

This is an educational research reproduction on a single controlled synthetic tone plus one interferer, not a real multi-instrument binaural mix. It is not a clinical, diagnostic, production audio-production, or safety-critical system. The point is to make one mechanism — collapsing independently-estimated channel gains into a shared value destroys spatial cues that keeping them separate preserves — measurable and audible without hiding it behind a checkpoint.

## Does the linked-gain advantage survive other pans and noise levels?

Worth flagging up front: `naive_ild_db: 0.0` isn't a variable measurement.
`naive_L` and `naive_R` are both computed as `avg_gain * target` — the
literal same array — so `ild(naive_L, naive_R)` is mathematically
guaranteed to equal exactly `0.0` for any seed, pan, or noise level. That's
not a hidden rigged baseline; the README already explains the mechanism
(collapsing both channels to one shared gain destroys any left/right
difference by construction). But it does mean the naive number itself
isn't worth stress-testing — the *linked method's* error-reduction claim
is.

```bash
python eval_v2.py
```
```
tuning (40 seeds):  naive_ild_always_exactly_zero=true  mean_reduction_pct=98.0  min_reduction_pct=85.6
holdout (30 seeds): naive_ild_always_exactly_zero=true  mean_reduction_pct=98.4  min_reduction_pct=95.0
```

`adversarial.py` randomizes target/interferer frequency, both channel
gains, and noise level per seed (rejecting near-centered pans below 2 dB,
where relative-error metrics are inherently noisy for any method). Across
40 tuning seeds and a disjoint 30-seed holdout (evaluated once), the naive
method's ILD is confirmed exactly `0.0` on every single seed as expected,
and the linked method holds a mean 98.0%/98.4% error reduction, never
dropping below 85.6%. The core mechanism generalizes well past the one
published configuration. `binauralbench.py` is unmodified.

## Research basis

- [The 2025 study of spatial-information loss in binaural music source separation](https://arxiv.org/abs/2507.00155)
- Original implementation and benchmark in this repository are MIT licensed.

## License

MIT
