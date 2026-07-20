# binauralbench

**A spatial-audio separation benchmark that checks whether the instrument stayed where you put it.**

Separate a stereo mix into stems and most benchmarks stop at "does the isolated instrument sound clean." Nobody asks the second question: does it still sound like it's coming from where it actually was? A naive mono-style separator collapses left and right into one blended channel per source, which sounds fine in headphones right up until you notice the guitar that used to be panned hard left is now dead center. binauralbench measures that specific failure — interaural level difference, the loudness gap between your two ears that your brain uses to localize sound — before and after separation.

It's a compact, inspectable implementation inspired by [the 2025 study of spatial-information loss in binaural music source separation](https://arxiv.org/abs/2507.00155), rebuilt small enough to read in one sitting and run without a GPU, a checkpoint, or an API key.

## The result

```bash
python binauralbench.py
```
```json
{
  "target_ild_db": 8.2,
  "naive_ild_db": 0.0,
  "linked_ild_db": 8.06,
  "ild_error_reduction_pct": 98.3
}
```

The source is genuinely panned with an 8.2 dB level difference between ears. Separate left and right independently the naive way and you get 0.0 dB — the spatial cue is just gone, collapsed to dead center. Link the two channels' gain so separation respects the original balance instead of solving each ear in isolation, and you recover 8.06 dB — a 98.3% reduction in localization error, on the exact cue a naive separator throws away for free.

## How it works

A mono tone is panned into left/right channels with a real, known level difference (the target ILD). The naive baseline separates each channel independently, which in this synthetic setup collapses the panning entirely — a stand-in for what happens when a separator processes stereo as two unrelated mono problems. The linked method instead applies the same relative gain relationship to both channels, preserving the ratio between them instead of solving them independently. It writes `input_binaural.wav` and `preserved.wav` to `demo/` so you can put on headphones and hear the localization difference yourself.

## Run it

```bash
python binauralbench.py
python -m unittest discover -s tests -v
```

The benchmark writes its result to stdout and two playable WAV files to `demo/`.

## What is tested

The test compares linked-channel separation against the naive independent-channel baseline and requires `ild_error_reduction_pct >= 70`. The data generator is deterministic, so the number in this README, in CI, and in the portfolio case study are the same number, not three different ones that happen to rhyme.

## Scope

This is an educational research reproduction on a single controlled synthetic tone, not a real multi-instrument binaural mix. It is not a clinical, diagnostic, production audio-production, or safety-critical system. The point is to make one mechanism — separating channels independently destroys spatial cues that linked processing preserves — measurable and audible without hiding it behind a checkpoint.

## Research basis

- [The 2025 study of spatial-information loss in binaural music source separation](https://arxiv.org/abs/2507.00155)
- Original implementation and benchmark in this repository are MIT licensed.

## License

MIT
