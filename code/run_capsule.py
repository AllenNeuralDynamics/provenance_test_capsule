"""Minimal demo of the Code Ocean release Files-panel stale-snapshot issue.

Writes /results/run_info.txt identifying which capsule produced it (editable
vs released, slug, GUID, version) and when. Compare what shows in the release
capsule's Files panel against what shows inside the latest Run in the timeline
pane — they should differ once you re-run the released version, demonstrating
that the Files panel still shows the editable's pre-release output.

Requires the "Code Ocean API Credentials" Secret attached to the capsule —
it exposes API_KEY automatically when bound.
"""

import base64
import json
import os
import urllib.request
from datetime import datetime, timezone

capsule_id = os.environ["CO_CAPSULE_ID"]
auth = base64.b64encode(f"{os.environ['API_KEY']}:".encode()).decode()
req = urllib.request.Request(
    f"https://codeocean.allenneuraldynamics.org/api/v1/capsules/{capsule_id}",
    headers={"Authorization": f"Basic {auth}"},
)
with urllib.request.urlopen(req, timeout=10) as resp:
    meta = json.loads(resp.read())

# Also probe the computation endpoint — does it carry any undocumented field
# that identifies which specific release version this run was launched from?
comp_req = urllib.request.Request(
    f"https://codeocean.allenneuraldynamics.org/api/v1/computations/{os.environ['CO_COMPUTATION_ID']}",
    headers={"Authorization": f"Basic {auth}"},
)
with urllib.request.urlopen(comp_req, timeout=10) as resp:
    comp_meta = json.loads(resp.read())
print("=== Computation API response ===")
print(json.dumps(comp_meta, indent=2, sort_keys=True))
print("================================")

if meta.get("status") == "release":
    # Undocumented but observed: the computation endpoint returns "version"
    # as an integer = the major version of the release this run was launched
    # from. Look up the matching entry in the capsule's versions list to also
    # get the minor version.
    running_major = comp_meta.get("version")
    match = next(
        (v for v in (meta.get("versions") or []) if v.get("major_version") == running_major),
        {},
    )
    version_label = f"v{running_major}.{match.get('minor_version', 0)}"
else:
    version_label = "editable"

info = (
    f"run timestamp: {datetime.now(timezone.utc).isoformat()}\n"
    f"status:        {meta.get('status')}\n"
    f"version:       {version_label}\n"
    f"capsule ID:    {capsule_id}\n"
    f"slug:          {meta.get('slug')}\n"
    f"capsule URL:   https://codeocean.allenneuraldynamics.org/capsule/{meta.get('slug')}/tree\n"
)
with open("/results/run_info.txt", "w") as f:
    f.write(info)
print(info)
