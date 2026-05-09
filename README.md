# Request Classifier — AI-Powered Workflow Automation

> Power Apps → Power Automate → Google Sheets → Python FastAPI

An end-to-end workflow automation system that accepts user requests via a Power Apps form, orchestrates them through Power Automate, stores data in Google Sheets, and classifies request priority using a Python FastAPI AI backend.

---

## Architecture

```
Power Apps (form UI)
      ↓  Power Apps trigger
Power Automate (orchestration)
      ↓  Insert row
Google Sheets (database)
      ↓  JSON payload
Python FastAPI (AI classification)
      ↓  ai_result + confidence
Power Automate (update row)
      ↓  Write AI_Result + Status = "Classified"
Google Sheets (updated)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend UI | Microsoft Power Apps (Canvas App) |
| Orchestration | Microsoft Power Automate |
| Database | Google Sheets |
| AI Classification | Python FastAPI |
| Tunnel (dev) | ngrok |
| Deployment (prod) | Railway / Render / Fly.io |

---

## Project Structure

```
request-classifier/
├── main.py                   # FastAPI app — classification engine
├── requirements.txt          # Python dependencies
├── test_api.py               # API test script (4 test cases)
├── power_automate_flow.json  # Flow reference / structure
├── powerapps_formulas.txt    # All Power Apps formulas
├── BUILD_GUIDE.html          # Full visual build guide
└── README.md                 # This file
```

---

## Google Sheets Schema

Set up Row 1 of `Sheet1` with exactly these column headers:

| A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|
| RequestID | UserName | RequestText | Category | Status | Timestamp | AI_Result |

Sample row after classification:

| REQ-001 | Test User | urgent approval needed | High Priority | Classified | 2026-05-07 | High Priority |

---

## Phase 1 — FastAPI Backend

### Prerequisites
- Python 3.10+
- ngrok account — [ngrok.com](https://ngrok.com)

### Setup

```bash
# Create project folder and virtual environment
mkdir request-classifier && cd request-classifier
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install fastapi uvicorn[standard] pydantic python-multipart
```

### Run the server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Visit **http://localhost:8000/docs** to see the interactive Swagger UI.

### Run tests

```bash
python test_api.py
# Expected: 4/4 tests passing
```

### Expose with ngrok

```bash
# In a second terminal (keep uvicorn running)
ngrok config add-authtoken YOUR_TOKEN
ngrok http 8000
```

Copy the `https://abc123.ngrok.io` URL — paste it into Power Automate.

> ⚠️ The free ngrok URL changes on every restart. Keep both terminals open for the full demo session.

---

## Classification Logic

The AI engine uses keyword scoring with confidence levels:

| Priority | Keywords | Example |
|---|---|---|
| 🔴 High | urgent, ASAP, critical, approval needed, emergency, blocker | "urgent approval needed ASAP" |
| 🟡 Medium | review, request, update, fix, please check, follow up | "please review this change" |
| 🟢 Low | FYI, no rush, whenever, suggestion, nice to have | "fyi no rush whenever you can" |

Exclamation marks and ALL CAPS words add a +1 boost to the High score.

### API Endpoints

```
GET  /          → health check
GET  /health    → status + timestamp
POST /classify  → classify a single request
POST /classify/batch → classify multiple at once
```

### POST /classify — request body

```json
{
  "request_id":   "REQ-001",
  "user_name":    "Test User",
  "request_text": "urgent approval needed",
  "timestamp":    "2026-05-07T10:00:00Z"
}
```

### POST /classify — response

```json
{
  "request_id":   "REQ-001",
  "user_name":    "Test User",
  "request_text": "urgent approval needed",
  "ai_result":    "High Priority",
  "category":     "High Priority",
  "confidence":   0.75,
  "reason":       "Detected urgency indicators: 2 high-priority keyword(s)",
  "status":       "Classified",
  "processed_at": "2026-05-07T10:00:01.123Z"
}
```

---

## Phase 2 — Google Sheets 

