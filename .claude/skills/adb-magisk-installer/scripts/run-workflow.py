#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

# Add parent directory of scripts to Python path to import common
scripts_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(scripts_dir))

from common import (
    MagiskInstallerError,
    adb,
    adb_shell,
    detect_adb_device,
    detect_fastboot_device,
    fail,
    output_payload,
    tap,
    tap_first_text,
    wait_for_adb_device,
    wait_for_text,
)


def parse_toon_file(path: Path) -> dict:
    """A lightweight, robust YAML-to-dict parser designed specifically for our .toon workflow format

    without requiring external PyYAML dependency.
    """
    if not path.is_file():
        raise MagiskInstallerError(f"Workflow file does not exist: {path}")

    with path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    result: dict = {}
    current_phase: dict | None = None
    current_step: dict | None = None
    in_phases = False
    in_steps = False
    in_recovery = False

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped or line_stripped.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())

        # Match key-value: "key: value" or "key: 'value'" or "key: \"value\""
        match = re.match(r"^([\w_-]+)\s*:\s*(.*)$", line_stripped)
        if match and not line_stripped.startswith("-"):
            key, val = match.groups()
            val = val.strip().strip("'\"")

            if indent == 0:
                if key == "phases":
                    result["phases"] = []
                    in_phases = True
                    in_recovery = False
                elif key == "recovery":
                    result["recovery"] = []
                    in_phases = False
                    in_recovery = True
                else:
                    result[key] = val
                    in_phases = False
                    in_recovery = False
            elif in_phases and current_phase:
                if key == "steps":
                    current_phase["steps"] = []
                    in_steps = True
                elif in_steps and current_step:
                    if "params" not in current_step:
                        current_step["params"] = {}
                    if key != "params":
                        current_step[key] = val
                else:
                    current_phase[key] = val
            elif in_recovery and result.get("recovery"):
                last_rec = result["recovery"][-1]
                if key == "then":
                    last_rec["then"] = val
                else:
                    last_rec[key] = val
            continue

        # Match list item: "- key: value"
        match_list_kv = re.match(r"^-\s+([\w_-]+)\s*:\s*(.*)$", line_stripped)
        if match_list_kv:
            key, val = match_list_kv.groups()
            val = val.strip().strip("'\"")

            if in_phases:
                if indent == 2:  # New phase
                    current_phase = {key: val, "steps": []}
                    result["phases"].append(current_phase)
                    in_steps = False
                elif in_steps and indent == 6:  # New step
                    current_step = {key: val, "params": {}}
                    current_phase["steps"].append(current_step)
            elif in_recovery:
                recovery_item = {key: val}
                result["recovery"].append(recovery_item)
            continue

        # Match param/sub-indent key-value: "param_name: value"
        match_param = re.match(r"^([\w_-]+)\s*:\s*(.*)$", line_stripped)
        if match_param:
            p_key, p_val = match_param.groups()
            p_val = p_val.strip().strip("'\"")
            if in_steps and current_step and indent >= 10:
                if "params" not in current_step:
                    current_step["params"] = {}
                current_step["params"][p_key] = p_val

    return result


def resolve_placeholders(val: str, params: dict[str, str]) -> str:
    if not isinstance(val, str):
        return val
    for p_key, p_val in params.items():
        val = val.replace(f"{{{{ {p_key} }}}}", p_val)
        val = val.replace(f"{{{{{p_key}}}}}", p_val)
    return val


def run_other_action(action: str, params: dict[str, str], device: str) -> None:
    """Implement the non-magisk adb actions natively as part of the orchestrator."""
    if action == "adb-push":
        local = params.get("local")
        remote = params.get("remote")
        if not local or not remote:
            raise MagiskInstallerError("adb-push requires both 'local' and 'remote' parameters.")
        adb(device, "push", local, remote)

    elif action == "adb-pull":
        local = params.get("local")
        remote = params.get("remote")
        if not local or not remote:
            raise MagiskInstallerError("adb-pull requires both 'local' and 'remote' parameters.")
        adb(device, "pull", remote, local)

    elif action == "adb-reboot":
        mode = params.get("mode", "")
        args = ["reboot"]
        if mode:
            args.append(mode)
        adb(device, *args)

    elif action == "adb-tap":
        x = params.get("x")
        y = params.get("y")
        if x is None or y is None:
            raise MagiskInstallerError("adb-tap requires 'x' and 'y' parameters.")
        tap(device, int(x), int(y))

    elif action == "adb-file-select":
        path = params.get("path")
        if not path:
            raise MagiskInstallerError("adb-file-select requires a 'path' parameter.")
        basename = path.replace("\\", "/").rstrip("/").split("/")[-1]
        if not tap_first_text(device, [basename], partial=True):
            raise MagiskInstallerError(f"Could not find or select file '{basename}' in Android file picker UI.")

    elif action == "adb-wait-for":
        method = params.get("method")
        target = params.get("target")
        timeout_sec = int(params.get("timeout", "30"))
        if method == "text" and target:
            result = wait_for_text(device, [target], timeout=timeout_sec, partial=True)
            if not result:
                raise MagiskInstallerError(f"Timed out waiting for text '{target}' to appear.")
        else:
            raise MagiskInstallerError(f"Unsupported adb-wait-for parameters: method={method}, target={target}")

    elif action == "adb-wait-fastboot":
        timeout_sec = int(params.get("timeout", "30"))
        try:
            detect_fastboot_device(timeout=timeout_sec)
        except MagiskInstallerError as exc:
            raise MagiskInstallerError(f"Timed out waiting for fastboot mode: {exc}")

    elif action == "adb-wait-device":
        timeout_sec = int(params.get("timeout", "60"))
        wait_for_adb_device(device, timeout=timeout_sec)

    else:
        raise MagiskInstallerError(f"Unknown workflow action: '{action}'")


