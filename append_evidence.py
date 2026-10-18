import os
import docx
from docx.shared import Pt, Inches, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

base_dir = r"c:\Users\mohan\OneDrive\Desktop\Work\Transit Optimizer Bus"
src_path = os.path.join(base_dir, "Individual_Contribution_Sheet_EAI_Uvaram.docx.bak")
out_evidence_path = os.path.join(base_dir, "Individual_Contribution_Sheet_EAI_Uvaram_With_Evidence.docx")
orig_path = os.path.join(base_dir, "Individual_Contribution_Sheet_EAI_Uvaram.docx")

doc = docx.Document(src_path)

# ==========================================
# 1. UPDATE TABLE 1: ELEVATED CONTRIBUTIONS
# ==========================================
t1 = doc.tables[1]

data = [
    (
        "MLP Model Architecture & Design",
        "Designed and implemented the 4-layer PyTorch neural network DemandPredictorMLP (Input 23 → 128 → 64 → 32 → 1). Integrated BatchNorm1d after dense layers to stabilize internal covariate shift across heterogeneous transit features, and Dropout (0.2) with ReLU activations to prevent co-adaptation and mitigate overfitting on dense passenger counts.",
        "PyTorch (torch.nn), Multilayer Perceptron (MLP), Batch Normalization, Dropout Regularization",
        "train_model.py (DemandPredictorMLP class); backend/models/demand_predictor.pth"
    ),
    (
        "Feature Pipeline & Leakage Prevention",
        "Built a leak-proof tabular preprocessing pipeline via ColumnTransformer. Scaled 11 continuous/calendar features using MinMaxScaler and encoded 3 nominal features (direction, stop_name, weather) with OneHotEncoder. Enforced strict chronological 80/20 train-test splitting by date so the model never trains on future passenger counts.",
        "scikit-learn (ColumnTransformer, MinMaxScaler, OneHotEncoder), pandas, joblib",
        "train_model.py (time_based_split); exported artifact models/preprocessor.pkl"
    ),
    (
        "Model Optimization & Robust Training",
        "Configured and executed model training using Huber loss (Smooth L1) for quadratic convergence on typical loads while penalizing extreme rush-hour passenger surges linearly (preventing gradient explosion). Utilized Adam optimizer (lr = 0.001, batch size 512) and an EarlyStopping routine (patience 10) to checkpoint the best model weights.",
        "PyTorch (optim.Adam, nn.HuberLoss), Early Stopping, Checkpoint Management",
        "models/demand_predictor.pth (state_dict + input_dim: 23); training log"
    ),
    (
        "Multi-Slice Model Evaluation",
        "Conducted rigorous holdout evaluation across N = 158,622 test records, measuring MAE, RMSE, and R². Computed granular slice evaluations across all 8 Galle Road stops, AM/PM peak hours, weather conditions (Clear vs Rain), and calendar types (term days vs holidays) to verify corridor-wide robustness.",
        "scikit-learn (metrics), pandas, NumPy, JSON serialization",
        "models/metrics.json (Overall: MAE 225.8, RMSE 519.3, R² 0.331; stop & peak error matrices)"
    ),
    (
        "Model Serving & System Verification",
        "Integrated the trained PyTorch model and preprocessor into the FastAPI backend service. Engineered an asynchronous @asynccontextmanager startup loader and vectorized batch inference pipeline (torch.no_grad()) delivering sub-millisecond predictions. Validated system reliability through an automated 7-scenario integration test suite.",
        "FastAPI, PyTorch (Vectorized Inference), joblib, TestClient",
        "main.py (_load_artifacts, process_and_predict); test report in test_verification.py (7/7 passed)"
    )
]

col_widths = [Emu(1250000), Emu(2550000), Emu(1350000), Emu(1525120)]

def set_cell_margins(cell, top=90, bottom=90, left=110, right=110):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for name, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{name}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

