import os
import docx
from docx.shared import Pt, Inches, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

base_dir = r"c:\Users\mohan\OneDrive\Desktop\Work\Transit Optimizer Bus"
evidence_dir = os.path.join(base_dir, "evidence_screenshots")
out_dir = os.path.join(base_dir, "Reports", "individual contribution reports")
os.makedirs(out_dir, exist_ok=True)
out_docx_path = os.path.join(out_dir, "Individual_Contribution_Sheet_D_BIT_24_0056_With_Evidence.docx")

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
    [("Student Name", True), ("JGJB Gamage", False), ("Registration No.", True), ("D/BIT/24/0056", False)],
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
        "Frontend Dashboard & UI Architecture",
        "Architected and implemented the reactive depot planning dashboard using Next.js 16 App Router, TypeScript, and Tailwind CSS. Implemented a tailored transit theme (deep teal/slate ink, Fraunces serif display headers, and Manrope sans typography) delivering a clutter-free operational surface for depot dispatchers.",
        "Next.js 16, React 19, TypeScript, Tailwind CSS",
        "Running dashboard at localhost:3000; Slides 11 & 13 in Route100_Fleet_Optimizer_Group40.pptx"
    ),
    (
        "Dynamic Scenario Controls & Real-Time State",
        "Engineered the multi-variable scenario input suite: corridor direction toggle, date selector, 24-hour slider, weather selector, special event override, and segmented tri-state buttons for Day Type, School Vacation, and School Rush hours, enabling instant scenario simulation without page reloads.",
        "React Hooks (useState, useEffect), Event Handlers",
        "Interactive scenario control bar; instant headway recalculation on condition toggle"
    ),
    (
        "Automated Live Weather Integration",
        "Integrated the Open-Meteo REST API (Colombo coordinates: lat 6.9271, lon 79.8612) with a 3-tier fallback strategy (forecast daily weathercode, historical archive, and live current_weather). Mapped WMO precipitation codes (>= 51) to dynamically prefill Clear/Rain conditions.",
        "Open-Meteo REST API, Asynchronous Fetch, WMO Code Mapping",
        "Live Colombo weather status badge; automated rain load multiplier triggers"
    ),
    (
        "Corridor Visualisation & KPI Dashboard",
        "Engineered the 4-metric executive KPI readout (headway, buses/hr, peak passenger load, corridor ETA), responsive crowd-status banner, 8-stop corridor transit rail with bottleneck badges, and an interactive Recharts bar chart highlighting peak boarding points in accent amber.",
        "Recharts Data Viz, Tailwind CSS, Responsive Flex/Grid",
        "Corridor transit rail component; stop-level boarding chart; crowd status alert banner"
    ),
    (
        "Backend API Synchronization & Lifecycle",
        "Integrated the client frontend with the FastAPI backend (/dispatch endpoint). Designed an AbortController lifecycle pipeline to prevent stale responses during rapid user slider scrubbing, structured JSON request payloads, and bound calendar context chips and override alerts.",
        "FastAPI Integration, fetch API, AbortController, CORS",
        "frontend/src/app/page.tsx (executeFetch pipeline, KPI state cards, calendar chip binding)"
    )
]

for r_idx, row_data in enumerate(contributions, start=1):
    row = t1.rows[r_idx]
    for c_idx, cell in enumerate(row.cells):
        cell.width = col_w_t1[c_idx]
        set_cell_margins(cell, top=35, bottom=35, left=55, right=55)
        set_cell_borders(cell, color="CBD5E1")
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(1)
        p.paragraph_format.line_spacing = 1.05
        run = p.add_run(row_data[c_idx])
        run.font.name = "Times New Roman"
        run.font.size = Pt(8.2)
        if c_idx == 0:
            run.bold = True

