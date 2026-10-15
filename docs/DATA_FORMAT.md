# Data format

## Phone logs

`data/raw/*.zip` are byte-for-byte copies of the selected original archives.
Each contains a single UTF-8 `gnss_log_*.txt` with its original filename.
Read each `# Raw,...` header to obtain the column layout. Record types include:

- `Raw`: Android raw GNSS measurements, approximately one epoch per second and multiple satellite/signal rows per epoch.
- `Fix`: GPS, fused and occasionally network position fixes. These can be duplicated, stale or asynchronous; use `Provider` and UTC time explicitly.
- `DeviceStatus`: memory, temperature and battery information; not a sensor observation.

The literal `CarrierPhase`/`CarrierCycles` columns may be empty. Carrier-phase-related
observables are available through `AccumulatedDeltaRangeMeters`, its uncertainty and
`AccumulatedDeltaRangeState`; empty `CarrierPhase` does not imply no ADR data.
Maintain satellite constellation, SVID and frequency identity between epochs.
An ADR flag that is valid with no reset or cycle slip is only an initial usability check,
not proof of a continuous, error-free inter-epoch TDCP observation.
See the [Android measurement API](https://developer.android.com/reference/android/location/GnssMeasurement).

## Reference CSV

The following 22 columns follow the original Inertial Explorer export order.
Numerical strings, including trailing digits, are copied unchanged; only delimiters
and column labels are normalized. No velocity, attitude or position smoothing is
added by this release, and no new lever-arm correction is applied.

| Column | Name |
|---:|---|
| 1 | `gps_week` |
| 2 | `gps_sow_s` |
| 3 | `x_ecef_m` |
| 4 | `y_ecef_m` |
| 5 | `z_ecef_m` |
| 6 | `solution_quality_code` |
| 7 | `sat_count_beidou` |
| 8 | `sat_count_galileo` |
| 9 | `sat_count_glonass` |
| 10 | `sat_count_gps` |
| 11 | `sat_count_qzss` |
| 12 | `pdop` |
| 13 | `sat_count_total` |
| 14 | `vel_e_mps` |
| 15 | `vel_n_mps` |
| 16 | `vel_u_mps` |
| 17 | `acc_e_mps2` |
| 18 | `acc_n_mps2` |
| 19 | `acc_u_mps2` |
| 20 | `roll_deg` |
| 21 | `pitch_deg` |
| 22 | `heading_deg` |

`gps_sow_s` is GPS seconds of week (not UTC time of day). Positions are WGS84 ECEF
in metres; velocities and accelerations are east/north/up in m/s and m/s²;
attitude columns preserve the original degree convention. Do not assume heading
is wrapped to [0, 360); negative values occur. `solution_quality_code` and constellation
counts are preserved export fields; consult the original software conventions before
using quality codes as a filter. These exports contain no covariance or velocity sigma.

`metadata/reference_*.txt` retains the export software, datum, antenna/secondary-sensor
lever arms and body-to-IMU rotation settings. Only local `SolFile` and `ProcessInfo`
lines are omitted. The original reference text file SHA-256 is in `sessions.json`.

## Epoch indexes and catalogs

`metadata/epochs/*.csv` lists receiver-clock epochs in original acquisition order,
including epoch GPS time, UTC display time and raw-row counts. Epoch keys combine
`HardwareClockDiscontinuityCount` and `TimeNanos`. Invalid clock timestamps are blank.
`adr_flag_usable_records` counts rows with VALID set and RESET/CYCLE_SLIP clear;
it does not test satellite continuity, residuals or positioning performance.

`metadata/acceleration_events.csv` uses a common event ID per vehicle event.
`core_*` fields delimit threshold-positive samples; `clip_*` adds five seconds on
each side. `core_elapsed_s` is last minus first timestamp, so three 1 Hz samples span
two seconds. Speeds are horizontal; 60 mph is 26.8224 m/s. `near_stop_start` means
the first core speed is below 2 m/s, not an exact standstill timestamp.
`reaches_60mph_in_core` does not certify a 0–60 mph trial.
`example_selected` marks inclusion in the quick-start archives. Padding may overlap
between events; these clips must not be randomly split as independent training/test samples.