for r_idx, (col0, col1, col2, col3) in enumerate(data, start=1):
    row = t1.rows[r_idx]
    row_data = [col0, col1, col2, col3]
    for c_idx, cell in enumerate(row.cells):
        cell.width = col_widths[c_idx]
        set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
        p = cell.paragraphs[0]
        p.text = ''
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.15
        run = p.add_run(row_data[c_idx])
        run.font.name = 'Times New Roman'
        run.font.size = Pt(9.5)
        if c_idx == 0:
            run.bold = True

# Format headers
for c_idx, cell in enumerate(t1.rows[0].cells):
    cell.width = col_widths[c_idx]
    set_cell_margins(cell, top=90, bottom=90, left=100, right=100)
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(2)
    for run in p.runs:
        run.font.name = 'Times New Roman'
        run.font.size = Pt(10.5)
        run.bold = True

# ==========================================
# 2. UPDATE TABLE 2: DATE
# ==========================================
t2 = doc.tables[2]
date_cell = t2.rows[0].cells[3]
date_cell.text = ''
p_date = date_cell.paragraphs[0]
p_date.paragraph_format.space_before = Pt(0)
p_date.paragraph_format.space_after = Pt(0)
r_date = p_date.add_run('18/10/2026')
r_date.font.name = 'Times New Roman'
r_date.font.size = Pt(11)

# ==========================================
# 3. APPEND EVIDENCE APPENDIX (PAGE 2)
# ==========================================
doc.add_page_break()

p_head = doc.add_paragraph()
p_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_head.paragraph_format.space_before = Pt(8)
p_head.paragraph_format.space_after = Pt(3)
r_head = p_head.add_run("APPENDIX: TECHNICAL EVIDENCE & SYSTEM ARTIFACTS")
r_head.font.name = "Times New Roman"
r_head.font.size = Pt(13)
r_head.bold = True

p_sub = doc.add_paragraph()
p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_sub.paragraph_format.space_before = Pt(0)
p_sub.paragraph_format.space_after = Pt(12)
r_sub = p_sub.add_run("Student: M Uvaram (D/BSE/25/0012) · Group 40 · Route 100 Transit Fleet Optimizer")
r_sub.font.name = "Times New Roman"
r_sub.font.size = Pt(10)
r_sub.font.italic = True
r_sub.font.color.rgb = RGBColor(75, 85, 99)

def add_evidence_header(title):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(title)
    r.font.name = "Times New Roman"
    r.font.size = Pt(11)
    r.bold = True
    r.font.color.rgb = RGBColor(30, 58, 138)

def add_code_box(code_text):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.rows[0].cells[0]
    cell.width = Inches(6.8)
    
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
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.05
    run = p.add_run(code_text)
    run.font.name = "Consolas"
    run.font.size = Pt(8.5)
    run.font.color.rgb = RGBColor(15, 23, 42)

# --- Evidence 1: MLP Architecture ---
add_evidence_header("Evidence 1: PyTorch MLP Architecture Implementation (train_model.py)")

img_path1 = os.path.join(base_dir, "evidence_mlp_architecture.png")
if os.path.exists(img_path1):
    p_img1 = doc.add_paragraph()
    p_img1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img1.paragraph_format.space_before = Pt(2)
    p_img1.paragraph_format.space_after = Pt(4)
    doc.add_picture(img_path1, width=Inches(6.8))

mlp_code = '''class DemandPredictorMLP(nn.Module):
    def __init__(self, input_dim: int = 23):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.BatchNorm1d(128),  # Mitigates internal covariate shift across features
            nn.ReLU(),
            nn.Dropout(0.2),       # Regularization against passenger count overfitting
            nn.Linear(128, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1)       # Predicts continuous passenger count per stop
        )

    def forward(self, x):
        return self.network(x)'''
add_code_box(mlp_code)

