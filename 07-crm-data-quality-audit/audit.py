"""
audit.py — Reusable CRM data-quality audit toolkit.

Loads a messy CRM opportunity export, runs a battery of data-quality checks,
scores overall hygiene (0-100), writes a cleaned file, and saves charts.

Usage:
    python3 audit.py [messy_csv]

Outputs:
    data/crm_export_clean.csv   — deduplicated, standardized, parsed
    data/audit_findings.json    — machine-readable results
    charts/*.png                — missingness, hygiene gauge, duplicates by source

The check functions are intentionally generic (pandas in, dict out) so the
module can be pointed at any opportunity-style export, not just this one.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).parent
MESSY = HERE / "data" / "crm_export_messy.csv"
CLEAN = HERE / "data" / "crm_export_clean.csv"
FINDINGS = HERE / "data" / "audit_findings.json"
CHART_DIR = HERE / "charts"

# --- canonical stage map (variant -> canonical) -----------------------------
STAGE_MAP = {
    "prospecting": "Prospecting", "prospect": "Prospecting", "new lead": "Prospecting",
    "qualification": "Qualification", "qualified": "Qualification",
    "qualifcation": "Qualification", "discovery": "Qualification",
    "proposal": "Proposal", "proposal sent": "Proposal", "quote sent": "Proposal",
    "negotiation": "Proposal",
    "closed won": "Closed Won", "closed-won": "Closed Won", "closedwon": "Closed Won",
    "won": "Closed Won",
    "closed lost": "Closed Lost", "closed-lost": "Closed Lost", "closedlost": "Closed Lost",
    "lost": "Closed Lost",
}

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
AMOUNT_RE = re.compile(r"[^\d.]")

TODAY = date(2026, 9, 25)   # audit "as of" date (fixed for reproducibility)

ORIGINAL_COLS = ["opportunity_id", "account_name", "contact_email", "owner_id",
                 "stage", "amount", "close_date", "created_date", "source"]


# ============================================================================
# loading / parsing helpers
# ============================================================================
def load_export(path: Path) -> pd.DataFrame:
    """Load the export as strings so messy values survive for diagnosis."""
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def parse_amount(raw: str):
    """Parse '$12,500.00' / 'USD 12500' / '12500.00' -> float; '' -> None."""
    s = raw.strip()
    if not s:
        return None
    try:
        return round(float(AMOUNT_RE.sub("", s)), 2)
    except ValueError:
        return None


def parse_date(raw: str):
    s = raw.strip()
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def standardize_stage(raw: str):
    s = raw.strip()
    if not s:
        return None
    return STAGE_MAP.get(s.lower(), f"UNMAPPED: {s}")


def email_valid(raw: str) -> bool:
    return bool(EMAIL_RE.match(raw.strip()))


# ============================================================================
# checks — each returns a plain dict of findings
# ============================================================================
def check_completeness(df: pd.DataFrame) -> dict:
    """% of non-blank values per field."""
    n = len(df)
    return {
        col: round((df[col].str.strip() != "").mean() * 100, 2)
        for col in df.columns
    }


def _dup_key(df: pd.DataFrame) -> pd.Series:
    """Normalized (account, amount, close_date) key — case/whitespace/format
    insensitive so 'Closed Won' vs 'closed won' dupes still match."""
    return (
        df["account_name"].str.strip().str.lower() + "|"
        + df["amount"].map(parse_amount).astype(str) + "|"
        + df["close_date"].str.strip()
    )


def check_duplicates(df: pd.DataFrame) -> dict:
    keys = _dup_key(df)
    dup_mask = keys.duplicated(keep="first") & (df["account_name"].str.strip() != "")
    dup_rows = df[dup_mask]
    by_source = dup_rows["source"].value_counts().to_dict() if len(dup_rows) else {}
    return {
        "duplicate_rows": int(dup_mask.sum()),
        "duplicate_rate_pct": round(dup_mask.mean() * 100, 2),
        "duplicate_groups": int(keys[dup_mask | keys.duplicated(keep=False)].nunique()) if dup_mask.any() else 0,
        "by_source": by_source,
    }


def check_emails(df: pd.DataFrame) -> dict:
    nonblank = df["contact_email"].str.strip() != ""
    invalid = nonblank & ~df["contact_email"].map(email_valid)
    return {
        "invalid_emails": int(invalid.sum()),
        "invalid_rate_pct": round(invalid[nonblank].mean() * 100, 2) if nonblank.any() else 0.0,
        "examples": df.loc[invalid, "contact_email"].head(5).tolist(),
    }


def check_stages(df: pd.DataFrame) -> dict:
    nonblank = df["stage"].str.strip() != ""
    mapped = df.loc[nonblank, "stage"].map(standardize_stage)
    unmapped = mapped[mapped.str.startswith("UNMAPPED")]
    return {
        "distinct_raw_values": int(df.loc[nonblank, "stage"].nunique()),
        "canonical_values": sorted(mapped[~mapped.str.startswith("UNMAPPED")].unique().tolist()),
        "unmapped_values": sorted(unmapped.unique().tolist()),
        "unmapped_count": int(len(unmapped)),
        "standardization_map": {k: v for k, v in sorted(STAGE_MAP.items())},
    }


def check_dates(df: pd.DataFrame) -> dict:
    created = df["created_date"].map(parse_date)
    closed = df["close_date"].map(parse_date)
    future_created = (created > TODAY).sum()
    close_before_created = ((closed.notna()) & (created.notna()) & (closed < created)).sum()
    unparseable_close = ((df["close_date"].str.strip() != "") & closed.isna()).sum()
    unparseable_created = ((df["created_date"].str.strip() != "") & created.isna()).sum()
    return {
        "future_created_dates": int(future_created),
        "close_before_created": int(close_before_created),
        "unparseable_close_dates": int(unparseable_close),
        "unparseable_created_dates": int(unparseable_created),
        "total_violations": int(future_created + close_before_created + unparseable_close + unparseable_created),
    }


def check_owners(df: pd.DataFrame, roster: set) -> dict:
    nonblank = df["owner_id"].str.strip() != ""
    orphan = nonblank & ~df["owner_id"].isin(roster)
    return {
        "orphan_owner_rows": int(orphan.sum()),
        "orphan_rate_pct": round(orphan[nonblank].mean() * 100, 2) if nonblank.any() else 0.0,
        "orphan_ids": sorted(df.loc[orphan, "owner_id"].unique().tolist()),
    }


# ============================================================================
# hygiene score
# ============================================================================
def compute_hygiene_score(n: int, completeness: dict, dups: dict,
                          emails: dict, dates: dict, owners: dict,
                          stages: dict) -> dict:
    """0-100 score: start at 100, subtract capped penalties per issue class."""
    avg_complete = sum(completeness.values()) / len(completeness)
    penalties = {
        "missing_values": round((100 - avg_complete) * 0.40, 2),
        "duplicates": round(min(20.0, dups["duplicate_rate_pct"] * 2), 2),
        "invalid_emails": round(min(10.0, emails["invalid_rate_pct"]), 2),
        "date_violations": round(min(15.0, dates["total_violations"] / n * 100 * 2), 2),
        "orphan_owners": round(min(10.0, owners["orphan_rate_pct"]), 2),
        "stage_inconsistency": round(min(5.0, max(0, stages["distinct_raw_values"] - 5) * 0.5), 2),
    }
    score = round(max(0.0, 100 - sum(penalties.values())), 1)
    return {"score": score, "penalties": penalties,
            "grade": "A" if score >= 90 else "B" if score >= 80 else "C"
                     if score >= 70 else "D" if score >= 60 else "F"}


# ============================================================================
# cleaning
# ============================================================================
def clean_export(df: pd.DataFrame) -> pd.DataFrame:
    """Deduplicate, standardize stages, parse amounts/dates, flag orphans."""
    clean = df.copy()
    clean["account_name"] = clean["account_name"].str.strip()
    clean["contact_email"] = clean["contact_email"].str.strip()
    clean["amount_parsed"] = clean["amount"].map(parse_amount)
    clean["close_date_parsed"] = clean["close_date"].map(
        lambda s: parse_date(s).isoformat() if parse_date(s) else "")
    clean["created_date_parsed"] = clean["created_date"].map(
        lambda s: parse_date(s).isoformat() if parse_date(s) else "")
    clean["stage_standardized"] = clean["stage"].map(standardize_stage)
    clean["email_valid"] = clean["contact_email"].map(
        lambda s: "" if not s else str(email_valid(s)))
    clean["is_duplicate"] = (_dup_key(df).duplicated(keep="first")
                             & (df["account_name"].str.strip() != ""))
    deduped = clean[~clean["is_duplicate"]].drop(columns=["is_duplicate"])
    return deduped.reset_index(drop=True)


# ============================================================================
# charts
# ============================================================================
def plot_missingness(completeness: dict, path: Path) -> None:
    items = sorted(completeness.items(), key=lambda kv: kv[1])
    fields = [k for k, _ in items]
    missing = [100 - v for _, v in items]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    bars = ax.barh(fields, missing, color="#c0392b")
    ax.set_xlabel("Missing (%)")
    ax.set_title("CRM Export — Missing Values by Field")
    ax.set_xlim(0, max(missing + [1]) * 1.25)
    for b, v in zip(bars, missing):
        ax.text(b.get_width() + 0.1, b.get_y() + b.get_height() / 2,
                f"{v:.1f}%", va="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def plot_hygiene_gauge(score: float, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 3.2))
    color = "#27ae60" if score >= 80 else "#f39c12" if score >= 60 else "#c0392b"
    ax.barh(["Hygiene score"], [score], color=color, height=0.45)
    ax.barh(["Hygiene score"], [100 - score], left=[score], color="#ecf0f1", height=0.45)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Score (0–100)")
    ax.set_title("Overall CRM Data-Hygiene Score")
    ax.text(score / 2, 0, f"{score:.1f}", ha="center", va="center",
            fontsize=22, fontweight="bold", color="white")
    for t in (25, 50, 75):
        ax.axvline(t, color="white", linewidth=2)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def plot_duplicates_by_source(by_source: dict, path: Path) -> None:
    if not by_source:
        fig, ax = plt.subplots(figsize=(7, 3))
        ax.text(0.5, 0.5, "No duplicates found", ha="center", fontsize=12)
        ax.axis("off")
    else:
        items = sorted(by_source.items(), key=lambda kv: kv[1], reverse=True)
        labels, vals = zip(*items)
        fig, ax = plt.subplots(figsize=(8, 4))
        bars = ax.bar(labels, vals, color="#2980b9")
        ax.set_ylabel("Duplicate rows")
        ax.set_title("Duplicate Opportunities by Lead Source")
        plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.5,
                    str(v), ha="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


# ============================================================================
# main
# ============================================================================
def run_audit(messy_path: Path = MESSY, roster: set | None = None) -> dict:
    df = load_export(messy_path)
    n = len(df)
    if roster is None:
        roster = {f"U-{1000 + i}" for i in range(40)}

    completeness = check_completeness(df)
    dups = check_duplicates(df)
    emails = check_emails(df)
    stages = check_stages(df)
    dates = check_dates(df)
    owners = check_owners(df, roster)
    hygiene = compute_hygiene_score(n, completeness, dups, emails, dates, owners, stages)

    # clean BEFORE score uses raw df only — score reflects the messy input
    clean = clean_export(df)
    clean.to_csv(CLEAN, index=False)

    # after-cleaning hygiene (re-run checks on cleaned frame, original cols only)
    after = compute_hygiene_score(
        len(clean), check_completeness(clean[ORIGINAL_COLS]),
        check_duplicates(clean[ORIGINAL_COLS]), check_emails(clean[ORIGINAL_COLS]),
        check_dates(clean[ORIGINAL_COLS]), check_owners(clean[ORIGINAL_COLS], roster),
        check_stages(clean[ORIGINAL_COLS]))

    findings = {
        "as_of": TODAY.isoformat(),
        "source_file": str(messy_path.name),
        "records": n,
        "completeness_pct": completeness,
        "duplicates": dups,
        "emails": emails,
        "stages": stages,
        "dates": dates,
        "owners": owners,
        "hygiene_before": hygiene,
        "hygiene_after": after,
        "clean_records": len(clean),
        "rows_removed_as_duplicates": n - len(clean),
    }

    CHART_DIR.mkdir(parents=True, exist_ok=True)
    plot_missingness(completeness, CHART_DIR / "missingness_by_field.png")
    plot_hygiene_gauge(hygiene["score"], CHART_DIR / "hygiene_score.png")
    plot_duplicates_by_source(dups["by_source"], CHART_DIR / "duplicates_by_source.png")

    FINDINGS.write_text(json.dumps(findings, indent=2))
    return findings


def print_summary(f: dict) -> None:
    print(f"\n{'=' * 60}\nCRM DATA-QUALITY AUDIT — {f['records']:,} records ({f['as_of']})")
    print(f"Hygiene score: {f['hygiene_before']['score']}/100 "
          f"(grade {f['hygiene_before']['grade']}) → {f['hygiene_after']['score']}/100 after cleaning")
    print("\nCompleteness (worst fields):")
    for col, pct in sorted(f["completeness_pct"].items(), key=lambda kv: kv[1])[:4]:
        print(f"  {col:15s} {pct:5.2f}%  (missing {100 - pct:.2f}%)")
    print(f"\nDuplicates: {f['duplicates']['duplicate_rows']:,} rows "
          f"({f['duplicates']['duplicate_rate_pct']}%) across {f['duplicates']['duplicate_groups']} groups")
    print(f"Invalid emails: {f['emails']['invalid_emails']:,}")
    print(f"Stage variants: {f['stages']['distinct_raw_values']} raw → "
          f"{len(f['stages']['canonical_values'])} canonical "
          f"(unmapped: {f['stages']['unmapped_count']})")
    print(f"Date violations: {f['dates']['total_violations']} "
          f"(future created: {f['dates']['future_created_dates']}, "
          f"close<created: {f['dates']['close_before_created']})")
    print(f"Orphan owners: {f['owners']['orphan_owner_rows']:,} rows "
          f"({f['owners']['orphan_rate_pct']}%)")
    print(f"\nClean file: {f['clean_records']:,} records "
          f"({f['rows_removed_as_duplicates']:,} duplicates removed)")
    print("=" * 60)


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else MESSY
    print_summary(run_audit(path))
