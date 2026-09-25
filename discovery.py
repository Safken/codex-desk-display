"""One-shot Codex usage probe. Python 3.10+, standard library only.

Only initialization and account read methods are sent. No turns are started.
Raw replies and subprocess stderr are never printed or persisted.
"""
import argparse
import asyncio
from datetime import datetime, timezone
import json
import math
import re
import hashlib


class ProbeError(Exception):
    """Safe-to-display error; never contains upstream message text."""

    def __init__(self, status, details=None):
        super().__init__(status)
        self.details = details


def error_details(error):
    """Classify errors using fixed labels, never echo upstream text."""
    if not isinstance(error, dict):
        return {"hints": []}
    message = error.get("message")
    message = message.lower() if isinstance(message, str) else ""
    labels = {
        "authentication": ("auth", "not logged in", "login", "sign in"),
        "request_parameters": ("params", "parameter", "invalid request", "missing field"),
        "unsupported_method": ("unknown method", "method not found"),
        "response_decoding": ("unknown variant", "decode", "decoding", "deserializ", "parse", "parsing"),
        "network": ("connect", "dns", "resolve", "network", "tls", "ssl"),
        "timeout": ("timeout", "timed out"),
        "access_denied": ("forbidden", "denied", "cloudflare"),
    }
    output = {"hints": [k for k, words in labels.items() if any(w in message for w in words)]}
    code = error.get("code")
    if type(code) is int and -(2**31) <= code < 2**31:
        output["rpc_code"] = code
    statuses = re.findall(r"\b(?:http(?: status)?|status(?: code)?)\D{0,8}([45]\d\d)\b", message)
    if statuses:
        output["http_status"] = int(statuses[0])
    return output


def number(value):
    return type(value) is int or (type(value) is float and math.isfinite(value))


def codex_bucket(result):
    """Select only the main Codex bucket."""
    if not isinstance(result, dict):
        return None
    buckets = result.get("rateLimitsByLimitId")
    if isinstance(buckets, dict):
        bucket = buckets.get("codex")
    else:
        bucket = result.get("rateLimits")
        if isinstance(bucket, dict) and bucket.get("limitId") not in (None, "codex"):
            return None
    if not isinstance(bucket, dict):
        return None
    return bucket


def credits(result):
    source = (codex_bucket(result) or {}).get('credits')
    if not isinstance(source, dict):
        return None
    balance = source.get('balance')
    if isinstance(balance, str) and len(balance) <= 64:
        try:
            balance = float(balance)
        except ValueError:
            balance = None
    if not number(balance) or not 0 <= balance <= 1e15:
        balance = None
    return {'balance': balance, 'unlimited': source.get('unlimited') is True}


def weekly(result):
    """Select the main Codex bucket's seven-day window."""
    bucket = codex_bucket(result)
    if bucket is None:
        return None
    candidates = [bucket.get(k) for k in ("primary", "secondary")]
    matches = [w for w in candidates if isinstance(w, dict)
               and w.get("windowDurationMins") == 10080]
    if len(matches) != 1:
        return None
    w = matches[0]
    used, reset = w.get("usedPercent"), w.get("resetsAt")
    if not number(used) or not 0 <= used <= 100:
        return None
    if type(reset) is not int or reset <= 0:
        return None
    try:
        reset_iso = datetime.fromtimestamp(reset, timezone.utc).isoformat()
    except (ValueError, OverflowError, OSError):
        return None
    return {"used_percent": used, "remaining_percent": 100 - used,
            "window_minutes": 10080, "resets_at": reset_iso}


def token_summary(result):
    source = result.get("summary") if isinstance(result, dict) else None
    if not isinstance(source, dict):
        return None
    # Only explicit numeric fields; never pass through arbitrary response data.
    output = {}
    for key in ("lifetimeTokens", "peakDailyTokens"):
        value = source.get(key)
        output[key] = value if type(value) is int and value >= 0 else None
    return output if any(v is not None for v in output.values()) else None