def execute_step(step: dict, context_params: dict[str, str], device: str) -> None:
    action = step.get("action", "")
    params = step.get("params", {})

    # Resolve template parameters
    resolved_params = {}
    for p_key, p_val in params.items():
        resolved_params[p_key] = resolve_placeholders(p_val, context_params)

    print(f"    Executing step '{step.get('id')}' via action '{action}'...")

    # Map Magisk actions to our dedicated scripts
    magisk_scripts = {
        "adb-magisk-download": "adb-magisk-download.py",
        "adb-magisk-install-app": "adb-magisk-install-app.py",
        "adb-magisk-launch": "adb-magisk-launch.py",
        "adb-magisk-extract-boot": "adb-magisk-extract-boot.py",
        "adb-magisk-patch-boot": "adb-magisk-patch-boot.py",
        "adb-magisk-flash-boot": "adb-magisk-flash-boot.py",
    }

    if action in magisk_scripts:
        script_name = magisk_scripts[action]
        script_path = scripts_dir / script_name

        cmd = [sys.executable, str(script_path), "--json"]
        if action != "adb-magisk-download":
            cmd.extend(["--device", device])

        # Add relevant parameters
        for p_key, p_val in resolved_params.items():
            if p_key == "device":
                continue
            dash_key = p_key.replace("_", "-")
            if p_val == "true" or p_val is True:
                cmd.append(f"--{dash_key}")
            elif p_val == "false" or p_val is False:
                pass
            else:
                cmd.extend([f"--{dash_key}", str(p_val)])

        print(f"      Calling helper script: {' '.join(shlex.quote(c) for cmd_part in cmd for c in (cmd_part if isinstance(cmd_part, list) else [cmd_part]))}")
        completed = subprocess.run(cmd, capture_output=True, text=True, check=False)

        try:
            res_json = json.loads(completed.stdout) if completed.stdout.strip() else {}
        except json.JSONDecodeError:
            res_json = {}

        if completed.returncode != 0 or not res_json.get("ok"):
            err_msg = res_json.get("error") or completed.stderr or "Script failed with error."
            raise MagiskInstallerError(f"Action '{action}' failed: {err_msg}")

        # Update context parameters if the script returned resolved fields (like exact downloaded version)
        if action == "adb-magisk-download":
            resolved_tag = res_json.get("resolved_tag", "")
            if resolved_tag.startswith("v"):
                context_params["version"] = resolved_tag[1:]
            elif resolved_tag:
                context_params["version"] = resolved_tag
    else:
        # Run generic native ADB actions directly inside the orchestrator
        run_other_action(action, resolved_params, device)


def run_workflow(workflow_path: Path, initial_params: dict[str, str]) -> dict:
    workflow = parse_toon_file(workflow_path)
    device = initial_params.get("device", "127.0.0.1:5555")

    # Establish full workflow parameter state
    context_params = {
        "device": device,
        "version": initial_params.get("version") or workflow.get("parameters", {}).get("version", "latest"),
    }

    phases = workflow.get("phases", [])
    print(f"Starting workflow '{workflow.get('name')}'...")
    print(f"Description: {workflow.get('description')}")
    print(f"Target Device: {device}")
    print(f"Initial Version spec: {context_params['version']}")

    completed_phases = []

    for phase in phases:
        phase_id = phase.get("id")
        phase_name = phase.get("name")
        print(f"\n--- Phase: {phase_name} ({phase_id}) ---")

        attempts = 1
        max_attempts = 1
        delay_sec = 0

        # Look up error recovery config for retry policies
        for rec in workflow.get("recovery", []):
            if rec.get("on_error") == phase_id and rec.get("action") == "retry":
                max_attempts = int(rec.get("max_attempts", "1")) + 1
                delay_sec = int(rec.get("delay", "0"))

        success = False
        while attempts <= max_attempts:
            try:
                for step in phase.get("steps", []):
                    execute_step(step, context_params, device)
                success = True
                break
            except Exception as exc:
                print(f"    [!] Error during phase '{phase_id}': {exc}", file=sys.stderr)
                if attempts < max_attempts:
                    print(f"    Retrying phase in {delay_sec} seconds (Attempt {attempts + 1}/{max_attempts})...")
                    time.sleep(delay_sec)
                    attempts += 1
                else:
                    # Check for non-retry recovery actions
                    for rec in workflow.get("recovery", []):
                        if rec.get("on_error") == phase_id and rec.get("then") == "pause":
                            print("\n[!] Execution paused due to critical flash failure. Review logs before continuing.")
                    raise

        if success:
            completed_phases.append(phase_id)

    return {
        "ok": True,
        "workflow": workflow.get("name"),
        "device": device,
        "completed_phases": completed_phases,
        "final_version": context_params.get("version"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Orchestrator for (.toon) Magisk Installation Workflows.")
    parser.add_argument("--workflow", required=True, help="Path to the .toon workflow description file.")
    parser.add_argument("--device", help="ADB serial for the target device.")
    parser.add_argument("--version", help="Override Magisk version to download.")
    parser.add_argument("--json", action="store_true", help="Emit process completion status as JSON.")
    args = parser.parse_args()

    try:
        workflow_path = Path(args.workflow).expanduser().resolve()
        initial_params = {}
        if args.device:
            initial_params["device"] = args.device
        if args.version:
            initial_params["version"] = args.version

        result = run_workflow(workflow_path, initial_params)
        output_payload(result, args.json)
    except Exception as exc:
        fail(str(exc), as_json=args.json)


if __name__ == "__main__":
    main()
