import os
import docx
from docx.shared import Pt, Inches, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

base_dir = r"c:\Users\mohan\OneDrive\Desktop\Work\Transit Optimizer Bus"
out_dir = os.path.join(base_dir, "individual contribution reports")
os.makedirs(out_dir, exist_ok=True)
out_docx_path = os.path.join(out_dir, "Individual_Contribution_Sheet_D-BIT-24-0039_With_Evidence.docx")

doc = docx.Document()

# Margins: 0.38 in top/bottom, 0.50 in left/right for pristine layout
sec = doc.sections[0]
sec.top_margin = Inches(0.38)
sec.bottom_margin = Inches(0.38)
sec.left_margin = Inches(0.50)
sec.right_margin = Inches(0.50)
sec.page_width = Inches(8.5)
sec.page_height = Inches(11.0)

doc.styles['Normal'].font.name = 'Times New Roman'
doc.styles['Normal'].font.size = Pt(9.5)

def set_cell_margins(cell, top=45, bottom=45, left=65, right=65):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for name, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{name}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_cell_borders(cell, color="94A3B8", sz="4"):
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(r'''
        <w:tcBorders {} >
            <w:top w:val="single" w:sz="{}" w:space="0" w:color="{}"/>
            <w:left w:val="single" w:sz="{}" w:space="0" w:color="{}"/>
            <w:bottom w:val="single" w:sz="{}" w:space="0" w:color="{}"/>
            <w:right w:val="single" w:sz="{}" w:space="0" w:color="{}"/>
        </w:tcBorders>
    '''.format(nsdecls('w'), sz, color, sz, color, sz, color, sz, color))
    tcPr.append(borders)

# ==========================================
# PAGE 1: HEADER & STUDENT INFO
# ==========================================
p0 = doc.add_paragraph()
p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
p0.paragraph_format.space_before = Pt(0)
p0.paragraph_format.space_after = Pt(1)
r0 = p0.add_run("ESSENTIALS OF ARTIFICIAL INTELLIGENCE")
r0.font.name = "Times New Roman"
r0.font.size = Pt(11.5)
r0.bold = True

p1 = doc.add_paragraph()
p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
p1.paragraph_format.space_before = Pt(0)
p1.paragraph_format.space_after = Pt(5)
r1 = p1.add_run("INDIVIDUAL CONTRIBUTION SHEET")
r1.font.name = "Times New Roman"
r1.font.size = Pt(11.5)
r1.bold = True

# Student Info Table
t0 = doc.add_table(rows=3, cols=4)
t0.alignment = WD_TABLE_ALIGNMENT.CENTER
t0_data = [
    [("Student Name", True), ("SNMRDS Arambepola", False), ("Registration No.", True), ("D/BIT/24/0039", False)],
    [("Degree / Intake", True), ("BIT / 41", False), ("Group No.", True), ("40", False)],
    [("Project Title", True), ("AI-Powered Dynamic Public Transport Fleet Optimizer (Route 100)", False), ("", False), ("", False)]
]

col_w_t0 = [Inches(1.4), Inches(2.4), Inches(1.5), Inches(2.2)]
for r_idx, row in enumerate(t0.rows):
    for c_idx, cell in enumerate(row.cells):
        cell.width = col_w_t0[c_idx]
        set_cell_margins(cell, top=35, bottom=35, left=55, right=55)
        set_cell_borders(cell, color="94A3B8")
        text, bold = t0_data[r_idx][c_idx]
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(text)
        run.font.name = "Times New Roman"
        run.font.size = Pt(9)
        run.bold = bold

t0.rows[2].cells[1].merge(t0.rows[2].cells[3])

p_tech = doc.add_paragraph()
p_tech.paragraph_format.space_before = Pt(5)
p_tech.paragraph_format.space_after = Pt(2)
r_tech = p_tech.add_run("Technical Contributions: ")
r_tech.font.name = "Times New Roman"
r_tech.font.size = Pt(10)
r_tech.bold = True

# ==========================================
# TABLE 1: TECHNICAL CONTRIBUTIONS
# ==========================================
t1 = doc.add_table(rows=6, cols=4)
t1.alignment = WD_TABLE_ALIGNMENT.CENTER

headers = ["Task / Component", "My Contribution", "Tools / AI Technique Used", "Evidence / Output"]
col_w_t1 = [Inches(1.35), Inches(3.05), Inches(1.45), Inches(1.65)]

