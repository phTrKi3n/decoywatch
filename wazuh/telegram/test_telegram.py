import copy
import io
import json
from pathlib import Path
import runpy
import sys
import unittest
from urllib.error import HTTPError
from unittest.mock import Mock, patch

MODULE = Path(__file__).with_name("custom-cowrie-telegram")
SAMPLES = [
    {"rule": {"id": "100110", "description": "Cowrie SSH"}, "data": {
        "eventid": "cowrie.login.success", "protocol": "ssh", "timestamp": "2026-01-01T07:00:00+07:00",
        "src_ip": "192.0.2.10", "session": "fixture-ssh", "password": "private-value"}},
    {"rule": {"id": "100120", "description": "Firewall"}, "data": {
        "eventid": "lab.firewall.scan", "timestamp": "2026-01-01T00:00:00Z", "src_ip": "192.0.2.25",
        "dest_ip": "192.0.2.20", "port_count": "5", "event_id": "0" * 32, "fixture": "true"}},
]


class TelegramTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log = Mock()
        with patch.dict(sys.modules, {"syslog": cls.log}):
            cls.script = runpy.run_path(str(MODULE))

    def test_format(self):
        for alert, field in zip(SAMPLES, ("session", "event_id")):
            with self.subTest(field=field):
                key, message = self.script["message"](alert)
                self.assertEqual(key, alert["data"][field])
                self.assertIn("00:00:00+00:00", message)
                self.assertNotIn("private-value", message)
                self.assertEqual(message.startswith("[MẪU KIỂM THỬ]"), field == "event_id")

    def test_reject_invalid_fields(self):
        cases = [
            (0, "rule", "id", "99999"), (0, "rule", "description", "x" * 121),
            (0, "rule", "description", "a\nb"), (0, "data", "src_ip", "invalid"),
            (0, "data", "protocol", "telnet"), (0, "data", "timestamp", "2026-01-01T00:00:00"),
            (1, "data", "port_count", "4"), (1, "data", "port_count", 5.5),
            (1, "data", "event_id", "bad"), (1, "data", "dest_ip", None),
        ]
        for index, section, key, value in cases:
            with self.subTest(key=key, value=value):
                alert = copy.deepcopy(SAMPLES[index])
                alert[section][key] = value
                with self.assertRaises((TypeError, ValueError)):
                    self.script["message"](alert)
        alert = copy.deepcopy(SAMPLES[0])
        alert["data"].pop("session")
        with self.assertRaises(KeyError):
            self.script["message"](alert)

    def test_api_request(self):
        with patch("urllib.request.urlopen", return_value=io.BytesIO(b'{"ok":true}')) as response:
            self.script["send"]("123:dummy", "-123", "Test <text>")
        request = response.call_args.args[0]
        self.assertTrue(request.full_url.startswith("https://api.telegram.org/"))
        self.assertEqual(json.loads(request.data), {"chat_id": "-123", "text": "Test <text>"})
        self.assertEqual(response.call_args.kwargs["timeout"], 10)

    def test_success_log_contains_only_metrics(self):
        with patch("urllib.request.urlopen", return_value=io.BytesIO(b'{"ok":true}')), \
                patch.object(self.log, "syslog") as log, patch("sys.argv", [str(MODULE), "fixture.json"]), \
                patch("builtins.open", side_effect=[io.StringIO(json.dumps(SAMPLES[0])),
                                                   io.StringIO('{"bot_token":"123:dummy","chat_id":"1"}')]):
            self.assertEqual(self.script["main"](), 0)
        log.assert_called_once()
        metric = log.call_args.args[1]
        self.assertRegex(metric, r"^fixture-ssh \S+ \S+ \d+ms$")
        self.assertNotIn("dummy", metric)

    def test_errors_fail_without_success_log(self):
        failures = [
            {"side_effect": TimeoutError("private-token")},
            {"side_effect": HTTPError("https://example.com/private-token", 429, "rate limit", {}, None)},
            {"return_value": io.BytesIO(b'{"ok":false}')},
        ]
        for failure in failures:
            with self.subTest(failure=failure), patch("urllib.request.urlopen", **failure), \
                    patch.object(self.log, "syslog") as log, patch("sys.argv", [str(MODULE), "fixture.json"]), \
                    patch("builtins.open", side_effect=[io.StringIO(json.dumps(SAMPLES[0])),
                                                       io.StringIO('{"bot_token":"123:dummy","chat_id":"1"}')]):
                self.assertEqual(self.script["main"](), 1)
                self.assertEqual(log.call_count, 1)
                self.assertIn("send failed:", log.call_args.args[1])
                self.assertNotIn("private-token", log.call_args.args[1])


if __name__ == "__main__":
    unittest.main()
