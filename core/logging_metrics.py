"""Logging and system metrics (RSS, RAM, Metal)."""

from __future__ import annotations

import os
import re
from typing import Dict

from config import settings


def log(msg: str) -> None:
    print(msg, flush=True)


def _format_bytes(n: int | None) -> str:
    if n is None:
        return "n/a"
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    x = float(n)
    for u in units:
        if x < 1024 or u == units[-1]:
            return f"{x:.1f}{u}"
        x /= 1024
    return f"{x:.1f}{units[-1]}"


def _process_rss_bytes() -> int | None:
    try:
        import resource
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(rss) if os.uname().sysname == "Darwin" else int(rss) * 1024
    except Exception:
        return None


def _system_memory_total_available_bytes() -> tuple[int | None, int | None]:
    try:
        if os.uname().sysname == "Linux":
            total = available = None
            with open("/proc/meminfo", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        total = int(line.split()[1]) * 1024
                    elif line.startswith("MemAvailable:"):
                        available = int(line.split()[1]) * 1024
            return total, available
    except Exception:
        pass
    try:
        if os.uname().sysname == "Darwin":
            import subprocess
            total = int(subprocess.check_output(["sysctl", "-n", "hw.memsize"]).strip())
            vm = subprocess.check_output(["vm_stat"], text=True)
            page_size = 4096
            m = re.search(r"page size of (\d+) bytes", vm)
            if m:
                page_size = int(m.group(1))
            pages = {}
            for line in vm.splitlines():
                mm = re.match(r"^Pages (.+?):\s+(\d+)\.$", line.strip())
                if mm:
                    pages[mm.group(1)] = int(mm.group(2))
            available_pages = (
                pages.get("free", 0)
                + pages.get("inactive", 0)
                + pages.get("speculative", 0)
            )
            available = available_pages * page_size
            return total, available
    except Exception:
        pass
    return None, None


def log_system_metrics(tag: str) -> None:
    rss = _process_rss_bytes()
    total, avail = _system_memory_total_available_bytes()
    log(
        f"{tag} rss={_format_bytes(rss)} "
        f"ram_total={_format_bytes(total)} ram_avail={_format_bytes(avail)}"
    )
