"""Suggest and optionally append manual state -> subdivision mappings.

Behavior:
- Reads existing manual mapping file at data/processed/manual_state_to_subdivision.csv (if present)
- Reads rainfall subdivisions from data/raw/rainfall_validation.csv SUBDIVISION column
- Reads missing states from data/processed/missing_year_state_counts.csv
- For each missing state not already in manual map, suggest a subdivision via token overlap/fuzzy match
- By default performs a dry-run and prints suggestions. Pass `apply=True` to append suggestions to the manual CSV.

This is intentionally conservative and records a backup before writing.
"""
from pathlib import Path
import csv
import re
from datetime import datetime
import difflib

BASE = Path(__file__).resolve().parents[1]
RAW = BASE / "data" / "raw"
PROC = BASE / "data" / "processed"
MANUAL_FILE = PROC / "manual_state_to_subdivision.csv"
MISSING_FILE = PROC / "missing_year_state_counts.csv"
RAINFALL_FILE = RAW / "rainfall_validation.csv"

_token_re = re.compile(r"[a-z0-9]+")

def normalize_text(s: str):
    return " ".join(_token_re.findall(str(s).lower()))


def load_manual_map(path=MANUAL_FILE):
    mapping = {}
    if not path.exists():
        return mapping
    with path.open(newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            state = row.get('state') or row.get('state_name')
            subdiv = row.get('subdivision')
            if state and subdiv:
                mapping[state.strip().lower()] = subdiv.strip().lower()
    return mapping


def load_missing_states(path=MISSING_FILE):
    if not path.exists():
        return []
    out = []
    with path.open(newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            st = row.get('state_name') or row.get('state')
            if st:
                out.append(st.strip().lower())
    return out


def load_subdivisions(path=RAINFALL_FILE):
    subs = set()
    if not path.exists():
        return subs
    with path.open(newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            s = row.get('SUBDIVISION') or row.get('subdivision')
            if s:
                subs.add(s.strip().lower())
    return subs



def suggest_mapping(missing_states=None, subdivisions=None):
    # Build normalized token sets for subdivisions
    subdivisions = subdivisions or set()
    missing_states = missing_states or []

    sub_tokens = {s: set(normalize_text(s).split()) for s in subdivisions}

    suggestions = {}
    for st in missing_states:
        if not st:
            continue
        st_tokens = set(normalize_text(st).split())
        # find subdivision with max token overlap
        best = None
        best_score = 0
        for sub, tokens in sub_tokens.items():
            score = len(st_tokens & tokens)
            if score > best_score:
                best_score = score
                best = sub
        # fallback: substring containment
        if best is None or best_score == 0:
            for sub in subdivisions:
                if normalize_text(st) in normalize_text(sub) or normalize_text(sub) in normalize_text(st):
                    best = sub
                    break
        # fallback: token-level fuzzy matching using sequence similarity
        if best is None:
            best_token_sub = None
            best_token_score = 0.0
            for sub, tokens in sub_tokens.items():
                for tk in tokens:
                    for stk in st_tokens:
                        score = difflib.SequenceMatcher(None, tk, stk).ratio()
                        if score > best_token_score:
                            best_token_score = score
                            best_token_sub = sub
            if best_token_score >= 0.60:
                best = best_token_sub

        # fallback: difflib close match on raw strings
        if best is None:
            raw_candidates = list(subdivisions)
            matches = difflib.get_close_matches(st, raw_candidates, n=1, cutoff=0.4)
            if matches:
                best = matches[0]

        if best:
            suggestions[st] = best
    return suggestions


def append_manual_mappings(suggestions: dict, path=MANUAL_FILE, backup=True):
    if not suggestions:
        print("No suggestions to append.")
        return path
    path.parent.mkdir(parents=True, exist_ok=True)

    # read existing rows (if any) and optionally backup
    if path.exists():
        with path.open(newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            fieldnames = reader.fieldnames or ['state','subdivision']
            old_rows = [r for r in reader]
        if backup:
            ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
            bak = path.with_suffix(f'.bak.{ts}')
            path.rename(bak)
    else:
        fieldnames = ['state','subdivision']
        old_rows = []

    # Avoid duplicating states already present in old_rows
    existing = {r['state'].strip().lower() for r in old_rows}
    new_rows = []
    for state, subdiv in suggestions.items():
        if state in existing:
            continue
        new_rows.append({'state': state, 'subdivision': subdiv})

    # write merged file (old rows first, then new rows)
    with path.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in old_rows:
            writer.writerow({k: r.get(k, '') for k in fieldnames})
        for r in new_rows:
            writer.writerow(r)

    print(f"Appended {len(new_rows)} entries to {path}")
    return path


def suggest_and_apply(apply=False, min_missing_count=0, raw_dir=None, processed_dir=None):
    """Main helper: suggest mappings for missing states and optionally append them.

    If min_missing_count > 0, only consider states with missing_rows >= threshold.
    Accepts optional raw_dir and processed_dir to operate on alternate paths (useful for testing).
    """
    proc_path = Path(processed_dir) if processed_dir else PROC
    raw_path = Path(raw_dir) if raw_dir else RAW

    missing = load_missing_states(path=proc_path / 'missing_year_state_counts.csv')
    if not missing:
        print("No missing states found to map.")
        return {}

    subs = load_subdivisions(path=raw_path / 'rainfall_validation.csv')
    if not subs:
        print("No subdivisions (rainfall file missing) to match against.")
        return {}

    existing = load_manual_map(path=proc_path / 'manual_state_to_subdivision.csv')
    to_consider = [s for s in missing if s not in existing]

    suggestions = suggest_mapping(to_consider, subs)

    if not suggestions:
        print("No confident suggestions found.")
        return {}

    print("Suggestions:")
    for k, v in suggestions.items():
        print(f"  {k} -> {v}")

    if apply:
        append_manual_mappings(suggestions, path=proc_path / 'manual_state_to_subdivision.csv')
    else:
        print("Dry run: pass apply=True to append suggestions to manual mapping file.")
    return suggestions


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--apply", action='store_true', help="Append suggestions to manual mapping file")
    args = p.parse_args()

    suggest_and_apply(apply=args.apply)