# --- Evidence 2: Preprocessing ---
add_evidence_header("Evidence 2: Chronological 80/20 Train-Test Split & ColumnTransformer (train_model.py)")
prep_code = '''def time_based_split(df: pd.DataFrame, test_size: float = 0.2):
    """Strict chronological split by date: past dates -> train, future -> val."""
    unique_dates = sorted(df["date"].unique())
    cutoff_idx = int(len(unique_dates) * (1 - test_size))
    train_dates = set(unique_dates[:cutoff_idx])
    return df[df["date"].isin(train_dates)], df[~df["date"].isin(train_dates)]

# Preprocessing: Fit ONLY on training partition to eliminate temporal data leakage
preprocessor = ColumnTransformer(transformers=[
    ("num", MinMaxScaler(), ["hour", "day_of_week", "is_weekend", "is_public_holiday",
                             "is_school_rush", "is_am_peak", "is_pm_peak", "month", ...]),
    ("cat", OneHotEncoder(handle_unknown="ignore"), ["direction", "stop_name", "weather"])
])
X_train_proc = preprocessor.fit_transform(X_train)  # Generates 23-dim feature tensor'''
add_code_box(prep_code)

# --- Evidence 3: Training Configuration ---
add_evidence_header("Evidence 3: Model Training Hyperparameters & Saved Checkpoints")
tbl_train = doc.add_table(rows=7, cols=2)
tbl_train.alignment = WD_TABLE_ALIGNMENT.CENTER
train_meta = [
    ("Training Dataset Size", "641,378 rows (80% chronological partition)"),
    ("Validation Dataset Size", "158,622 rows (20% chronological holdout partition)"),
    ("Loss Function", "Huber Loss / Smooth L1 (robust against peak rush surge outliers)"),
    ("Optimization Algorithm", "Adam Optimizer (learning rate = 0.001, batch size = 512)"),
    ("Early Stopping & Best Epoch", "Stopped at Epoch 31 (Patience 10); Best Val Huber Loss: 225.27"),
    ("Input Dimensions", "23 features (11 MinMax scaled numerical + 12 One-Hot encoded categorical)"),
    ("Exported Model Artifact", "backend/models/demand_predictor.pth (state_dict + input_dim: 23)")
]

for r_idx, (k, v) in enumerate(train_meta):
    r = tbl_train.rows[r_idx]
    r.cells[0].width = Inches(2.3)
    r.cells[1].width = Inches(4.5)
    for c in r.cells:
        borders = parse_xml(r'''
            <w:tcBorders {} >
                <w:top w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>
                <w:left w:val="none"/>
                <w:bottom w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>
                <w:right w:val="none"/>
            </w:tcBorders>
        '''.format(nsdecls('w')))
        c._tc.get_or_add_tcPr().append(borders)
    
    p0 = r.cells[0].paragraphs[0]
    p0.paragraph_format.space_before = Pt(2)
    p0.paragraph_format.space_after = Pt(2)
    run0 = p0.add_run(k)
    run0.font.name = "Times New Roman"
    run0.font.size = Pt(9.5)
    run0.bold = True
    
    p1 = r.cells[1].paragraphs[0]
    p1.paragraph_format.space_before = Pt(2)
    p1.paragraph_format.space_after = Pt(2)
    run1 = p1.add_run(v)
    run1.font.name = "Times New Roman"
    run1.font.size = Pt(9.5)

# --- Evidence 4: Holdout Evaluation ---
add_evidence_header("Evidence 4: Holdout Evaluation Error Across Stops & Slices (models/metrics.json)")

img_path2 = os.path.join(base_dir, "evidence_metrics_by_stop.png")
if os.path.exists(img_path2):
    p_img2 = doc.add_paragraph()
    p_img2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img2.paragraph_format.space_before = Pt(2)
    p_img2.paragraph_format.space_after = Pt(4)
    doc.add_picture(img_path2, width=Inches(6.8))

tbl_eval = doc.add_table(rows=5, cols=5)
tbl_eval.alignment = WD_TABLE_ALIGNMENT.CENTER
eval_rows = [
    ["Slice / Condition", "Sample Count (N)", "MAE (pax)", "RMSE (pax)", "R² Score"],
    ["Overall Holdout Partition", "158,622", "225.8", "519.3", "0.331"],
    ["Weather: Clear vs Rain", "132,626 / 25,996", "196.6 / 374.4", "474.7 / 704.0", "0.260 / 0.324"],
    ["Weekday vs Weekend", "124,554 / 34,068", "265.3 / 81.3", "580.6 / 152.0", "0.308 / 0.316"],
    ["AM Peak vs School Rush", "17,992 / 16,817", "447.0 / 577.9", "818.0 / 929.2", "0.110 / 0.046"]
]

