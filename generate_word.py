from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

document = Document()

# Main Title
p = document.add_heading('PC-Min 完整欄位總表 (Proposal 1 + Phase 4 Impl)', 0)
p.alignment = WD_ALIGN_PARAGRAPH.CENTER

document.add_heading('1. 欄位細節 (Field Details)', level=1)

table = document.add_table(rows=1, cols=5)
table.style = 'Table Grid'
hdr_cells = table.rows[0].cells
hdr_cells[0].text = '欄位名稱'
hdr_cells[1].text = '當前結果'
hdr_cells[2].text = '可能結果'
hdr_cells[3].text = '判斷依據'
hdr_cells[4].text = '說明'

# Helper to format header
for cell in hdr_cells:
    cell.paragraphs[0].runs[0].font.bold = True

data = [
    ("episode_id", "ep-a664e7c3", "Any UUID ep-{hex}", "M00 (Common): 每次 OBH 觸發時自動生成。", "診斷事件唯一 ID。"),
    ("window_ref", "W-LATEST", "W-LATEST\nW-{Date}", "M01 (Windowing): 根據觸發時間對應到的 Time Slot。", "時間窗口 ID。"),
    ("data_range_start", "2026-02-12...", "ISO 8601 Timestamp", "Aggregation: 採樣數據中的最小值 (Min TS)。", "採樣開始時間。"),
    ("data_range_end", "2026-02-12...", "ISO 8601 Timestamp", "Aggregation: 採樣數據中的最大值 (Max TS)。", "採樣結束時間。"),
    ("primary_verdict", "INSUFFICIENT", "READY\nWAN_UNSTABLE\nWIFI_CONGESTION\nINSUFFICIENT", "M13 (Profile Check): 依據 Metrics 是否超過 P95/P50 閾值 (Profile Rules)。", "主要網路診斷結論。"),
    ("admission_verdict", "ADMIT", "ADMIT\nDENY\nDEGRADE", "M22 (Governance): 綜合考量 Privacy Check 結果與 Strict Mode 設定。", "能否通過 Egress Gate 的准入判決。"),
    ("privacy_check_verdict", "PASS", "PASS\nFAIL\nINCONCLUSIVE", "M22 (Hook 1): 檢查資料中是否含有敏感或未授權的 PII。", "隱私檢查的細節判決。"),
    ("evidence_grade", "DELIVERY", "DELIVERY\nPARTIAL\nNOT_CLOSURE", "M13/M22: 檢查是否缺少關鍵 Metrics 或因隱私原因被剝離。", "證據完整性與信賴等級。"),
    ("gate_ref", "EG-DEFAULT-V1", "EG-DEFAULT-V1\nEG-STRICT-V2", "M22 (Egress): 根據系統當下的 Strict Mode 或 Authority Scope 動態決定。", "通過的合規閘口標準 ID。"),
    ("policy_snapshot_ref", "POL-DEFAULT-V1.0", "POL-DEFAULT-V1.0\nPOL-GDPR-V2", "M22 (Propagation): 從 ProofCardPriv 繼承，代表當時生效的 Policy 版本。", "隱私策略快照 ID。"),
    ("byuse_context_ref", "None", "None\nUPREQ-SIGNED\nCTX-DISPUTE", "Input/M22: 根據觸發者的身份 (User/CSR) 與目的 (Diagnosis/Dispute) 決定。", "特殊使用情境或補件需求。"),
]

for row_data in data:
    row_cells = table.add_row().cells
    for i, text in enumerate(row_data):
        row_cells[i].text = text

document.add_heading('2. 解讀亮點 (Key Takeaways)', level=1)

document.add_heading('primary_verdict 與 admission_verdict 的分離', level=2)
document.add_paragraph('雖然網路診斷結果是 INSUFFICIENT (不夠好)，但准入判決是 ADMIT (允許傳送)。這證明了系統能區分「技術品質」與「合規狀態」。')

document.add_heading('gate_ref 與 policy_snapshot_ref 的連動', level=2)
document.add_paragraph('EG-DEFAULT 對應 POL-DEFAULT，這顯示了系統的一致性配置。如果是 EG-STRICT，理論上這裡也會對應到更嚴格的 Policy ID。')

document.add_heading('evidence_grade 的價值', level=2)
document.add_paragraph('即使樣本不足，evidence_grade 仍是 DELIVERY，表示這份資料「結構完整，可交付」，即便內容可能無法支持某些結論。')


# --- NEW SECTION: Technical Deep Dive ---
document.add_page_break()
document.add_heading('3. 欄位輸入與判斷邏輯 (Input & Logic Deep Dive)', level=1)
document.add_paragraph('本節針對每個欄位，詳細列出其生成的輸入來源 (Input)、內部的核心判斷邏輯 (Logic)、以及最終產生的輸出格式 (Output) 。')

