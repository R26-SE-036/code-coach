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
A(para("How to get all four services running on your own machine, now that they share one "
       "login, one set of student data and one interface.", SMALL))
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
A(para(
    "<b>Every student record now lives in Code Coach.</b> Its shared deployment stores accounts, "
    "sessions, diagnostics and remediation triggers in <b>MongoDB</b>. Your service still owns its own "
    "domain data - PairPath its pair sessions in Postgres, the Gamification Engine its questions and game "
    "sessions in MongoDB, Study Guider its quiz history in Neo4j - but none of them owns <i>who the "
    "student is</i> any more.", BODY))

A(callout("Your old login no longer works",
          "PairPath used to keep its own passwords, the Gamification Engine had its own user table, and "
          "Study Guider had a student id hardcoded in App.jsx. All three are gone. Whatever credentials "
          "you were testing with before will now be rejected, and that is correct behaviour, not a bug."
          "<br/><br/>"
          "Register once through the portal at <font face='Courier'>http://localhost:4200</font> and use "
          "that account everywhere. One account, all four services."))

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
    ["Gamification ml-service", "5000", "Gamification devs, for difficulty prediction."],
    ["VS Code sign-in callback", "53682", "Nothing to start. The extension opens it briefly."],
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
A(para(
    "You already have your own repository. What is new is that <b>everyone also needs code-coach</b> - "
    "it is the identity provider, so nothing in your service authenticates without it running.", BODY))
A(table([
    ["You are the...", "Already have", "Also need to clone"],
    ["Study Guider dev", "Study-Guider", "code-coach"],
    ["PairPath dev", "Pair_Path", "code-coach"],
    ["Gamification dev", "adaptive-gamification-engine", "code-coach"],
], [38 * mm, 62 * mm, 68 * mm]))
A(para(
    "You have write access to your own repository only, which is all you need - nobody is expected to "
    "push to a service they do not own. code-coach is cloned to <b>run</b>, not to change. If you find a "
    "bug in it, tell the Code Coach developer rather than opening a branch there.", BODY))
A(code("""
# Put code-coach beside your existing repo, in the same parent folder.
cd <the folder that already contains your repo>

git clone https://github.com/R26-SE-036/code-coach.git
"""))
A(para("Then bring your own repo up to date. Every repo does its work on the <b>dev</b> branch - "
       "never commit to main.", BODY))
A(code("""
cd <your repo>   && git checkout dev && git pull && cd ..
cd code-coach    && git checkout dev && git pull && cd ..
"""))

A(para("Your .env files come separately, by message", H2))
A(para(
    "A <font face='Courier'>.env</font> is gitignored in every repo, so pulling never brings one and "
    "never overwrites one. That is deliberate: they hold real database URLs and API keys. It also means "
    "the integration settings your service now needs <b>cannot reach you through git</b>.", BODY))
A(para(
    "You will be sent the merged .env files privately. They are your original settings - your own "
    "database, your own API keys, unchanged - <b>plus</b> the handful of keys integration added. "
    "Replace your existing files with them.", BODY))
A(callout("Read this before you replace anything",
          "The files you are sent were merged from the .env you gave us, so nothing of yours was dropped. "
          "But keep a copy of your current .env anyway - takes two seconds, and if a value did get lost in "
          "transit you will want it back rather than regenerated."
          "<br/><br/>"
          "Do NOT copy <font face='Courier'>.env.example</font> over a real .env. The examples carry "
          "placeholder values, and overwriting a .env with one destroys credentials that exist nowhere "
          "else."))
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
    ["Accounts", "Yours only, in memory. Gone when you restart it.",
     "Shared, in MongoDB. Everyone sees the same students and triggers."],
    ["Setup", "No credentials, no accounts, no tunnel.",
     "Tunnel owner needs the database URI; you need their URL."],
    ["Cloudflare", "Not needed at all.", "Required."],
], [22 * mm, 73 * mm, 73 * mm]))
A(para(
    "In Mode A, Code Coach falls back to <b>in-memory storage</b> when it finds no database URI. "
    "That is exactly what you want while building: no setup, no shared state to corrupt, and a clean slate "
    "on every restart. It prints "
    "<font face='Courier'>Storage backend: in-memory</font> at startup so you always know which mode you are in.", BODY))
