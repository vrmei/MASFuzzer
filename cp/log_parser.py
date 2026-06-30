"""
Log Parser Module - Extract traces and original grades from batch log files.
Supports both Config B (Worker-Only) and Config A (Full MAS) log formats.
"""
import re
import json
import os
from typing import List, Dict, Tuple


def parse_worker_only_log(log_path: str) -> List[Dict]:
    """
    Parse a Config B worker-only log file.
    Returns list of dicts with: payload_id, strategy, target_tool, worker_trace, original_grade
    """
    with open(log_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by payload blocks
    blocks = re.split(r'### \[PAYLOAD (\d+)\] ###', content)
    results = []

    for i in range(1, len(blocks), 2):
        payload_id = int(blocks[i])
        block = blocks[i + 1]

        # Extract strategy and target_tool
        strategy_m = re.search(r'STRATEGY:\s*(.+)', block)
        target_m = re.search(r'TARGET_TOOL:\s*(.+)', block)
        strategy = strategy_m.group(1).strip() if strategy_m else ""
        target_tool = target_m.group(1).strip() if target_m else ""

        # Extract worker response (content after MESSAGE [Worker])
        worker_trace = ""
        worker_m = re.search(
            r'MESSAGE \[Worker\].*?CONTENT:\s*\n(.*?)(?=────|====================)',
            block, re.DOTALL
        )
        if worker_m:
            worker_trace = worker_m.group(1).strip()
            # Clean up indentation
            worker_trace = '\n'.join(
                line.strip() for line in worker_trace.split('\n')
            )

        # Extract payload from UserProxy message
        payload = ""
        payload_m = re.search(
            r'MESSAGE \[UserProxy\].*?CONTENT:\s*\n.*?\[Payload:\s*(.*?)\]',
            block, re.DOTALL
        )
        if payload_m:
            payload = payload_m.group(1).strip()

        # Extract original oracle grade
        grade_m = re.search(r'"grade":\s*(\d+)', block)
        original_grade = int(grade_m.group(1)) if grade_m else -1

        results.append({
            "payload_id": payload_id,
            "strategy": strategy,
            "target_tool": target_tool,
            "payload": payload,
            "worker_trace": worker_trace,
            "original_grade": original_grade,
        })

    return results


def parse_full_mas_log(log_path: str) -> List[Dict]:
    """
    Parse a Config A Full-MAS log file.
    Returns list of dicts with: payload_id, strategy, target_tool, payload,
                                worker_trace, manager_trace, original_grade
    """
    with open(log_path, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = re.split(r'### \[PAYLOAD (\d+)\] ###', content)
    results = []

    for i in range(1, len(blocks), 2):
        payload_id = int(blocks[i])
        block = blocks[i + 1]

        strategy_m = re.search(r'STRATEGY:\s*(.+)', block)
        target_m = re.search(r'TARGET_TOOL:\s*(.+)', block)
        strategy = strategy_m.group(1).strip() if strategy_m else ""
        target_tool = target_m.group(1).strip() if target_m else ""

        # Extract payload from first UserProxy message
        payload = ""
        payload_m = re.search(
            r'WORKER CONVERSATION LOG:.*?MESSAGE \[UserProxy\].*?CONTENT:\s*\n.*?\[Payload:\s*(.*?)\]',
            block, re.DOTALL
        )
        if payload_m:
            payload = payload_m.group(1).strip()

        # Extract manager conversation section
        manager_trace = []
        manager_section = ""
        mgr_m = re.search(
            r'MANAGER CONVERSATION LOG:(.*?)(?:====================\s*🧠|$)',
            block, re.DOTALL
        )
        if mgr_m:
            manager_section = mgr_m.group(1)

        # Parse manager messages
        msg_blocks = re.split(r'📨 MESSAGE \[(\w+)\]', manager_section)
        for j in range(1, len(msg_blocks), 2):
            role = msg_blocks[j]
            msg_content = msg_blocks[j + 1] if j + 1 < len(msg_blocks) else ""
            content_m = re.search(r'CONTENT:\s*\n(.*?)(?=\n\s*(?:🔨|📊|────)|$)', msg_content, re.DOTALL)
            text = content_m.group(1).strip() if content_m else ""
            # Check for tool calls
            tool_calls = []
            tc_m = re.findall(r'Tool:\s*(\S+)', msg_content)
            if tc_m:
                tool_calls = tc_m
            manager_trace.append({
                "role": role,
                "content": text[:500],  # truncate for API
                "tool_calls": tool_calls
            })

        # Extract original grade
        grade_m = re.search(r'"grade":\s*(\d+)', block)
        original_grade = int(grade_m.group(1)) if grade_m else -1

        results.append({
            "payload_id": payload_id,
            "strategy": strategy,
            "target_tool": target_tool,
            "payload": payload,
            "manager_trace": manager_trace,
            "original_grade": original_grade,
        })

    return results


def get_config_b_log_files() -> Dict[str, str]:
    """Return mapping of worker_model_name -> log_file_path for Config B."""
    log_dir = "logs_worker_eval"
    files = {}
    for f in os.listdir(log_dir):
        if f.startswith("batch_") and f.endswith(".log"):
            # Extract model name: batch_ModelName_YYYYMMDD_HHMM.log
            parts = f[len("batch_"):]
            # Remove timestamp suffix
            m = re.match(r'(.+?)_\d{8}_\d{4}\.log', parts)
            if m:
                model_name = m.group(1)
                full_path = os.path.join(log_dir, f)
                # Keep latest file per model
                if model_name not in files or f > files[model_name].split(os.sep)[-1]:
                    files[model_name] = full_path
    return files


def get_config_a_log_files() -> Dict[Tuple[str, str], str]:
    """
    Return mapping of (manager_name, worker_name) -> log_file_path for Config A.
    Covers: logs/ (Worker=Llama-3.1-8B) and logs_deepseek-r1/ (Worker=DeepSeek-R1)
    Target managers: Llama-3.1-8B, Mistral-Small-3.2-24B, Qwen-2.5-72B
    """
    target_managers = [
        "Llama-3.1-8B", "Mistral-Small-3.2-24B", "Qwen-2.5-72B"
    ]
    files = {}

    # logs/ directory - Worker = Llama-3.1-8B
    log_dir = "logs"
    if os.path.isdir(log_dir):
        for f in os.listdir(log_dir):
            if not f.startswith("batch_") or not f.endswith(".log"):
                continue
            for mgr in target_managers:
                if f.startswith(f"batch_{mgr}_vs_Llama-3.1-8B"):
                    files[(mgr, "Llama-3.1-8B")] = os.path.join(log_dir, f)

    # logs_deepseek-r1/ directory - Worker = DeepSeek-R1
    log_dir = "logs_deepseek-r1"
    if os.path.isdir(log_dir):
        for f in os.listdir(log_dir):
            if not f.startswith("batch_") or not f.endswith(".log"):
                continue
            for mgr in target_managers:
                if f.startswith(f"batch_{mgr}_vs_DeepSeek-R1"):
                    files[(mgr, "DeepSeek-R1")] = os.path.join(log_dir, f)

    return files
