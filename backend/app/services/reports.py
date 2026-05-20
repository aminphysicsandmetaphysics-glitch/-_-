from io import BytesIO

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


MONTH_NAMES_FA = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
]


def build_excel_report(building, bills: list[dict], weather_rows: list[dict], result: dict) -> BytesIO:
    output = BytesIO()
    monthly = pd.DataFrame(result["monthly"])
    if not monthly.empty:
        monthly.insert(1, "month_name_fa", monthly["month"].apply(lambda month: MONTH_NAMES_FA[month - 1]))
    summary = pd.DataFrame([{
        "project_name": building.project_name,
        "city": building.city,
        "area_m2": building.area_m2,
        "occupants": building.occupants,
        "total_energy_mj": result["total_energy_mj"],
        "eui_mj_m2_year": result["eui"],
        "energy_per_person_mj_person_year": result["energy_per_person"],
        "hdd": result["hdd"],
        "cdd": result["cdd"],
        "energy_rating": result["energy_rating"],
        "standard_eui": result["standard_eui"],
        "high_consumption_flag": result["high_consumption_flag"],
    }])
    weather = pd.DataFrame(weather_rows)
    raw_bills = pd.DataFrame(bills)
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        summary.to_excel(writer, sheet_name="Audit Summary", index=False)
        monthly.to_excel(writer, sheet_name="Monthly Energy", index=False)
        raw_bills.to_excel(writer, sheet_name="Raw Bills", index=False)
        weather.to_excel(writer, sheet_name="Weather HDD CDD", index=False)
    output.seek(0)
    return output


def build_pdf_report(building, result: dict, recommendations: list[dict]) -> BytesIO:
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    def title(text: str):
        story.append(Paragraph(text, styles["Title"]))
        story.append(Spacer(1, 12))

    def heading(text: str):
        story.append(Paragraph(text, styles["Heading2"]))
        story.append(Spacer(1, 8))

    title("Residential Energy Audit Report - Iran")
    story.append(Paragraph(f"Project: {building.project_name}", styles["Normal"]))
    story.append(Paragraph(f"City: {building.city} | Address: {building.address or '-'}", styles["Normal"]))
    story.append(Paragraph(f"Area: {building.area_m2} m² | Occupants: {building.occupants}", styles["Normal"]))
    story.append(Paragraph(f"Systems: Heating={building.heating_system or '-'}, Cooling={building.cooling_system or '-'}", styles["Normal"]))
    story.append(PageBreak())

    heading("Energy Bills Analysis")
    monthly_table = [["Month", "Electricity kWh", "Gas m³", "Total MJ", "MJ/m²", "MJ/person"]]
    for item in result["monthly"]:
        monthly_table.append([
            MONTH_NAMES_FA[item["month"] - 1],
            f"{item['electricity_kwh']:.1f}",
            f"{item['gas_m3']:.1f}",
            f"{item['total_mj']:.1f}",
            f"{item['energy_per_m2']:.1f}",
            f"{item['energy_per_person']:.1f}",
        ])
    table = Table(monthly_table, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))
    story.append(table)
    story.append(PageBreak())

    heading("Energy Indices and Climate")
    index_rows = [
        ["Annual Total Energy", f"{result['total_energy_mj']:.1f} MJ/year"],
        ["EUI", f"{result['eui']:.1f} MJ/m².year"],
        ["Energy per Person", f"{result['energy_per_person']:.1f} MJ/person.year"],
        ["HDD / CDD", f"{result['hdd']:.1f} / {result['cdd']:.1f}"],
        ["Rating", result["energy_rating"]],
        ["مبحث ۱۹ Benchmark", f"{result['standard_eui']:.1f} MJ/m².year"],
    ]
    story.append(Table(index_rows, style=[("GRID", (0, 0), (-1, -1), 0.25, colors.grey)]))
    story.append(PageBreak())

    heading("Energy Rating and Recommendations")
    flag_text = "High Energy Consumption" if result["high_consumption_flag"] else "Within configured benchmark"
    story.append(Paragraph(f"Consumption status: {flag_text}", styles["Normal"]))
    story.append(Spacer(1, 12))
    recommendation_rows = [["Category", "Recommendation", "Impact"]]
    for rec in recommendations:
        recommendation_rows.append([rec["category"], rec["recommendation"], rec["impact_level"]])
    story.append(Table(recommendation_rows, repeatRows=1, style=[
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
    ]))

    doc.build(story)
    output.seek(0)
    return output
