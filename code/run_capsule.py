# """Minimal demo of the Code Ocean release Files-panel stale-snapshot issue.

# Writes /results/run_info.txt identifying which capsule produced it. Compare
# what shows in the release capsule's Files panel against what shows inside
# the latest Run in the timeline pane — they should differ once you re-run
# the released version, demonstrating that the Files panel still shows the
# editable's pre-release output.

# Requires the "Code Ocean API Credentials" Secret attached to the capsule
# (exposes API_KEY automatically when bound), plus a local utils.py module
# that defines get_provenance().
# """

# import json
# import os
# import subprocess
# from pathlib import Path

# from utils import _get_json, get_code_ocean_provenance, get_local_git_provenance

# provenance = {
#     "code_ocean": get_code_ocean_provenance(),
#     "local_git": get_local_git_provenance(),
# }

# # --- experiment-only probes (remove before extracting utils.py as a library) ---
# # Prospecting for where CO stores the linked-GitHub repo URL / commit hash:
# # raw API responses, all CO_* env vars, filesystem scan for .git/ at unusual paths.

# probes: dict = {
#     "co_env_vars": {k: v for k, v in sorted(os.environ.items()) if k.startswith("CO_")},
# }

# try:
#     capsule_id = os.environ["CO_CAPSULE_ID"]
#     computation_id = os.environ["CO_COMPUTATION_ID"]
#     token = os.environ["API_KEY"]
#     probes["raw_capsule"] = _get_json(f"/capsules/{capsule_id}", token)
#     probes["raw_computation"] = _get_json(f"/computations/{computation_id}", token)
# except KeyError:
#     pass


# def _safe_run(args: list[str]) -> str:
#     try:
#         r = subprocess.run(
#             args,
#             stdout=subprocess.PIPE,
#             stderr=subprocess.DEVNULL,
#             text=True,
#             timeout=20,
#         )
#         return r.stdout.strip()
#     except (subprocess.SubprocessError, FileNotFoundError) as e:
#         return f"(error: {e})"


# probes["ls_slash_code"] = _safe_run(["ls", "-la", "/code"])
# probes["find_git_dirs"] = _safe_run([
#     "find", "/", "-maxdepth", "5", "-name", ".git",
#     "-not", "-path", "/proc/*", "-not", "-path", "/sys/*",
# ])

# provenance["probes"] = probes

# out_dir = (
#     Path("/results")
#     if Path("/results").is_dir()
#     else Path(__file__).resolve().parent.parent / "results"
# )
# out_dir.mkdir(parents=True, exist_ok=True)
# out_path = out_dir / "run_info.json"
# out_path.write_text(json.dumps(provenance, indent=2))

# print(json.dumps(provenance, indent=2))
# print(f"wrote {out_path}")

import base64, json, os, urllib.request

token = os.environ["API_KEY"]
url = f"https://codeocean.allenneuraldynamics.org/api/v1/computations/{os.environ['CO_COMPUTATION_ID']}"
auth = base64.b64encode(f"{token}:".encode()).decode()
req = urllib.request.Request(url, headers={"Authorization": f"Basic {auth}"})
print(json.loads(urllib.request.urlopen(req).read())["version"])