A(callout("What Mode A costs you",
          "Because storage is in-memory, every account and every remediation trigger is lost when you restart "
          "Code Coach - including the account you registered in the portal. Register again, or re-run the "
          "seed tool (section 14), which takes about ten seconds."
          "<br/><br/>"
          "This is also why your teammates cannot see your test data in Mode A, and why the numbers on Home "
          "start at zero every morning. If you want data that persists and is shared, that is Mode B."))

A(callout("Already have a .env? Do NOT copy over it",
          "Every service in this project keeps a <font face='Courier'>.env</font> that is gitignored, "
          "so it never travels with the code - it holds real database URLs and API keys that only "
          "exist on your machine. <b>Copying .env.example over it destroys those values.</b> "
          "<br/><br/>"
          "If you already have a .env: open the .env.example beside it and ADD only the keys you are "
          "missing. The examples are written as supersets - they list the original settings as well "
          "as the ones integration added - so a key-by-key comparison is all it takes. Copy the whole "
          "file only when there is no .env there at all."))

A(para("5. Code Coach - everyone needs this", H1))
A(para("Backend", H3))
A(code(r"""
cd code-coach/backend

python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
"""))
A(para("<b>No .env file is required for Mode A.</b> Leave it absent and Code Coach uses in-memory storage. "
       "Confirm the startup line says <font face='Courier'>Storage backend: in-memory</font>. "
       "Then check <font face='Courier'>http://127.0.0.1:8000/health</font> returns "
       "<font face='Courier'>{\"status\":\"ok\"}</font>.", BODY))

A(para("The portal (the login screen)", H3))
A(code("""
cd code-coach/portal

npm install
copy .env.example .env          # ONLY if you have no .env yet - see section 3

npm run dev                     # http://localhost:4200
"""))
A(para("File to edit: <font face='Courier'>code-coach/portal/.env</font>", SMALL))
A(table([
    ["Variable", "Mode A (local)", "Mode B (Cloudflare)"],
    ["VITE_CODE_COACH_URL", "http://127.0.0.1:8000", "the shared tunnel URL"],
    ["VITE_ALLOWED_REDIRECTS", "http://localhost:5173,http://localhost:3000,http://localhost:5174", "same"],
    ["VITE_STUDY_GUIDER_URL", "http://localhost:5173", "same"],
    ["VITE_PAIRPATH_URL", "http://localhost:3000", "same"],
    ["VITE_GAMIFICATION_URL", "http://localhost:5174", "same"],
    ["VITE_ENABLE_DEV_LOGIN", "true", "true"],
    ["VITE_VSCODE_LOOPBACK_PORT", "53682", "same"],
], [48 * mm, 62 * mm, 58 * mm], mono_cols=(0, 1, 2)))
A(para(
    "<font face='Courier'>VITE_ALLOWED_REDIRECTS</font> must also contain "
    "<font face='Courier'>http://127.0.0.1:53682</font>, which is where the VS Code extension listens "
    "while you sign in through the browser. It is a fixed port precisely because this list is checked by "
    "exact origin - a random port could never be allowed.", SMALL))
A(callout("Adding a new service? It needs TWO entries here",
          "A service missing from <font face='Courier'>VITE_ALLOWED_REDIRECTS</font> is refused at "
          "sign-in with <i>\"That return address is not allowed\"</i>, and one missing its "
          "<font face='Courier'>VITE_*_URL</font> simply never appears on the hub - so there is no "
          "link to click and no error explaining why. Both were missed when the Gamification Engine "
          "was added.", kind="ok"))

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
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env          # ONLY if you have no .env yet - see section 3

.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8010
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
copy .env.example .env          # ONLY if you have no .env yet - see section 3

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
copy .env.example .env          # ONLY if you have no .env yet - see section 3

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
copy .env.local.example .env.local   # ONLY if you have no .env.local yet

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
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8020
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
copy .env.example .env          # ONLY if you have no .env yet - see section 3

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
copy .env.example .env          # ONLY if you have no .env yet - see section 3

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

A(para("ml-service (port 5000)", H3))
A(code(r"""
cd adaptive-gamification-engine/ml-service

python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

.\.venv\Scripts\python.exe app.py          # http://localhost:5000
"""))
A(para("If it is down the backend falls back to a simple rule (many unresolved errors or a low average "
       "score means an easier game), so the engine keeps working - but the difficulty you see is then a "
       "hand-written if/else, not the Random Forest. The response carries "
       "<font face='Courier'>fallback: true</font> when that happens.", SMALL))

