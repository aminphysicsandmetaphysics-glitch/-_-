from io import BytesIO

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


MONTH_NAMES_FA = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
]

MONTH_NAMES_EN = [
    "Farvardin", "Ordibehesht", "Khordad", "Tir", "Mordad", "Shahrivar",
    "Mehr", "Aban", "Azar", "Dey", "Bahman", "Esfand",
]


def _table_style(header_color: str = "#0f766e") -> TableStyle:
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header_color)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
    ])


def build_excel_report(building, bills: list[dict], weather_rows: list[dict], result: dict) -> BytesIO:
    output = BytesIO()
    monthly = pd.DataFrame(result.get("monthly", []))
    if not monthly.empty:
        monthly.insert(1, "month_name_fa", monthly["month"].apply(lambda month: MONTH_NAMES_FA[month - 1]))
        monthly.insert(2, "month_name_en", monthly["month"].apply(lambda month: MONTH_NAMES_EN[month - 1]))
        monthly["total_mj_formula_note"] = "electricity_kwh*3.6 + gas_m3*38"
    summary = pd.DataFrame([{
        "project_name": building.project_name,
        "city": building.city,
        "area_m2": building.area_m2,
        "occupants": building.occupants,
        "climate_zone": result.get("climate_zone"),
        "ideal_e2_mj_m2_year": result.get("ideal_e2"),
        "actual_eui_mj_m2_year": result.get("eui"),
        "energy_index_ratio_actual_to_e2": result.get("energy_index_ratio"),
        "energy_label": result.get("energy_rating"),
        "total_energy_mj": result.get("total_energy_mj"),
        "energy_per_person_mj_person_year": result.get("energy_per_person"),
        "hdd": result.get("hdd"),
        "cdd": result.get("cdd"),
        "high_consumption_flag": result.get("high_consumption_flag"),
    }])
    weather = pd.DataFrame(weather_rows)
    weather_monthly = pd.DataFrame(result.get("weather_monthly", []))
    raw_bills = pd.DataFrame(bills)
    electric_equipment = pd.DataFrame(result.get("electric_equipment", []))
    gas_equipment = pd.DataFrame(result.get("gas_equipment", []))
    label_ranges = pd.DataFrame(result.get("energy_label_ranges", []))
    anomalies = pd.DataFrame(result.get("anomalies", []))
    recommendations = pd.DataFrame(result.get("recommendations", []))

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book
        header_format = workbook.add_format({"bold": True, "bg_color": "#0F766E", "font_color": "white", "border": 1})
        number_format = workbook.add_format({"num_format": "#,##0.00"})
        sheets = {
            "Audit Summary": summary,
            "Monthly Energy": monthly,
            "Raw Bills": raw_bills,
            "Weather Daily": weather,
            "Weather Monthly": weather_monthly,
            "Energy Label Ranges": label_ranges,
            "Anomalies": anomalies,
            "Electric Equipment": electric_equipment,
            "Gas Equipment": gas_equipment,
            "Recommendations": recommendations,
        }
        for sheet_name, frame in sheets.items():
            frame.to_excel(writer, sheet_name=sheet_name, index=False)
            worksheet = writer.sheets[sheet_name]
            worksheet.freeze_panes(1, 0)
            worksheet.autofilter(0, 0, max(len(frame), 1), max(len(frame.columns) - 1, 0))
            for column_index, column in enumerate(frame.columns):
                worksheet.write(0, column_index, column, header_format)
                worksheet.set_column(column_index, column_index, min(max(len(str(column)) + 4, 14), 34), number_format)
            if sheet_name == "Monthly Energy" and not frame.empty:
                formula_col = len(frame.columns)
                worksheet.write(0, formula_col, "excel_formula_total_mj", header_format)
                electricity_col = frame.columns.get_loc("electricity_kwh")
                gas_col = frame.columns.get_loc("gas_m3")
                for row_index in range(1, len(frame) + 1):
                    electricity_cell = chr(65 + electricity_col) + str(row_index + 1)
                    gas_cell = chr(65 + gas_col) + str(row_index + 1)
                    worksheet.write_formula(row_index, formula_col, f"={electricity_cell}*3.6+{gas_cell}*38")

        chart_sheet = workbook.add_worksheet("Charts Guide")
        chart_sheet.write("A1", "Professional chart-ready data is available in Monthly Energy, Weather Monthly, Electric Equipment, and Gas Equipment.")
        chart_sheet.write("A3", "Suggested charts:")
        chart_sheet.write("A4", "1. Monthly electricity kWh and gas m³ clustered columns")
        chart_sheet.write("A5", "2. Monthly total MJ line chart")
        chart_sheet.write("A6", "3. EUI vs E2 benchmark bar chart")
        chart_sheet.write("A7", "4. Weather monthly temperature, humidity, rainfall, solar radiation")
    output.seek(0)
    return output


