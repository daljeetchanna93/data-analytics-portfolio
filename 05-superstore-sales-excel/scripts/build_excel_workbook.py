"""Build the stakeholder Excel workbook for the Superstore analysis.

Input : data/clean/orders_clean.csv, regional_managers.csv, returned_orders.csv
Output: results/Superstore_Sales_Analysis.xlsx

Every summary number in the workbook is a live Excel formula (SUMIFS, COUNTIFS,
AVERAGEIFS, INDEX/MATCH, IFERROR) pointing at the Data sheet, so regional managers
can filter, audit or extend it in Excel. Run from the project folder:
    python scripts/build_excel_workbook.py
"""
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.formatting.rule import CellIsRule, DataBarRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import Table, TableStyleInfo

ROOT = Path(__file__).resolve().parents[1]
orders = pd.read_csv(ROOT / "data/clean/orders_clean.csv", parse_dates=["Order Date", "Ship Date"])
people = pd.read_csv(ROOT / "data/clean/regional_managers.csv")
returns = pd.read_csv(ROOT / "data/clean/returned_orders.csv")
OUT = ROOT / "results/Superstore_Sales_Analysis.xlsx"

FONT = "Arial"
NAVY = "1F3864"
HDR_FILL = PatternFill("solid", fgColor=NAVY)
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")
KPI_FILL = PatternFill("solid", fgColor="EEF3FB")
THIN = Side(style="thin", color="BFBFBF")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
USD = '$#,##0;($#,##0);"-"'
PCT = '0.0%;(0.0%);"-"'
INT = '#,##0'
RED_FONT = Font(name=FONT, color="C00000")
RED_FILL = PatternFill("solid", fgColor="FDE2E2")
GREEN_FILL = PatternFill("solid", fgColor="E2F5E9")

wb = Workbook()