1. Go to [sheets.google.com](https://sheets.google.com) → New spreadsheet
2. Name it **Request Classifier DB**
3. Add the 7 column headers in Row 1 (see schema above)
4. Copy the Spreadsheet ID from the URL:
   `https://docs.google.com/spreadsheets/d/`**`YOUR_ID_HERE`**`/edit`

---

## Phase 3 — Power Automate Flow 

Go to [make.powerautomate.com](https://make.powerautomate.com) → Create → Instant cloud flow.

### Trigger: Power Apps

Use the **"Power Apps"** trigger (not HTTP) so Power Apps can call it directly with `.Run()`.

### Flow actions in order

**1. Google Sheets — Insert row**
- File: `Request Classifier DB`
- Sheet: `Sheet1`
- Map fields from trigger inputs
- Status: `Pending` (hardcoded)
- Timestamp: `utcNow()`
- AI_Result: *(leave blank)*

**2. HTTP — Call FastAPI**
```
Method:  POST
URI:     https://YOUR_NGROK_URL/classify
Headers: Content-Type: application/json
Body:
{
  "request_id":   "@{triggerBody()?['RequestID']}",
  "user_name":    "@{triggerBody()?['UserName']}",
  "request_text": "@{triggerBody()?['RequestText']}",
  "timestamp":    "@{utcNow()}"
}
```

**3. Parse JSON** — parse the HTTP response body with schema:
```json
{
  "type": "object",
  "properties": {
    "ai_result":  { "type": "string" },
    "confidence": { "type": "number" },
    "reason":     { "type": "string" },
    "status":     { "type": "string" }
  }
}
```

**4. Google Sheets — Update row**
- Row ID: use the row ID returned by the Insert Row action
- AI_Result: `ai_result` from Parse JSON output
- Status: `Classified` (hardcoded)

**5. Respond to Power Apps**
```json
{
  "success":    true,
  "ai_result":  "@{body('Parse_JSON')?['ai_result']}",
  "confidence": "@{body('Parse_JSON')?['confidence']}",
  "reason":     "@{body('Parse_JSON')?['reason']}"
}
```

Save → test using the built-in Test button.

---

## Phase 4 — Power Apps Canvas App

Go to [make.powerapps.com](https://make.powerapps.com) → Create → Blank canvas app.

### Screen 1 — Submit form

Insert these controls and rename them exactly:

| Control type | Rename to | Setting |
|---|---|---|
| Text input | `txtUserName` | Placeholder: "Your Name" |
| Text input (multiline) | `txtRequestText` | Placeholder: "Describe your request..." |
| Dropdown | `drpCategory` | Items: `["General","IT","HR","Finance","Operations"]` |
| Button | `btnSubmit` | Text: "Submit Request" |
| Label | `lblStatus` | Text: `varStatus` |

### App.OnStart

```
Set(varStatus, "");
Set(varLoading, false);
ClearCollect(colResults, []);
```

### btnSubmit.OnSelect

Add your flow via the ⚡ Power Automate sidebar first, then:

```
Set(varLoading, true);
Set(varStatus, "Submitting...");

Set(varResult,
    YourFlowName.Run(
        "REQ-" & Text(Now(), "YYYYMMDDHHmmss"),
        txtUserName.Text,
        txtRequestText.Text,
        drpCategory.Selected.Value,
        "Pending",
        Text(Now(), "YYYY-MM-DD HH:mm:ss")
    )
);

Set(varStatus, "✅ AI Result: " & varResult.ai_result &
    " (" & Text(varResult.confidence * 100, "0") & "% confidence)");

Collect(colResults, {
    RequestID:  "REQ-" & Text(Now(), "YYYYMMDDHHmmss"),
    AIResult:   varResult.ai_result,
    Confidence: varResult.confidence,
    Status:     "Classified"
});

Set(varLoading, false);
```

> Replace `YourFlowName` with the actual name shown after adding the flow.

### Screen 2 — Results gallery

Insert → New screen → Gallery (vertical) → Items: `colResults`

Badge color formula inside gallery:
```
Switch(
    ThisItem.AIResult,
    "High Priority",   RGBA(220, 38,  38,  0.15),
    "Medium Priority", RGBA(234, 179, 8,   0.15),
    "Low Priority",    RGBA(34,  197, 94,  0.15),
    RGBA(148, 163, 184, 0.15)
)
```



## Common Errors & Fixes

| Error | Cause | Fix |
|---|---|---|
| `PostJSON is unknown` | Not a valid Power Apps function | Use Power Apps trigger + `.Run()` instead |
| `txtUserName isn't recognized` | Control name mismatch | Rename controls in Tree View to match formula names |
| `The '.' operator cannot be used on Error values` | Cascades from the above errors | Fix control names + function first |
| ngrok `ERR_NGROK_3200` | Tunnel expired or not running | Restart ngrok, update URL in Power Automate |
| Google Sheets `Update row` fails | Wrong row ID reference | Use the `Row` output from Insert Row action, not RequestID |
