# Ekene Nwokoye — Data Analyst Portfolio

Thirteen end-to-end projects covering the sales operations / business analyst toolkit:
**Power BI, SQL, Python, Excel, and Jupyter** — each with a business question, reproducible code, and honest findings.

## Sales Operations & Analytics

| # | Project | Tools | Question it answers |
|---|---|---|---|
| 1 | [Sales Pipeline & Forecast Dashboard](01-sales-pipeline-forecast-dashboard/) | Power BI, DAX | How much did we close, what's in the pipe, who's hitting quota? |
| 2 | [Order Operations Analysis](02-order-operations-sql/) | SQL (SQLite) | Where are we missing delivery promises, and who's at risk? |
| 5 | [Sales Commission Calculator](05-sales-commission-calculator/) | Advanced Excel | What does each rep earn under a tiered comp plan? |
| 6 | [RFM Customer Segmentation](06-rfm-customer-segmentation/) | SQL, Python | Which customers deserve retention vs. win-back spend? |
| 7 | [CRM Data-Quality Audit](07-crm-data-quality-audit/) | Python | Can we trust the pipeline data behind our forecast? |
| 8 | [Pipeline Forecast & Quota Attainment](08-pipeline-forecast-quota/) | Python, sklearn | Will we hit quota next half, and where's the risk? |

## Machine Learning & Data Science

| # | Project | Tools | Question it answers |
|---|---|---|---|
| 3 | [Customer Churn Analysis](03-customer-churn-python/) | Python, matplotlib | Which customers will leave, and what drives it? |
| 9 | [Store Sales Analysis](09-store-sales/) | Jupyter, pandas | When and where do we sell the most? |
| 10 | [Data Science Salary Analysis](10-ds-salary-analysis/) | Jupyter, sklearn, Plotly | What drives data-science compensation? |
| 11 | [Airbnb Listings Exploration](11-airbnb-listings/) | Jupyter, pandas | What can 1M+ listings teach us at scale? |
| 12 | [House Prices & Heating](12-house-prices-heating/) | Jupyter, seaborn | What actually drives home sale prices? |
| 13 | [World Happiness Analysis](13-world-happiness/) | Jupyter, seaborn | Which factors track with national happiness? |

## Financial Controls

| # | Project | Tools | Question it answers |
|---|---|---|---|
| 4 | [Revenue Reconciliation Case Study](04-revenue-reconciliation-excel/) | Advanced Excel | Do the billing system and ERP agree at month-end? |

## Publishing to GitHub Pages

1. Create a repo named `data-analyst-portfolio` on GitHub
2. Push this folder's contents to `main`
3. Repo Settings → Pages → Deploy from branch → `main` / root
4. Your site goes live at `https://<username>.github.io/data-analyst-portfolio/`

Link it from your resume header, LinkedIn featured section, and job applications.

## Notes

- Every dataset is **synthetic** — no real employer or customer data anywhere
- SQL is standard and portable (CTEs, window functions); the Python churn script runs on stdlib + matplotlib
- If you rename the repo, update the project links in `index.html`
