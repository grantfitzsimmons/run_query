#!/usr/bin/env python3
import os
import json
import subprocess
import logging
from datetime import date
from dotenv import load_dotenv

# ─── Load .env ────────────────────────────────────────────────────────────────
load_dotenv()

# ─── Configuration ─────────────────────────────────────────────────────────────
TODAY               = date.today().isoformat()
LOG_FILE            = os.getenv("LOG_FILE", "orchestration.log")
REMOTE_SCRIPT_DIR   = os.getenv("REMOTE_SCRIPT_DIR", "~/run_query")
LOCAL_RETRIEVED_DIR = os.getenv("LOCAL_RETRIEVED_DIR", "./RetrievedReports")
os.makedirs(LOCAL_RETRIEVED_DIR, exist_ok=True)

# ─── Load SERVERS from JSON in .env ────────────────────────────────────────────
raw_servers = os.getenv("SERVERS_JSON", "[]")
try:
    SERVERS = json.loads(raw_servers)
except json.JSONDecodeError as e:
    raise RuntimeError(f"Failed to parse SERVERS_JSON from .env: {e}")

# ─── Logging Setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
    ]
)
logger = logging.getLogger("orchestrator")

# ─── Function to run the script remotely and fetch results ─────────────────────
def run_remote_script_and_fetch(cfg):
    label    = cfg["label"]
    ssh_host = cfg["ssh_host"]
    ssh_user = cfg["ssh_user"]
    ssh_key  = os.path.expanduser(cfg["ssh_key"])
    remote_dir = REMOTE_SCRIPT_DIR

    logger.info(f"[{label}] Connecting to {ssh_user}@{ssh_host}…")

    remote_commands = [
        f"cd {remote_dir}",
        "git pull",
        "git switch size",
        "sudo apt update && sudo apt install -y python3-venv",
        "python3 -m venv venv || true",
        "source venv/bin/activate",
        "pip install -r requirements.txt",
        "python3 runQueryOnAllDatabases.py",
    ]
    full_remote_command = " && ".join(remote_commands)

    ssh_cmd = ["ssh", "-i", ssh_key, f"{ssh_user}@{ssh_host}", full_remote_command]
    logger.debug(f"[{label}] SSH cmd: {' '.join(ssh_cmd)}")

    try:
        result = subprocess.run(
            ssh_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, check=True
        )
        logger.info(f"[{label}] Remote execution succeeded.")

        # Extract the REPORT_PATH:
        remote_report = None
        for line in result.stdout.splitlines():
            if line.startswith("REPORT_PATH:"):
                remote_report = line.split("REPORT_PATH:", 1)[1].strip()
                logger.info(f"[{label}] Found REPORT_PATH: {remote_report}")
                break

        if result.stderr:
            logger.warning(f"[{label}] Remote stderr:\n{result.stderr.strip()}")

        if not remote_report:
            logger.error(f"[{label}] No REPORT_PATH marker; skipping fetch.")
            return

        full_remote_path = f"{remote_dir}/{remote_report.lstrip('./')}"
        remote_src       = f"{ssh_user}@{ssh_host}:{full_remote_path}"
        local_dst        = LOCAL_RETRIEVED_DIR

        logger.info(f"[{label}] Fetching report via SCP…")
        scp_cmd = ["scp", "-i", ssh_key, remote_src, local_dst]
        logger.debug(f"[{label}] SCP cmd: {' '.join(scp_cmd)}")

        scp_res = subprocess.run(
            scp_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, check=True
        )
        logger.info(f"[{label}] SCP succeeded; saved to {LOCAL_RETRIEVED_DIR}.")
        if scp_res.stderr:
            logger.warning(f"[{label}] SCP stderr:\n{scp_res.stderr.strip()}")

    except FileNotFoundError:
        logger.error(f"[{label}] SSH/SCP not found. Is OpenSSH installed?")
    except subprocess.CalledProcessError as e:
        proc = "SCP" if "scp" in e.cmd[0] else "Remote command"
        logger.error(f"[{label}] {proc} failed (code {e.returncode}).")
        logger.error(f"[{label}] Stdout:\n{e.stdout.strip() or 'None'}")
        logger.error(f"[{label}] Stderr:\n{e.stderr.strip() or 'None'}")
    except Exception as e:
        logger.error(f"[{label}] Unexpected error: {e}")

# ─── Main execution ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("=== Starting Orchestration Job ===")
    for srv in SERVERS:
        run_remote_script_and_fetch(srv)
    logger.info("=== Orchestration Job Completed ===")
