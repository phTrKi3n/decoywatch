import contextlib
import io
import json
from pathlib import Path
import runpy
import shutil
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
ENTRY = runpy.run_path(str(ROOT / "docker/entrypoint.py"))


class SelfTestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.app = Path(self.temp.name) / "app"
        self.app.mkdir()
        shutil.copyfile(ROOT / "wazuh/firewall/firewall.py", self.app / "firewall.py")
        shutil.copyfile(ROOT / "wazuh/telegram/custom-cowrie-telegram", self.app / "custom-cowrie-telegram")
        self.fixtures = Path(self.temp.name) / "fixtures"
        shutil.copytree(ROOT / "wazuh/fixtures", self.fixtures)

    def run_check(self, send=False):
        self.output = io.StringIO()
        with contextlib.redirect_stdout(self.output), patch.dict(sys.modules, {"syslog": Mock()}):
            return ENTRY["run_self_test"](self.fixtures, self.app, send, Path(self.temp.name) / "absent.json")

    def test_complete_fixture_set_passes_and_is_labeled(self):
        self.assertEqual(self.run_check(), 0)
        output = self.output.getvalue()
        self.assertEqual(output.count("--- SOC ALERT rule="), 4)
        self.assertEqual(output.count("[MẪU KIỂM THỬ]"), 5)

    def test_missing_required_file_fails(self):
        for name in ("nftables-block.log", "telegram-alerts.ndjson"):
            with self.subTest(name=name):
                file = self.fixtures / name
                original = file.read_bytes()
                file.unlink()
                with self.assertRaises(FileNotFoundError):
                    self.run_check()
                file.write_bytes(original)

    def test_empty_required_file_fails(self):
        for name in ("nftables-block.log", "telegram-alerts.ndjson"):
            with self.subTest(name=name):
                file = self.fixtures / name
                original = file.read_bytes()
                file.write_text("\n", encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.run_check()
                file.write_bytes(original)

    def test_incomplete_rule_coverage_fails(self):
        file = self.fixtures / "telegram-alerts.ndjson"
        rows = file.read_text(encoding="utf-8").splitlines()
        for missing in range(4):
            with self.subTest(missing=missing):
                file.write_text("\n".join(rows[:missing] + rows[missing + 1:]), encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.run_check()

    def test_explicit_send_without_config_fails(self):
        with self.assertRaises(FileNotFoundError):
            self.run_check(send=True)

    def test_firewall_fixture_must_contain_an_eligible_event(self):
        for line in ("garbage", "LAB_WAN_BLOCK IN=ens37 SRC=invalid DST=192.168.100.20 PROTO=TCP DPT=22",
                     "LAB_WAN_BLOCK IN=ens33 SRC=192.0.2.10 DST=192.168.100.20 PROTO=TCP DPT=22"):
            with self.subTest(line=line):
                (self.fixtures / "nftables-block.log").write_text(line, encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.run_check()


if __name__ == "__main__":
    unittest.main()
