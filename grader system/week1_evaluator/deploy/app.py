"""
EEP1 Week 1 — Production Grading Server
Flask + Gunicorn ready, Railway deployable.
PostgreSQL for persistent submission storage.
"""

import base64
import json
import logging
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# ── App setup ─────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder="static", static_url_path="")

# ── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

# ── Config from environment ───────────────────────────────────────────────────
_key_tmp = Path("/tmp/instructor_private.pem")

# Option 1: base64-encoded key (recommended for Railway — no newline issues)
_KEY_B64 = os.environ.get("PRIVATE_KEY_B64", "")
if _KEY_B64:
    import base64 as _b64
    _key_tmp.write_bytes(_b64.b64decode(_KEY_B64))
    PRIVATE_KEY_PATH = str(_key_tmp)

# Option 2: raw PEM content (newlines may be lost in some platforms)
elif os.environ.get("PRIVATE_KEY_CONTENT", ""):
    _KEY_CONTENT = os.environ["PRIVATE_KEY_CONTENT"].replace("\\n", "\n").replace(" ", "\n")
    # Fix header/footer that got spaces replaced
    _KEY_CONTENT = _KEY_CONTENT.replace("-----BEGIN\nRSA\nPRIVATE\nKEY-----", "-----BEGIN RSA PRIVATE KEY-----")
    _KEY_CONTENT = _KEY_CONTENT.replace("-----END\nRSA\nPRIVATE\nKEY-----", "-----END RSA PRIVATE KEY-----")
    _key_tmp.write_text(_KEY_CONTENT)
    PRIVATE_KEY_PATH = str(_key_tmp)

# Option 3: local file path (for local dev)
else:
    PRIVATE_KEY_PATH = os.environ.get("PRIVATE_KEY_PATH", "keys/instructor_private.pem")

UPLOADS_DIR      = Path(os.environ.get("UPLOADS_DIR", "uploads"))
MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_BYTES", 50_000))
PORT             = int(os.environ.get("PORT", 8080))

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# ── Database ──────────────────────────────────────────────────────────────────

def get_db():
    """Get a PostgreSQL connection, or None if not configured."""
    # Read at call time (not module load) so Railway env vars are available
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        return None
    try:
        import psycopg2
        try:
            conn = psycopg2.connect(db_url, sslmode="require")
        except Exception:
            conn = psycopg2.connect(db_url, sslmode="prefer")
        return conn
    except Exception as e:
        log.warning("DB connection failed: %s", e)
        return None