# ------------------------------------------------- what your service asks for
A(para("9. What your service asks Code Coach for", H1))
A(para(
    "These are the calls your code already makes. You do not have to wire them up - they are in place - "
    "but you should know what they are for, because breaking one shows up as a blank screen rather than "
    "an error.", BODY))
A(para(
    "All of them take <font face='Courier'>Authorization: Bearer &lt;the student's access token&gt;</font>. "
    "The <font face='Courier'>me</font> in each path means <i>the student this token belongs to</i> - "
    "there is no student id in any URL or body, and that is deliberate. Study Guider used to read the "
    "student id out of the request body, which let anyone read anyone else's progress by typing a "
    "different id.", BODY))

A(para("Study Guider", H3))
A(table([
    ["Call", "What it is for"],
    ["GET /api/v1/auth/me",
     "Verify the caller and learn who they are. Runs on every authenticated route, cached ~60s."],
    ["GET /api/v1/remediation/me/recommendations",
     "The trigger cards on the home screen: concepts Code Coach watched the student get wrong "
     "repeatedly, already shaped into lesson + quiz + rationale."],
    ["GET /api/v1/remediation/me/triggers",
     "The raw trigger list behind those recommendations."],
    ["POST /api/v1/remediation/me/triggers/{id}/lesson-opened",
     "Fired when a micro-lesson is opened. Moves the trigger off pending."],
    ["POST /api/v1/remediation/me/triggers/{id}/quiz-completed",
     "Fired with {quiz_id, score_percent}. 70% or more closes the trigger - this is what completes "
     "the remediation loop."],
    ["GET /api/v1/dashboard/me/overview",
     "The Analytics tab: counts, mastery, concept trends and recent activity across all four services."],
    ["GET /api/v1/dashboard/me/timeline",
     "A longer activity history than the overview carries."],
], [70 * mm, 98 * mm], mono_cols=(0,)))

A(para("Adaptive Gamification Engine", H3))
A(table([
    ["Call", "What it is for"],
    ["GET /api/v1/auth/me",
     "Verify the caller. Every route in the Express API goes through this."],
    ["GET /api/v1/students/me/struggling-concepts",
     "Which concepts to build a game around. This is the real diagnostic history - it replaced a local "
     "Mongo mirror that was only ever filled by a seed script."],
    ["GET /api/v1/gamification/me/recommendations",
     "What practice Code Coach suggests next, including the game type."],
    ["POST /api/v1/gamification/me/adaptation-decisions",
     "Reports the difficulty the engine chose and why, so the decision is on the student's record."],
    ["POST /api/v1/gamification/me/session-results",
     "Reports the finished game - score, concept, difficulty actually played. This is what feeds the "
     "student's mastery and makes the game count for something."],
    ["POST /api/v1/learning-sessions",
     "Opens a learning session so activity can be grouped over time."],
], [70 * mm, 98 * mm], mono_cols=(0,)))

A(para("PairPath", H3))
A(table([
    ["Call", "What it is for"],
    ["GET /api/v1/auth/me",
     "Called inside POST /auth/exchange to verify the platform token before issuing a PairPath one. "
     "Fails closed: an unverifiable token is refused, never waved through."],
    ["POST /api/v1/auth/login, /register",
     "The older password proxy. Still present only because the seeded demo pair has no Code Coach "
     "account. Not part of the normal sign-in path any more."],
], [70 * mm, 98 * mm], mono_cols=(0,)))

A(callout("503 and 401 mean different things",
          "<b>401</b> - Code Coach answered and refused the token. The student needs to sign in again. "
          "<b>503</b> - Code Coach could not be reached at all. The student's login is fine; your service "
          "just cannot check it. Do not clear the session on a 503, or an outage logs everyone out."))


# ------------------------------------------------- pairpath identity
A(para("10. PairPath keeps its own user rows - here is why", H1))
A(para(
    "This section is mainly for the PairPath developer, but it explains the one place where the platform "
    "deliberately does <i>not</i> use Code Coach's id directly.", BODY))
A(para(
    "Every other service can simply carry the Code Coach access token around. PairPath cannot, for two "
    "concrete reasons:", BODY))
