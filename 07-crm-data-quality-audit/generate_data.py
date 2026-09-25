"""
generate_data.py — Synthetic messy CRM opportunity export generator.

Creates data/crm_export_messy.csv (~5,000 opportunity records) with realistic
data-quality problems baked in, mimicking what a Sales Operations analyst would
pull from a poorly-governed CRM:

  * Duplicate opportunities (same account + amount + close date)
  * Missing close dates / amounts / stages
  * Invalid contact emails
  * Inconsistent stage names ("Closed Won" vs "Closed-Won" vs "closed won")
  * Created dates in the future (bad system integrations / backfills)
  * Amounts stored as text with $ and commas
  * Owner IDs that don't exist in the owner roster (orphans)

Everything is synthetic. Fixed random seed (42) for reproducibility.
"""
import csv
import random
from datetime import date, timedelta

SEED = 42
N_BASE = 4700          # clean base records
N_DUPLICATES = 300     # extra duplicate rows appended
OUT = "data/crm_export_messy.csv"

random.seed(SEED)

# ------------------------------------------------------------------ roster --
# Legitimate sales owners — anything else is an "orphan" owner ID.
OWNERS = [f"U-{1000 + i}" for i in range(40)]
ORPHAN_OWNERS = ["U-9999", "U-8888", "inactive_user", "U-0000", "admin"]

ACCOUNTS = [
    "Acme Industrial", "BluePeak Logistics", "Copperline Foods", "DeltaWave Media",
    "Everline Health", "ForgePoint Systems", "Granite Ridge Co", "Harborline Bank",
    "Ironclad Security", "Juniper Retail", "Keystone Energy", "Larkspur Labs",
    "Meridian Freight", "Northgate Auto", "Onyx Pharma", "Pinnacle Travel",
    "Quartzline Telecom", "Redwood Outdoors", "Silverline SaaS", "Tidewater Marine",
    "Umbra Defense", "Vertex Capital", "Willow Creek Farms", "Xenon Robotics",
    "Yellowpine Lumber", "Zephyr Airlines",
]

FIRST = ["Ava", "Liam", "Maya", "Noah", "Zoe", "Ethan", "Priya", "Owen", "Lena",
         "Marcus", "Sofia", "Raj", "Ella", "Chris", "Nina", "Tom", "Aisha", "Ben",
         "Kara", "Dev"]
LAST = ["Smith", "Johnson", "Garcia", "Nguyen", "Patel", "Kim", "Brown", "Lee",
        "Davis", "Miller", "Wilson", "Moore", "Taylor", "Anderson", "Thomas"]

DOMAINS = ["gmail.com", "outlook.com", "yahoo.com", "company.com", "example.org"]

# Canonical stages + the messy variants reps actually type.
STAGE_VARIANTS = {
    "Prospecting": ["Prospecting", "prospecting", "PROSPECTING", "Prospect", "New Lead"],
    "Qualification": ["Qualification", "qualification", "Qualifcation", "Qualified", "Discovery"],
    "Proposal": ["Proposal", "proposal", "Proposal Sent", "Quote Sent", "Negotiation"],
    "Closed Won": ["Closed Won", "Closed-Won", "closed won", "CLOSED WON", "Won", "ClosedWon"],
    "Closed Lost": ["Closed Lost", "Closed-Lost", "closed lost", "Lost", "ClosedLost"],
}

SOURCES = ["Web Form", "Inbound Call", "Partner Referral", "Outbound SDR", "Bulk Import", "Trade Show"]


def money_text(amount: float) -> str:
    """Render an amount the way a bad import leaves it: text with $ and commas."""
    style = random.random()
    if style < 0.5:
        return f"${amount:,.2f}"
    if style < 0.75:
        return f"${amount:,.0f}"
    if style < 0.9:
        return f"USD {amount:,.2f}"
    return f"{amount:,.2f} $"


def rand_date(start: date, end: date) -> date:
    return start + timedelta(days=random.randint(0, (end - start).days))


def make_base(i: int) -> dict:
    account = random.choice(ACCOUNTS)
    created = rand_date(date(2024, 1, 1), date(2026, 8, 31))
    close = created + timedelta(days=random.randint(7, 240))
    canonical = random.choices(
        list(STAGE_VARIANTS), weights=[25, 30, 20, 15, 10], k=1)[0]
    stage = random.choice(STAGE_VARIANTS[canonical])
    amount = round(random.uniform(2_000, 250_000), 2)

    # email: mostly fine, sometimes broken
    email_roll = random.random()
    contact = f"{random.choice(FIRST).lower()}.{random.choice(LAST).lower()}@{random.choice(DOMAINS)}"
    if email_roll < 0.04:
        contact = random.choice([
            contact.replace("@", ""),            # no @
            contact.replace(".", "", 1),         # no dot
            contact + " ",                       # trailing space
            " " + contact,                       # leading space
            contact.replace("@", "@@"),          # double @
            "not-an-email",
            contact.split("@")[0],               # missing domain
        ])

    # owner: mostly legit, sometimes orphaned
    owner = random.choice(OWNERS) if random.random() > 0.03 else random.choice(ORPHAN_OWNERS)

    row = {
        "opportunity_id": f"OP-{i:05d}",
        "account_name": account,
        "contact_email": contact,
        "owner_id": owner,
        "stage": stage,
        "amount": f"{amount:.2f}",               # clean numeric-as-string by default
        "close_date": close.isoformat(),
        "created_date": created.isoformat(),
        "source": random.choice(SOURCES),
    }

    # ---- inject missingness ---------------------------------------------
    if random.random() < 0.06:      # missing close date
        row["close_date"] = ""
    if random.random() < 0.05:      # missing amount
        row["amount"] = ""
    if random.random() < 0.04:      # missing stage
        row["stage"] = ""
    if random.random() < 0.03:      # missing contact email
        row["contact_email"] = ""
    if random.random() < 0.02:      # missing account name
        row["account_name"] = ""

    # ---- amounts stored as messy text ------------------------------------
    if row["amount"] and random.random() < 0.22:
        row["amount"] = money_text(float(row["amount"]))

    # ---- future created dates (bad integration backfill) -----------------
    if random.random() < 0.015:
        row["created_date"] = rand_date(date(2026, 10, 1), date(2027, 6, 30)).isoformat()

    return row


def main() -> None:
    rows = [make_base(i) for i in range(1, N_BASE + 1)]

    # ---- duplicates: copy an existing row, give it a new ID ----------------
    # (some exact, some with a slightly different stage spelling — same deal)
    dup_sources = []
    for j in range(N_DUPLICATES):
        src = random.choice(rows)
        dup = dict(src)
        dup["opportunity_id"] = f"OP-D{j:04d}"
        if random.random() < 0.4 and dup["stage"]:
            canon = next((k for k, v in STAGE_VARIANTS.items() if dup["stage"] in v), None)
            if canon:
                dup["stage"] = random.choice([v for v in STAGE_VARIANTS[canon] if v != dup["stage"]] or [dup["stage"]])
        rows.append(dup)
        dup_sources.append(dup["source"])

    random.shuffle(rows)

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows):,} rows -> {OUT}")
    print(f"  base records : {N_BASE:,}")
    print(f"  injected dups: {N_DUPLICATES:,}")


if __name__ == "__main__":
    main()
