"""
Builds commission_calculator.xlsx — a fully formula-driven sales commission workbook.

Reads data/deals.csv + data/reps.csv (see generate_data.py) and writes:
    commission_calculator.xlsx
Sheets: Deals | Plan | Rep Summary | Dashboard
Every calculated cell is a real Excel formula (SUMIFS/COUNTIFS/MAX/MIN/IF/INDEX/MATCH...).
No values are hardcoded into formula cells — change a plan parameter on the Plan
sheet and the whole workbook recalculates.
"""
import csv
from pathlib import Path
from copy import copy

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.formatting.rule import CellIsRule
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.chart import BarChart, PieChart, Reference

BASE = Path(__file__).resolve().parent
QUARTERS = ["Q1", "Q2", "Q3", "Q4"]

# ---------- styling ----------
NAVY = "1F3864"
ACCENT = "2E75B6"
LIGHT = "D9E2F3"
GREEN_FILL = PatternFill("solid", fgColor="C6EFCE")
AMBER_FILL = PatternFill("solid", fgColor="FFEB9C")
RED_FILL = PatternFill("solid", fgColor="FFC7CE")
GREEN_FONT = Font(color="006100")
AMBER_FONT = Font(color="9C6500")
RED_FONT = Font(color="9C0006")

hdr_font = Font(bold=True, color="FFFFFF", size=11)
hdr_fill = PatternFill("solid", fgColor=NAVY)
title_font = Font(bold=True, color=NAVY, size=16)
sub_font = Font(bold=True, color=NAVY, size=12)
thin = Side(style="thin", color="B4C6E7")
border = Border(left=thin, right=thin, top=thin, bottom=thin)

CURR = '"$"#,##0'
PCT = "0.0%"
INT = "#,##0"


def style_header(ws, row, ncols):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = hdr_font
        cell.fill = hdr_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border


def style_body(ws, min_row, max_row, ncols, fmts=None):
    fmts = fmts or {}
    for r in range(min_row, max_row + 1):
        for c in range(1, ncols + 1):
            cell = ws.cell(row=r, column=c)
            cell.border = border
            cell.alignment = Alignment(vertical="center")
            if c in fmts:
                cell.number_format = fmts[c]


def add_name(wb, name, ref):
    wb.defined_names[name] = DefinedName(name, attr_text=ref)