for c_idx, cell in enumerate(t1.rows[0].cells):
    cell.width = col_w_t1[c_idx]
    set_cell_margins(cell, top=45, bottom=45, left=65, right=65)
    set_cell_borders(cell, color="334155", sz="6")
    shd = parse_xml(r'<w:shd {} w:fill="F1F5F9"/>'.format(nsdecls('w')))
    cell._tc.get_or_add_tcPr().append(shd)
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(1)
    run = p.add_run(headers[c_idx])
    run.font.name = "Times New Roman"
    run.font.size = Pt(9)
    run.bold = True

contributions = [
    (
        "Dynamic Dispatch Headway Logic",
        "Developed the fleet dispatch algorithm in calculate_dispatch(): determined bottleneck demand (peak = max(predictions)), calculated fleet requirements based on 80-pax capacity (buses = max(1, ceil(peak / 80))), and clamped headway between 3 and 30 minutes (headway = clamp(round(60 / buses), 3, 30)) to mitigate bus bunching.",
        "Python, Rule-Based Optimization, Fleet Sizing",
        "backend/dispatch.py (calculate_dispatch); Slide Deck Slide 8"
    ),
    (
        "Congestion-Aware Corridor ETA Model",
        "Modeled realistic end-to-end corridor travel times along the 8 Galle Road segments ([14, 12, 10, 12, 8, 8, 10] min). Applied a 1.25x peak congestion factor during rush hours and dynamic dwell delay (0.05 min × predicted passengers per stop) so predicted crowding extends route travel times.",
        "Python, Transit Travel-Time Calibration",
        "backend/dispatch.py (corridor ETA logic); JSON response corridor_eta_minutes"
    ),
    (
        "FastAPI Backend Service & Routing",
        "Architected and built the high-performance asynchronous REST API using FastAPI and Uvicorn. Implemented Pydantic v2 validation schemas and exposed GET /, POST /predict, POST /predict/batch, and POST /dispatch endpoints with automated OpenAPI interactive documentation.",
        "FastAPI, Pydantic, Uvicorn, OpenAPI / Swagger",
        "backend/main.py (API routing & schemas); Swagger UI at 127.0.0.1:8000/docs"
    ),
    (
        "Automated Calendar Enrichment Engine",
        "Engineered enrich_calendar() to infer day-of-week, Sri Lanka public and Poya holidays (holidays LK library), school rush hours (06–07 & 13–14), and payday cycles directly from the requested timestamp, supporting manual scenario overrides (holiday_mode, school_rush_mode, event_override).",
        "pandas, holidays (LK), Temporal Enrichment",
        "backend/main.py (enrich_calendar); calendar_context JSON payload"
    ),
    (
        "End-to-End System Verification Testing",
        "Authored automated verification test suites verifying root health, single and batch predictions, and dynamic dispatch behavior across 4 stress scenarios (AM rush, off-peak night clamping, Poya holiday demand reduction, and special-event surges).",
        "FastAPI TestClient, Automated Test Suites",
        "backend/test_verification.py (7/7 test suites passing with verified outputs)"
    )
]

for r_idx, (col0, col1, col2, col3) in enumerate(contributions, start=1):
    row = t1.rows[r_idx]
    row_vals = [col0, col1, col2, col3]
    for c_idx, cell in enumerate(row.cells):
        cell.width = col_w_t1[c_idx]
        set_cell_margins(cell, top=40, bottom=40, left=60, right=60)
        set_cell_borders(cell, color="CBD5E1", sz="4")
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(1)
        p.paragraph_format.line_spacing = 1.08
        run = p.add_run(row_vals[c_idx])
        run.font.name = "Times New Roman"
        run.font.size = Pt(8.5)
        if c_idx == 0:
            run.bold = True

# Declaration
p_dec = doc.add_paragraph()
p_dec.paragraph_format.space_before = Pt(5)
p_dec.paragraph_format.space_after = Pt(1)
r_dec = p_dec.add_run("Declaration")
r_dec.font.name = "Times New Roman"
r_dec.font.size = Pt(9.5)
r_dec.bold = True

p_dec_text = doc.add_paragraph()
p_dec_text.paragraph_format.space_before = Pt(0)
p_dec_text.paragraph_format.space_after = Pt(4)
r_dec_text = p_dec_text.add_run("I confirm that the contributions listed above accurately represent my individual work in this group project, and I can explain or demonstrate the stated work if required.")
r_dec_text.font.name = "Times New Roman"
r_dec_text.font.size = Pt(8.5)

# --- SPACIOUS SIGNATURE TABLE ---
t2 = doc.add_table(rows=1, cols=2)
t2.alignment = WD_TABLE_ALIGNMENT.CENTER
t2.rows[0].cells[0].width = Inches(5.2)
t2.rows[0].cells[1].width = Inches(2.3)