A(table([
    ["What", "Why it forces a local id"],
    ["Foreign keys",
     "Every row in PairPath's Postgres - pair sessions, session members, peer reviews, ML events - "
     "points at users.id. Swapping in a foreign id would orphan the lot."],
    ["The Socket.IO handshake",
     "It verifies PairPath's own JWT signature. It cannot validate a token Code Coach signed, and "
     "changing that is how you break live pair sessions."],
], [38 * mm, 130 * mm]))

A(para("So PairPath exchanges rather than adopts", H3))
A(para(
    "<font face='Courier'>POST /auth/exchange</font> takes the Code Coach access token, verifies it with "
    "<font face='Courier'>GET /api/v1/auth/me</font>, then finds or creates the matching local row and "
    "issues <b>PairPath's own JWT</b>. Matching order matters:", BODY))
A(table([
    ["#", "Match on", "Outcome"],
    ["1", "users.codeCoachUserId", "Already linked. Reuse the row - all its history stays attached."],
    ["2", "users.email", "The account existed locally before integration. Link it by writing "
                         "codeCoachUserId, rather than creating a duplicate."],
    ["3", "nothing matched", "First time here. Create the row and link it."],
], [8 * mm, 42 * mm, 118 * mm], mono_cols=(1,)))

A(para("Two tokens live in the browser, and they are not interchangeable", H3))
A(table([
    ["localStorage key", "Whose token", "Used by"],
    ["token", "PairPath's own JWT",
     "Every call to the PairPath API, and the Socket.IO handshake. This is the one that matters "
     "inside PairPath."],
    ["codeguru.accessToken", "Code Coach's platform token",
     "Kept so PairPath can call Code Coach on the student's behalf. Sending it to PairPath's own API "
     "will be rejected - and there is a test asserting that."],
], [40 * mm, 42 * mm, 86 * mm], mono_cols=(0,)))

A(callout("Do not 'simplify' this by deleting the local user table",
          "It looks like duplication and it is not. <font face='Courier'>users.codeCoachUserId</font> is "
          "the join between the platform identity and PairPath's data; drop it, rename it, or point a "
          "foreign key at the Code Coach id instead, and every existing session, review and ML event "
          "loses its owner."))


# ------------------------------------------------- the shared UI
A(para("11. The shared interface", H1))
A(para(
    "The four services used to look like four products - one was light with a purple accent and pastel "
    "backgrounds, the other three were dark, in two different typefaces. They now share one light "
    "blue-and-white theme and one navigation bar.", BODY))

A(para("Where you start", H3))
A(para(
    "<font face='Courier'>http://localhost:4200</font> is the whole platform's front door. Sign in there "
    "and you land on <b>Home</b>: a card per service, each showing a live number pulled from Code Coach "
    "(diagnostics, open remediations, pair sessions, games played), and a recent-activity feed showing "
    "which service did what. If the numbers are all zero you have a working setup and no data yet - "
    "run the seed tool in section 14.", BODY))

A(para("The bar at the top of every service", H3))
A(para(
    "Same bar, same position, in all four apps. Its links are the supported way to move between "
    "services, because the four run on four different origins and a plain link would arrive with no "
    "session. Each link goes through "
    "<font face='Courier'>{portal}/go?to=&lt;service&gt;</font>, which hands the token over on the way.", BODY))
A(callout("Moving between services by typing the URL will look broken",
          "Typing <font face='Courier'>localhost:3000</font> straight into the address bar takes you to "
          "PairPath with no session, so it bounces you to the portal to sign in again. That is not a bug - "
          "browsers keep localStorage per origin. Use the bar.", kind="ok"))

A(para("Changing how it looks", H3))
A(table([
    ["File", "What it controls"],
    ["portal/src/styles/codeguru-theme.css",
     "MASTER copy. Every colour, radius, shadow, easing and font for all four services, plus the bar's "
     "own styling."],
    ["<your repo>/src/styles/codeguru-theme.css",
     "A copy. Editing it changes only your service and puts you out of step with everyone else."],
], [66 * mm, 102 * mm], mono_cols=(0,)))
A(para(
    "Colours are exposed twice: <font face='Courier'>--cg-rgb-*</font> holds raw 'R G B' triplets (which "
    "is what lets PairPath's Tailwind keep working with opacity modifiers like "
    "<font face='Courier'>bg-surface-800/50</font>), and <font face='Courier'>--cg-*</font> holds "
    "ready-made colours for stylesheets and inline styles. Use the token, never a hex code.", BODY))
