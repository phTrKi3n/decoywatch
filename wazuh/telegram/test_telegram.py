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
    {"rule": {"id": "100110", "description": "Cowrie SSH", "level": 7}, "data": {
        "eventid": "cowrie.login.success", "protocol": "ssh", "timestamp": "2026-01-01T07:00:00+07:00",
        "src_ip": "192.0.2.10", "session": "fixture-ssh", "password": "private-value"}},
    {"rule": {"id": "100112", "description": "SSH Brute Force", "level": 10}, "data": {
        "eventid": "cowrie.login.failed", "protocol": "ssh", "timestamp": "2026-01-01T00:00:02Z",
        "src_ip": "192.0.2.10", "session": "fixture-brute", "password": "private-password"}},
    {"rule": {"id": "100115", "description": "Post Exploitation", "level": 9}, "data": {
        "eventid": "cowrie.command.input", "timestamp": "2026-01-01T00:00:04Z",
        "src_ip": "192.0.2.10", "session": "fixture-cmd", "input": "cat /etc/shadow"}},
    {"rule": {"id": "100120", "description": "Firewall", "level": 7}, "data": {
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
        for alert, field in zip(SAMPLES, ("session", "session", "session", "event_id")):
            with self.subTest(rule=alert["rule"]["id"]):
                key, message = self.script["message"](alert)
                self.assertEqual(key, alert["data"][field])
                self.assertIn("<pre>", message)
                self.assertIn("<blockquote>", message)
                self.assertIn("<b>WAZUH SIEM</b>", message)
                self.assertIn("<code>", message)
                self.assertIn(f"RULE #{alert['rule']['id']}", message)
                self.assertIn("MITRE", message)
                self.assertIn("00:00:", message)
                self.assertIn("+07:00", message)
                self.assertNotIn("private-value", message)
                self.assertNotIn("private-password", message)
                self.assertNotIn("/etc/shadow", message)
                self.assertEqual(message.startswith("[MẪU KIỂM THỬ]"), field == "event_id")

    def test_html_escaping_prevents_tag_injection(self):
        alert = copy.deepcopy(SAMPLES[0])
        alert["rule"]["description"] = '<script>alert(1)</script> & "x"'
        _, message = self.script["message"](alert)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt; &amp; &quot;x&quot;", message)
        self.assertNotIn("<script>", message)

    def test_post_exploitation_actions_and_hides_url(self):
        dl_alert = {
            "rule": {"id": "100115", "description": "File Download", "level": 9},
            "data": {
                "eventid": "cowrie.session.file_download",
                "timestamp": "2026-01-01T00:00:05Z",
                "src_ip": "192.0.2.10",
                "session": "fixture-dl",
                "url": "http://198.51.100.1/secret-payload.sh",
            },
        }
        key, msg = self.script["message"](dl_alert)
        self.assertEqual(key, "fixture-dl")
        self.assertIn("Payload Download Attempt", msg)
        self.assertNotIn("secret-payload.sh", msg)

    def test_reject_invalid_fields(self):
        cases = [
            (0, "rule", "id", "99999"), (0, "rule", "description", "x" * 121),
            (0, "rule", "description", "a\nb"), (0, "rule", "level", True),
            (0, "data", "src_ip", "invalid"), (0, "data", "src_ip", True),
            (0, "data", "src_ip", 2130706433), (0, "data", "protocol", "telnet"),
            (0, "data", "timestamp", "2026-01-01T00:00:00"),
            (1, "data", "protocol", "telnet"),
            (2, "data", "eventid", "cowrie.session.closed"),
            (3, "data", "port_count", "4"), (3, "data", "port_count", 5.5),
            (3, "data", "port_count", True), (3, "data", "dest_ip", 3232235777),
            (3, "data", "event_id", "bad"), (3, "data", "dest_ip", None),
        ]
        for index, section, key, value in cases:
            with self.subTest(index=index, key=key, value=value):
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
            self.script["send"]("123:dummy", "-123", "Test &lt;text&gt;")
        request = response.call_args.args[0]
        self.assertTrue(request.full_url.startswith("https://api.telegram.org/"))
        self.assertEqual(
            json.loads(request.data),
            {
                "chat_id": "-123",
                "text": "Test &lt;text&gt;",
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
        )
        self.assertEqual(response.call_args.kwargs["timeout"], 10)

    def test_dashboard_url_is_configurable_and_optional(self):
        _, message = self.script["message"](SAMPLES[0], "https://10.20.30.40:8443/wazuh")
        self.assertIn("https://10.20.30.40:8443/wazuh", message)
        self.assertNotIn("192.168.100.20", message)
        _, message = self.script["message"](SAMPLES[0])
        self.assertNotIn("https://", message)

    def test_reject_invalid_dashboard_url(self):
        for value in (True, "", "http://example.test", "https://u:p@example.test", "https://",
                      "https://example.test/#x", "https://example.test/?token=private",
                      "https://example.test/\nsecret", "https://example.test:99999", "https://example.test:0",
                      "https://example.test/?", "https://example.test/#"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.script["message"](SAMPLES[0], value)

    def test_main_reads_dashboard_url_from_config(self):
        config = '{"bot_token":"123:dummy","chat_id":"1","dashboard_url":"https://10.20.30.40"}'
        with patch("urllib.request.urlopen", return_value=io.BytesIO(b'{"ok":true}')) as response, \
                patch("sys.argv", [str(MODULE), "fixture.json"]), \
                patch("builtins.open", side_effect=[io.StringIO(json.dumps(SAMPLES[0])), io.StringIO(config)]):
            self.assertEqual(self.script["main"](), 0)
        self.assertIn("https://10.20.30.40", json.loads(response.call_args.args[0].data)["text"])

    def test_rate_limit_retries_only_confirmed_rejection(self):
        limited = HTTPError("https://example.test", 429, "rate limit", {},
                            io.BytesIO(b'{"ok":false,"parameters":{"retry_after":2}}'))
        with patch("urllib.request.urlopen", side_effect=[limited, io.BytesIO(b'{"ok":true}')]) as request, \
                patch("time.sleep") as sleep:
            self.script["send"]("123:dummy", "1", "fixture")
        self.assertEqual(request.call_count, 2)
        sleep.assert_called_once_with(2)

    def test_rate_limit_retry_is_bounded(self):
        errors = [HTTPError("https://example.test", 429, "rate limit", {},
                            io.BytesIO(b'{"ok":false,"parameters":{"retry_after":1}}')) for _ in range(3)]
        with patch("urllib.request.urlopen", side_effect=errors) as request, patch("time.sleep") as sleep:
            with self.assertRaises(HTTPError):
                self.script["send"]("123:dummy", "1", "fixture")
        self.assertEqual(request.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    def test_rate_limit_rejects_unbounded_or_invalid_delay(self):
        for delay in (0, 6, True, "2", 1.5, None):
            limited = HTTPError("https://example.test", 429, "rate limit", {},
                                io.BytesIO(json.dumps({"ok": False, "parameters": {"retry_after": delay}}).encode()))
            with self.subTest(delay=delay), patch("urllib.request.urlopen", side_effect=limited) as request, \
                    patch("time.sleep") as sleep, self.assertRaises((ValueError, HTTPError)):
                self.script["send"]("123:dummy", "1", "fixture")
            self.assertEqual(request.call_count, 1)
            sleep.assert_not_called()

    def test_invalid_rate_limit_body_fails_without_retry(self):
        for body in (b'not-json', b'[]', b'{"ok":false,"parameters":[]}', b'{"ok":true}'):
            error = HTTPError("https://example.test", 429, "rate limit", {}, io.BytesIO(body))
            with self.subTest(body=body), patch("urllib.request.urlopen", side_effect=error) as request, \
                    patch("time.sleep") as sleep, self.assertRaises(ValueError):
                self.script["send"]("123:dummy", "1", "fixture")
            self.assertEqual(request.call_count, 1)
            sleep.assert_not_called()

    def test_ambiguous_network_failures_are_not_retried(self):
        for error in (TimeoutError(), HTTPError("https://example.test", 503, "unavailable", {}, None)):
            with self.subTest(error=type(error).__name__), \
                    patch("urllib.request.urlopen", side_effect=error) as request, \
                    patch("time.sleep") as sleep, self.assertRaises((TimeoutError, HTTPError)):
                self.script["send"]("123:dummy", "1", "fixture")
            self.assertEqual(request.call_count, 1)
            sleep.assert_not_called()

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