for cell in t2.rows[0].cells:
    set_cell_margins(cell, top=65, bottom=65, left=85, right=85)
    set_cell_borders(cell, color="94A3B8")

# Signature Cell
cell_sig = t2.rows[0].cells[0]
p_sig1 = cell_sig.paragraphs[0]
p_sig1.paragraph_format.space_before = Pt(0)
p_sig1.paragraph_format.space_after = Pt(0)
r_slabel = p_sig1.add_run("Student Signature:")
r_slabel.font.name = "Times New Roman"
r_slabel.font.size = Pt(9)
r_slabel.bold = True

p_space = cell_sig.add_paragraph()
p_space.paragraph_format.space_before = Pt(30)  # Extra generous vertical space to sign!
p_space.paragraph_format.space_after = Pt(0)
r_line = p_space.add_run("_________________________________________")
r_line.font.name = "Times New Roman"
r_line.font.size = Pt(9.5)

# Date Cell
cell_date = t2.rows[0].cells[1]
p_d1 = cell_date.paragraphs[0]
p_d1.paragraph_format.space_before = Pt(0)
p_d1.paragraph_format.space_after = Pt(0)
r_dlabel = p_d1.add_run("Date:")
r_dlabel.font.name = "Times New Roman"
r_dlabel.font.size = Pt(9)
r_dlabel.bold = True

p_d2 = cell_date.add_paragraph()
p_d2.paragraph_format.space_before = Pt(30)
p_d2.paragraph_format.space_after = Pt(0)
r_dval = p_d2.add_run("18 / 10 / 2026")
r_dval.font.name = "Times New Roman"
r_dval.font.size = Pt(9.5)

p_note = doc.add_paragraph()
p_note.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_note.paragraph_format.space_before = Pt(3)
p_note.paragraph_format.space_after = Pt(0)
r_note = p_note.add_run("Evidence may include source code, model/notebook, diagram, dataset work, test results, screenshots, report section or presentation slides.")
r_note.font.name = "Times New Roman"
r_note.font.size = Pt(8)
r_note.font.italic = True
r_note.font.color.rgb = RGBColor(100, 116, 139)

# ==========================================
# PAGE 2: APPENDIX - EVIDENCE & ARTIFACTS
# ==========================================
doc.add_page_break()

p_app_head = doc.add_paragraph()
p_app_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_app_head.paragraph_format.space_before = Pt(2)
p_app_head.paragraph_format.space_after = Pt(1)
r_app_head = p_app_head.add_run("APPENDIX: TECHNICAL EVIDENCE & SYSTEM ARTIFACTS")
r_app_head.font.name = "Times New Roman"
r_app_head.font.size = Pt(11)
r_app_head.bold = True

p_app_sub = doc.add_paragraph()
p_app_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_app_sub.paragraph_format.space_before = Pt(0)
p_app_sub.paragraph_format.space_after = Pt(4)
r_app_sub = p_app_sub.add_run("Student: SNMRDS Arambepola (D/BIT/24/0039) · Group 40 · Route 100 Transit Fleet Optimizer")
r_app_sub.font.name = "Times New Roman"
r_app_sub.font.size = Pt(8.5)
r_app_sub.font.italic = True
r_app_sub.font.color.rgb = RGBColor(75, 85, 99)

def add_evidence_header(title):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(5)
    p.paragraph_format.space_after = Pt(1.5)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(title)
    r.font.name = "Times New Roman"
    r.font.size = Pt(9)
    r.bold = True
    r.font.color.rgb = RGBColor(30, 58, 138)

def add_code_box(code_text, font_size=7.2):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.rows[0].cells[0]
    cell.width = Inches(7.5)
    
    shd = parse_xml(r'<w:shd {} w:fill="F8FAFC"/>'.format(nsdecls('w')))
    cell._tc.get_or_add_tcPr().append(shd)
    
    borders = parse_xml(r'''
        <w:tcBorders {} >
            <w:top w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>
            <w:left w:val="single" w:sz="16" w:space="0" w:color="2563EB"/>
            <w:bottom w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>
            <w:right w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>
        </w:tcBorders>
    '''.format(nsdecls('w')))
    cell._tc.get_or_add_tcPr().append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.02
    run = p.add_run(code_text)
    run.font.name = "Consolas"
    run.font.size = Pt(font_size)
    run.font.color.rgb = RGBColor(15, 23, 42)

# --- Evidence 1: Dynamic Headway Algorithm ---
add_evidence_header("Evidence 1: Dynamic Headway & Fleet Sizing Algorithm Implementation (backend/dispatch.py)")

