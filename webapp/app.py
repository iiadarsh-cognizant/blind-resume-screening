"""
Blindspot Flask Backend

Run with:
    python app.py

This Flask app:
1. Serves the Blindspot web UI
2. Reads candidate data from SQLite database
3. Proxies requests from the UI to the Neuro SAN server

Prerequisites:
    pip install flask flask-cors requests

Neuro SAN must be running in another terminal:
    ns run
"""

import sqlite3
import json
import os
import re
import requests

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS


# ── Flask setup ────────────────────────────────────────────

app = Flask(__name__)
CORS(app)


# ── Config ─────────────────────────────────────────────────

NEURO_SAN_URL = "http://localhost:8080"
AGENT_NAME = "blindspot"

DB_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "data",
    "blindspot.db"
)


# ── Database helper ────────────────────────────────────────

def get_db():
    """
    Open a SQLite connection to the blindspot database.
    """
    db_path = os.path.normpath(DB_PATH)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


# ── Database routes ────────────────────────────────────────

@app.route("/api/roles")
def get_roles():
    """
    Return all distinct job roles with candidate counts.
    """
    try:
        conn = get_db()
        rows = conn.execute(
            """
            SELECT job_role, COUNT(*) as count
            FROM applicants
            GROUP BY job_role
            ORDER BY job_role
            """
        ).fetchall()
        conn.close()

        return jsonify([
            {
                "role": r["job_role"],
                "count": r["count"]
            }
            for r in rows
        ])

    except Exception as e:
        print("[BLINDSPOT] ERROR in /api/roles:")
        print(str(e))

        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route("/api/applicants/<job_role>")
def get_applicants(job_role):
    """
    Return all applicants for a given job role.
    """
    try:
        conn = get_db()
        rows = conn.execute(
            """
            SELECT
                resume_id,
                name,
                skills,
                experience_years,
                education,
                certifications,
                projects_count,
                ai_score
            FROM applicants
            WHERE job_role = ?
            ORDER BY ai_score DESC
            """,
            (job_role,)
        ).fetchall()
        conn.close()

        return jsonify([dict(r) for r in rows])

    except Exception as e:
        print("[BLINDSPOT] ERROR in /api/applicants:")
        print(str(e))

        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# ── Neuro SAN health check route ───────────────────────────

@app.route("/api/check-neuro-san")
def check_neuro_san():
    """
    Check whether Neuro SAN server is reachable and whether blindspot is registered.
    """
    try:
        url = f"{NEURO_SAN_URL}/api/v1/list"

        resp = requests.get(url, timeout=5)

        if resp.status_code != 200:
            return jsonify({
                "status": "error",
                "neuro_san_running": False,
                "blindspot_available": False,
                "error": f"Neuro SAN returned HTTP {resp.status_code}",
                "details": resp.text
            })

        try:
            data = resp.json()
        except Exception:
            data = {}

        agents = data.get("agents", data)
        blindspot_available = AGENT_NAME in str(agents)

        return jsonify({
            "status": "ok",
            "neuro_san_running": True,
            "blindspot_available": blindspot_available,
            "agents": agents
        })

    except Exception as e:
        print("[BLINDSPOT] ERROR in /api/check-neuro-san:")
        print(str(e))

        return jsonify({
            "status": "error",
            "neuro_san_running": False,
            "blindspot_available": False,
            "error": str(e)
        })


# ── Neuro SAN response parser ──────────────────────────────

def extract_text_from_message(message):
    """
    Extract readable text from a Neuro SAN chat message.
    """
    parts = []

    if not isinstance(message, dict):
        return parts

    response_obj = message.get("response")

    if isinstance(response_obj, dict):
        text = response_obj.get("text")
        if text:
            parts.append(str(text))

    elif isinstance(response_obj, str):
        parts.append(response_obj)

    for key in ["text", "message", "content"]:
        value = message.get(key)
        if value:
            parts.append(str(value))

    return parts


def extract_token_accounting(message):
    """
    Extract token accounting from a Neuro SAN chat message if present.
    """
    if not isinstance(message, dict):
        return {}

    if "token_accounting" in message:
        return message.get("token_accounting") or {}

    response_obj = message.get("response")
    if isinstance(response_obj, dict) and "token_accounting" in response_obj:
        return response_obj.get("token_accounting") or {}

    return {}


def parse_neuro_san_response(raw_text):
    """
    Parse Neuro SAN response text.

    Neuro SAN streaming_chat may return:
    1. A single JSON object
    2. Multiple JSON lines
    3. Server-sent event style lines beginning with data:
    """
    response_parts = []
    token_accounting = {}

    if not raw_text:
        return "", token_accounting

    # First try direct JSON.
    try:
        obj = json.loads(raw_text)

        response_parts.extend(extract_text_from_message(obj))

        found_tokens = extract_token_accounting(obj)
        if found_tokens:
            token_accounting = found_tokens

        final_text = "\n".join(response_parts).strip()
        if final_text:
            return final_text, token_accounting

    except Exception:
        pass

    # Then try line-by-line JSON / SSE parsing.
    for line in raw_text.splitlines():
        line = line.strip()

        if not line:
            continue

        if line.startswith("data:"):
            line = line[5:].strip()

        if not line:
            continue

        try:
            item = json.loads(line)
        except Exception:
            continue

        response_parts.extend(extract_text_from_message(item))

        found_tokens = extract_token_accounting(item)
        if found_tokens:
            token_accounting = found_tokens

    final_text = "\n".join(response_parts).strip()

    if not final_text:
        final_text = raw_text

    return final_text, token_accounting


