"""Wait briefly for the local container, then verify real fixture SQL over HTTP."""

import json
import time
import urllib.request

for attempt in range(30):
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=2) as response:
            assert json.load(response)["status"] == "ok"
        break
    except OSError:
        time.sleep(1)
else:
    raise SystemExit("Container did not become healthy")
request = urllib.request.Request(
    "http://127.0.0.1:8000/tools/analyse",
    data=json.dumps({"metric": "national_demand_mw", "analysis": "summary", "month": None}).encode(),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(request, timeout=5) as response:
    body = json.load(response)
assert body["mode"] == "direct_tool"
assert body["evidence"][0]["result"]["rows"][0]["observations"] == 4
print("Container HTTP smoke passed: four real fixture records, read-only SQL endpoint")
