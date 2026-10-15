"""Small standard-library readers for the released GEDVM data."""
import csv
import io
import math
from decimal import Decimal
from pathlib import Path
from zipfile import ZipFile

GPS_WEEK_SECONDS = 604800
GPS_UTC_OFFSET_SECONDS_2024 = 18
REFERENCE_COLUMNS = [
    'gps_week', 'gps_sow_s', 'x_ecef_m', 'y_ecef_m', 'z_ecef_m',
    'solution_quality_code', 'sat_count_beidou', 'sat_count_galileo',
    'sat_count_glonass', 'sat_count_gps', 'sat_count_qzss', 'pdop',
    'sat_count_total', 'vel_e_mps', 'vel_n_mps', 'vel_u_mps',
    'acc_e_mps2', 'acc_n_mps2', 'acc_u_mps2', 'roll_deg', 'pitch_deg',
    'heading_deg',
]


def read_reference(path):
    with Path(path).open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def read_log_archive(path):
    with ZipFile(path) as z:
        names = [n for n in z.namelist() if n.endswith('.txt')]
        if len(names) != 1:
            raise ValueError('Expected exactly one text log in archive')
        payload = z.read(names[0])
    lines = payload.decode('utf-8').splitlines(keepends=True)
    header_line = next(s for s in lines if s.startswith('# Raw,'))
    columns = header_line.strip().removeprefix('# ').split(',')
    return lines, {name: i for i, name in enumerate(columns)}


def receiver_gps_seconds(fields, columns):
    """Receiver clock epoch, not a constellation transmit-time calculation."""
    full = fields[columns['FullBiasNanos']]
    if full in ('', '-9223372036854775808'):
        return None
    bias = fields[columns['BiasNanos']] or '0'
    value = (Decimal(fields[columns['TimeNanos']]) - Decimal(full)
             - Decimal(bias)) / Decimal(10**9)
    return value


def horizontal_speed(row):
    return math.hypot(float(row['vel_e_mps']), float(row['vel_n_mps']))


def write_csv(path, rows, columns=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def detect_acceleration_events(rows, start_sow, end_sow):
    """Reference-speed screening; these are newly generated candidate labels."""
    t = [float(r['gps_sow_s']) for r in rows]
    v = [horizontal_speed(r) for r in rows]
    acceleration = [float('nan')] * len(rows)
    for i in range(1, len(rows) - 1):
        if 0 < t[i] - t[i-1] <= 1.01 and 0 < t[i+1] - t[i] <= 1.01:
            acceleration[i] = (v[i+1] - v[i-1]) / (t[i+1] - t[i-1])
    events = []
    first = None
    for i in range(len(rows) + 1):
        active = (i < len(rows) and acceleration[i] > 0.5
                  and start_sow + 5 <= t[i] <= end_sow - 5)
        if active and first is None:
            first = i
        if not active and first is not None:
            last = i - 1
            if last - first + 1 >= 3 and v[last] - v[first] >= 2:
                events.append({
                    'core_start_sow_s': t[first], 'core_end_sow_s': t[last],
                    'clip_start_sow_s': t[first] - 5, 'clip_end_sow_s': t[last] + 5,
                    'core_samples': last - first + 1,
                    'core_elapsed_s': t[last] - t[first],
                    'speed_start_mps': round(v[first], 6),
                    'speed_end_mps': round(v[last], 6),
                    'speed_gain_mps': round(v[last] - v[first], 6),
                    'peak_speed_mps': round(max(v[first:last+1]), 6),
                    'peak_accel_mps2': round(max(acceleration[first:last+1]), 6),
                    'near_stop_start': int(v[first] < 2),
                    'reaches_60mph_in_core': int(max(v[first:last+1]) >= 26.8224),
                })
            first = None
    return events


def extract_event_files(repo, event, session, destination):
    """Extract Raw records and reference rows for one phone/event pair."""
    repo, destination = Path(repo), Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    week = int(session['gps_week'])
    start = Decimal(str(event['clip_start_sow_s'])) + week * GPS_WEEK_SECONDS
    end = Decimal(str(event['clip_end_sow_s'])) + week * GPS_WEEK_SECONDS
    lines, columns = read_log_archive(repo / session['raw_archive'])
    output = [s for s in lines if s.startswith('#')]
    count = 0
    epochs = set()
    for line in lines:
        if not line.startswith('Raw,'):
            continue
        fields = line.rstrip('\r\n').split(',')
        time = receiver_gps_seconds(fields, columns)
        if time is not None and start <= time <= end:
            output.append(line)
            count += 1
            epochs.add((fields[columns['HardwareClockDiscontinuityCount']],
                        fields[columns['TimeNanos']]))
    name = session['session_id']
    (destination / (name + '_raw.txt')).write_text(''.join(output), encoding='utf-8', newline='')
    rows = [r for r in read_reference(repo / session['reference_csv'])
            if float(event['clip_start_sow_s']) <= float(r['gps_sow_s'])
            <= float(event['clip_end_sow_s'])]
    write_csv(destination / (name + '_reference.csv'), rows)
    return {'raw_records': count, 'raw_epochs': len(epochs), 'reference_rows': len(rows)}