def build_pdf_report(building, result: dict, recommendations: list[dict]) -> BytesIO:
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=32, leftMargin=32, topMargin=32, bottomMargin=32)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Small", parent=styles["Normal"], fontSize=8, leading=10))
    styles.add(ParagraphStyle(name="CoverTitle", parent=styles["Title"], fontSize=22, textColor=colors.HexColor("#0f766e")))
    story = []

    def title(text: str):
        story.append(Paragraph(text, styles["CoverTitle"]))
        story.append(Spacer(1, 12))

    def heading(text: str):
        story.append(Paragraph(text, styles["Heading2"]))
        story.append(Spacer(1, 8))

    def add_table(rows: list[list], color: str = "#0f766e", widths: list[int] | None = None):
        table = Table(rows, repeatRows=1, colWidths=widths)
        table.setStyle(_table_style(color))
        story.append(table)
        story.append(Spacer(1, 12))

    title("Residential Energy Audit Report | گزارش ممیزی انرژی ساختمان")
    story.append(Paragraph("Prepared for Iranian residential buildings aligned with مبحث ۱۹ and common energy audit practice.", styles["Normal"]))
    cover_rows = [
        ["Field", "Value"],
        ["Project | پروژه", building.project_name],
        ["City | شهر", building.city],
        ["Address | آدرس", building.address or "-"],
        ["Area | مساحت", f"{building.area_m2} m²"],
        ["Occupants | نفرات", str(building.occupants)],
        ["Climate zone | اقلیم", result.get("climate_zone") or "-"],
        ["Heating / Cooling | گرمایش / سرمایش", f"{building.heating_system or '-'} / {building.cooling_system or '-'}"],
    ]
    add_table(cover_rows)
    story.append(PageBreak())

    heading("Executive Summary | خلاصه مدیریتی")
    ratio = result.get("energy_index_ratio") or 0
    flag_text = "High Energy Consumption | مصرف بالاتر از معیار" if result.get("high_consumption_flag") else "Within configured benchmark | در محدوده معیار"
    summary_rows = [
        ["Metric | شاخص", "Value | مقدار"],
        ["Annual total energy | انرژی سالانه", f"{result.get('total_energy_mj', 0):,.1f} MJ/year"],
        ["Actual EUI | مصرف ویژه واقعی", f"{result.get('eui', 0):,.1f} MJ/m².year"],
        ["Ideal E2 | مصرف ایده‌آل", f"{result.get('ideal_e2', 0):,.1f} MJ/m².year"],
        ["Actual/E2 index | نسبت مصرف واقعی به ایده‌آل", f"{ratio:.2f}"],
        ["Energy label | رده انرژی", result.get("energy_rating", "-")],
        ["Energy per person | انرژی بر نفر", f"{result.get('energy_per_person', 0):,.1f} MJ/person.year"],
        ["HDD / CDD", f"{result.get('hdd', 0):,.1f} / {result.get('cdd', 0):,.1f}"],
        ["Status | وضعیت", flag_text],
    ]
    add_table(summary_rows, "#1d4ed8")
    story.append(PageBreak())

    heading("Energy Bills Analysis | تحلیل قبض برق و گاز")
    monthly_table = [["Month", "Electricity kWh", "Gas m³", "Total MJ", "MJ/m²", "MJ/person"]]
    for item in result.get("monthly", []):
        monthly_table.append([
            MONTH_NAMES_FA[item["month"] - 1],
            f"{item['electricity_kwh']:.1f}",
            f"{item['gas_m3']:.1f}",
            f"{item['total_mj']:.1f}",
            f"{item['energy_per_m2']:.1f}",
            f"{item['energy_per_person']:.1f}",
        ])
    add_table(monthly_table)

    anomalies = result.get("anomalies", [])
    if anomalies:
        heading("Consumption Pattern Alerts | هشدارهای الگوی مصرف")
        add_table([["Month", "Type", "Message"]] + [[MONTH_NAMES_FA[item["month"] - 1], item["type"], item["message"]] for item in anomalies], "#dc2626")
    story.append(PageBreak())

    heading("Energy Label | برچسب انرژی")
    label_rows = [["Rating", "Ratio range", "Description"]]
    for item in result.get("energy_label_ranges", []):
        label_rows.append([item["rating"], f"{item['min_ratio']} - {item['max_ratio']}", item["label"]])
    add_table(label_rows, "#ca8a04")

    heading("Weather and Degree-Day Analysis | تحلیل هواشناسی")
    weather_rows = [["Month", "Avg Temp °C", "Humidity %", "Solar", "Rainfall"]]
    for item in result.get("weather_monthly", []):
        weather_rows.append([
            MONTH_NAMES_FA[item["month"] - 1],
            f"{item['temp_avg']:.1f}",
            f"{item['humidity']:.1f}",
            f"{item['solar_radiation']:.1f}",
            f"{item['rainfall']:.1f}",
        ])
    add_table(weather_rows, "#0891b2")
    story.append(PageBreak())

    heading("Equipment Analysis | تحلیل تجهیزات")
    electric_rows = [["Electric device", "Qty", "Power W", "h/day", "kWh/year"]]
    for item in result.get("electric_equipment", []):
        electric_rows.append([item["name"], f"{item['quantity']:.1f}", f"{item['power_w']:.1f}", f"{item['hours_per_day']:.1f}", f"{item.get('annual_kwh', 0):.1f}"])
    add_table(electric_rows, "#7c3aed")
    gas_rows = [["Gas device", "Qty", "m³/h", "h/day", "m³/year"]]
    for item in result.get("gas_equipment", []):
        gas_rows.append([item["name"], f"{item['quantity']:.1f}", f"{item['gas_m3_per_hour']:.2f}", f"{item['hours_per_day']:.1f}", f"{item.get('annual_m3', 0):.1f}"])
    add_table(gas_rows, "#ea580c")
    story.append(PageBreak())

    heading("Optimization Recommendations | پیشنهادهای بهینه‌سازی")
    recommendation_rows = [["Category", "Recommendation", "Impact"]]
    for rec in recommendations:
        recommendation_rows.append([rec["category"], rec["recommendation"], rec["impact_level"]])
    add_table(recommendation_rows, "#166534", [70, 360, 60])

    doc.build(story)
    output.seek(0)
    return output