def main():
    with open(BASE / "data" / "deals.csv") as f:
        deals = list(csv.DictReader(f))
    with open(BASE / "data" / "reps.csv") as f:
        reps = list(csv.DictReader(f))

    n = len(deals)
    last_deal = n + 1          # Deals data rows: 2..n+1
    nsum = len(reps) * 4       # 48 rep-quarter rows
    last_sum = nsum + 1        # Rep Summary data rows: 2..49

    wb = Workbook()

    # ================= DEALS =================
    ws = wb.active
    ws.title = "Deals"
    ws.sheet_properties.tabColor = ACCENT
    headers = ["deal_id", "rep_name", "region", "quarter",
               "product_line", "deal_size", "new_logo"]
    ws.append(headers)
    for d in deals:
        ws.append([d["deal_id"], d["rep_name"], d["region"], d["quarter"],
                   d["product_line"], int(d["deal_size"]), d["new_logo"]])
    style_header(ws, 1, 7)
    style_body(ws, 2, last_deal, 7, {6: CURR})
    widths = [10, 16, 10, 10, 18, 13, 10]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = w
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:G{last_deal}"

    # ================= PLAN =================
    wp = wb.create_sheet("Plan")
    wp.sheet_properties.tabColor = "70AD47"
    wp["A1"] = "Commission Plan — FY2025"
    wp["A1"].font = title_font
    wp.merge_cells("A1:B1")
    wp["A2"] = "Change any blue parameter and the whole workbook recalculates."
    wp["A2"].font = Font(italic=True, color="595959")
    wp.merge_cells("A2:B2")

    params = [
        ("Tier 1 rate — 0–100% of quota", 0.05, PCT),
        ("Tier 2 rate — 100–150% of quota", 0.08, PCT),
        ("Tier 3 rate — above 150% of quota", 0.12, PCT),
        ("Accelerator rate — revenue above 125% of quota", 0.02, PCT),
        ("Accelerator threshold (× quota)", 1.25, "0.00"),
        ("New-logo spiff per deal", 500, CURR),
        ("Monthly draw per rep", 3000, CURR),
        ("Quarterly draw (monthly × 3)", "=B9*3", CURR),
        ("Tier 2 / Tier 3 threshold (× quota)", 1.50, "0.00"),
    ]
    wp["A3"], wp["B3"] = "Parameter", "Value"
    style_header(wp, 3, 2)
    for i, (label, val, fmt) in enumerate(params):
        r = 4 + i
        wp.cell(row=r, column=1, value=label).border = border
        c = wp.cell(row=r, column=2, value=val)
        c.border = border
        c.number_format = fmt
        if isinstance(val, (int, float)):
            c.fill = PatternFill("solid", fgColor="DDEBF7")  # blue = editable input
    wp.column_dimensions["A"].width = 46
    wp.column_dimensions["B"].width = 16

    notes = [
        "",
        "How the plan works:",
        "• Commission is paid on MARGINAL revenue: 5% on the first 100% of quota,",
        "  8% on revenue from 100–150% of quota, 12% above 150%.",
        "• Accelerator: an extra 2% on all revenue above 125% of quota (stacks with tiers).",
        "• $500 spiff for every new-logo (Y) deal, paid on top of tiered commission.",
        "• $3,000/month recoverable draw: payout each quarter is MAX(commission, $9,000).",
        "• Rep Summary is 100% formulas — no hardcoded payouts.",
    ]
    r0 = 4 + len(params) + 1
    for i, line in enumerate(notes):
        c = wp.cell(row=r0 + i, column=1, value=line)
        if i == 1:
            c.font = sub_font

    # named ranges for plan parameters (Plan rows 4..12)
    add_name(wb, "rate_t1", "Plan!$B$4")
    add_name(wb, "rate_t2", "Plan!$B$5")
    add_name(wb, "rate_t3", "Plan!$B$6")
    add_name(wb, "rate_accel", "Plan!$B$7")
    add_name(wb, "accel_mult", "Plan!$B$8")
    add_name(wb, "spiff_amt", "Plan!$B$9")
    add_name(wb, "qtr_draw", "Plan!$B$11")
    add_name(wb, "t2_mult", "Plan!$B$12")
    # deal column ranges
    add_name(wb, "d_rep", f"Deals!$B$2:$B${last_deal}")
    add_name(wb, "d_qtr", f"Deals!$D$2:$D${last_deal}")
    add_name(wb, "d_size", f"Deals!$F$2:$F${last_deal}")
    add_name(wb, "d_newlogo", f"Deals!$G$2:$G${last_deal}")

    # ================= REP SUMMARY =================
    wr = wb.create_sheet("Rep Summary")
    wr.sheet_properties.tabColor = "ED7D31"
    cols = ["Rep", "Region", "Quarter", "Quota", "Revenue", "Attainment %",
            "Tier 1 $", "Tier 2 $", "Tier 3 $", "Accelerator $",
            "New-logo deals", "Spiff $", "Total commission $",
            "Draw $", "Payout $", "Payout vs quota", "Band"]
    wr.append(cols)
    style_header(wr, 1, len(cols))

    r = 2
    for rep in reps:
        for q in QUARTERS:
            wr.cell(row=r, column=1, value=rep["rep_name"])
            wr.cell(row=r, column=2, value=rep["region"])
            wr.cell(row=r, column=3, value=q)
            wr.cell(row=r, column=4, value=int(rep["quarterly_quota"]))
            # E revenue
            wr.cell(row=r, column=5, value=f"=SUMIFS(d_size,d_rep,A{r},d_qtr,C{r})")
            # F attainment
            wr.cell(row=r, column=6, value=f"=IF(D{r}=0,0,E{r}/D{r})")
            # G/H/I tiers (marginal)
            wr.cell(row=r, column=7, value=f"=MIN(E{r},D{r})*rate_t1")
            wr.cell(row=r, column=8, value=f"=MAX(MIN(E{r},D{r}*t2_mult)-D{r},0)*rate_t2")
            wr.cell(row=r, column=9, value=f"=MAX(E{r}-D{r}*t2_mult,0)*rate_t3")
            # J accelerator
            wr.cell(row=r, column=10, value=f"=MAX(E{r}-D{r}*accel_mult,0)*rate_accel")
            # K new-logo count, L spiff
            wr.cell(row=r, column=11,
                    value=f'=COUNTIFS(d_rep,A{r},d_qtr,C{r},d_newlogo,"Y")')
            wr.cell(row=r, column=12, value=f"=K{r}*spiff_amt")
            # M total commission, N draw, O payout, P payout vs quota
            wr.cell(row=r, column=13, value=f"=G{r}+H{r}+I{r}+J{r}+L{r}")
            wr.cell(row=r, column=14, value="=qtr_draw")
            wr.cell(row=r, column=15, value=f"=MAX(M{r},N{r})")
            wr.cell(row=r, column=16, value=f"=IF(D{r}=0,0,O{r}/D{r})")
            # Q attainment band
            wr.cell(row=r, column=17,
                    value=(f'=IF(F{r}>=1.5,"≥150%",IF(F{r}>=1.25,"125-149%",'
                           f'IF(F{r}>=1,"100-124%",IF(F{r}>=0.8,"80-99%","<80%"))))'))
            r += 1

    fmts = {4: CURR, 5: CURR, 6: PCT, 7: CURR, 8: CURR, 9: CURR, 10: CURR,
            12: CURR, 13: CURR, 14: CURR, 15: CURR, 16: PCT}
    style_body(wr, 2, last_sum, len(cols), fmts)
    for c, w in zip("ABCDEFGHJKLMNOPQ", [16, 10, 9, 12, 13, 12, 11, 11, 11, 13, 13, 11, 17, 11, 13, 14, 11]):
        wr.column_dimensions[c].width = w
    wr.freeze_panes = "A2"
    wr.auto_filter.ref = f"A1:Q{last_sum}"
    # attainment traffic lights
    wr.conditional_formatting.add(f"F2:F{last_sum}",
        CellIsRule(operator="greaterThanOrEqual", formula=["1"], fill=GREEN_FILL, font=GREEN_FONT))
    wr.conditional_formatting.add(f"F2:F{last_sum}",
        CellIsRule(operator="between", formula=["0.8", "1"], fill=AMBER_FILL, font=AMBER_FONT))
    wr.conditional_formatting.add(f"F2:F{last_sum}",
        CellIsRule(operator="lessThan", formula=["0.8"], fill=RED_FILL, font=RED_FONT))

    add_name(wb, "rs_rep", f"'Rep Summary'!$A$2:$A${last_sum}")
    add_name(wb, "rs_qtr", f"'Rep Summary'!$C$2:$C${last_sum}")
    add_name(wb, "rs_att", f"'Rep Summary'!$F$2:$F${last_sum}")
    add_name(wb, "rs_comm", f"'Rep Summary'!$M$2:$M${last_sum}")
    add_name(wb, "rs_spiff", f"'Rep Summary'!$L$2:$L${last_sum}")
    add_name(wb, "rs_payout", f"'Rep Summary'!$O$2:$O${last_sum}")
    add_name(wb, "rs_band", f"'Rep Summary'!$Q$2:$Q${last_sum}")

    # ================= DASHBOARD =================
    wd = wb.create_sheet("Dashboard")
    wd.sheet_properties.tabColor = NAVY
    wd["A1"] = "Sales Commission Dashboard — FY2025"
    wd["A1"].font = title_font
    wd.merge_cells("A1:B1")

    kpis = [
        ("Total deals closed", "=COUNT(d_size)", INT),
        ("Total revenue", "=SUM(d_size)", CURR),
        ("Total commission earned (pre-draw)", "=SUM(rs_comm)", CURR),
        ("Total payout (after draw guarantee)", "=SUM(rs_payout)", CURR),
        ("Payout as % of revenue", "=B6/B4", PCT),
        ("Average attainment (48 rep-quarters)", "=AVERAGE(rs_att)", PCT),
        ("New-logo spiffs paid", "=SUM(rs_spiff)", CURR),
        ('Rep-quarters paid at draw (commission < $9k)', "=SUMPRODUCT(--(rs_comm<qtr_draw))", INT),
        ("Top single-quarter earner", '=INDEX(rs_rep,MATCH(MAX(rs_payout),rs_payout,0))', None),
        ("Top single-quarter payout", "=MAX(rs_payout)", CURR),
    ]
    wd["A2"], wd["B2"] = "Metric", "Value"
    style_header(wd, 2, 2)
    for i, (label, formula, fmt) in enumerate(kpis):
        row = 3 + i
        wd.cell(row=row, column=1, value=label).border = border
        c = wd.cell(row=row, column=2, value=formula)
        c.border = border
        if fmt:
            c.number_format = fmt
    wd.column_dimensions["A"].width = 44
    wd.column_dimensions["B"].width = 24

    # annual payout by rep
    r0 = 3 + len(kpis) + 2          # row 15
    wd.cell(row=r0, column=1, value="Annual payout by rep").font = sub_font
    wd.cell(row=r0 + 1, column=1, value="Rep")
    wd.cell(row=r0 + 1, column=2, value="Annual payout")
    style_header(wd, r0 + 1, 2)
    for i, rep in enumerate(reps):
        row = r0 + 2 + i
        wd.cell(row=row, column=1, value=rep["rep_name"]).border = border
        c = wd.cell(row=row, column=2, value=f"=SUMIFS(rs_payout,rs_rep,A{row})")
        c.border = border
        c.number_format = CURR
    ann_lo, ann_hi = r0 + 2, r0 + 1 + len(reps)   # 17..28
    wd.cell(row=ann_hi + 1, column=1, value="Highest annual earner").font = Font(bold=True)
    wd.cell(row=ann_hi + 1, column=2,
            value=f"=INDEX(A{ann_lo}:A{ann_hi},MATCH(MAX(B{ann_lo}:B{ann_hi}),B{ann_lo}:B{ann_hi},0))")
    wd.cell(row=ann_hi + 2, column=1, value="Highest annual payout").font = Font(bold=True)
    c = wd.cell(row=ann_hi + 2, column=2, value=f"=MAX(B{ann_lo}:B{ann_hi})")
    c.number_format = CURR

    # attainment distribution
    d0 = ann_hi + 4                 # row 32
    wd.cell(row=d0, column=1, value="Attainment distribution (48 rep-quarters)").font = sub_font
    wd.cell(row=d0 + 1, column=1, value="Band")
    wd.cell(row=d0 + 1, column=2, value="Rep-quarters")
    style_header(wd, d0 + 1, 2)
    bands = ["<80%", "80-99%", "100-124%", "125-149%", "≥150%"]
    for i, b in enumerate(bands):
        row = d0 + 2 + i
        wd.cell(row=row, column=1, value=b).border = border
        c = wd.cell(row=row, column=2, value=f'=COUNTIF(rs_band,"{b}")')
        c.border = border
        c.number_format = INT
    dist_lo, dist_hi = d0 + 2, d0 + 1 + len(bands)   # 34..38

    # quarterly payout
    q0 = dist_hi + 2                # row 40
    wd.cell(row=q0, column=1, value="Payout by quarter").font = sub_font
    wd.cell(row=q0 + 1, column=1, value="Quarter")
    wd.cell(row=q0 + 1, column=2, value="Total payout")
    style_header(wd, q0 + 1, 2)
    for i, q in enumerate(QUARTERS):
        row = q0 + 2 + i
        wd.cell(row=row, column=1, value=q).border = border
        c = wd.cell(row=row, column=2, value=f'=SUMIFS(rs_payout,rs_qtr,"{q}")')
        c.border = border
        c.number_format = CURR
    qtr_lo, qtr_hi = q0 + 2, q0 + 1 + len(QUARTERS)  # 42..45

    # charts
    bar = BarChart()
    bar.type = "col"
    bar.title = "Payout by quarter"
    bar.y_axis.title = "$"
    data = Reference(wd, min_col=2, min_row=q0 + 1, max_row=qtr_hi)
    cats = Reference(wd, min_col=1, min_row=qtr_lo, max_row=qtr_hi)
    bar.add_data(data, titles_from_data=True)
    bar.set_categories(cats)
    bar.shape = 4
    wd.add_chart(bar, "D40")

    pie = PieChart()
    pie.title = "Attainment distribution (rep-quarters)"
    data = Reference(wd, min_col=2, min_row=d0 + 1, max_row=dist_hi)
    cats = Reference(wd, min_col=1, min_row=dist_lo, max_row=dist_hi)
    pie.add_data(data, titles_from_data=True)
    pie.set_categories(cats)
    wd.add_chart(pie, "D22")

    out = BASE / "commission_calculator.xlsx"
    wb.save(out)
    print(f"wrote {out}  ({n} deals, {nsum} rep-quarter rows)")


if __name__ == "__main__":
    main()
