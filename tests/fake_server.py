"""Synthetic subprocess for protocol tests. Does not contact OpenAI."""
import json
import sys
import time

mode = sys.argv[1]
initialized = False
for line in sys.stdin:
    request = json.loads(line)
    method = request["method"]
    if method == "initialized":
        initialized = True
        continue
    if method == "initialize":
        result = {}
    elif not initialized:
        raise RuntimeError("Missing initialized notification")
    elif "params" not in request:
        print(json.dumps({"id": request["id"], "error": {
            "code": -32600, "message": "missing field params SECRET_SENTINEL"}}), flush=True)
        continue
    elif method == "account/read":
        result = {"account": {"type": "chatgpt", "email": "SECRET_SENTINEL"}}
    elif method == "account/rateLimits/read":
        if mode == "timeout":
            time.sleep(10)
        if mode == "malformed":
            print("NOT JSON", flush=True)
            continue
        if mode == "error":
            print(json.dumps({"id": request["id"], "error": {
                "code": -32000, "message": "SECRET_SENTINEL"}}), flush=True)
            continue
        result = {"accountId": "SECRET_SENTINEL", "rateLimits": {
            "limitId": "codex", "primary": {"usedPercent": 87,
            "windowDurationMins": 10080, "resetsAt": 1790298894}}}
        print(json.dumps({"method": "ignored/notification", "params": {}}), flush=True)
    elif method == "account/usage/read":
        print(json.dumps({"id": request["id"], "error": {
            "code": -32601, "message": "SECRET_SENTINEL"}}), flush=True)
        continue
    else:
        raise RuntimeError("Unexpected method")
    print(json.dumps({"id": request["id"], "result": result}), flush=True)
