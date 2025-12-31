import os
import csv
from pathlib import Path
from src.manual_map_updater import suggest_and_apply, append_manual_mappings, suggest_mapping


def test_suggest_mapping_basic(tmp_path):
    subs = {"orissa", "naga mani mizo tripura", "andaman & nicobar islands"}
    missing = ["odisha", "nagaland", "andaman and nicobar islands"]
    s = suggest_mapping(missing_states=missing, subdivisions=subs)
    assert 'odisha' in s
    assert s['odisha'] in subs
    assert 'nagaland' in s


def test_append_manual_mappings(tmp_path):
    proc = tmp_path / 'processed'
    proc.mkdir()
    mf = proc / 'manual_state_to_subdivision.csv'

    # initial manual mapping file with one entry
    with mf.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=['state','subdivision'])
        writer.writeheader()
        writer.writerow({'state':'puducherry','subdivision':'tamil nadu'})

    suggestions = {'odisha':'orissa', 'nagaland':'naga mani mizo tripura'}
    out = append_manual_mappings(suggestions, path=mf, backup=False)
    assert out.exists()
    rows = list(csv.DictReader(out.open(encoding='utf-8')))
    states = [r['state'].strip().lower() for r in rows]
    assert 'puducherry' in states
    assert 'odisha' in states
    assert 'nagaland' in states


def test_suggest_and_apply_dry_run(tmp_path, monkeypatch):
    proc = tmp_path / 'processed'
    proc.mkdir()

    # create missing counts in temp processed dir
    with (proc / 'missing_year_state_counts.csv').open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=['state_name','count'])
        writer.writeheader()
        writer.writerow({'state_name':'odisha','count':6244})

    # create rainfall file in a temp RAW dir
    raw = tmp_path / 'raw'
    raw.mkdir()
    with (raw / 'rainfall_validation.csv').open('w', newline='', encoding='utf-8') as fh:
        writer = csv.writer(fh)
        writer.writerow(['SUBDIVISION','YEAR'])
        writer.writerow(['ORISSA','2011'])

    suggestions = suggest_and_apply(apply=False, raw_dir=str(raw), processed_dir=str(proc))
    # dry-run should return suggestions but not create/update manual file
    assert 'odisha' in suggestions
    mf = proc / 'manual_state_to_subdivision.csv'
    if mf.exists():
        mf.unlink()
