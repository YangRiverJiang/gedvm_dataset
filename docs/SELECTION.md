# Selection, provenance and limits

## Sessions

Six phone archives are selected according to the final paper analysis scripts:
drive01 = gp51 + gp7p3; drive02 = gp52 + gp7p3; drive03 = gp51 + gp7p4.
The extra gp7p1/gp7p2/gp7p4 logs for drive02 are not part of this selected release.
No raw measurements are edited, downsampled or repaired. Source archive SHA-256
hashes in `sessions.json` equal the distributed ZIP hashes.

Six associated reference exports are normalized into CSV. Numeric tokens are
unchanged. Export metadata retains phone-specific lever arms and rotations while
omitting workstation paths and processing-account lines. The exports identify
Inertial Explorer 8.90.6611; the manuscript describes version 9. The actual export
headers are the provenance used in this data release.

The Trimble NETR9 CREF0001 `.T02`/RINEX base observations are excluded. They must
not be labelled PwrPak7 rover raw data. Also excluded are intermediate binary
results, proprietary processing projects, manuscript files, photographs and emails.

## New acceleration candidates

For each drive, detect events on the Pixel 7 Pro's reference trajectory so that
the same physical event ID applies to both phones:

1. Horizontal speed = `hypot(VEast, VNorth)`.
2. Central-difference acceleration = `(speed[i+1]-speed[i-1])/(time[i+1]-time[i-1])`.
   Both adjacent steps must be positive and at most 1.01 seconds; endpoints are excluded.
3. Use maximal runs above 0.5 m/s², with at least three consecutive samples and a
   net speed gain of at least 2 m/s.
4. Add five seconds of context on each side. Retain only events whose full context
   lies inside both phones' valid-clock time envelopes and both reference envelopes.
   This checks envelopes, not per-satellite ADR completeness or INS accuracy.
5. For quick-start examples, choose four largest speed gains beginning below 2 m/s
   and two largest peak-speed events beginning at or above 2 m/s per drive.
   Selection uses reference kinematics only, not phone algorithm accuracy.

The resulting catalog has 271 vehicle events; 18 have pre-extracted
paired-phone clips. All candidates can be extracted using the supplied helper.
The detector implementation is in `tools/dataset_lib.py`; thresholds are explicit.

These are newly generated candidates, not original paper annotations. In particular,
the paper/research scripts used different padding/merging and motion-estimation
definitions; this release does not claim to reconstruct those event counts.
Short dips below the acceleration threshold can split a longer driving manoeuvre.
Context windows may overlap, and the two phones share the same vehicle motion.
Group train/test splits by drive and account for overlap to prevent leakage.

## Limits

- Approximately 1 Hz raw GNSS and 1 Hz processed references limit timing resolution;
  interpolated crossings must not be presented as a validated sub-second timer benchmark.
- No dedicated or certified standstill-to-60 mph trial is identified or promised.
- No phone IMU sample records are present in the selected archives.
- No original PwrPak7 receiver binary or higher-rate reference product is included.
- Smoothed post-processed GNSS/INS references are not independent absolute error bounds;
  quality codes are retained, and exported per-epoch velocity uncertainty is unavailable.
- Original raw logs retain invalid startup clocks, discontinuities, missing/flagged ADR,
  fused fixes and, in drive03 Pixel 7 Pro, network fixes. Apply signal/clock quality checks.
- Exact trajectories and times are intentionally retained. This is not geographically
  anonymized data, although no driver names or demographic table is included.
- This is a selected dataset release, not the complete processing software or all
  artifacts required to reproduce every paper figure or published RMS value.

## Verification

`tools/verify_dataset.py` checks checksums, archive CRCs, source archive identity,
reference shape/time steps, catalog regeneration, event containment and all packaged
example files against timestamp-filtered rows of the full archives/reference CSVs.
