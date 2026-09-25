import asyncio
import copy
import json
from pathlib import Path
import sys
import unittest

from discovery import AppServer, ProbeError, error_details, probe, token_summary, weekly, credits

WINDOW = {"usedPercent": 87, "windowDurationMins": 10080, "resetsAt": 1790298894}


class NormalizationTests(unittest.TestCase):
    def test_credits_normalization_and_bucket_scope(self):
        for value in ('123.75', 123.75, 0):
            self.assertEqual(credits({'rateLimits': {'credits': {'balance': value}}})['balance'], float(value))
        for value in (None, True, -1, 'nan', 'inf', 'bad', {}, 10**1000):
            self.assertIsNone(credits({'rateLimits': {'credits': {'balance': value}}})['balance'])
        self.assertIsNone(credits({'rateLimitsByLimitId': {'other': {'credits': {'balance': '9'}}}}))
        self.assertTrue(credits({'rateLimits': {'credits': {'unlimited': True}}})['unlimited'])
        self.assertIsNone(credits({}))

    def test_diagnostics_are_allowlisted(self):
        details = error_details({"code": -32600,
            "message": "missing field params HTTP status 403 SECRET_SENTINEL"})
        self.assertEqual(details, {"rpc_code": -32600,
            "hints": ["request_parameters"], "http_status": 403})
        self.assertNotIn("SECRET_SENTINEL", json.dumps(details))
        self.assertEqual(error_details({"message": "unknown variant SECRET_SENTINEL"}),
                         {"hints": ["response_decoding"]})

    def test_weekly_can_be_primary_or_secondary(self):
        for key in ("primary", "secondary"):
            result = weekly({"rateLimits": {key: WINDOW}})
            self.assertEqual(result["remaining_percent"], 13)
            self.assertEqual(result["resets_at"], "2026-09-25T01:14:54+00:00")

    def test_bucket_map_takes_precedence(self):
        result = {"rateLimits": {"primary": WINDOW}, "rateLimitsByLimitId": {
            "codex": {"secondary": dict(WINDOW, usedPercent=20)}}}
        self.assertEqual(weekly(result)["remaining_percent"], 80)
        result["rateLimitsByLimitId"] = {"other": {"primary": WINDOW}}
        self.assertIsNone(weekly(result))

    def test_invalid_and_missing_values_are_not_zero(self):
        for value in (None, True, -1, 101, 10**1000, "87", float("nan"), float("inf")):
            self.assertIsNone(weekly({"rateLimits": {
                "primary": dict(WINDOW, usedPercent=value)}}))
        for value in (None, True, -1, 10**100, "1790298894"):
            self.assertIsNone(weekly({"rateLimits": {
                "primary": dict(WINDOW, resetsAt=value)}}))
        self.assertIsNone(weekly({}))

    def test_other_windows_and_ambiguous_weekly_are_rejected(self):
        self.assertIsNone(weekly({"rateLimits": {
            "primary": dict(WINDOW, windowDurationMins=300)}}))
        self.assertIsNone(weekly({"rateLimits": {"primary": WINDOW, "secondary": WINDOW}}))
        self.assertIsNone(weekly({"rateLimits": {"limitId": "other", "primary": WINDOW}}))

    def test_allowlist_does_not_mutate_or_leak(self):
        result = {"rateLimits": {"primary": WINDOW}, "accountId": "SECRET_SENTINEL"}
        before = copy.deepcopy(result)
        self.assertNotIn("SECRET_SENTINEL", json.dumps(weekly(result)))
        self.assertEqual(result, before)
        self.assertEqual(token_summary({"summary": {"lifetimeTokens": 0,
            "peakDailyTokens": None, "secret": "SECRET_SENTINEL"}}),
            {"lifetimeTokens": 0, "peakDailyTokens": None})
        self.assertIsNone(token_summary({"summary": {"lifetimeTokens": True}}))


class ProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_diagnostics_keep_account_identity_private(self):
        result = await self.run_probe("ok", diagnostics=True, include_tokens=True)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["auth_state"], "chatgpt")
        self.assertEqual(result["token_error"]["rpc_code"], -32601)
        self.assertNotIn("SECRET_SENTINEL", json.dumps(result))

    async def run_probe(self, mode, **kwargs):
        return await probe([sys.executable, str(Path(__file__).with_name("fake_server.py")), mode],
                           **kwargs)

    async def test_handshake_notification_and_optional_failure(self):
        result = await self.run_probe("ok", include_tokens=True)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["weekly"]["remaining_percent"], 13)
        self.assertEqual(result["token_status"], "method_unavailable")
        self.assertNotIn("SECRET_SENTINEL", json.dumps(result))

    async def test_timeout_is_bounded(self):
        result = await asyncio.wait_for(self.run_probe("timeout", timeout=0.5), 5)
        self.assertEqual(result["status"], "app_server_timeout")

    async def test_error_is_sanitized(self):
        result = await self.run_probe("error")
        self.assertEqual(result["status"], "account_request_failed_check_login_or_connectivity")
        self.assertNotIn("SECRET_SENTINEL", json.dumps(result))

    async def test_malformed_response(self):
        self.assertEqual((await self.run_probe("malformed"))["status"], "invalid_app_server_response")

    async def test_mutation_not_allowed(self):
        client = AppServer([])
        with self.assertRaisesRegex(ProbeError, "method_not_allowed"):
            await client.request("turn/start")


if __name__ == "__main__":
    unittest.main()
