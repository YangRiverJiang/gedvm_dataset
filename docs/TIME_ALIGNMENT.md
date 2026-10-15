# Time alignment

1. Use GPS week and GPS seconds of week as the reference time base. All three
   collection days are in GPS week 2331. File names and device wall-clock labels
   are provenance only and must not be used as synchronization timestamps.
2. For Android Raw receiver-clock epochs, the logged-clock estimate is:

   `gps_time_ns = TimeNanos - (FullBiasNanos + BiasNanos)`

   Keep nanosecond integers/Decimal precision until subtraction is complete. The
   included helpers use `decimal.Decimal`. Empty optional `BiasNanos` is treated
   as zero. Empty/sentinel `FullBiasNanos` is invalid. The indexes also reject GPS
   times outside the collection-period envelope. This is a receiver-clock epoch
   formula; per-measurement receive-time/pseudorange calculations may additionally
   need `TimeOffsetNanos`, GNSS-constellation offsets and measurement-state checks.
   See [Android GnssClock](https://developer.android.com/reference/android/location/GnssClock).
3. `Fix` UTC milliseconds are a different time scale. GPS minus UTC was 18 seconds
   on the September 2024 collection dates. The helpers use that fixed historical
   offset only for human-readable UTC displays. Do not carry it into unrelated dates.
4. Phone sampling is asynchronous. Pixel 5 epochs are commonly near .44 seconds of
   the GPS second, while Pixel 7 Pro epochs are commonly near integer seconds.
   Match by physical timestamp, not by CSV row or by rounding all clocks to a second.
   Interpolate reference ENU velocities to the measurement epoch only across valid,
   adjacent reference samples, and account for remaining reference interpolation error.
5. TDCP displacement is measured over an epoch interval. If converted to an interval
   average velocity, compare with the reference over that same interval (e.g. integrate
   the reference velocity), rather than silently comparing with an endpoint velocity.
   A midpoint velocity is an approximation whose error grows with changing acceleration.
6. Preserve acquisition order and hardware discontinuity counts. Startup invalid times,
   gaps and a non-increasing clock estimate in drive03 Pixel 7 Pro are retained in the
   original archives and reflected in the QA metadata. Do not bridge invalid clock
   epochs or blindly sort them into a continuous phase arc.

The package applies no empirical lag or two-second offset. Some internal research
scripts shifted trimmed array indexes; those conventions are not synchronization
corrections and are not copied into this release. Each reference CSV retains its
own phone's export/lever-arm association. No row-by-row phone/reference match or
real-time latency calibration is claimed by this release.
