"""Verify the portable data release without access to the source workstation."""
import csv
import hashlib
import json
import math
import tempfile
from pathlib import Path
from zipfile import ZipFile
from dataset_lib import (REFERENCE_COLUMNS, read_reference, detect_acceleration_events,
                         extract_event_files)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    repo = Path(__file__).resolve().parents[1]
    checked = 0
    for line in (repo / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ', 1)
        target = (repo / name).resolve()
        assert target.is_relative_to(repo.resolve()), 'Unsafe checksum path'
        assert sha(target) == digest, 'SHA-256 mismatch: ' + name
        checked += 1
    print('PASS:', checked, 'SHA-256 checksums')
    files = [p for p in repo.rglob('*') if p.is_file() and '__pycache__' not in p.parts
             and '.git' not in p.parts and 'extracted' not in p.parts]
    assert all(p.stat().st_size < 25 * 2**20 for p in files), 'Browser upload file limit exceeded'
    archives = list((repo / 'data').rglob('*.zip'))
    for archive in archives:
        with ZipFile(archive) as z:
            assert z.testzip() is None, 'ZIP CRC failure: ' + str(archive)
            assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist())
    print('PASS:', len(archives), 'ZIP CRC checks; every repository file below 25 MiB')
    sessions = json.loads((repo / 'metadata/sessions.json').read_text())
    references = {}
    for session in sessions:
        assert sha(repo / session['raw_archive']) == session['source_raw_sha256']
        rows = read_reference(repo / session['reference_csv'])
        assert list(rows[0]) == REFERENCE_COLUMNS
        assert len(rows) == session['reference_rows']
        assert all(all(math.isfinite(float(v)) for v in r.values()) for r in rows)
        time = [float(r['gps_sow_s']) for r in rows]
        assert all(abs(b-a-1) < 1e-9 for a,b in zip(time,time[1:]))
        references[session['session_id']] = rows
        with (repo / session['epoch_csv']).open(newline='') as f:
            epochs = list(csv.DictReader(f))
        assert len(epochs) == session['epoch_count']
        assert sum(int(e['raw_records']) for e in epochs) == session['record_counts']['Raw']
        assert session['sensor_data_records'] == 0
    print('PASS: six original archive identities; six 1 Hz reference tables and epoch indexes')
    with (repo / 'metadata/acceleration_events.csv').open(newline='') as f:
        events = list(csv.DictReader(f))
    with (repo / 'metadata/drives.csv').open(newline='') as f:
        drives = list(csv.DictReader(f))
    for drive in drives:
        expected = detect_acceleration_events(
            references[drive['detection_reference']],
            float(drive['common_reference_start_sow_s']), float(drive['common_reference_end_sow_s']))
        actual = [e for e in events if e['drive_id'] == drive['drive_id']]
        assert len(expected) == len(actual) == int(drive['acceleration_candidates'])
        for original, regenerated in zip(actual, expected):
            for key, value in regenerated.items():
                assert abs(float(original[key])-float(value)) < 1e-8, (original['event_id'], key)
        pair = [s for s in sessions if s['drive_id'] == drive['drive_id']]
        for event in actual:
            for s in pair:
                assert float(event['clip_start_sow_s']) >= max(s['raw_start_sow_s'],s['reference_start_sow_s'])
                assert float(event['clip_end_sow_s']) <= min(s['raw_end_sow_s'],s['reference_end_sow_s'])
    print('PASS:', len(events), 'regenerated acceleration events inside common time coverage')
    example_count = 0
    with tempfile.TemporaryDirectory(prefix='gedvm-verify-') as tmp:
        for drive in drives:
            name = drive['drive_id']
            selected = [e for e in events if e['drive_id'] == name and e['example_selected'] == '1']
            with ZipFile(repo / f'data/examples/{name}_acceleration_examples.zip') as z:
                for event in selected:
                    eid = event['event_id']
                    assert json.loads(z.read(eid + '/event.json'))['event']['event_id'] == eid
                    for s in sessions:
                        if s['drive_id'] != name:
                            continue
                        out = Path(tmp) / eid
                        counts = extract_event_files(repo, event, s, out)
                        assert counts['raw_records'] > 0 and counts['reference_rows'] > 0
                        for suffix in ('_raw.txt','_reference.csv'):
                            filename = s['session_id'] + suffix
                            assert (out / filename).read_bytes() == z.read(eid + '/' + filename), (eid, filename)
                    example_count += 1
    print('PASS:', example_count, 'paired examples match source Raw records and reference CSVs exactly')
    print('Dataset verification completed successfully.')


if __name__ == '__main__':
    main()
