# Release validation

Validation completed on 2026-10-15 for release 1.0.0.

- Six distributed source phone ZIPs match their original source SHA-256 values.
- All nine data ZIPs passed archive CRC checks.
- Every numeric token in all six reference CSVs was compared with its original Inertial Explorer export and is unchanged.
- All 271 acceleration candidates were regenerated from the released reference CSVs and lie within common phone/reference time envelopes.
- All 18 packaged paired examples were regenerated and compared byte-for-byte with timestamp-filtered source Raw records and reference rows.
- CITATION.cff passed the official Citation File Format JSON schema validation.
- Every repository file is below 25 MiB. The nine inner data ZIP files are intentionally kept compressed.
- No phone SensorData records were found in the six original archives.

| Session | Raw rows | Receiver-clock epochs | Invalid-clock Raw rows | Non-increasing valid-clock steps | ADR flags usable (%) |
|---|---:|---:|---:|---:|---:|
| drive01_gp51 | 191821 | 5286 | 0 | 0 | 66.07 |
| drive01_gp7p3 | 230462 | 5286 | 0 | 0 | 67.44 |
| drive02_gp52 | 142923 | 4241 | 81 | 0 | 71.03 |
| drive02_gp7p3 | 193015 | 4238 | 500 | 0 | 74.91 |
| drive03_gp51 | 103950 | 2487 | 0 | 0 | 64.32 |
| drive03_gp7p4 | 113931 | 2490 | 0 | 1 | 75.39 |

ADR flag usability is only VALID=1, RESET=0, CYCLE_SLIP=0 at one record. It is not a TDCP success rate, phase-continuity guarantee, reference accuracy certificate or algorithm performance measurement.

These checks establish packaging and selection integrity. They do not validate an end-to-end velocity estimator, reconstruct the paper results or certify a 0?60 mph timer.