A(callout("var() does not work everywhere",
          "It does not resolve inside SVG presentation attributes. "
          "<font face='Courier'>stroke=\"var(--cg-accent)\"</font> on a Recharts series or a lucide icon "
          "renders with no colour at all. Set CSS <font face='Courier'>color</font> and let "
          "<font face='Courier'>currentColor</font> do the work, or resolve the token in JS first - "
          "Study Guider's <font face='Courier'>src/lib/theme.js</font> does exactly that for its charts. "
          "The same applies to anything that draws its own SVG, like Mermaid and Monaco."))
A(para(
    "Dark mode is not built yet. <font face='Courier'>:root[data-theme='dark']</font> in the theme file "
    "is deliberately empty - because everything reaches colour through these tokens, filling it in is a "
    "values-only change plus a toggle in the bar. No component needs to be touched.", SMALL))

A(para("Signing in to the VS Code extension", H3))
A(para(
    "Code Coach's extension no longer asks for a password in a VS Code prompt. Sign In opens the portal "
    "in your browser; when you finish, the extension picks the session up automatically over a loopback "
    "callback on port 53682. If that port is busy it says so and falls back to the old prompts.", BODY))


# ------------------------------------------------- do not touch
A(para("12. What not to touch", H1))
A(para(
    "None of these are style preferences. Each one has a specific failure attached, and most of them "
    "fail quietly - a blank panel, a wrong name, a silent 401 - rather than throwing something you "
    "would notice.", BODY))
A(table([
    ["Leave alone", "What breaks if you change it"],
    ["The wire field names in codeguru-auth.js: identifier, password, client_name, full_name, email",
     "They are the Code Coach API contract, not a naming style. Renaming any of them to camelCase makes "
     "the request fail validation."],
    ["codeguru-auth.js itself, in your repo",
     "It is a copy. The master is in code-coach/portal/src/lib/. Edit it there and run "
     "sync-codeguru-auth.sh, or the four services drift apart."],
    ["codeguru-theme.css and CodeGuruBar in your repo",
     "Also copies, synced by sync-codeguru-shared.sh. Change one and your service stops matching "
     "the others."],
    ["The codeguru.* localStorage keys",
     "The portal hands a session over by writing exactly those keys. Rename one and the handoff "
     "silently writes past your app - it will look like login simply did nothing."],
    ["VITE_ALLOWED_REDIRECTS - never add a wildcard",
     "It is the list of addresses the portal may hand a token to. Without it the portal is an open "
     "redirect that gives anyone's token to any URL that asks."],
    ["The ports in the table in section 1",
     "They were chosen to stop collisions that already happened: the Gamification API was on 3000 "
     "(PairPath's frontend) and Study Guider's backend on 8000 (Code Coach)."],
    ["users.codeCoachUserId in PairPath's schema",
     "The join between platform identity and PairPath's own data. See section 10."],
    ["Reading a student id from a request body or URL",
     "It comes from the bearer token. Anything else lets one student read another's data."],
    ["Clearing the session on a 503",
     "503 means Code Coach was unreachable, not that the token was bad. Clearing it logs everyone out "
     "over a blip."],
], [64 * mm, 104 * mm]))


A(para("13. Running it day to day", H1))
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
    ["5", "adaptive-gamification-engine/ml-service", r".venv\Scripts\python.exe app.py   # port 5000"],
], [8 * mm, 52 * mm, 108 * mm], mono_cols=(2,)))
A(para("This service needs its MongoDB Atlas cluster reachable for the game routes.", SMALL))

A(para("Mode B only - the Cloudflare tunnel", H3))
A(para("One person runs Code Coach and exposes it. Everyone else points their "
       "<font face='Courier'>CODE_COACH_URL</font> at the printed address.", BODY))
A(code("""
cloudflared tunnel --url http://localhost:8000
"""))
A(table([
    ["Who", "What they do"],
    ["Tunnel owner", "Runs Code Coach with MONGODB_URI configured (so data persists and is shared). "
                     "Adds everyone's browser origins to CORS_ALLOWED_ORIGINS in code-coach/backend/.env."],
    ["Everyone else", "Puts the tunnel URL in CODE_COACH_URL, VITE_CODE_COACH_URL and "
                      "NEXT_PUBLIC_CODE_COACH_URL, then restarts their dev servers."],
], [30 * mm, 138 * mm]))
A(callout("The tunnel URL changes every restart",
          "Cloudflare quick tunnels get a new hostname each time. When the tunnel owner restarts, everyone "
          "must update their .env files and restart their dev servers. This is why no URL is hardcoded "
          "anywhere in the codebase."))

