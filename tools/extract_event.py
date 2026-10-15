"""Extract one catalogued acceleration event for both phones (Python 3.10+)."""
import argparse
import csv
import json
from pathlib import Path
from dataset_lib import extract_event_files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('event_id', help='Event ID from metadata/acceleration_events.csv')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    sessions = json.loads((args.repo / 'metadata/sessions.json').read_text())
    with (args.repo / 'metadata/acceleration_events.csv').open(newline='') as f:
        event = next((r for r in csv.DictReader(f) if r['event_id'] == args.event_id), None)
    if event is None:
        parser.error('Unknown event ID')
    out = args.output / args.event_id
    if out.exists():
        parser.error('Event output directory already exists; choose a new output directory')
    for session in sessions:
        if session['drive_id'] == event['drive_id']:
            print(session['session_id'], extract_event_files(args.repo, event, session, out))
    (out / 'event.json').write_text(json.dumps(event, indent=2) + '\n')


if __name__ == '__main__':
    main()