def daily_tokens(result):
    buckets = result.get("dailyUsageBuckets") if isinstance(result, dict) else None
    if not isinstance(buckets, list) or len(buckets) > 3660:
        return None
    output = {}
    for bucket in buckets:
        if not isinstance(bucket, dict):
            return None
        day, tokens = bucket.get("startDate"), bucket.get("tokens")
        if not isinstance(day, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
            return None
        try:
            datetime.strptime(day, "%Y-%m-%d")
        except ValueError:
            return None
        if type(tokens) is not int or not 0 <= tokens < 2**63 or day in output:
            return None
        output[day] = tokens
    return [{"date": day, "tokens": output[day]} for day in sorted(output)[-370:]]


class AppServer:
    def __init__(self, command, timeout=20):
        self.command = command
        self.timeout = timeout
        self.process = None
        self.sequence = 0

    async def __aenter__(self):
        try:
            self.process = await asyncio.create_subprocess_exec(
                *self.command, stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
                limit=1024 * 1024)
        except OSError:
            raise ProbeError("app_server_start_failed") from None
        try:
            await self.request("initialize", {"clientInfo": {
                "name": "codex_usage_monitor", "title": "Codex Usage Monitor",
                "version": "0.1.0"}})
            await self.send({"method": "initialized", "params": {}})
        except BaseException:
            await self.close()
            raise
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def close(self):
        p = self.process
        if p is None:
            return
        if p.stdin:
            p.stdin.close()
        if p.returncode is None:
            try:
                p.terminate()
            except ProcessLookupError:
                pass
            try:
                await asyncio.wait_for(p.wait(), 3)
            except asyncio.TimeoutError:
                p.kill()
                await p.wait()

    async def send(self, message):
        try:
            self.process.stdin.write((json.dumps(message) + "\n").encode())
            await self.process.stdin.drain()
        except (OSError, ConnectionError):
            raise ProbeError("app_server_disconnected") from None

    async def request(self, method, params=None):
        if method not in {"initialize", "account/read", "account/rateLimits/read", "account/usage/read"}:
            raise ProbeError("method_not_allowed")
        self.sequence += 1
        request_id = self.sequence

        async def exchange():
            message = {"method": method, "id": request_id,
                       "params": params if params is not None else {}}
            await self.send(message)
            while True:
                try:
                    line = await self.process.stdout.readline()
                    reply = json.loads(line)
                except (ValueError, UnicodeError):
                    raise ProbeError("invalid_app_server_response") from None
                if not isinstance(reply, dict):
                    raise ProbeError("invalid_app_server_response")
                if "method" in reply:
                    if "id" in reply:
                        raise ProbeError("unexpected_server_request")
                    continue
                if reply.get("id") != request_id:
                    continue
                if "error" in reply:
                    error = reply["error"]
                    code = error.get("code") if isinstance(error, dict) else None
                    if code == -32601:
                        raise ProbeError("method_unavailable", error_details(error))
                    raise ProbeError("account_request_failed_check_login_or_connectivity", error_details(error))
                if not isinstance(reply.get("result"), dict):
                    raise ProbeError("invalid_app_server_response")
                return reply["result"]

        try:
            return await asyncio.wait_for(exchange(), self.timeout)
        except asyncio.TimeoutError:
            raise ProbeError("app_server_timeout") from None


async def probe(command, timeout=20, include_tokens=False, diagnostics=False, track_account=False):
    output = {"source": "codex_app_server", "weekly": None,
              "token_summary": None, "token_status": "not_requested"}
    try:
        async with AppServer(command, timeout) as client:
            if diagnostics or track_account:
                try:
                    account_result = await client.request("account/read", {"refreshToken": False})
                    account = account_result.get("account")
                    kind = account.get("type") if isinstance(account, dict) else None
                    output["auth_state"] = (kind if kind in {"chatgpt", "apiKey"}
                                            else "not_logged_in" if account is None else "other")
                    if track_account:
                        identity = account.get("email") if isinstance(account, dict) else None
                        if kind != "chatgpt" or not isinstance(identity, str) or not identity.strip():
                            raise ProbeError("account_identity_unavailable")
                        output["account_fingerprint"] = hashlib.sha256(identity.strip().lower().encode()).hexdigest()
                except ProbeError as exc:
                    if track_account:
                        raise
                    output["auth_state"] = "check_failed"
                    output["auth_error"] = exc.details
            limits = await client.request("account/rateLimits/read")
            output["weekly"] = weekly(limits)
            output["credits"] = credits(limits)
            output["weekly_observed_at"] = datetime.now(timezone.utc).isoformat()
            output["status"] = "ok" if output["weekly"] else "weekly_unavailable"
            if include_tokens:
                try:
                    token_result = await client.request("account/usage/read")
                    output["token_summary"] = token_summary(token_result)
                    output["daily_tokens"] = daily_tokens(token_result)
                    output["tokens_observed_at"] = datetime.now(timezone.utc).isoformat()
                    output["token_status"] = ("reported_scope_unverified"
                                              if output["token_summary"] else "unavailable")
                except ProbeError as exc:
                    output["token_status"] = str(exc)
                    if diagnostics:
                        output["token_error"] = exc.details
    except ProbeError as exc:
        output["status"] = str(exc)
        if diagnostics:
            output["error_details"] = exc.details
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex", default="codex", help="Codex executable path")
    parser.add_argument("--timeout", type=float, default=20, help="Seconds per request (1–120)")
    parser.add_argument("--include-tokens", action="store_true")
    parser.add_argument("--diagnostics", action="store_true", help="Include safe auth category and error labels")
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or not 1 <= args.timeout <= 120:
        parser.error("timeout must be between 1 and 120 seconds")
    result = asyncio.run(probe([args.codex, "app-server"], args.timeout, args.include_tokens, args.diagnostics))
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