p_dec = doc.add_paragraph()
p_dec.paragraph_format.space_before = Pt(5)
p_dec.paragraph_format.space_after = Pt(1)
r_dec = p_dec.add_run("Declaration")
r_dec.font.name = "Times New Roman"
r_dec.font.size = Pt(9.5)
r_dec.bold = True

p_dec_text = doc.add_paragraph()
p_dec_text.paragraph_format.space_before = Pt(0)
p_dec_text.paragraph_format.space_after = Pt(3)
r_dtext = p_dec_text.add_run("I confirm that the contributions listed above accurately represent my individual work in this group project, and I can explain or demonstrate the stated work if required.")
r_dtext.font.name = "Times New Roman"
r_dtext.font.size = Pt(8.5)

# Signature & Date Table
t2 = doc.add_table(rows=1, cols=2)
t2.alignment = WD_TABLE_ALIGNMENT.CENTER
t2.rows[0].cells[0].width = Inches(4.7)
t2.rows[0].cells[1].width = Inches(2.8)

for cell in t2.rows[0].cells:
    set_cell_margins(cell, top=65, bottom=65, left=85, right=85)
    set_cell_borders(cell, color="94A3B8")

cell_sig = t2.rows[0].cells[0]
p_sig1 = cell_sig.paragraphs[0]
p_sig1.paragraph_format.space_before = Pt(0)
p_sig1.paragraph_format.space_after = Pt(0)
r_slabel = p_sig1.add_run("Student Signature:")
r_slabel.font.name = "Times New Roman"
r_slabel.font.size = Pt(9)
r_slabel.bold = True

p_space = cell_sig.add_paragraph()
p_space.paragraph_format.space_before = Pt(28)
p_space.paragraph_format.space_after = Pt(0)
r_line = p_space.add_run("_________________________________________")
r_line.font.name = "Times New Roman"
r_line.font.size = Pt(9.5)

cell_date = t2.rows[0].cells[1]
p_d1 = cell_date.paragraphs[0]
p_d1.paragraph_format.space_before = Pt(0)
p_d1.paragraph_format.space_after = Pt(0)
r_dlabel = p_d1.add_run("Date:")
r_dlabel.font.name = "Times New Roman"
r_dlabel.font.size = Pt(9)
r_dlabel.bold = True

p_d2 = cell_date.add_paragraph()
p_d2.paragraph_format.space_before = Pt(28)
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
# PAGE 2+: APPENDIX - TECHNICAL EVIDENCE
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
p_app_sub.paragraph_format.space_after = Pt(6)
r_app_sub = p_app_sub.add_run("Student: JGJB Gamage (D/BIT/24/0056) · Group 40 · Route 100 Transit Fleet Optimizer")
r_app_sub.font.name = "Times New Roman"
r_app_sub.font.size = Pt(8.5)
r_app_sub.font.italic = True
r_app_sub.font.color.rgb = RGBColor(75, 85, 99)

def add_evidence_header(title):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(title)
    r.font.name = "Times New Roman"
    r.font.size = Pt(9.5)
    r.bold = True
    r.font.color.rgb = RGBColor(30, 58, 138)

def add_evidence_caption(caption):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(caption)
    r.font.name = "Times New Roman"
    r.font.size = Pt(8)
    r.font.italic = True
    r.font.color.rgb = RGBColor(71, 85, 105)

def add_code_box(code_text, font_size=7.0):
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

# --- Evidence 1: Full-Page Running Dashboard at Morning Peak ---
add_evidence_header("Evidence 1: Full-Page Screenshot of Running Depot Dashboard (localhost:3000)")
add_evidence_caption("Figure 1: Full dashboard during weekday AM peak commute (08:00 AM, Inbound). Note 8 min headway, 8 buses/hr, peak bottleneck load at Kollupitiya (620 pax, highlighted in amber), and corridor ETA of 112.5 min.")

img1 = os.path.join(evidence_dir, "evidence_1_dashboard_morning_peak.png")
if os.path.exists(img1):
    doc.add_picture(img1, width=Inches(7.2))