def style_header(ws, row, c1, c2):
    for c in range(c1, c2 + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = Font(name=FONT, bold=True, color="FFFFFF")
        cell.fill = HDR_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BOX


def body(cell, fmt=None, bold=False, color="000000"):
    cell.font = Font(name=FONT, bold=bold, color=color)
    cell.border = BOX
    if fmt:
        cell.number_format = fmt


def title(ws, text, subtitle=None):
    ws["A1"] = text
    ws["A1"].font = Font(name=FONT, bold=True, size=16, color=NAVY)
    if subtitle:
        ws["A2"] = subtitle
        ws["A2"].font = Font(name=FONT, italic=True, size=10, color="595959")
    ws.sheet_view.showGridLines = False


def finish_chart(ch):
    ch.roundedCorners = False
    if ch.legend is not None:
        ch.legend.overlay = False
    for ax in (ch.x_axis, ch.y_axis):
        ax.delete = False


# ---------------------------------------------------------------- Data sheet
data_cols = ["Row ID", "Order ID", "Order Date", "Ship Date", "Ship Mode", "Customer ID", "Customer Name",
             "Segment", "City", "State", "Postal Code", "Region", "Manager", "Product ID", "Category",
             "Sub-Category", "Product Name", "Sales", "Quantity", "Discount", "Profit", "Year",
             "Ship Days", "Returned"]
ws_data = wb.active
ws_data.title = "Data"
ws_data.append(data_cols)
for row in orders[data_cols].itertuples(index=False):
    ws_data.append([v.to_pydatetime() if isinstance(v, pd.Timestamp) else v for v in row])
N = len(orders) + 1  # last data row
col = {name: get_column_letter(i + 1) for i, name in enumerate(data_cols)}
fmt_map = {"Order Date": "yyyy-mm-dd", "Ship Date": "yyyy-mm-dd", "Sales": '$#,##0.00',
           "Profit": '$#,##0.00;[Red]($#,##0.00)', "Discount": "0%", "Postal Code": "00000", "Year": "0"}
for name, fmt in fmt_map.items():
    for r in range(2, N + 1):
        ws_data[f"{col[name]}{r}"].number_format = fmt
tbl = Table(displayName="Orders", ref=f"A1:{get_column_letter(len(data_cols))}{N}")
tbl.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
ws_data.add_table(tbl)
ws_data.freeze_panes = "A2"
widths = {"Order ID": 16, "Customer Name": 20, "Product Name": 45, "Ship Mode": 14, "Sub-Category": 13,
          "Order Date": 12, "Ship Date": 12, "Product ID": 17, "Customer ID": 11, "City": 15, "State": 14}
for name, letter in col.items():
    ws_data.column_dimensions[letter].width = widths.get(name, 10)


def rng(name):
    """Absolute range of a Data column, e.g. Data!$R$2:$R$9995"""
    return f"Data!${col[name]}$2:${col[name]}${N}"


SALES, PROFIT, DISC, REGION, YEAR = rng("Sales"), rng("Profit"), rng("Discount"), rng("Region"), rng("Year")
CAT, SUBCAT, STATE, RET, QTY = rng("Category"), rng("Sub-Category"), rng("State"), rng("Returned"), rng("Quantity")

# ---------------------------------------------------------------- Managers / Returns lookup sheets
ws_mgr = wb.create_sheet("Managers")
ws_mgr.append(["Region", "Manager"])
for r in people[["Region", "Manager"]].itertuples(index=False):
    ws_mgr.append(list(r))
style_header(ws_mgr, 1, 1, 2)
for r in range(2, ws_mgr.max_row + 1):
    for c in (1, 2):
        body(ws_mgr.cell(row=r, column=c))
ws_mgr.column_dimensions["A"].width = 12
ws_mgr.column_dimensions["B"].width = 22

ws_ret = wb.create_sheet("Returns")
ws_ret.append(["Order ID", "Returned"])
for r in returns[["Order ID", "Returned"]].itertuples(index=False):
    ws_ret.append(list(r))
style_header(ws_ret, 1, 1, 2)
ws_ret.column_dimensions["A"].width = 18

# ---------------------------------------------------------------- Dashboard
ws = wb.create_sheet("Dashboard", 0)
title(ws, "Superstore Sales & Profitability Dashboard",
      "Pick a Region and Year in the yellow cells. Every number below recalculates from the Data sheet.")
for c, w in zip("ABCDEFGHI", [32, 16, 16, 16, 12, 22, 16, 16, 16]):
    ws.column_dimensions[c].width = w

ws["A4"], ws["A5"] = "Region", "Year"
for ref, opts in (("B4", "All,Central,East,South,West"), ("B5", "All,2015,2016,2017,2018")):
    ws[ref] = "All"
    ws[ref].fill = INPUT_FILL
    ws[ref].font = Font(name=FONT, bold=True, color="0000FF")
    ws[ref].border = BOX
    ws[ref].alignment = Alignment(horizontal="center")
    dv = DataValidation(type="list", formula1=f'"{opts}"', allow_blank=False)
    ws.add_data_validation(dv)
    dv.add(ws[ref])
for ref in ("A4", "A5"):
    ws[ref].font = Font(name=FONT, bold=True)
ws["C4"] = "◄ dropdown (input)"
ws["C4"].font = Font(name=FONT, italic=True, size=9, color="595959")

# hidden helper criteria (wildcard for "All", year bounds)
ws["K4"], ws["K5"], ws["K6"] = "region_crit", "year_from", "year_to"
ws["L4"] = '=IF($B$4="All","*",$B$4)'
ws["L5"] = '=IF($B$5="All",2015,VALUE($B$5))'
ws["L6"] = '=IF($B$5="All",2018,VALUE($B$5))'
ws.column_dimensions["K"].hidden = True   # helper criteria, hidden from managers
ws.column_dimensions["L"].hidden = True
F = f'{REGION},$L$4,{YEAR},">="&$L$5,{YEAR},"<="&$L$6'   # common filter criteria

kpis = [
    ("Sales", f"=SUMIFS({SALES},{F})", USD),
    ("Profit", f"=SUMIFS({PROFIT},{F})", USD),
    ("Profit margin", "=IFERROR(B9/B8,0)", PCT),
    ("Order lines", f"=COUNTIFS({F})", INT),
    ("Units sold", f"=SUMIFS({QTY},{F})", INT),
    ("Average discount", f"=IFERROR(AVERAGEIFS({DISC},{F}),0)", PCT),
    ("Lines discounted > 20%", f'=COUNTIFS({F},{DISC},">0.2")', INT),
    ("Profit on lines discounted > 20%", f'=SUMIFS({PROFIT},{F},{DISC},">0.2")', USD),
    ("Share of lines returned", f'=IFERROR(COUNTIFS({F},{RET},"Yes")/B11,0)', PCT),
    ("Regional manager", '=IF($B$4="All","All regions",INDEX(Managers!$B$2:$B$5,MATCH($B$4,Managers!$A$2:$A$5,0)))', None),
]
ws["A7"] = "Key metrics"
ws["A7"].font = Font(name=FONT, bold=True, size=12, color=NAVY)
for i, (label, formula, fmt) in enumerate(kpis):
    r = 8 + i
    ws[f"A{r}"] = label
    ws[f"B{r}"] = formula
    body(ws[f"A{r}"], bold=True)
    body(ws[f"B{r}"], fmt, bold=True)
    ws[f"A{r}"].fill = KPI_FILL
    ws[f"B{r}"].fill = KPI_FILL
ws.conditional_formatting.add("B9", CellIsRule(operator="lessThan", formula=["0"], font=RED_FONT, fill=RED_FILL))
ws.conditional_formatting.add("B15", CellIsRule(operator="lessThan", formula=["0"], font=RED_FONT, fill=RED_FILL))

# Category table (responds to selectors)
ws["F7"] = "By category (filtered)"
ws["F7"].font = Font(name=FONT, bold=True, size=12, color=NAVY)
for j, h in enumerate(["Category", "Sales", "Profit", "Margin"]):
    ws.cell(row=8, column=6 + j, value=h)
style_header(ws, 8, 6, 9)
for i, catname in enumerate(sorted(orders.Category.unique())):
    r = 9 + i
    ws[f"F{r}"] = catname
    ws[f"G{r}"] = f"=SUMIFS({SALES},{F},{CAT},$F{r})"
    ws[f"H{r}"] = f"=SUMIFS({PROFIT},{F},{CAT},$F{r})"
    ws[f"I{r}"] = f"=IFERROR(H{r}/G{r},0)"
    body(ws[f"F{r}"], bold=True); body(ws[f"G{r}"], USD); body(ws[f"H{r}"], USD); body(ws[f"I{r}"], PCT)
ws["F12"] = "Total"
ws["G12"], ws["H12"], ws["I12"] = "=SUM(G9:G11)", "=SUM(H9:H11)", "=IFERROR(H12/G12,0)"
body(ws["F12"], bold=True); body(ws["G12"], USD, True); body(ws["H12"], USD, True); body(ws["I12"], PCT, True)
ws["F13"] = "Check: total = KPI sales"
ws["G13"] = '=IF(ABS(G12-B8)<0.01,"OK","MISMATCH")'
ws["F13"].font = Font(name=FONT, italic=True, size=9, color="595959")
ws["G13"].font = Font(name=FONT, italic=True, size=9, color="008000")
ws.conditional_formatting.add("H9:H12", CellIsRule(operator="lessThan", formula=["0"], font=RED_FONT, fill=RED_FILL))

# Yearly trend table (respects Region selector only)
ws["A20"] = "Trend by year (selected region)"
ws["A20"].font = Font(name=FONT, bold=True, size=12, color=NAVY)
for j, h in enumerate(["Year", "Sales", "Profit", "Margin", "Sales YoY"]):
    ws.cell(row=21, column=1 + j, value=h)
style_header(ws, 21, 1, 5)
for i, yr in enumerate([2015, 2016, 2017, 2018]):
    r = 22 + i
    ws[f"A{r}"] = str(yr)
    ws[f"B{r}"] = f"=SUMIFS({SALES},{REGION},$L$4,{YEAR},VALUE($A{r}))"
    ws[f"C{r}"] = f"=SUMIFS({PROFIT},{REGION},$L$4,{YEAR},VALUE($A{r}))"
    ws[f"D{r}"] = f"=IFERROR(C{r}/B{r},0)"
    ws[f"E{r}"] = f"=IFERROR(B{r}/B{r-1}-1,0)" if i else "n/a"
    body(ws[f"A{r}"], bold=True); body(ws[f"B{r}"], USD); body(ws[f"C{r}"], USD); body(ws[f"D{r}"], PCT); body(ws[f"E{r}"], PCT)
    ws[f"E{r}"].alignment = Alignment(horizontal="right")
    ws[f"A{r}"].alignment = Alignment(horizontal="center")

line = LineChart()
line.title = "Sales and profit by year (selected region)"
line.y_axis.title = "USD"
line.y_axis.numFmt = '$#,##0'
line.add_data(Reference(ws, min_col=2, max_col=3, min_row=21, max_row=25), titles_from_data=True)
line.set_categories(Reference(ws, min_col=1, min_row=22, max_row=25))
line.height, line.width = 7.5, 16
for srs in line.series:
    srs.smooth = False
finish_chart(line)
line.title.overlay = False
ws.add_chart(line, "A28")

# ---------------------------------------------------------------- Sub-Category sheet
ws_sc = wb.create_sheet("Sub-Category", 1)
title(ws_sc, "Profit by Sub-Category (all years, all regions)",
      "Sorted by profit. Red = loss-making. Formulas: SUMIFS / AVERAGEIFS on the Data sheet.")
hdr = ["Category", "Sub-Category", "Sales", "Profit", "Margin", "Avg discount", "Order lines"]
for j, h in enumerate(hdr):
    ws_sc.cell(row=4, column=1 + j, value=h)
style_header(ws_sc, 4, 1, len(hdr))
sc_order = orders.groupby(["Category", "Sub-Category"]).Profit.sum().sort_values().reset_index()
for i, r_ in sc_order.iterrows():
    r = 5 + i
    ws_sc[f"A{r}"], ws_sc[f"B{r}"] = r_["Category"], r_["Sub-Category"]
    ws_sc[f"C{r}"] = f"=SUMIFS({SALES},{SUBCAT},$B{r})"
    ws_sc[f"D{r}"] = f"=SUMIFS({PROFIT},{SUBCAT},$B{r})"
    ws_sc[f"E{r}"] = f"=IFERROR(D{r}/C{r},0)"
    ws_sc[f"F{r}"] = f"=AVERAGEIFS({DISC},{SUBCAT},$B{r})"
    ws_sc[f"G{r}"] = f"=COUNTIFS({SUBCAT},$B{r})"
    for c_, fmt in zip("ABCDEFG", [None, None, USD, USD, PCT, PCT, INT]):
        body(ws_sc[f"{c_}{r}"], fmt)
last_sc = 4 + len(sc_order)
tot = last_sc + 1
ws_sc[f"B{tot}"] = "Total"
ws_sc[f"C{tot}"], ws_sc[f"D{tot}"] = f"=SUM(C5:C{last_sc})", f"=SUM(D5:D{last_sc})"
ws_sc[f"E{tot}"], ws_sc[f"G{tot}"] = f"=IFERROR(D{tot}/C{tot},0)", f"=SUM(G5:G{last_sc})"
for c_, fmt in zip("BCDEG", [None, USD, USD, PCT, INT]):
    body(ws_sc[f"{c_}{tot}"], fmt, bold=True)
ws_sc.conditional_formatting.add(f"D5:D{last_sc}", CellIsRule(operator="lessThan", formula=["0"], font=RED_FONT, fill=RED_FILL))
ws_sc.conditional_formatting.add(f"C5:C{last_sc}", DataBarRule(start_type="min", end_type="max", color="5B9BD5"))
for c_, w in zip("ABCDEFG", [16, 14, 14, 14, 10, 12, 11]):
    ws_sc.column_dimensions[c_].width = w
bar = BarChart()
bar.type = "bar"
bar.title = "Profit by sub-category"
bar.add_data(Reference(ws_sc, min_col=4, min_row=4, max_row=last_sc), titles_from_data=True)
bar.set_categories(Reference(ws_sc, min_col=2, min_row=5, max_row=last_sc))
bar.y_axis.numFmt = '$#,##0'
bar.x_axis.tickLblPos = "low"
bar.legend = None
bar.height, bar.width = 10, 16
finish_chart(bar)
bar.title.overlay = False
ws_sc.add_chart(bar, "I4")

# ---------------------------------------------------------------- Discount sheet
ws_d = wb.create_sheet("Discounts", 2)
title(ws_d, "Discount bands vs profitability",
      "Band bounds (blue) are inputs: change them to test a different cut-off. Lower bound is exclusive.")
hdr = ["Band", "Lower (>)", "Upper (<=)", "Order lines", "Share of lines", "Sales", "Profit", "Margin"]
for j, h in enumerate(hdr):
    ws_d.cell(row=4, column=1 + j, value=h)
style_header(ws_d, 4, 1, len(hdr))
bands = [("0%", -0.01, 0), ("1–10%", 0, 0.1), ("11–20%", 0.1, 0.2), ("21–30%", 0.2, 0.3),
         ("31–50%", 0.3, 0.5), ("51–80%", 0.5, 0.8)]
for i, (lbl, lo, hi) in enumerate(bands):
    r = 5 + i
    ws_d[f"A{r}"], ws_d[f"B{r}"], ws_d[f"C{r}"] = lbl, lo, hi
    ws_d[f"D{r}"] = f'=COUNTIFS({DISC},">"&B{r},{DISC},"<="&C{r})'
    ws_d[f"E{r}"] = f"=D{r}/$D$11"
    ws_d[f"F{r}"] = f'=SUMIFS({SALES},{DISC},">"&B{r},{DISC},"<="&C{r})'
    ws_d[f"G{r}"] = f'=SUMIFS({PROFIT},{DISC},">"&B{r},{DISC},"<="&C{r})'
    ws_d[f"H{r}"] = f"=IFERROR(G{r}/F{r},0)"
    for c_, fmt in zip("ABCDEFGH", [None, "0%", "0%", INT, PCT, USD, USD, PCT]):
        body(ws_d[f"{c_}{r}"], fmt)
    for c_ in "BC":
        ws_d[f"{c_}{r}"].font = Font(name=FONT, color="0000FF")
ws_d["A11"] = "Total"
ws_d["D11"], ws_d["F11"], ws_d["G11"] = "=SUM(D5:D10)", "=SUM(F5:F10)", "=SUM(G5:G10)"
ws_d["E11"], ws_d["H11"] = "=SUM(E5:E10)", "=IFERROR(G11/F11,0)"
for c_, fmt in zip("ADEFGH", [None, INT, PCT, USD, USD, PCT]):
    body(ws_d[f"{c_}11"], fmt, bold=True)
ws_d["A12"] = "Check: lines = Data rows"
ws_d["D12"] = f'=IF(D11=COUNTA({rng("Order ID")}),"OK","MISMATCH")'
ws_d["A12"].font = Font(name=FONT, italic=True, size=9, color="595959")
ws_d["D12"].font = Font(name=FONT, italic=True, size=9, color="008000")
ws_d["B6"].comment = None
ws_d.conditional_formatting.add("G5:H10", CellIsRule(operator="lessThan", formula=["0"], font=RED_FONT, fill=RED_FILL))
ws_d.conditional_formatting.add("H5:H10", CellIsRule(operator="greaterThan", formula=["0"], fill=GREEN_FILL))
ws_d["A14"] = "What-if: profit if discounts above the cap had been avoided"
ws_d["A14"].font = Font(name=FONT, bold=True, color=NAVY)
ws_d["A15"], ws_d["B15"] = "Discount cap", 0.2
ws_d["B15"].fill = INPUT_FILL
ws_d["B15"].font = Font(name=FONT, bold=True, color="0000FF")
ws_d["B15"].number_format = "0%"
ws_d["A16"], ws_d["B16"] = "Profit on lines above cap", f'=SUMIFS({PROFIT},{DISC},">"&B15)'
ws_d["A17"], ws_d["B17"] = "Profit on all other lines", f'=SUMIFS({PROFIT},{DISC},"<="&B15)'
ws_d["A18"], ws_d["B18"] = "Uplift vs actual profit (if loss lines dropped)", "=IFERROR(B17/G11-1,0)"
for r, fmt in ((16, USD), (17, USD), (18, PCT)):
    body(ws_d[f"A{r}"]); body(ws_d[f"B{r}"], fmt, bold=True)
ws_d["A19"] = ("Assumption: simplest case: the over-cap lines are not sold at all. In reality some would "
               "sell at the capped discount, so the true uplift could be larger.")
ws_d["A19"].font = Font(name=FONT, italic=True, size=9, color="595959")
for c_, w in zip("ABCDEFGH", [44, 10, 10, 12, 13, 14, 14, 10]):
    ws_d.column_dimensions[c_].width = w
dbar = BarChart()
dbar.title = "Profit margin by discount band"
dbar.add_data(Reference(ws_d, min_col=8, min_row=4, max_row=10), titles_from_data=True)
dbar.set_categories(Reference(ws_d, min_col=1, min_row=5, max_row=10))
dbar.y_axis.numFmt = "0%"
dbar.x_axis.tickLblPos = "low"
dbar.legend = None
dbar.height, dbar.width = 7.5, 14
finish_chart(dbar)
dbar.title.overlay = False
ws_d.add_chart(dbar, "J4")

# ---------------------------------------------------------------- Regions sheet
ws_r = wb.create_sheet("Regions", 3)
title(ws_r, "Region scorecard", "Manager looked up from the Managers sheet with INDEX/MATCH.")
hdr = ["Region", "Manager", "Sales", "Profit", "Margin", "Avg discount", "Order lines", "Lines returned", "Return rate (lines)"]
for j, h in enumerate(hdr):
    ws_r.cell(row=4, column=1 + j, value=h)
style_header(ws_r, 4, 1, len(hdr))
for i, reg in enumerate(["Central", "East", "South", "West"]):
    r = 5 + i
    ws_r[f"A{r}"] = reg
    ws_r[f"B{r}"] = f"=INDEX(Managers!$B$2:$B$5,MATCH($A{r},Managers!$A$2:$A$5,0))"
    ws_r[f"C{r}"] = f"=SUMIFS({SALES},{REGION},$A{r})"
    ws_r[f"D{r}"] = f"=SUMIFS({PROFIT},{REGION},$A{r})"
    ws_r[f"E{r}"] = f"=IFERROR(D{r}/C{r},0)"
    ws_r[f"F{r}"] = f"=AVERAGEIFS({DISC},{REGION},$A{r})"
    ws_r[f"G{r}"] = f"=COUNTIFS({REGION},$A{r})"
    ws_r[f"H{r}"] = f'=COUNTIFS({REGION},$A{r},{RET},"Yes")'
    ws_r[f"I{r}"] = f"=IFERROR(H{r}/G{r},0)"
    for c_, fmt in zip("ABCDEFGHI", [None, None, USD, USD, PCT, PCT, INT, INT, PCT]):
        body(ws_r[f"{c_}{r}"], fmt)
ws_r.conditional_formatting.add("E5:E8", CellIsRule(operator="lessThan", formula=["0.1"], font=RED_FONT, fill=RED_FILL))
ws_r.conditional_formatting.add("I5:I8", CellIsRule(operator="greaterThan", formula=["0.08"], font=RED_FONT, fill=RED_FILL))
ws_r["A10"] = "Red flags: margin below 10% · line return rate above 8%"
ws_r["A10"].font = Font(name=FONT, italic=True, size=9, color="595959")
for c_, w in zip("ABCDEFGHI", [12, 20, 14, 14, 10, 12, 12, 13, 16]):
    ws_r.column_dimensions[c_].width = w

# ---------------------------------------------------------------- States sheet
ws_s = wb.create_sheet("States", 4)
title(ws_s, "State profitability (sorted by profit, worst first)", "Red rows lose money.")
hdr = ["State", "Region", "Sales", "Profit", "Margin", "Avg discount"]
for j, h in enumerate(hdr):
    ws_s.cell(row=4, column=1 + j, value=h)
style_header(ws_s, 4, 1, len(hdr))
st = orders.groupby(["State", "Region"]).Profit.sum().sort_values().reset_index()
for i, r_ in st.iterrows():
    r = 5 + i
    ws_s[f"A{r}"], ws_s[f"B{r}"] = r_["State"], r_["Region"]
    ws_s[f"C{r}"] = f"=SUMIFS({SALES},{STATE},$A{r})"
    ws_s[f"D{r}"] = f"=SUMIFS({PROFIT},{STATE},$A{r})"
    ws_s[f"E{r}"] = f"=IFERROR(D{r}/C{r},0)"
    ws_s[f"F{r}"] = f"=AVERAGEIFS({DISC},{STATE},$A{r})"
    for c_, fmt in zip("ABCDEF", [None, None, USD, USD, PCT, PCT]):
        body(ws_s[f"{c_}{r}"], fmt)
last_s = 4 + len(st)
ws_s.conditional_formatting.add(f"A5:F{last_s}", __import__("openpyxl").formatting.rule.FormulaRule(
    formula=[f"$D5<0"], fill=RED_FILL, font=RED_FONT))
ws_s.freeze_panes = "A5"
for c_, w in zip("ABCDEF", [20, 10, 14, 14, 10, 12]):
    ws_s.column_dimensions[c_].width = w

# ---------------------------------------------------------------- Notes sheet
ws_n = wb.create_sheet("Notes")
title(ws_n, "About this workbook")
notes = [
    ("Purpose", "Self-service view of Superstore sales and profitability for regional managers."),
    ("Source", "Tableau 'Sample - Superstore' (fictional US retailer), raw export; 9,994 order lines, Jan 2015 – Dec 2018."),
    ("Cleaning", "Raw file had 3 tables stacked together (orders, managers, returns) → split; 504 duplicate return rows removed; "
                 "11 missing postal codes (Burlington, VT) filled with 05401. Full steps: notebooks/superstore_sales_analysis.ipynb."),
    ("How to use", "Dashboard: choose Region and Year in the yellow cells. Discounts: change the blue band bounds or the yellow "
                   "discount cap to run what-ifs. All summary numbers are formulas on the Data sheet."),
    ("Colour key", "Yellow fill = input you can change · Blue text = hard-coded input · Black = formula · Red = loss / red flag."),
    ("Checks", "Dashboard!G13 and Discounts!D12 confirm totals reconcile to the Data sheet."),
    ("Return rate", "Regions sheet return rate = share of order LINES belonging to a returned order."),
    ("Author", "Daljeet Kaur"),
]
for i, (k, v) in enumerate(notes):
    ws_n[f"A{4 + i}"], ws_n[f"B{4 + i}"] = k, v
    ws_n[f"A{4 + i}"].font = Font(name=FONT, bold=True)
    ws_n[f"B{4 + i}"].font = Font(name=FONT)
    ws_n[f"B{4 + i}"].alignment = Alignment(wrap_text=True, vertical="top")
    ws_n[f"A{4 + i}"].alignment = Alignment(vertical="top")
ws_n.column_dimensions["A"].width = 14
ws_n.column_dimensions["B"].width = 110

# global font for the remaining defaults
for sheet in wb.worksheets:
    for row in sheet.iter_rows():
        for c in row:
            if c.value is not None and c.font.name != FONT:
                c.font = Font(name=FONT, bold=c.font.bold, italic=c.font.italic, color=c.font.color, size=c.font.size)

wb.calculation.fullCalcOnLoad = True
OUT.parent.mkdir(exist_ok=True)
wb.save(OUT)
print(f"Saved {OUT}")