A(para("14. Getting test data", H1))
A(para("Study Guider shows nothing until Code Coach has raised a remediation trigger, and that only happens "
       "after the same mistake repeats three times. Rather than doing that by hand, run the seed tool:", BODY))
A(code(r"""
cd code-coach/backend
.\.venv\Scripts\python.exe -m app.dev_tools.seed_student

# Mode B - seed against the shared backend instead:
.\.venv\Scripts\python.exe -m app.dev_tools.seed_student --base-url https://<tunnel-url>
"""))
A(para("It creates a student, generates three real struggles (array indexing, loop boundaries, conditional "
       "logic), and prints an access token you can paste into curl or Postman. Sign in as "
       "<font face='Courier'>seed.student@example.com / seed-student-1234</font>. "
       "Running it twice is safe - it reuses the account and creates no duplicates.", BODY))


# ---------------------------------------------------------------- verify + troubleshooting
A(para("15. Check it actually works", H1))
A(table([
    ["#", "Do this", "You should see"],
    ["1", "Open http://127.0.0.1:8000/health", "{\"status\":\"ok\"}"],
    ["2", "Open http://localhost:4200", "The Code Guru sign-in screen, blue on white"],
    ["3", "Register a new account there", "Home, with a card per service and a bar across the top"],
    ["4", "Use the bar to open your service", "You arrive already signed in - no second login"],
    ["5", "Check the address bar after arriving", "No access_token left in the URL"],
    ["6", "Check the name in the bar", "Your name, and the same name in every service"],
    ["7", "Run the seed tool, reload Study Guider", "Three struggle cards with real concept names"],
    ["8", "Reload Home", "The counts moved - the services are writing to one student record"],
], [8 * mm, 78 * mm, 82 * mm]))
A(para("If step 4 sends you back to a login screen, your service's origin is probably missing from "
       "VITE_ALLOWED_REDIRECTS - see section 5.", SMALL))

A(para("16. Troubleshooting", H1))
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
     "Run the seed tool (section 14) and sign in as that student."],
    ["Gamification game routes fail but the dashboard works",
     "MongoDB is down. Only this service truly needs it.",
     "Start MongoDB on 27017."],
    ["Gamification API returns 503 on every route",
     "It cannot reach Code Coach to verify your token.",
     "Check CODE_COACH_URL and that Code Coach is running. 503 means unreachable, 401 means the token was refused."],
    ["Your old test login is rejected",
     "Identity moved to Code Coach. Per-service accounts are gone.",
     "Register once at http://localhost:4200 and use that account everywhere."],
    ["Signing in from VS Code says \"Not Found\"",
     "Your Code Coach backend predates the handoff endpoints.",
     "Restart it. Python does not reload without --reload."],
    ["The bar shows the wrong person's name",
     "A stale profile in localStorage from an earlier account.",
     "Pull code-coach and your repo - this was fixed in codeguru-auth.js. Or clear site data."],
    ["A page element is hidden behind the top bar",
     "It is position:fixed or sticky at top-0.",
     "Anchor it at top: var(--cg-bar-h) instead of 0."],
    ["Sign-in feels slow the first time",
     "A brand-new token misses the auth cache and Code Coach must reach the database.",
     "Expected. Roughly a second. Later calls with the same token are cached and near-instant."],
], [46 * mm, 58 * mm, 64 * mm]))

A(keep(para("17. Rules of the road", H1), table([
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
    ["Do not edit codeguru-theme.css or CodeGuruBar in your own repo.",
     "Copies, like codeguru-auth.js. The master is in code-coach/portal, synced by "
     "sync-codeguru-shared.sh."],
    ["Never hardcode a colour. Use a --cg-* token.",
     "A hex code cannot follow the theme, and will be the one thing on screen that looks wrong when "
     "dark mode lands."],
    ["Treat a 503 from Code Coach as temporary, not as a bad login.",
     "401 means the token was refused. 503 means Code Coach was unreachable - clearing the session "
     "there logs everyone out over a blip."],
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