def extract_ranking_block(text):
    """
    Extract the <<<RANKING>>>...<<<END>>> JSON block from the agent's
    final response text, if present. Returns None if the block is
    missing or isn't valid JSON, so callers can fall back gracefully.
    """
    if not text:
        return None

    match = re.search(r"<<<RANKING>>>(.*?)<<<END>>>", text, re.DOTALL)
    if not match:
        return None

    try:
        return json.loads(match.group(1).strip())
    except Exception as e:
        print("[BLINDSPOT] Could not parse <<<RANKING>>> block as JSON:")
        print(str(e))
        return None


# ── Neuro SAN proxy route ──────────────────────────────────

@app.route("/api/screen", methods=["POST"])
def screen_candidates():
    """
    Send a screening request to the blindspot Neuro SAN agent.

    Frontend sends:
        {
            "job_role": "Data Scientist",
            "top_n": 3
        }

    This route converts that into a Neuro SAN user_message.
    """
    try:
        data = request.get_json() or {}

        job_role = data.get("job_role", "")
        top_n = data.get("top_n", 3)

        if not job_role:
            return jsonify({
                "status": "error",
                "error": "job_role is required"
            }), 400

        human_message = (
            f"Screen candidates for {job_role} and recommend top {top_n}. "
            f"After your normal summary, also include the final ranked list wrapped exactly like this: "
            f"<<<RANKING>>>[{{\"candidate_id\":\"Candidate_01\",\"name\":\"...\",\"score\":87,"
            f"\"justification\":\"...\"}}, ...]<<<END>>> "
            f"— a strict JSON array, best to worst, with no other text between the markers."
        )

        print("=" * 70)
        print("[BLINDSPOT] /api/screen called")
        print(f"[BLINDSPOT] job_role      : {job_role}")
        print(f"[BLINDSPOT] top_n         : {top_n}")
        print(f"[BLINDSPOT] human_message : {human_message}")
        print("=" * 70)

        payload = {
            "user_message": {
                "text": human_message
            }
        }

        url = f"{NEURO_SAN_URL}/api/v1/{AGENT_NAME}/streaming_chat"

        print("[BLINDSPOT] Calling Neuro SAN URL:")
        print(url)

        print("[BLINDSPOT] Payload:")
        print(json.dumps(payload, indent=2))

        raw_chunks = []

        # Important:
        # stream=True keeps Flask reading the Neuro SAN response steadily.
        # timeout=(connect_timeout, read_timeout)
        # read_timeout is high because your agent takes around 5 min 50 sec.
        with requests.post(
            url,
            json=payload,
            stream=True,
            timeout=(10, 1200)
        ) as resp:

            print(f"[BLINDSPOT] Neuro SAN HTTP status: {resp.status_code}")

            if resp.status_code != 200:
                error_text = resp.text
                print("[BLINDSPOT] Neuro SAN error response:")
                print(error_text[:5000])

                return jsonify({
                    "status": "error",
                    "error": f"Neuro SAN returned HTTP {resp.status_code}",
                    "details": error_text
                }), 500

            for line in resp.iter_lines(decode_unicode=True):
                if line is None:
                    continue

                line = line.strip()

                if not line:
                    continue

                raw_chunks.append(line)

                # Print first part of streaming output for visibility.
                if len(raw_chunks) <= 10:
                    print("[BLINDSPOT] Neuro SAN stream line:")
                    print(line[:1000])

        raw_response = "\n".join(raw_chunks)

        print("[BLINDSPOT] Neuro SAN raw response collected.")
        print(raw_response[:5000])

        final_response, token_accounting = parse_neuro_san_response(raw_response)

        print("[BLINDSPOT] Parsed final response:")
        print(final_response[:3000])

        print("[BLINDSPOT] Parsed token accounting:")
        print(token_accounting)

        ranking = extract_ranking_block(final_response)
        print(f"[BLINDSPOT] Structured ranking block parsed: {len(ranking) if ranking else 0} candidate(s)")

        return jsonify({
            "status": "complete",
            "response": final_response,
            "ranking": ranking,
            "token_accounting": token_accounting
        })

    except requests.exceptions.Timeout:
        print("[BLINDSPOT] ERROR: Neuro SAN request timed out")

        return jsonify({
            "status": "error",
            "error": "Neuro SAN request timed out. The agent may still be running. Check the ns run terminal."
        }), 504

    except requests.exceptions.ConnectionError as e:
        print("[BLINDSPOT] ERROR: Could not connect to Neuro SAN")
        print(str(e))

        return jsonify({
            "status": "error",
            "error": "Could not connect to Neuro SAN. Make sure 'ns run' is running on http://localhost:8080."
        }), 500

    except Exception as e:
        print("[BLINDSPOT] ERROR in /api/screen:")
        print(str(e))

        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# ── Serve frontend ─────────────────────────────────────────

@app.route("/")
def index():
    """
    Serve the Blindspot frontend.
    """
    return render_template("index.html")


# ── Main ───────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 56)
    print("  Blindspot — Blind Hiring Pipeline")
    print("=" * 56)
    print(f"  Database : {os.path.normpath(DB_PATH)}")
    print(f"  Neuro SAN: {NEURO_SAN_URL}")
    print("  UI       : http://localhost:5000")
    print("=" * 56)
    print("  Make sure 'ns run' is running in another terminal")
    print("=" * 56)

    # Critical:
    # debug=False and use_reloader=False prevent Flask from restarting
    # during the 5-6 minute Neuro SAN agent call.
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False,
        threaded=True
    )
