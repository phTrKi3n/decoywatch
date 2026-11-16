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
    fw = load_firewall(app_dir / "firewall.py")
    tg = runpy.run_path(str(app_dir / "custom-cowrie-telegram"))

    fw.check()

    nft_log = fixtures_dir / "nftables-block.log"
    if nft_log.exists():
        state = collections.OrderedDict()
        lines = nft_log.read_text(encoding="utf-8").splitlines()
        emitted = [fw.event(line, idx, state) for idx, line in enumerate(lines)]
        emitted = [e for e in emitted if e is not None]
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
    alerts_file = fixtures_dir / "telegram-alerts.ndjson"
    if alerts_file.exists():
        for raw_line in alerts_file.read_text(encoding="utf-8").splitlines():
            if not raw_line.strip():
                continue
            alert = json.loads(raw_line)
            key, text = tg["message"](alert)
            formatted_messages.append((alert["rule"]["id"], key, text))
            print(f"--- SOC ALERT rule={alert['rule']['id']} key={key} ---")
            print(text)

    if send_telegram:
        if not config_path.is_file():
            print(f"SKIP send: config not mounted at {config_path}")
            return 0
        cfg = json.loads(config_path.read_text(encoding="utf-8-sig"))
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
