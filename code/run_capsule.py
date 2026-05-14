"""Minimal demo of the Code Ocean release Files-panel stale-snapshot issue.

Writes /results/run_info.txt identifying which capsule produced it. Compare
what shows in the release capsule's Files panel against what shows inside
the latest Run in the timeline pane — they should differ once you re-run
the released version, demonstrating that the Files panel still shows the
editable's pre-release output.

Requires the "Code Ocean API Credentials" Secret attached to the capsule
(exposes API_KEY automatically when bound), plus a local utils.py module
that defines get_provenance().
"""

from utils import get_provenance

p = get_provenance()

info = (
    f"run timestamp: {p['run_timestamp']}\n"
    f"status:        {p['status']}\n"
    f"version:       {p['version']}\n"
    f"capsule ID:    {p['capsule_id']}\n"
    f"slug:          {p['slug']}\n"
    f"capsule URL:   {p['capsule_url']}\n"
)

with open("/results/run_info.txt", "w") as f:
    f.write(info)
print(info)
