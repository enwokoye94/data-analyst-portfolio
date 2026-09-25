# Data Science Salary Analysis (Python + SQL + Selenium)

Multi-part analysis of data-science compensation: Glassdoor scraping, data cleaning,
exploratory analysis with Plotly choropleths, and salary prediction with machine learning.

**Notebooks:** `EDA.ipynb`, `ML modeling.ipynb` (both run clean); `GlassDoor_Scrapper.ipynb`
(Selenium scraper, modernized to Selenium 4 syntax — requires a live browser session to execute).

## What was done
- Scraped Glassdoor postings with Selenium (`glassdoor_scrapper.py`, `glassdoor_selenium_scrapper.py`)
- Cleaned and normalized titles, salaries, locations, and company metadata
- Built interactive Plotly choropleth maps of salary by state
- Trained Linear Regression, Lasso (tuned via GridSearchCV), Random Forest, and Decision Tree models

## Key findings
- **Lasso regression (α = 0.44)** predicts salary with **MAE ≈ $21.3K** — best of the tested models
- Random Forest close behind at MAE ≈ $21.9K; plain linear regression trails at ≈ $30.2K
- State-level choropleths show the expected coastal salary premiums

## Skills
Python, pandas, scikit-learn (GridSearchCV, regularization), Plotly, Selenium, EDA

*Source: original project at github.com/enwokoye94/DS-Salary-Analysis. Notebooks verified
and repaired — see the portfolio's `FIXES.md` notes.*
