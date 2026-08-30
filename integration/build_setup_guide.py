"""Build the Code Guru team setup guide as a PDF."""

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageBreak, PageTemplate, Paragraph, Preformatted,
    Spacer, Table, TableStyle, KeepTogether,
)

import os

# Written next to this script, inside integration/.
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "Code_Guru_Team_Setup_Guide.pdf")

INK = colors.HexColor("#1a2233")
MUTED = colors.HexColor("#5b6779")
ACCENT = colors.HexColor("#2f5fd0")
RULE = colors.HexColor("#d4dae6")
CODE_BG = colors.HexColor("#f4f6fa")
WARN_BG = colors.HexColor("#fff6e5")
WARN_BAR = colors.HexColor("#d98b00")
OK_BG = colors.HexColor("#eef7ef")
OK_BAR = colors.HexColor("#3f9350")

ss = getSampleStyleSheet()

H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontName="Helvetica-Bold",
                    fontSize=17, leading=21, textColor=INK, spaceBefore=2, spaceAfter=8)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontName="Helvetica-Bold",
                    fontSize=12.5, leading=16, textColor=INK, spaceBefore=14, spaceAfter=5)
H3 = ParagraphStyle("H3", parent=ss["Heading3"], fontName="Helvetica-Bold",
                    fontSize=10.5, leading=14, textColor=ACCENT, spaceBefore=10, spaceAfter=3)
BODY = ParagraphStyle("BODY", parent=ss["BodyText"], fontName="Helvetica",
                      fontSize=9.5, leading=13.6, textColor=INK, spaceAfter=6, alignment=TA_LEFT)
SMALL = ParagraphStyle("SMALL", parent=BODY, fontSize=8.4, leading=11.6, textColor=MUTED)
CELL = ParagraphStyle("CELL", parent=BODY, fontSize=8.3, leading=11, spaceAfter=0)
CELLB = ParagraphStyle("CELLB", parent=CELL, fontName="Helvetica-Bold")
MONO = ParagraphStyle("MONO", parent=CELL, fontName="Courier", fontSize=7.8, leading=10.5)
CODE = ParagraphStyle("CODE", parent=ss["Code"], fontName="Courier", fontSize=8.2,
                      leading=11.4, textColor=INK, leftIndent=7, spaceBefore=1, spaceAfter=1)


def para(t, style=BODY):
    return Paragraph(t, style)


def code(text):
    """A shaded command block."""
    inner = Preformatted(text.strip("\n"), CODE)
    t = Table([[inner]], colWidths=[168 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, RULE),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def callout(title, body, kind="warn"):
    bg, bar = (WARN_BG, WARN_BAR) if kind == "warn" else (OK_BG, OK_BAR)
    txt = para(f"<b>{title}</b><br/>{body}", ParagraphStyle(
        "CO", parent=BODY, fontSize=8.8, leading=12.4, spaceAfter=0))
    t = Table([[txt]], colWidths=[168 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LINEBEFORE", (0, 0), (0, -1), 2.6, bar),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return t


def keep(*flowables):
    """Keep these together on one page (headings with their content)."""
    return KeepTogether(list(flowables))


def table(rows, widths, header=True, mono_cols=()):
    data = []
    for r_i, row in enumerate(rows):
        cells = []
        for c_i, cell in enumerate(row):
            if r_i == 0 and header:
                cells.append(para(f"<b>{cell}</b>", CELLB))
            else:
                cells.append(para(cell, MONO if c_i in mono_cols else CELL))
        data.append(cells)

    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -2), 0.35, RULE),
        ("BOX", (0, 0), (-1, -1), 0.5, RULE),
    ]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef1f7")),
                  ("LINEBELOW", (0, 0), (-1, 0), 0.7, RULE)]
    t.setStyle(TableStyle(style))
    return t


