#!/usr/bin/python3
import argparse
import collections
import importlib.util
import json
from pathlib import Path
import runpy
import sys


def load_firewall(path: Path):
    spec = importlib.util.spec_from_file_location("firewall", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_self_test(fixtures_dir: Path, app_dir: Path, send_telegram: bool, config_path: Path) -> int:
    nft_log = fixtures_dir / "nftables-block.log"
    alerts_file = fixtures_dir / "telegram-alerts.ndjson"
    fixture_text = {}
    for file in (nft_log, alerts_file):
        text = file.read_text(encoding="utf-8")
        if not text.strip():
            raise ValueError(f"empty fixture: {file.name}")
        fixture_text[file.name] = text
    alerts = [json.loads(line) for line in fixture_text[alerts_file.name].splitlines() if line.strip()]
    if {str(alert["rule"]["id"]) for alert in alerts} != {"100110", "100112", "100115", "100120"}:
        raise ValueError("fixtures must cover all four alert rules")
    cfg = json.loads(config_path.read_text(encoding="utf-8-sig")) if send_telegram else None
    fw = load_firewall(app_dir / "firewall.py")
    tg = runpy.run_path(str(app_dir / "custom-cowrie-telegram"))

    fw.check()

    state = collections.OrderedDict()
    lines = fixture_text[nft_log.name].splitlines()
    emitted = [fw.event(line, idx, state) for idx, line in enumerate(lines)]
    emitted = [e for e in emitted if e is not None]
    if not state:
        raise ValueError("firewall fixture contains no eligible event")
    print(f"FIXTURE nftables-block.log: lines={len(lines)} correlated_alerts={len(emitted)}")

    state = collections.OrderedDict()
    scan_alert = None
    for now, port in enumerate((21, 22, 23, 80, 443)):
        line = f"LAB_WAN_BLOCK IN=ens37 OUT= SRC=192.0.2.50 DST=192.168.100.20 PROTO=TCP DPT={port}"
        scan_alert = fw.event(line, now, state)
    assert scan_alert is not None and scan_alert["port_count"] == 5
    scan_alert["fixture"] = True
    key, formatted_scan = tg["message"]({
        "rule": {
            "id": "100120",
            "level": 7,
            "description": "Phát hiện dấu hiệu dò quét vào WAN mô phỏng",
        },
        "data": scan_alert,
    })
    print(f"CORRELATED_SCAN key={key}")
    print(formatted_scan)

    formatted_messages = []
    for alert in alerts:
        alert["data"]["fixture"] = True
        key, text = tg["message"](alert, cfg.get("dashboard_url") if cfg else None)
        formatted_messages.append((alert["rule"]["id"], key, text))
        print(f"--- SOC ALERT rule={alert['rule']['id']} key={key} ---")
        print(text)

    if send_telegram:
        for rule_id, key, text in formatted_messages:
            tg["send"](cfg["bot_token"], str(cfg["chat_id"]), text)
            print(f"SENT rule={rule_id} key={key} ok=true")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Containerized SOC detector and Telegram formatter")
    parser.add_argument("--self-test", action="store_true", help="Run correlation and SOC format verification")
    parser.add_argument("--fixtures", type=Path, default=Path("/app/fixtures"), help="Fixtures directory")
    parser.add_argument("--send-telegram", action="store_true", help="Send formatted alerts if config exists")
    parser.add_argument("--config", type=Path, default=Path("/etc/soc/cowrie-telegram.json"), help="Bot config JSON")
    args = parser.parse_args()

    app_dir = Path(__file__).resolve().parent
    if args.self_test:
        return run_self_test(args.fixtures, app_dir, args.send_telegram, args.config)
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