img_path1 = os.path.join(base_dir, "evidence_dispatch_flow.png")
if os.path.exists(img_path1):
    p_img1 = doc.add_paragraph()
    p_img1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img1.paragraph_format.space_before = Pt(1)
    p_img1.paragraph_format.space_after = Pt(2)
    doc.add_picture(img_path1, width=Inches(6.6))

dispatch_code = '''def calculate_dispatch(predictions: list[float], stop_names: list[str] | None = None, *, hour: int | None = None, is_weekend: int = 0, is_public_holiday: int = 0) -> dict:
    peak_idx = max(range(len(predictions)), key=lambda i: predictions[i])
    peak_load = float(predictions[peak_idx])
    peak_stop = stop_names[peak_idx] if stop_names and peak_idx < len(stop_names) else None
    if peak_load <= 0:
        buses_needed = 1; headway = MAX_HEADWAY  # 30 min
    else:
        buses_needed = max(1, math.ceil(peak_load / CAPACITY_PER_BUS))  # 80 pax/bus
        raw_headway = round(60 / buses_needed)
        headway = max(MIN_HEADWAY, min(MAX_HEADWAY, raw_headway))  # Clamped strictly 3 to 30 min
    return {"peak_load": round(peak_load, 2), "peak_stop": peak_stop, "buses_needed": buses_needed, "headway_minutes": headway, ...}'''
add_code_box(dispatch_code, font_size=7.0)

# --- Evidence 2: Congestion-Aware Corridor ETA ---
add_evidence_header("Evidence 2: Congestion-Aware Corridor ETA & Dwell Delay Model (backend/dispatch.py)")
eta_code = '''BASE_TRAVEL_MINUTES = [14, 12, 10, 12, 8, 8, 10]  # Panadura → Moratuwa → Mt_Lavinia → Dehiwala → Wellawatta → Bambalapitiya → Kollupitiya → Pettah
DWELL_MIN_PER_PAX = 0.05; PEAK_CONGESTION = 1.25  # Rush hour congestion factor
is_peak_hour = hour in {7, 8, 9, 16, 17, 18, 19}
congestion_factor = PEAK_CONGESTION if (is_peak_hour and not soft_day) else 1.0
dwell_delay = sum(min(p, 500) * DWELL_MIN_PER_PAX for p in predictions)
corridor_eta = round(sum(BASE_TRAVEL_MINUTES) * congestion_factor + dwell_delay, 1)'''
add_code_box(eta_code, font_size=7.0)

tbl_eta = doc.add_table(rows=4, cols=4)
tbl_eta.alignment = WD_TABLE_ALIGNMENT.CENTER
eta_rows = [
    ["Corridor Commute Scenario", "Base Travel", "Peak Congestion Factor", "Total Corridor ETA (with dwell)"],
    ["Off-Peak Midday / Night", "74.0 min", "1.00x (Free-flow)", "74.0 – 76.5 minutes"],
    ["Weekday Morning Peak (08:00)", "74.0 min", "1.25x (Peak Rush)", "112.5 minutes (8 buses, tight 8 min headway)"],
    ["Special Event Surge Spike", "74.0 min", "1.25x (Congested)", "148.2 minutes (14 buses, 4 min headway)"]
]
col_w_eta = [Inches(2.5), Inches(1.3), Inches(1.8), Inches(1.9)]
for r_idx, row_vals in enumerate(eta_rows):
    r = tbl_eta.rows[r_idx]
    for c_idx, val in enumerate(row_vals):
        cell = r.cells[c_idx]
        cell.width = col_w_eta[c_idx]
        if r_idx == 0:
            shd = parse_xml(r'<w:shd {} w:fill="F1F5F9"/>'.format(nsdecls('w')))
            cell._tc.get_or_add_tcPr().append(shd)
            borders = parse_xml(r'''
                <w:tcBorders {} >
                    <w:top w:val="single" w:sz="6" w:space="0" w:color="94A3B8"/>
                    <w:left w:val="none"/><w:bottom w:val="single" w:sz="8" w:space="0" w:color="334155"/><w:right w:val="none"/>
                </w:tcBorders>
            '''.format(nsdecls('w')))
        else:
            borders = parse_xml(r'''
                <w:tcBorders {} >
                    <w:top w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>
                    <w:left w:val="none"/><w:bottom w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/><w:right w:val="none"/>
                </w:tcBorders>
            '''.format(nsdecls('w')))
        cell._tc.get_or_add_tcPr().append(borders)
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(1)
        run = p.add_run(val)
        run.font.name = "Times New Roman"
        run.font.size = Pt(8)
        if r_idx == 0:
            run.bold = True