col_w = [Inches(2.0), Inches(1.5), Inches(1.1), Inches(1.1), Inches(1.1)]

for r_idx, row_vals in enumerate(eval_rows):
    r = tbl_eval.rows[r_idx]
    for c_idx, val in enumerate(row_vals):
        cell = r.cells[c_idx]
        cell.width = col_w[c_idx]
        if r_idx == 0:
            shd = parse_xml(r'<w:shd {} w:fill="F1F5F9"/>'.format(nsdecls('w')))
            cell._tc.get_or_add_tcPr().append(shd)
            borders = parse_xml(r'''
                <w:tcBorders {} >
                    <w:top w:val="single" w:sz="6" w:space="0" w:color="94A3B8"/>
                    <w:left w:val="none"/>
                    <w:bottom w:val="single" w:sz="8" w:space="0" w:color="334155"/>
                    <w:right w:val="none"/>
                </w:tcBorders>
            '''.format(nsdecls('w')))
        else:
            borders = parse_xml(r'''
                <w:tcBorders {} >
                    <w:top w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>
                    <w:left w:val="none"/>
                    <w:bottom w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>
                    <w:right w:val="none"/>
                </w:tcBorders>
            '''.format(nsdecls('w')))
        cell._tc.get_or_add_tcPr().append(borders)
        
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        run = p.add_run(val)
        run.font.name = "Times New Roman"
        run.font.size = Pt(9)
        if r_idx == 0:
            run.bold = True

# --- Evidence 5: Automated Verification ---
add_evidence_header("Evidence 5: End-to-End System Integration & 7-Scenario Test Run (test_verification.py)")
test_log = '''=== 1. Health / Root Endpoint ===
Service: Route 100 Transit Optimizer | Framework: PyTorch MLP | Input dim: 23 | Stops: 8 stops

=== 2. Single Predict Endpoint ===
Predicted single stop (Kollupitiya 08:00): 619.6 pax (Verified: pax > 0)

=== 3. Batch Predict Endpoint ===
Batch predictions count: 2 (Panadura: 339.9, Pettah: 493.1 pax)

=== 4. Dispatch Scenario A: Weekday 08:00 AM Peak (Rush Hour) ===
Calendar Day: Wednesday (Weekend: 0, Holiday: 0) | Peak Period: am_peak
Peak Load: 619.58 at stop: Kollupitiya | Buses Needed: 8 | Headway: 8 minutes (Rush headway <= 15 min)
Corridor ETA: 112.5 min (Peak congestion multiplier: 1.25x)

=== 5. Dispatch Scenario B: Off-Peak / Night (02:00) ===
Night Peak Load: 7.37 pax | Buses Needed: 1 | Headway: 30 minutes (Clamped at max 30 min)

=== 6. Dispatch Scenario C: Poya Day Holiday Override ===
Poya Holiday Type: poya | Peak Load: 170.92 pax | Headway: 20 minutes (Lower demand on holiday)

=== 7. Dispatch Scenario D: Special Event Override ===
Event Peak Load: 1082.21 pax (vs Normal: 619.58 pax) | Buses Needed: 14 (Extreme demand surge verified)

>>> ALL 7 SYSTEM VERIFICATION CHECKS PASSED PERFECTLY! <<<'''
add_code_box(test_log)

# Save to output file
doc.save(out_evidence_path)
print("Saved to:", out_evidence_path)

# Also attempt saving to original if unlocked
try:
    doc.save(orig_path)
    print("Also successfully updated original:", orig_path)
except Exception as e:
    print("Original file currently locked by Word; saved to With_Evidence file:", e)