def init_db():
    """Create submissions table if it doesn't exist."""
    conn = get_db()
    if not conn:
        log.info("No DATABASE_URL set — using file storage only")
        return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS submissions (
                    id          SERIAL PRIMARY KEY,
                    student_id  TEXT NOT NULL,
                    submitted_at TIMESTAMPTZ DEFAULT NOW(),
                    overall     TEXT,
                    grade       TEXT,
                    score_pct   INTEGER,
                    checks_json TEXT,
                    raw_report  TEXT
                )
            """)
        conn.commit()
        conn.close()
        log.info("Database ready")
    except Exception as e:
        log.error("DB init failed: %s", e)

def save_to_db(student_id, overall, grading, checks, raw_report):
    """Save a submission to PostgreSQL."""
    conn = get_db()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO submissions
                    (student_id, overall, grade, score_pct, checks_json, raw_report)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                student_id,
                overall,
                grading["grade"],
                grading["pct"],
                json.dumps(checks),
                raw_report,
            ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        log.error("DB save failed: %s", e)
        return False

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Grading rubric ────────────────────────────────────────────────────────────
RUBRIC_WEEK1 = {
    "dir:week-":        (1, "Weekly folder",     "Create the missing week folder:\n  mkdir ~/eep-software/week-XX"),
    "dir:notes":        (2, "Notes folder",      "Run: mkdir ~/eep-software/notes"),
    "dir:scripts":      (2, "Scripts folder",    "Run: mkdir ~/eep-software/scripts"),
    "dir:capstone":     (2, "Capstone folder",   "Run: mkdir ~/eep-software/capstone"),
    "readme:week-":     (1, "Weekly README",     "Create README.md in the week folder:\n  echo '# Week X' > ~/eep-software/week-XX/README.md"),
    "bashrc":           (5, "Bash aliases",      "Add at least 2 aliases to ~/.bashrc:\n  alias ll='ls -la'\n  alias gs='git status'\nThen run: source ~/.bashrc"),
    "workspace-report": (5, "Workspace report",  "Generate the workspace report:\n  ls -la ~/eep-software/ > ~/eep-software/workspace-report.txt"),
}
TOTAL_POINTS_WEEK1 = 40

RUBRIC_WEEK2 = {
    "dir:week-02":          (5,  "Week 2 directory",    "Create: mkdir ~/eep-software/week-02"),
    "file:server.log":      (5,  "Sample log file",     "Put server.log in ~/eep-software/week-02/\n  Download from the course website"),
    "file:analyze.sh":      (10, "Analysis script",     "Create analyze.sh in ~/eep-software/week-02/"),
    "executable:analyze":   (5,  "Script executable",   "Run: chmod +x ~/eep-software/week-02/analyze.sh"),
    "script:runs":          (10, "Script runs OK",      "Fix errors in analyze.sh so it runs without crashing"),
    "output:report.txt":    (10, "Produces report.txt", "Your script must produce report.txt using > and >>"),
    "analysis:request_count":(10,"Request count",       "Add a pipeline counting total lines:\n  wc -l < server.log > report.txt"),
    "analysis:top_ips":     (10, "Top IPs analysis",    "Add a pipeline for top IPs:\n  awk '{print $1}' server.log | sort | uniq -c | sort -rn | head -5"),
    "analysis:top_urls":    (10, "Top URLs analysis",   "Add a pipeline for top URLs:\n  awk '{print $7}' server.log | sort | uniq -c | sort -rn | head -5"),
    "analysis:status_codes":(10, "Status codes",        "Add a pipeline for status distribution:\n  awk '{print $9}' server.log | sort | uniq -c | sort -rn"),
    "technique:pipelines":  (10, "Uses pipes",          "Your script must use | (pipe) to chain commands"),
    "technique:redirection":(5,  "Uses redirection",    "Your script must use > or >> to write report.txt"),
}
TOTAL_POINTS_WEEK2 = 100

RUBRIC_WEEK3 = {
    "dir:week-03":           (5,  "Week 3 directory",      "Create: mkdir ~/eep-software/week-03"),
    "file:organize.sh":      (10, "Script exists",         "Create organize.sh in ~/eep-software/week-03/"),
    "executable:organize":   (5,  "Script executable",     "Run: chmod +x organize.sh"),
    "validation:no_args":    (5,  "Validates no args",     "Add: if [[ $# -ne 1 ]]; then echo 'Usage...'; exit 1; fi"),
    "validation:bad_dir":    (5,  "Validates bad dir",     "Add: if [[ ! -d \"$1\" ]]; then echo 'Error...'; exit 1; fi"),
    "org:creates_folders":   (10, "Creates sub-folders",   "Add: mkdir -p \"$1/Documents\" \"$1/Images\" \"$1/Code\" \"$1/Other\""),
    "org:documents_correct": (10, "Documents sorted",      "Move .txt/.pdf/.doc files to Documents/"),
    "org:images_correct":    (10, "Images sorted",         "Move .jpg/.png/.gif files to Images/"),
    "org:code_correct":      (10, "Code sorted",           "Move .py/.sh/.js files to Code/"),
    "org:other_correct":     (10, "Other sorted",          "Move remaining files to Other/"),
    "org:no_files_left":     (5,  "All files moved",       "Make sure every file gets moved to a sub-folder"),
    "org:summary_output":    (5,  "Prints summary",        "Print counts: echo \"Documents: $count files\""),
    "technique:conditionals":(5,  "Uses conditionals",     "Use if/elif or case to check extensions"),
    "technique:loop":        (5,  "Uses loops",            "Use for or while to iterate over files"),
}
TOTAL_POINTS_WEEK3 = 100

# ── Grading logic ─────────────────────────────────────────────────────────────
def grade_checks(checks: list, week="1") -> dict:
    rubric = RUBRIC_WEEK1 if week == "1" else RUBRIC_WEEK2 if week == "2" else RUBRIC_WEEK3
    total  = TOTAL_POINTS_WEEK1 if week == "1" else TOTAL_POINTS_WEEK2 if week == "2" else TOTAL_POINTS_WEEK3
    earned, passed, failed = 0, [], []
    for c in checks:
        name, status = c["name"], c["status"]
        points, label, hint = 0, name, ""
        for prefix, (pts, lbl, fix) in rubric.items():
            if name.startswith(prefix):
                points = pts
                label  = lbl + (f" ({name})" if "week-" in prefix and prefix != "dir:week-02" else "")
                hint   = fix
                break
        if status == "PASS":
            earned += points
            passed.append({"name": name, "label": label, "points": points})
        else:
            failed.append({"name": name, "label": label, "points": points,
                           "reason": c.get("reason", ""), "hint": hint})

    pct = round(earned / total * 100) if total else 0
    grade = "A+" if pct == 100 else "A" if pct >= 90 else "B" if pct >= 80 \
          else "C" if pct >= 70 else "D" if pct >= 60 else "F"
    return {"earned": earned, "total": total, "pct": pct,
            "grade": grade, "passed": passed, "failed": failed}

# ── Decrypt .eep1 ─────────────────────────────────────────────────────────────
def decrypt_eep1(blob_text: str) -> str:
    blob = blob_text.strip()
    if ":" not in blob:
        raise ValueError("Invalid .eep1 format")

    enc_key_b64, enc_body_b64 = blob.split(":", 1)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        enc_key  = tmp / "enc_key.bin"
        enc_body = tmp / "enc_body.bin"
        aes_key  = tmp / "aes_key.bin"
        plain    = tmp / "plain.txt"

        try:
            enc_key.write_bytes(base64.b64decode(enc_key_b64))
            enc_body.write_bytes(base64.b64decode(enc_body_b64))
        except Exception:
            raise ValueError("File is corrupted or not a valid .eep1")

        r = subprocess.run(
            ["openssl", "pkeyutl", "-decrypt", "-inkey", PRIVATE_KEY_PATH,
             "-in", str(enc_key), "-out", str(aes_key)],
            capture_output=True
        )
        if r.returncode != 0:
            raise ValueError("Decryption failed — file may be tampered or from a different key")

        r = subprocess.run(
            ["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2",
             "-pass", f"file:{aes_key}",
             "-in", str(enc_body), "-out", str(plain)],
            capture_output=True
        )
        if r.returncode != 0:
            raise ValueError("File is corrupted")

        return plain.read_text()

# ── Parse report ──────────────────────────────────────────────────────────────
def parse_report(text: str) -> dict:
    result = {"checks": []}
    for line in text.strip().splitlines():
        if line.startswith("STUDENT_ID:"):
            result["student_id"] = line.split(":", 1)[1].strip()
        elif line.startswith("TIMESTAMP:"):
            result["timestamp"] = line.split(":", 1)[1].strip()
        elif line.startswith("Overall:"):
            result["overall"] = line.split(":", 1)[1].strip()
        elif ": PASS" in line or ": FAIL" in line:
            parts = line.rsplit(": ", 1)
            if len(parts) == 2:
                result["checks"].append({"name": parts[0].strip(), "status": parts[1].strip()})
    return result

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)

@app.route("/download/eep1_verifier.sh")
def download_verifier_sh():
    f = Path("eep1_verifier.sh")
    if not f.exists():
        return jsonify({"error": "Verifier not found"}), 404
    return send_file(f.resolve(), as_attachment=True,
                     download_name="eep1_verifier.sh", mimetype="text/plain")

@app.route("/download/eep1_verifier")
def download_verifier_bin():
    f = Path("eep1_verifier")
    if not f.exists():
        return jsonify({"error": "Binary not found"}), 404
    return send_file(f.resolve(), as_attachment=True,
                     download_name="eep1_verifier",
                     mimetype="application/octet-stream")

@app.route("/download/eep2_verifier.sh")
def download_eep2_sh():
    f = Path("eep2_verifier.sh")
    if not f.exists():
        return jsonify({"error": "Verifier not found"}), 404
    return send_file(f.resolve(), as_attachment=True,
                     download_name="eep2_verifier.sh", mimetype="text/plain")

@app.route("/download/eep2_verifier")
def download_eep2_bin():
    f = Path("eep2_verifier")
    if not f.exists():
        return jsonify({"error": "Binary not found"}), 404
    return send_file(f.resolve(), as_attachment=True,
                     download_name="eep2_verifier",
                     mimetype="application/octet-stream")

@app.route("/download/server.log")
def download_sample_log():
    f = Path("static/server.log")
    if not f.exists():
        return jsonify({"error": "Sample log not found"}), 404
    return send_file(f.resolve(), as_attachment=True,
                     download_name="server.log", mimetype="text/plain")

@app.route("/download/eep3_verifier.sh")
def download_eep3_sh():
    f = Path("eep3_verifier.sh")
    if not f.exists():
        return jsonify({"error": "Verifier not found"}), 404
    return send_file(f.resolve(), as_attachment=True,
                     download_name="eep3_verifier.sh", mimetype="text/plain")

@app.route("/download/eep3_verifier")
def download_eep3_bin():
    f = Path("eep3_verifier")
    if not f.exists():
        return jsonify({"error": "Binary not found"}), 404
    return send_file(f.resolve(), as_attachment=True,
                     download_name="eep3_verifier",
                     mimetype="application/octet-stream")

@app.route("/api/grade", methods=["POST"])
@limiter.limit("10 per hour")
def api_grade():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "Empty filename"}), 400

    # Detect week from filename
    week = "1"
    if f.filename and "EEP2" in f.filename.upper():
        week = "2"
    elif f.filename and ".eep2" in f.filename.lower():
        week = "2"
    elif f.filename and "EEP3" in f.filename.upper():
        week = "3"
    elif f.filename and ".eep3" in f.filename.lower():
        week = "3"

    content = f.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        return jsonify({"error": "File too large (max 50KB)"}), 413

    blob_text = content.decode("utf-8", errors="replace")

    try:
        plaintext = decrypt_eep1(blob_text)
    except ValueError as e:
        log.warning("Decryption failed: %s", e)
        return jsonify({"error": str(e), "tampered": True}), 422

    try:
        report = parse_report(plaintext)
    except Exception as e:
        log.error("Parse error: %s", e)
        return jsonify({"error": "Could not parse report"}), 422

    sid = report.get("student_id", "unknown")
    ts  = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    grading = grade_checks(report.get("checks", []), week=week)

    # Save to database (primary) + file (backup)
    saved_db = save_to_db(sid, report.get("overall"), grading,
                          report.get("checks", []), plaintext)
    if not saved_db:
        # Fallback to file if DB not available
        (UPLOADS_DIR / f"{sid}_{ts}.txt").write_text(plaintext)
    log.info("Graded %s → %s %s%%", sid, grading["grade"], grading["pct"])

    return jsonify({
        "student_id": sid,
        "timestamp":  report.get("timestamp"),
        "overall":    report.get("overall"),
        "checks":     report.get("checks"),
        "grading":    grading,
        "week":       week,
    })

@app.route("/health")
def health():
    db_url = os.environ.get("DATABASE_URL", "")
    db_ok = get_db() is not None
    return jsonify({
        "status": "ok",
        "db": "connected" if db_ok else "not configured",
        "db_url_set": bool(db_url)
    })

@app.route("/api/submissions")
def api_submissions():
    """Instructor endpoint — list all submissions from DB."""
    conn = get_db()
    if not conn:
        return jsonify({"error": "Database not configured"}), 503
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT student_id, submitted_at, overall, grade, score_pct
                FROM submissions
                ORDER BY submitted_at DESC
                LIMIT 500
            """)
            rows = cur.fetchall()
        conn.close()
        return jsonify([{
            "student_id":   r[0],
            "submitted_at": r[1].isoformat() if r[1] else None,
            "overall":      r[2],
            "grade":        r[3],
            "score_pct":    r[4],
        } for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Entry point ───────────────────────────────────────────────────────────────
with app.app_context():
    init_db()

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=False)