# Define Data
logic_data = [
    {
        "field": "episode_id",
        "input": "System Entropy (UUID Generator, Python `uuid` lib)",
        "logic": "Generate standard Version 4 UUID (Random). Convert to Hexadecimal String.",
        "output": "String (`ep-{hex}`), e.g., 'ep-a664e7c3...'"
    },
    {
        "field": "primary_verdict",
        "input": "Metrics List (Latency, Loss, Jitter), Threshold Profiles (M13)",
        "logic": "1. Aggregate raw metrics (P95/P50).\n2. Apply Rule Engine:\n   - IF P95_RTT > 100ms: Set `WAN_UNSTABLE`\n   - IF Loss% > 2%: Set `WIFI_CONGESTION`\n   - ELSE: Set `READY`\n3. Check Data Sufficiency: IF samples < 100 -> `INSUFFICIENT`",
        "output": "Enum String (`READY`, `WAN_UNSTABLE`, `INSUFFICIENT`...)"
    },
    {
        "field": "admission_verdict",
        "input": "Primary Verdict, Privacy Check Result, System Config (`strict_mode`)",
        "logic": "Egress Gate Decision (M22):\n1. IF `privacy_check` == FAIL -> **DENY** (Blocks Export).\n2. IF `strict_mode` == TRUE AND `primary_verdict` != READY -> **DENY** (Quality Gate).\n3. ELSE -> **ADMIT** (Allow Export).",
        "output": "Enum String (`ADMIT`, `DENY`)"
    },
     {
        "field": "gate_ref",
        "input": "User Authority Scope ('isp-support' or 'public'), Strict Mode Flag",
        "logic": "Select Gate Policy (M22):\n1. IF Scope == 'public' -> `EG-PUBLIC-V1` (High Privacy)\n2. IF `strict_mode` -> `EG-STRICT-V2` (High Quality Bar)\n3. ELSE -> `EG-DEFAULT-V1` (Balanced)",
        "output": "String Ref (`EG-DEFAULT-V1`, `EG-STRICT-V2`)"
    },
    {
        "field": "privacy_check_verdict",
        "input": "Private Data Fields (SSID, MAC, Hostnames), PII Regex Patterns",
        "logic": "Sensitive Data Scan (M22 Hook 1):\n1. Scan all string fields against Regex (Credit Card, Email, Precise Location).\n2. IF Match Found -> **FAIL**.\n3. IF Data is Encrypted/Hashed -> **PASS**.\n4. Default: **PASS**.",
        "output": "Enum String (`PASS`, `FAIL`, `INCONCLUSIVE`)"
    },
    {
        "field": "evidence_grade",
        "input": "Metric Availability (Count of valid samples), Required Columns List",
        "logic": "Completeness Check (M13):\n1. Verify presence of essential columns (RTT, Loss).\n2. Verify Sample Size > Minimum Threshold.\n3. IF missing critical data -> `PARTIAL_RELIANCE`.\n4. IF size < min -> `PARTIAL_RELIANCE`.\n5. ELSE -> `DELIVERY_GRADE`.",
        "output": "Enum String (`DELIVERY_GRADE`, `PARTIAL_RELIANCE`)"
    },
    {
        "field": "policy_snapshot_ref",
        "input": "Active Global Privacy Policy (Singleton Object)",
        "logic": "Version Linking (M22):\n- Reads the `current_version` ID from the active Policy Manager at the moment of generation.\n- Ensures the dataset is linked to the specific rules under which it was collected.",
        "output": "String (`POL-DEFAULT-V1.0`)"
    },
    {
        "field": "byuse_context_ref",
        "input": "Trigger Source (User vs Automated), Intent (Support vs Analytics)",
        "logic": "Context Mapping (M22):\n1. IF Trigger == 'User' AND Intent == 'Dispute' -> `CTX-DISPUTE` (May trigger higher retention).\n2. IF Trigger == 'Auto' -> `CTX-AUTO-DIAG`.\n3. Default: `None`.",
        "output": "String or None"
    },
    {
        "field": "window_ref",
        "input": "Current Timestamp, Window Size Config (e.g., 15min)",
        "logic": "Time Slotting (M01):\n- Calculate `floor(timestamp / window_size)` to assign a normalized ID.\n- Default: `W-LATEST` for real-time trigger.",
        "output": "String Output"
    }
]

# Create Detailed Table
table_logic = document.add_table(rows=1, cols=4)
table_logic.style = 'Table Grid'
hdr_logic = table_logic.rows[0].cells
hdr_logic[0].text = '欄位 (Field)'
hdr_logic[1].text = '輸入來源 (Input)'
hdr_logic[2].text = '核心邏輯 (Judgment Logic)'
hdr_logic[3].text = '輸出 (Output)'

for cell in hdr_logic:
    cell.paragraphs[0].runs[0].font.bold = True

for item in logic_data:
    row_cells = table_logic.add_row().cells
    row_cells[0].text = item['field']
    row_cells[1].text = item['input']
    row_cells[2].text = item['logic']
    row_cells[3].text = item['output']

document.save('PC_MIN_FULL_DETAILS_v2.docx')
print("Detailed document generated successfully.")