# --- Evidence 3: FastAPI Backend Service ---
add_evidence_header("Evidence 3: FastAPI Backend REST Service & Swagger UI Documentation (backend/main.py)")

img_path2 = os.path.join(base_dir, "evidence_swagger_docs.png")
if os.path.exists(img_path2):
    p_img2 = doc.add_paragraph()
    p_img2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img2.paragraph_format.space_before = Pt(1)
    p_img2.paragraph_format.space_after = Pt(2)
    doc.add_picture(img_path2, width=Inches(6.6))

api_code = '''@app.post("/dispatch", response_model=DispatchResponse)
def dispatch(req: DispatchRequest):
    cal = enrich_calendar(req.date, req.hour, holiday_mode=req.holiday_mode, ...)
    predictions = process_and_predict(batch_df)
    recommendation = calculate_dispatch(predictions, STOPS, hour=req.hour, is_weekend=cal["is_weekend"], is_public_holiday=cal["is_public_holiday"])
    return DispatchResponse(predictions=[{"stop_name": s, "predicted_pax": p} for s, p in zip(STOPS, predictions)],
                            dispatch_recommendation=recommendation, calendar_context=cal)'''
add_code_box(api_code, font_size=7.0)

# --- Evidence 4: Calendar Enrichment & Output Payload ---
add_evidence_header("Evidence 4: Real-Time Sri Lanka Calendar Enrichment Engine & Output Payload (backend/main.py)")
cal_code = '''def enrich_calendar(date_str: str, hour: int, ...) -> dict:
    dt = pd.to_datetime(date_str)
    lk_holidays = holidays.country_holidays("LK", years=[dt.year])
    is_pub_holiday = 1 if (dt in lk_holidays or holiday_mode in {"poya", "public"}) else 0
    is_school_rush = 1 if (hour in {7, 13, 14} and dt.dayofweek < 5 and not is_pub_holiday) else 0
    return {"day_name": dt.strftime("%A"), "is_weekend": int(dt.dayofweek >= 5), "is_public_holiday": is_pub_holiday,
            "is_school_rush": is_school_rush, "peak_period": "am_peak" if hour in {7,8,9} else ("pm_peak" if hour in {16,17,18,19} else "off_peak")}'''
add_code_box(cal_code, font_size=7.0)

json_payload = '''{
  "dispatch_recommendation": { "peak_load": 619.58, "peak_stop": "Kollupitiya", "buses_needed": 8, "headway_minutes": 8, "corridor_eta_minutes": 112.5, "congestion_factor": 1.25 },
  "calendar_context": { "day_name": "Wednesday", "is_weekend": 0, "is_public_holiday": 0, "is_school_rush": 1, "peak_period": "am_peak" }
}'''
add_code_box(json_payload, font_size=7.0)

# --- Evidence 5: Automated Verification ---
add_evidence_header("Evidence 5: End-to-End System Integration & 7-Scenario Test Run (backend/test_verification.py)")
test_log = '''=== 1. Health / Root Endpoint ===
Service: Route 100 Transit Optimizer | Framework: PyTorch MLP | Input dim: 23 | Stops: 8 stops
=== 2. Single Predict Endpoint ===
Predicted single stop (Kollupitiya 08:00): 619.6 pax (Verified: pax > 0)
=== 3. Batch Predict Endpoint ===
Batch predictions count: 2 (Panadura: 339.9, Pettah: 493.1 pax)
=== 4. Dispatch Scenario A: Weekday 08:00 AM Peak (Rush Hour) ===
Calendar Day: Wednesday (Weekend: 0, Holiday: 0) | Peak Period: am_peak | Peak Load: 619.58 at stop: Kollupitiya
Buses Needed: 8 | Headway: 8 minutes (Rush headway <= 15 min) | Corridor ETA: 112.5 min (Peak congestion multiplier: 1.25x)
=== 5. Dispatch Scenario B: Off-Peak / Night (02:00) ===
Night Peak Load: 7.37 pax | Buses Needed: 1 | Headway: 30 minutes (Clamped at max 30 min)
=== 6. Dispatch Scenario C: Poya Day Holiday Override ===
Poya Holiday Type: poya | Peak Load: 170.92 pax | Headway: 20 minutes (Lower demand on holiday)
=== 7. Dispatch Scenario D: Special Event Override ===
Event Peak Load: 1082.21 pax (vs Normal: 619.58 pax) | Buses Needed: 14 (Extreme demand surge verified)
>>> ALL 7 SYSTEM VERIFICATION CHECKS PASSED PERFECTLY! <<<'''
add_code_box(test_log, font_size=6.8)

doc.save(out_docx_path)
print(f"Successfully generated clean docx: {out_docx_path}")
