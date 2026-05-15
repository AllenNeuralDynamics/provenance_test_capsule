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

import json
from pathlib import Path

from utils import get_code_ocean_provenance, get_local_git_provenance

provenance = {
    "code_ocean": get_code_ocean_provenance(),
    "local_git": get_local_git_provenance(),
}

out_dir = (
    Path("/results")
    if Path("/results").is_dir()
    else Path(__file__).resolve().parent.parent / "results"
)
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / "run_info.json"
out_path.write_text(json.dumps(provenance, indent=2))

print(json.dumps(provenance, indent=2))
print(f"wrote {out_path}")