# --- Evidence 2: Corridor Rail, Crowd Banner & Live Weather Badge ---
add_evidence_header("Evidence 2: Corridor Stop Rail Component, Crowd Status & Live Open-Meteo Weather Badge")
add_evidence_caption("Figure 2: Component-level visualization showing the 8-stop Galle Road transit rail with amber bottleneck indicator, real-time crowd status ('Crowded'), and Open-Meteo weather prefill.")

img2 = os.path.join(evidence_dir, "evidence_2_corridor_rail_and_weather_focus.png")
if os.path.exists(img2):
    doc.add_picture(img2, width=Inches(7.2))

# --- Evidence 3: Scenario Controls & Instant Recalculation ---
add_evidence_header("Evidence 3: Scenario Controls Toggling 'Special Event Rush' & Instant Headway Updates")
add_evidence_caption("Figure 3: Scenario simulation panel with Special Event surge toggled. Headway compresses from 8 min down to 4 min, fleet expands to 14 buses/hr, and corridor load increases to 1,082 pax with 'Override active' indicator.")

img3 = os.path.join(evidence_dir, "evidence_3_scenario_toggles_and_kpis.png")
if os.path.exists(img3):
    doc.add_picture(img3, width=Inches(7.2))

# --- Evidence 4: Code Implementation ---
add_evidence_header("Evidence 4: Frontend Implementation Code Snapshot (frontend/src/app/page.tsx)")
add_evidence_caption("Figure 4: Asynchronous /dispatch API fetch handler with AbortController lifecycle management and KPI readout card architecture.")

img4 = os.path.join(evidence_dir, "evidence_4_code_kpi_and_fetch.png")
if os.path.exists(img4):
    doc.add_picture(img4, width=Inches(7.2))

fetch_code = '''// Asynchronous Dispatch API Synchronization with Request Cancellation
useEffect(() => {
  let ignore = false;
  const controller = new AbortController();

  async function executeFetch() {
    try {
      const payload = { date, hour, direction, event_override: eventOverride ? 1 : 0,
                        weather, holiday_mode: holidayMode, school_holiday_mode: schoolHolidayMode,
                        school_rush_mode: schoolRushMode };
      const res = await fetch(`${API_BASE_URL}/dispatch`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload), signal: controller.signal,
      });
      if (!res.ok) throw new Error("API request failed");
      const result = await res.json();
      if (!ignore) setData(result);
    } catch (err) {
      if (!ignore && err.name !== "AbortError") setError(err.message);
    }
  }
  executeFetch();
  return () => { ignore = true; controller.abort(); };
}, [date, hour, direction, weather, eventOverride, holidayMode, schoolHolidayMode, schoolRushMode]);'''
add_code_box(fetch_code, font_size=7.0)

# --- Evidence 5: Slide Deck References ---
add_evidence_header("Evidence 5: Presentation Slide Deck Reference (Slides 11 & 13 — Decision Support & Impact)")
add_evidence_caption("Figure 5: Slide 11 ('Part 4: Decision Support — Depot Manager Dashboard') and Slide 13 ('Part 4: Conclusion — Operational Impact & Scalability') from Route100_Fleet_Optimizer_Group40.pptx.")

img5a = os.path.join(evidence_dir, "evidence_5_slide_11_dashboard.png")
if os.path.exists(img5a):
    doc.add_picture(img5a, width=Inches(7.0))

img5b = os.path.join(evidence_dir, "evidence_5_slide_13_operational_impact.png")
if os.path.exists(img5b):
    p_sp = doc.add_paragraph()
    p_sp.paragraph_format.space_before = Pt(4)
    p_sp.paragraph_format.space_after = Pt(2)
    doc.add_picture(img5b, width=Inches(7.0))

doc.save(out_docx_path)
print(f"Successfully generated pristine Word document: {out_docx_path}")
