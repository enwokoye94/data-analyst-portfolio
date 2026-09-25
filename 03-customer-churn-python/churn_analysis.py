"""Customer churn analysis: synthetic telecom data, EDA, logistic regression."""
import csv, random
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

random.seed(99)
BASE = "/home/hatch/workspace/goals/remote-sales-operations-analyst-job-applications/files/data-analyst-portfolio/03-customer-churn-python"

rows = []
for i in range(1, 3001):
    tenure = random.randint(1, 72)
    contract = random.choices(["Month-to-month", "One year", "Two year"], weights=[45, 30, 25])[0]
    internet = random.choices(["Fiber optic", "DSL", "No internet"], weights=[45, 35, 20])[0]
    monthly = round(random.uniform(30, 120) if internet != "No internet" else random.uniform(20, 60), 2)
    # churn probability driven by contract, tenure, fiber, high charges
    p = 0.08
    if contract == "Month-to-month": p += 0.22
    if tenure < 12: p += 0.12
    if internet == "Fiber optic": p += 0.06
    if monthly > 90: p += 0.08
    churn = 1 if random.random() < p else 0
    rows.append([f"C{i:05d}", tenure, contract, internet,
                 random.choice(["Yes", "No"]),  # paperless billing
                 random.choice(["Electronic check", "Mailed check", "Bank transfer", "Credit card"]),
                 monthly, round(monthly * tenure * random.uniform(0.85, 1.0), 2), churn])

with open(f"{BASE}/data/telecom_customers.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["customer_id", "tenure_months", "contract", "internet_service",
                "paperless_billing", "payment_method", "monthly_charges",
                "total_charges", "churn"])
    w.writerows(rows)

# --- EDA (pure stdlib) ---
from collections import defaultdict
n = len(rows)
churned = [r for r in rows if r[8] == 1]
print(f"customers={n} churn_rate={len(churned)/n:.1%}")

def rate(key_idx, label):
    groups = defaultdict(lambda: [0, 0])
    for r in rows:
        g = groups[r[key_idx]]; g[1] += 1; g[0] += r[8]
    print(f"\nChurn by {label}:")
    for k in sorted(groups):
        print(f"  {k}: {groups[k][0]/groups[k][1]:.1%} (n={groups[k][1]})")
    return groups

g_contract = rate(2, "contract")
g_internet = rate(3, "internet_service")

# --- charts ---
fig, axes = plt.subplots(2, 2, figsize=(12, 9))
fig.suptitle("Customer Churn — Exploratory Analysis (synthetic telecom data)", fontsize=14, fontweight="bold")

ax = axes[0, 0]
cats = sorted(g_contract); vals = [g_contract[c][0]/g_contract[c][1]*100 for c in cats]
ax.bar(cats, vals, color=["#c0392b", "#e67e22", "#27ae60"])
ax.set_title("Churn % by Contract Type"); ax.set_ylabel("% churned")
for x, v in zip(cats, vals): ax.text(x, v+0.5, f"{v:.1f}%", ha="center", fontsize=9)

ax = axes[0, 1]
cats = sorted(g_internet); vals = [g_internet[c][0]/g_internet[c][1]*100 for c in cats]
ax.bar(cats, vals, color=["#8e44ad", "#2980b9", "#7f8c8d"])
ax.set_title("Churn % by Internet Service"); ax.set_ylabel("% churned")

ax = axes[1, 0]
ten_c = [r[1] for r in churned]; ten_s = [r[1] for r in rows if r[8] == 0]
ax.hist([ten_s, ten_c], bins=18, label=["Stayed", "Churned"], color=["#27ae60", "#c0392b"], alpha=0.7)
ax.set_title("Tenure Distribution: Stayed vs Churned"); ax.set_xlabel("Tenure (months)"); ax.legend()

ax = axes[1, 1]
ch_c = [r[6] for r in churned]; ch_s = [r[6] for r in rows if r[8] == 0]
ax.hist([ch_s, ch_c], bins=18, label=["Stayed", "Churned"], color=["#27ae60", "#c0392b"], alpha=0.7)
ax.set_title("Monthly Charges: Stayed vs Churned"); ax.set_xlabel("Monthly charges ($)"); ax.legend()

fig.tight_layout()
fig.savefig(f"{BASE}/charts/churn_eda.png", dpi=120)
print("\nchart saved")

# --- simple logistic regression (from scratch, gradient descent) ---
import math
def encode(r):
    return [1.0, r[1]/72,
            1.0 if r[2] == "Month-to-month" else 0.0,
            1.0 if r[3] == "Fiber optic" else 0.0,
            r[6]/120]
X = [encode(r) for r in rows]; y = [r[8] for r in rows]
random.shuffle(list(zip(X, y)))
pairs = list(zip(X, y)); random.shuffle(pairs)
X, y = [p[0] for p in pairs], [p[1] for p in pairs]
split = int(0.8 * n)
Xtr, ytr, Xte, yte = X[:split], y[:split], X[split:], y[split:]

w = [0.0]*5
lr = 0.5
for _ in range(400):
    grad = [0.0]*5
    for xi, yi in zip(Xtr, ytr):
        p = 1/(1+math.exp(-sum(a*b for a, b in zip(w, xi))))
        err = p - yi
        for j in range(5): grad[j] += err*xi[j]
    w = [wj - lr*g/len(Xtr) for wj, g in zip(w, grad)]

def predict(xi): return 1 if sum(a*b for a, b in zip(w, xi)) > 0 else 0
preds = [predict(xi) for xi in Xte]
acc = sum(p == t for p, t in zip(preds, yte))/len(yte)
tp = sum(1 for p, t in zip(preds, yte) if p == 1 and t == 1)
fp = sum(1 for p, t in zip(preds, yte) if p == 1 and t == 0)
fn = sum(1 for p, t in zip(preds, yte) if p == 0 and t == 1)
prec = tp/(tp+fp) if tp+fp else 0; rec = tp/(tp+fn) if tp+fn else 0
print(f"\nlogistic regression — accuracy={acc:.1%} precision={prec:.1%} recall={rec:.1%}")
names = ["intercept", "tenure", "month_to_month", "fiber_optic", "monthly_charges"]
print("coefficients:", {k: round(v, 3) for k, v in zip(names, w)})