story = []
A = story.append


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)
    canvas.line(21 * mm, 285 * mm, 189 * mm, 285 * mm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(21 * mm, 288 * mm, "Code Guru - Team Setup Guide")
    canvas.drawRightString(189 * mm, 288 * mm, "R26-SE-036")
    canvas.line(21 * mm, 15 * mm, 189 * mm, 15 * mm)
    canvas.drawString(21 * mm, 10 * mm, "Generated for the Code Guru team")
    canvas.drawRightString(189 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


# ---------------------------------------------------------------- title
A(Spacer(1, 6 * mm))
A(para("Code Guru", ParagraphStyle("T", parent=H1, fontSize=27, leading=31, spaceAfter=1)))
A(para("Team Setup Guide", ParagraphStyle("T2", parent=H1, fontSize=15, leading=19,
                                          textColor=ACCENT, spaceAfter=8)))
A(para("Everything you need to run PairPath and Study Guider on your own machine - "
       "with or without Cloudflare.", SMALL))
A(Spacer(1, 5 * mm))

A(para("1. What you are setting up", H1))
A(para(
    "Code Guru is four services in separate repositories: <b>Code Coach</b>, <b>Study Guider</b>, "
    "<b>PairPath</b> and the <b>Adaptive Gamification Engine</b>. All four are integrated against "
    "the same login.", BODY))
A(para(
    "The one thing to understand before anything else: <b>Code Coach owns login for the entire platform.</b> "
    "It is the only service that checks passwords. Study Guider and PairPath do not have their own accounts - "
    "they receive a token that Code Coach issued and ask Code Coach whether it is valid. "
    "There is a single web login screen, the <b>CodeGuru Portal</b>, which lives in the code-coach repo.", BODY))
A(para(
    "This means <b>you must run Code Coach locally</b>, even if you are only working on Study Guider or "
    "PairPath. Without it, every authenticated route in your service returns 503. The good news is that "
    "Code Coach needs no configuration at all to run locally - see section 5.", BODY))

A(para("Ports", H2))
A(table([
    ["Service", "Port", "Who needs it"],
    ["Code Coach backend", "8000", "Everyone. The identity provider."],
    ["CodeGuru Portal (login UI)", "4200", "Everyone, unless you use your own dev-login page."],
    ["Study Guider backend", "8010", "Study Guider devs."],
    ["Study Guider frontend", "5173", "Study Guider devs."],
    ["PairPath API", "3001", "PairPath devs."],
    ["PairPath frontend", "3000", "PairPath devs."],
    ["PairPath ml-service", "8020", "PairPath devs, only for live pair sessions."],
    ["Gamification API", "3002", "Gamification devs."],
    ["Gamification frontend", "5174", "Gamification devs."],
    ["Gamification ml-service", "8030", "Gamification devs, for difficulty prediction."],
], [58 * mm, 20 * mm, 90 * mm], mono_cols=(1,)))

A(callout("Port 8000 is taken by Code Coach",
          "PairPath's ml-service README says to run it on port 8000. Do not. That is Code Coach's port. "
          "Start the ml-service on <b>8020</b> and make sure <font face='Courier'>ML_SERVICE_URL</font> in "
          "<font face='Courier'>Pair_Path/api/.env</font> points at 8020 - its built-in default is 8000, "
          "which would send ML requests to Code Coach."))

A(para("2. Before you start", H1))
A(para("Check you have these. Versions below are what the team is using.", BODY))
A(table([
    ["Tool", "Check with", "Needed for"],
    ["Node.js 20+", "node --version", "All frontends, PairPath API, the portal"],
    ["Python 3.12+", "python --version", "Code Coach, Study Guider, ml-service"],
    ["Git", "git --version", "Everything"],
    ["Java 17+ (optional)", "java -version", "Only to run Code Coach's VS Code extension"],
], [38 * mm, 45 * mm, 85 * mm], mono_cols=(1,)))

A(para("3. Get the code", H1))
A(para("Clone all three repositories side by side, into one parent folder. "
       "The folder layout matters for nothing technical, but it keeps everyone's paths comparable.", BODY))
A(code("""
mkdir Code_Guru && cd Code_Guru

git clone https://github.com/R26-SE-036/code-coach.git
git clone https://github.com/R26-SE-036/Study-Guider.git
git clone https://github.com/R26-SE-036/Pair_Path.git
git clone https://github.com/R26-SE-036/adaptive-gamification-engine.git
"""))
A(para("Every repo does its work on the <b>dev</b> branch. Never commit to main.", BODY))
A(code("""
cd code-coach    && git checkout dev && git pull && cd ..
cd Study-Guider  && git checkout dev && git pull && cd ..
cd Pair_Path     && git checkout dev && git pull && cd ..
cd adaptive-gamification-engine && git checkout dev && git pull && cd ..
"""))
A(callout("Pulling later",
          "Code Coach changes affect everyone, because it owns the login and the API contract. "
          "Run <font face='Courier'>git pull</font> in <b>code-coach</b> before you start work each day, "
          "not just in your own repo.", kind="ok"))


# ---------------------------------------------------------------- modes
A(para("4. Two ways to run it", H1))
A(para("Pick one. Most of the time you want Mode A.", BODY))
A(table([
    ["", "Mode A - everything on your machine", "Mode B - shared Code Coach via Cloudflare"],
    ["When", "Daily development. Building your own features.",
     "Testing the real integration together, or demoing."],
    ["Code Coach", "You run your own on localhost:8000.",
     "One person runs it and shares a tunnel URL."],
    ["Accounts", "Yours only. Disappear when you restart it.",
     "Shared. Everyone sees the same students and triggers."],
    ["Setup", "No credentials, no accounts, no tunnel.",
     "Tunnel owner needs the Firebase key; you need their URL."],
    ["Cloudflare", "Not needed at all.", "Required."],
], [22 * mm, 73 * mm, 73 * mm]))
A(para(
    "In Mode A, Code Coach falls back to <b>in-memory storage</b> when it finds no Firebase credentials. "
    "That is exactly what you want while building: no setup, no shared state to corrupt, and a clean slate "
    "on every restart. It prints "
    "<font face='Courier'>Storage backend: in-memory</font> at startup so you always know which mode you are in.", BODY))
A(callout("What Mode A costs you",
          "Because storage is in-memory, every account and every remediation trigger is lost when you restart "
          "Code Coach. Re-run the seed tool (section 9) - it takes about ten seconds."))

A(para("5. Code Coach - everyone needs this", H1))
A(para("Backend", H3))
A(code(r"""
cd code-coach/backend

python -m venv .venv
.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt

.\\.venv\\Scripts\\python.exe -m uvicorn app.main:app --port 8000
"""))
A(para("<b>No .env file is required for Mode A.</b> Leave it absent and Code Coach uses in-memory storage. "
       "Confirm the startup line says <font face='Courier'>Storage backend: in-memory</font>. "
       "Then check <font face='Courier'>http://127.0.0.1:8000/health</font> returns "
       "<font face='Courier'>{\"status\":\"ok\"}</font>.", BODY))

A(para("The portal (the login screen)", H3))
A(code("""
cd code-coach/portal

npm install
copy .env.example .env          # macOS/Linux: cp .env.example .env

npm run dev                     # http://localhost:4200
"""))
A(para("File to edit: <font face='Courier'>code-coach/portal/.env</font>", SMALL))
A(table([
    ["Variable", "Mode A (local)", "Mode B (Cloudflare)"],
    ["VITE_CODE_COACH_URL", "http://127.0.0.1:8000", "the shared tunnel URL"],
    ["VITE_ALLOWED_REDIRECTS", "http://localhost:5173,http://localhost:3000", "same"],
    ["VITE_STUDY_GUIDER_URL", "http://localhost:5173", "same"],
    ["VITE_PAIRPATH_URL", "http://localhost:3000", "same"],
    ["VITE_ENABLE_DEV_LOGIN", "true", "true"],
], [48 * mm, 62 * mm, 58 * mm], mono_cols=(0, 1, 2)))
A(callout("VITE_ALLOWED_REDIRECTS is a security control, not a convenience",
          "It is the list of addresses the portal is allowed to hand your login token back to. Without it, "
          "anyone could link you to the portal with their own address and collect your token the moment you "
          "signed in. If the portal says <i>\"That return address is not allowed\"</i>, add your origin to "
          "this list - do not disable the check."))


# ---------------------------------------------------------------- study guider
A(para("6. Study Guider", H1))
A(para("Backend (port 8010)", H3))
A(code(r"""
cd Study-Guider/backend

python -m venv .venv
.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt
copy .env.example .env

.\\.venv\\Scripts\\python.exe -m uvicorn app.main:app --port 8010
"""))
A(para("File to edit: <font face='Courier'>Study-Guider/backend/.env</font>", SMALL))
A(table([
    ["Variable", "Mode A (local)", "Mode B (Cloudflare)", "Required?"],
    ["CODE_COACH_URL", "http://127.0.0.1:8000", "the shared tunnel URL", "Yes"],
    ["CORS_ORIGINS", "leave the default", "leave the default", "Yes"],
    ["NEO4J_URI", "your Neo4j Aura URI", "same", "Only to save quiz progress"],
    ["NEO4J_PASSWORD", "your Neo4j password", "same", "Only to save quiz progress"],
    ["OPENROUTER_API_KEY", "your OpenRouter key", "same", "Only for AI lessons"],
], [40 * mm, 43 * mm, 40 * mm, 45 * mm], mono_cols=(0,)))
A(para(
    "Login and remediation work <b>without</b> Neo4j and without an OpenRouter key. You will see "
    "<font face='Courier'>\"database\": \"Disconnected\"</font> on <font face='Courier'>/api/health</font>, "
    "the Analytics tab will say \"No Data Points Found\", and lessons will use fallback text instead of "
    "AI-generated content. That is fine for building UI. Ask the team for the real values when you need them.", BODY))
A(callout("If the backend crashes instantly with UnicodeEncodeError",
          "This is a known bug: <font face='Courier'>app/services/ml_service.py</font> prints emoji, which the "
          "default Windows console cannot encode. Work around it by setting "
          "<font face='Courier'>PYTHONIOENCODING=utf-8</font> before running "
          "(PowerShell: <font face='Courier'>$env:PYTHONIOENCODING=\"utf-8\"</font>)."))

A(para("Frontend (port 5173)", H3))
A(code("""
cd Study-Guider/frontend

npm install
copy .env.example .env

npm run dev                     # http://localhost:5173
"""))
A(para("File to edit: <font face='Courier'>Study-Guider/frontend/.env</font>", SMALL))
A(table([
    ["Variable", "Mode A (local)", "Mode B (Cloudflare)"],
    ["VITE_API_BASE_URL", "http://127.0.0.1:8010", "http://127.0.0.1:8010 (still local)"],
    ["VITE_CODE_COACH_URL", "http://127.0.0.1:8000", "the shared tunnel URL"],
    ["VITE_PORTAL_URL", "http://localhost:4200", "http://localhost:4200 (run your own)"],
    ["VITE_ENABLE_DEV_LOGIN", "true = own login form; false = use the portal", "same"],
], [45 * mm, 63 * mm, 60 * mm], mono_cols=(0,)))
A(callout("VITE_ENABLE_DEV_LOGIN decides which login you see",
          "Set to <b>true</b>, Study Guider shows its own small login form and never touches the portal - "
          "faster while building. Set to <b>false</b> (or delete the line), it redirects to the portal, which "
          "is the real production flow. If you are testing the portal handoff and nothing happens, this is why. "
          "Vite only reads .env at startup, so restart after changing it.", kind="ok"))


# ---------------------------------------------------------------- pairpath
A(para("7. PairPath", H1))
A(para("PairPath needs a PostgreSQL database. The team uses a free <b>Neon</b> cloud database - "
       "no local install, and it survives reboots. Ask for the connection strings.", BODY))

A(para("API (port 3001)", H3))
A(code("""
cd Pair_Path/api

npm install
copy .env.example .env          # then fill in the values below

npx prisma generate
npx prisma migrate dev          # creates the tables, first time only

npm run start:dev               # http://localhost:3001
"""))
A(para("File to edit: <font face='Courier'>Pair_Path/api/.env</font>", SMALL))
A(table([
    ["Variable", "What to put", "Required?"],
    ["DATABASE_URL", "Neon DIRECT connection string. Used by migrations only.", "Yes"],
    ["DATABASE_URL_POOLED", "Neon POOLED string, plus &amp;pgbouncer=true on the end. Used at runtime.", "Yes"],
    ["JWT_SECRET", "Any long random string. Must be the same for the whole team if you share a database.", "Yes"],
    ["CODE_COACH_URL", "Mode A: http://127.0.0.1:8000  /  Mode B: the tunnel URL", "Yes"],
    ["ML_SERVICE_URL", "http://127.0.0.1:8020  (NOT 8000 - that is Code Coach)", "Live sessions only"],
    ["MONGODB_URI", "Leave blank. Logs an error and continues.", "No"],
    ["REDIS_URL", "Leave blank. Falls back to an in-memory store.", "No"],
], [42 * mm, 100 * mm, 26 * mm], mono_cols=(0,)))
A(callout("Do not change the Prisma versions",
          "<font face='Courier'>prisma</font> and <font face='Courier'>@prisma/client</font> must both stay on "
          "<b>5.22.x</b>. If npm upgrades them, the API dies at startup with "
          "<font face='Courier'>Cannot find module '@prisma/client/runtime/library.js'</font>. "
          "Fix: set both back to ^5.22.0 in package.json, delete node_modules/@prisma, "
          "then <font face='Courier'>npm install &amp;&amp; npx prisma generate</font>."))

A(para("Frontend (port 3000)", H3))
A(code("""
cd Pair_Path/frontend

npm install
copy .env.local.example .env.local

npm run dev                     # http://localhost:3000
"""))
A(para("File to edit: <font face='Courier'>Pair_Path/frontend/.env.local</font>", SMALL))
A(table([
    ["Variable", "Mode A (local)", "Mode B (Cloudflare)"],
    ["NEXT_PUBLIC_CODE_COACH_URL", "http://127.0.0.1:8000", "the shared tunnel URL"],
    ["NEXT_PUBLIC_PORTAL_URL", "http://localhost:4200", "http://localhost:4200"],
    ["NEXT_PUBLIC_ENABLE_DEV_LOGIN", "true = own login form; unset = use the portal", "same"],
], [56 * mm, 56 * mm, 56 * mm], mono_cols=(0,)))
A(callout("The filename must start with a dot",
          "Next.js reads <font face='Courier'>.env.local</font>. A file named "
          "<font face='Courier'>env.local</font> without the leading dot is silently ignored - your settings "
          "will look applied and will not be. This has already caught someone on this team."))

A(para("ml-service (port 8020) - only for live pair sessions", H3))
A(code(r"""
cd Pair_Path/ml-service

python -m venv .venv
.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt

.\\.venv\\Scripts\\python.exe -m uvicorn app.main:app --port 8020
"""))
A(para("You do not need this for login, the dashboard, or session history. Start it only when you are "
       "testing the live collaboration features that call the ML model.", SMALL))


# ---------------------------------------------------------------- running
A(para("8. Adaptive Gamification Engine", H1))
A(para("Three parts: an Express API backed by MongoDB, a React frontend, and a Flask service that "
       "predicts game difficulty with a Random Forest. It has no accounts of its own - it verifies "
       "every request against Code Coach and reads the student's struggle data from there.", BODY))

A(para("Backend API (port 3002)", H3))
A(code("""
cd adaptive-gamification-engine/backend

npm install
copy .env.example .env

npm start                       # http://localhost:3002
"""))
A(para("File to edit: <font face='Courier'>adaptive-gamification-engine/backend/.env</font>", SMALL))
A(table([
    ["Variable", "Mode A (local)", "Mode B (Cloudflare)", "Required?"],
    ["CODE_COACH_URL", "http://127.0.0.1:8000", "the shared tunnel URL", "Yes"],
    ["PORT", "3002", "3002", "Yes"],
    ["MONGODB_URI", "mongodb://localhost:27017/code-guru", "same", "Yes - games and questions"],
    ["ML_SERVICE_URL", "http://127.0.0.1:8030", "same", "Difficulty prediction only"],
    ["CORS_ORIGINS", "leave the default", "leave the default", "Yes"],
], [40 * mm, 45 * mm, 38 * mm, 45 * mm], mono_cols=(0,)))
A(callout("There is deliberately no JWT_SECRET here",
          "This service does not issue or verify tokens itself - Code Coach does, via "
          "<font face='Courier'>GET /api/v1/auth/me</font>. An earlier version verified signatures "
          "locally with a shared secret, which meant signing out of Code Coach did nothing here. "
          "If you find code reaching for a signing secret, it is a leftover.", kind="ok"))
A(para("MongoDB is genuinely required for this service - unlike the others, its own data (question "
       "bank, game sessions, player profiles) lives there. Without it the API starts but the game "
       "routes fail. The dashboard still works, because struggle data comes from Code Coach.", BODY))

A(para("Frontend (port 5174)", H3))
A(code("""
cd adaptive-gamification-engine/frontend

npm install
copy .env.example .env

npm run dev                     # http://localhost:5174
"""))
A(para("File to edit: <font face='Courier'>adaptive-gamification-engine/frontend/.env</font>", SMALL))
A(table([
    ["Variable", "Mode A (local)", "Mode B (Cloudflare)"],
    ["VITE_CODE_COACH_ORIGIN", "http://127.0.0.1:8000", "the shared tunnel URL"],
    ["VITE_GAMIFICATION_API_URL", "http://localhost:3002/api/v1", "same"],
    ["VITE_PORTAL_URL", "http://localhost:4200", "http://localhost:4200"],
    ["VITE_ENABLE_DEV_LOGIN", "true = own login form; false = use the portal", "same"],
], [50 * mm, 60 * mm, 58 * mm], mono_cols=(0,)))
A(para("The frontend reaches Code Coach through a Vite proxy rather than calling it directly, so the "
       "browser stays same-origin and CORS never applies. "
       "<font face='Courier'>VITE_CODE_COACH_ORIGIN</font> is where that proxy forwards to - change "
       "that one, not the API path below it.", SMALL))

A(para("ml-service (port 8030)", H3))
A(code(r"""
cd adaptive-gamification-engine/ml-service

python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

.\.venv\Scripts\python.exe app.py          # http://localhost:8030
"""))
A(para("Optional. If it is down the backend falls back to a simple rule (many unresolved errors or a "
       "low average score means an easier game), so the engine keeps working.", SMALL))

A(para("9. Running it day to day", H1))
A(para("Open a terminal per service and start them in this order. Code Coach must be first - "
       "the others verify tokens against it.", BODY))
A(para("Study Guider developers", H3))
A(table([
    ["#", "Terminal", "Command"],
    ["1", "code-coach/backend", ".venv\\Scripts\\python.exe -m uvicorn app.main:app --port 8000"],
    ["2", "code-coach/portal", "npm run dev"],
    ["3", "Study-Guider/backend", ".venv\\Scripts\\python.exe -m uvicorn app.main:app --port 8010"],
    ["4", "Study-Guider/frontend", "npm run dev"],
], [8 * mm, 45 * mm, 115 * mm], mono_cols=(2,)))
A(para("PairPath developers", H3))
A(table([
    ["#", "Terminal", "Command"],
    ["1", "code-coach/backend", ".venv\\Scripts\\python.exe -m uvicorn app.main:app --port 8000"],
    ["2", "code-coach/portal", "npm run dev"],
    ["3", "Pair_Path/api", "npm run start:dev"],
    ["4", "Pair_Path/frontend", "npm run dev"],
    ["5", "Pair_Path/ml-service", ".venv\\Scripts\\python.exe -m uvicorn app.main:app --port 8020"],
], [8 * mm, 45 * mm, 115 * mm], mono_cols=(2,)))
A(para("If you set the dev-login flag to true in your frontend, you can skip terminal 2 (the portal) entirely.", SMALL))

A(para("Gamification developers", H3))
A(table([
    ["#", "Terminal", "Command"],
    ["1", "code-coach/backend", r".venv\Scripts\python.exe -m uvicorn app.main:app --port 8000"],
    ["2", "code-coach/portal", "npm run dev"],
    ["3", "adaptive-gamification-engine/backend", "npm start"],
    ["4", "adaptive-gamification-engine/frontend", "npm run dev"],
    ["5", "adaptive-gamification-engine/ml-service", r".venv\Scripts\python.exe app.py"],
], [8 * mm, 52 * mm, 108 * mm], mono_cols=(2,)))
A(para("MongoDB must also be running for the game routes.", SMALL))

A(para("Mode B only - the Cloudflare tunnel", H3))
A(para("One person runs Code Coach and exposes it. Everyone else points their "
       "<font face='Courier'>CODE_COACH_URL</font> at the printed address.", BODY))
A(code("""
cloudflared tunnel --url http://localhost:8000
"""))
A(table([
    ["Who", "What they do"],
    ["Tunnel owner", "Runs Code Coach with the Firebase key configured (so data persists and is shared). "
                     "Adds everyone's browser origins to CORS_ALLOWED_ORIGINS in code-coach/backend/.env."],
    ["Everyone else", "Puts the tunnel URL in CODE_COACH_URL, VITE_CODE_COACH_URL and "
                      "NEXT_PUBLIC_CODE_COACH_URL, then restarts their dev servers."],
], [30 * mm, 138 * mm]))
A(callout("The tunnel URL changes every restart",
          "Cloudflare quick tunnels get a new hostname each time. When the tunnel owner restarts, everyone "
          "must update their .env files and restart their dev servers. This is why no URL is hardcoded "
          "anywhere in the codebase."))

A(para("10. Getting test data", H1))
A(para("Study Guider shows nothing until Code Coach has raised a remediation trigger, and that only happens "
       "after the same mistake repeats three times. Rather than doing that by hand, run the seed tool:", BODY))
A(code(r"""
cd code-coach/backend
.\\.venv\\Scripts\\python.exe -m app.dev_tools.seed_student

# Mode B - seed against the shared backend instead:
.\\.venv\\Scripts\\python.exe -m app.dev_tools.seed_student --base-url https://<tunnel-url>
"""))
A(para("It creates a student, generates three real struggles (array indexing, loop boundaries, conditional "
       "logic), and prints an access token you can paste into curl or Postman. Sign in as "
       "<font face='Courier'>seed.student@example.com / seed-student-1234</font>. "
       "Running it twice is safe - it reuses the account and creates no duplicates.", BODY))


# ---------------------------------------------------------------- verify + troubleshooting
A(para("11. Check it actually works", H1))
A(table([
    ["#", "Do this", "You should see"],
    ["1", "Open http://127.0.0.1:8000/health", "{\"status\":\"ok\"}"],
    ["2", "Open http://localhost:4200", "The Code Guru login screen"],
    ["3", "Register a new account there", "You land on the hub page"],
    ["4", "Click through to your service", "You arrive already signed in - no second login"],
    ["5", "Check the address bar", "No access_token left in the URL"],
    ["6", "Run the seed tool, reload Study Guider", "Three struggle cards with real concept names"],
], [8 * mm, 78 * mm, 82 * mm]))

A(para("12. Troubleshooting", H1))
A(para("Every one of these has actually happened to someone on this team.", SMALL))
A(table([
    ["Symptom", "Cause", "Fix"],
    ["Your service returns 503 on every route",
     "Code Coach is not running.",
     "Start it on port 8000. Everything needs it."],
    ["Portal says \"That return address is not allowed\"",
     "Your origin is missing from the allow-list.",
     "Add it to VITE_ALLOWED_REDIRECTS in code-coach/portal/.env, restart."],
    ["Study Guider shows its own login, not the portal",
     "VITE_ENABLE_DEV_LOGIN is true.",
     "Set it to false in Study-Guider/frontend/.env and restart Vite."],
    ["PairPath: \"PairPath is not responding\"",
     "The PairPath API on 3001 is not running.",
     "Start it. Your login is fine - click Try again after."],
    ["PairPath .env.local seems to be ignored",
     "The file is named env.local without the dot.",
     "Rename it to .env.local and restart."],
    ["Cannot find module '@prisma/client/runtime/library.js'",
     "prisma and @prisma/client are on different majors.",
     "Pin both to ^5.22.0, delete node_modules/@prisma, npm install, npx prisma generate."],
    ["UnicodeEncodeError on Study Guider startup",
     "Emoji in print() vs the Windows console encoding.",
     "Set PYTHONIOENCODING=utf-8 before running."],
    ["uvicorn.exe: \"Fatal error in launcher\"",
     "The venv was created before the folder moved. Venvs are not relocatable.",
     "Delete .venv, recreate it, reinstall requirements. Or use python -m uvicorn."],
    ["VS Code extension: no yellow underlines, no error",
     "You are signed out. Auto-analysis fails silently by design.",
     "Ctrl+Shift+P, \"Code Coach: Sign In\"."],
    ["ML requests behave strangely in PairPath",
     "ml-service is on 8000, colliding with Code Coach.",
     "Run it on 8020 and set ML_SERVICE_URL to match."],
    ["Gamification dashboard is empty for a student who has struggles",
     "No triggers yet, or you are signed in as a different student.",
     "Run the seed tool (section 10) and sign in as that student."],
    ["Gamification game routes fail but the dashboard works",
     "MongoDB is down. Only this service truly needs it.",
     "Start MongoDB on 27017."],
    ["Gamification API returns 503 on every route",
     "It cannot reach Code Coach to verify your token.",
     "Check CODE_COACH_URL and that Code Coach is running. 503 means unreachable, 401 means the token was refused."],
], [46 * mm, 58 * mm, 64 * mm]))

A(keep(para("13. Rules of the road", H1), table([
    ["Rule", "Why"],
    ["Work on the dev branch. Never commit to main.",
     "main is the reviewed branch. All three repos follow this."],
    ["Never commit a .env file.",
     "They hold database passwords and API keys. Every repo already gitignores them - keep it that way."],
    ["Do not edit codeguru-auth.js in your own repo.",
     "It is a copy. The master lives in code-coach/portal/src/lib/. Change it there and run "
     "code-coach/sync-codeguru-auth.sh, or the three services drift apart."],
    ["Never read the student id from a request body.",
     "It comes from the bearer token. Trusting the body lets anyone read anyone else's data - "
     "Study Guider had exactly this bug before integration."],
    ["Pull code-coach before you start work.",
     "It owns the login and the API contract, so its changes affect everyone."],
], [62 * mm, 106 * mm])))

A(Spacer(1, 4 * mm))
A(para("Full API reference: <font face='Courier'>code-coach/integration/README.md</font> and "
       "<font face='Courier'>API_CONTRACT.md</font> in the same folder, which is generated from the running "
       "service and therefore cannot drift from the code.", SMALL))

doc = BaseDocTemplate(OUT, pagesize=A4,
                      leftMargin=21 * mm, rightMargin=21 * mm,
                      topMargin=23 * mm, bottomMargin=20 * mm,
                      title="Code Guru - Team Setup Guide", author="R26-SE-036")
frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="n")
doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=header_footer)])
doc.build(story)
print("WROTE", OUT)
