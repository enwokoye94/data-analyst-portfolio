# Data Dictionary — CRM Opportunity Export

Source table: synthetic Salesforce-style Opportunity export, 5,000 rows.
Seed: 42 (`generate_data.py`). "As of" date for the audit: 2026-09-25.

## Messy input fields (`data/crm_export_messy.csv`)

| Field | Type (raw) | Description | Known quality problems |
|---|---|---|---|
| `opportunity_id` | string | Unique row ID (`OP-00001` …; duplicates get `OP-D0001` …) | None — the only trustworthy key |
| `account_name` | string | Customer account | ~2% blank; case/whitespace inconsistent |
| `contact_email` | string | Primary contact email | ~3% blank; ~2.7% of non-blank are invalid (`no @`, `double @@`, leading/trailing spaces, `not-an-email`) |
| `owner_id` | string | Owning rep (`U-1000`–`U-1039` are real) | ~3% orphaned (`U-9999`, `inactive_user`, `admin`, …) |
| `stage` | string | Sales stage, free-text | ~4% blank; **26 distinct spellings** for 5 real stages |
| `amount` | string | Deal size | ~5% blank; ~22% stored as text (`"$12,500.00"`, `"USD 12500"`, `"12500 $"`) |
| `close_date` | string | Expected close (`YYYY-MM-DD`) | ~6% blank — the worst-completeness field |
| `created_date` | string | Record creation date | ~1.5% in the **future** (bad backfill); most of those have `close_date` *before* `created_date` |
| `source` | string | Lead source | Clean; `Bulk Import` is the main duplicate factory |

## Cleaning rules (`audit.py :: clean_export`)

| Rule | Detail |
|---|---|
| **Deduplicate** | Normalized key = `lower(strip(account_name))` + parsed `amount` + `close_date`; keep first occurrence, drop the rest (294 rows removed) |
| **Stage standardization** | Lookup table → `Prospecting`, `Qualification`, `Proposal`, `Closed Won`, `Closed Lost`; unmapped values prefixed `UNMAPPED:` (none in this dataset) |
| **Amount parsing** | Strip `$`, `USD`, commas, spaces → float; blank/unparseable → null. Raw value kept in `amount` |
| **Date parsing** | ISO parse → `YYYY-MM-DD`; blank/unparseable → blank. Raw value kept alongside |
| **Email check** | Regex validation → `email_valid` = `True`/`False`/blank; raw email preserved |
| **No imputation** | Missing values are **never** filled — they're flagged. Imputing deal amounts or close dates would fabricate the forecast |
| **Column retention** | Every raw column is kept; cleaned values go in `*_parsed` / `stage_standardized` columns so the transformation is fully auditable |

## Clean output fields (`data/crm_export_clean.csv`)

All 9 raw fields **plus**:

| Field | Description |
|---|---|
| `amount_parsed` | Numeric deal size (float), null where missing/unparseable |
| `close_date_parsed` | Parsed close date (`YYYY-MM-DD`) |
| `created_date_parsed` | Parsed created date (`YYYY-MM-DD`) |
| `stage_standardized` | One of the 5 canonical stages (null if blank) |
| `email_valid` | `True` / `False` / blank (blank email) |

Result: 4,706 rows (294 duplicates removed), hygiene score 71.4 → 83.2.
