"""Helpers for discovering the running Code Ocean capsule's provenance.

The primary entry point is :func:`get_provenance`, which queries the Code
Ocean REST API from inside a running capsule and returns a dict suitable for
populating provenance fields in AIND metadata (e.g. the `Code` object in
aind-data-schema's `processing.json`).

This module is stdlib-only — no Code Ocean SDK dependency.

Required runtime environment:

  - ``CO_CAPSULE_ID``     — auto-injected by Code Ocean.
  - ``CO_COMPUTATION_ID`` — auto-injected by Code Ocean.
  - ``API_KEY``           — exposed when the "Code Ocean API Credentials"
                            Secret is attached to the capsule in
                            Capsule Settings → Credentials.

Example:

    >>> from aind_code_ocean_utils import get_provenance
    >>> p = get_provenance()
    >>> p["version"]
    'v3.0'
    >>> p["capsule_url"]
    'https://codeocean.allenneuraldynamics.org/capsule/5336256/tree'
"""

import base64
import json
import os
import re
import subprocess
import urllib.request
from datetime import datetime, timezone
from typing import Any

_CO_API_BASE = "https://codeocean.allenneuraldynamics.org/api/v1"


def _get_json(path: str, token: str) -> dict[str, Any]:
    """Issue a Basic-Auth GET against the Code Ocean API and return parsed JSON."""
    auth = base64.b64encode(f"{token}:".encode()).decode()
    req = urllib.request.Request(
        f"{_CO_API_BASE}{path}",
        headers={"Authorization": f"Basic {auth}"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def get_code_ocean_provenance() -> dict[str, Any]:
    """Look up provenance for the currently running Code Ocean capsule.

    Returns a dict with the following keys:

      ``status``         : ``"release"`` or ``"non_release"`` — string from CO's
                           capsule record.
      ``is_released``    : ``bool`` — convenience, ``status == "release"``.
      ``version``        : ``str`` — version label. ``"v{major}.{minor}"`` when
                           running a specific release (e.g. ``"v3.0"``);
                           ``"editable"`` when running a non-released capsule.
      ``version_major``  : ``int`` or ``None`` — major version when running a
                           release; ``None`` otherwise.
      ``version_minor``  : ``int`` or ``None`` — minor version when running a
                           release; ``None`` otherwise.
      ``capsule_id``     : ``str`` — capsule UUID (matches ``CO_CAPSULE_ID``).
      ``computation_id`` : ``str`` — UUID of this run (matches
                           ``CO_COMPUTATION_ID``).
      ``slug``           : ``str`` — short numeric ID used in the CO web URL.
      ``capsule_url``    : ``str`` — canonical web URL of this capsule, of
                           the form
                           ``https://codeocean.allenneuraldynamics.org/capsule/<slug>/tree``.
      ``commit_hash``    : ``None`` — the CO REST API does not expose the git
                           commit hash for a release in any documented or
                           undocumented endpoint we've found. Included in the
                           return dict for interface stability so callers can
                           write ``provenance["commit_hash"]`` unconditionally.
      ``run_timestamp``  : ``str`` — ISO 8601 UTC timestamp of when Code Ocean
                           recorded the start of this computation (from the
                           computation endpoint's ``created`` epoch field).
                           More canonical than calling ``datetime.now()`` in
                           user code because it reflects CO's view of when
                           the run began rather than when this function was
                           called.

    Implementation notes — particularly relevant for anyone debugging or
    extending this:

    - The version of a specific release run is discovered by querying
      ``GET /api/v1/computations/{CO_COMPUTATION_ID}`` and reading the
      top-level ``version`` field. This field is **partially documented**: it
      appears in the CO REST API reference only as a sub-field of pipeline
      ``processes``, with documented type ``boolean``. Empirically, for a
      single-capsule release run, ``version`` is returned at the top level of
      the response with type ``int`` (the major version of the release the
      run was launched from). This was discovered by trial and error — CO's
      docs do not describe it for non-pipeline runs. The CO Capsule endpoint
      response, by contrast, lists *all* releases of the capsule but no
      indicator of which one is currently running, so the capsule endpoint
      alone is not sufficient to identify the running version.

    - The ``commit_hash`` field is reserved for forward-compatibility. As of
      this writing, no Code Ocean API endpoint we've inspected returns the
      git commit hash for a release. If Code Ocean adds it (e.g. via the
      documented but absent ``submission.commit`` field on the capsule
      object, or via a new env var), this function can populate the field
      without changing its signature.

    When the required CO env vars are not present (e.g. running on a laptop),
    returns a no-op dict with ``status="no_code_ocean"`` and a ``message``
    field explaining what was missing — never raises ``KeyError``. This lets
    callers invoke it unconditionally without an outer try/except.

    Raises:
      ``urllib.error.HTTPError`` on a non-2xx response from the CO API
      (commonly a 401 if ``API_KEY`` is missing the Capsules scope, or a 404
      if ``CO_CAPSULE_ID`` doesn't resolve).
    """
    try:
        capsule_id = os.environ["CO_CAPSULE_ID"]
        computation_id = os.environ["CO_COMPUTATION_ID"]
        token = os.environ["API_KEY"]
    except KeyError as e:
        return {
            "status": "no_code_ocean",
            "message": f"Missing Code Ocean env var {e}. Likely not running in a CO capsule.",
            "is_released": None,
            "version": None,
            "version_major": None,
            "version_minor": None,
            "capsule_id": None,
            "computation_id": None,
            "slug": None,
            "capsule_url": None,
            "commit_hash": None,
            "run_timestamp": None,
        }

    capsule = _get_json(f"/capsules/{capsule_id}", token)
    computation = _get_json(f"/computations/{computation_id}", token)

    is_released = capsule.get("status") == "release"

    if is_released:
        major = computation.get("version")
        match = next(
            (v for v in (capsule.get("versions") or [])
             if v.get("major_version") == major),
            {},
        )
        minor = match.get("minor_version", 0)
        version_label = f"v{major}.{minor}"
    else:
        major = None
        minor = None
        version_label = "editable"

    slug = capsule.get("slug")
    capsule_url = (
        f"https://codeocean.allenneuraldynamics.org/capsule/{slug}/tree"
        if slug
        else None
    )

    created_epoch = computation.get("created")
    run_timestamp = (
        datetime.fromtimestamp(created_epoch, tz=timezone.utc).isoformat()
        if created_epoch is not None
        else None
    )

    return {
        "status": capsule.get("status"),
        "is_released": is_released,
        "version": version_label,
        "version_major": major,
        "version_minor": minor,
        "capsule_id": capsule_id,
        "computation_id": computation_id,
        "slug": slug,
        "capsule_url": capsule_url,
        "commit_hash": None,
        "run_timestamp": run_timestamp,
    }


def _git(args: list[str], cwd: str | None = None) -> str | None:
    """Run a git command, return stripped stdout or None on failure."""
    try:
        r = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return r.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def get_local_git_provenance(cwd: str | None = None) -> dict[str, Any]:
    """Look up provenance from the local git working tree.

    Useful when running outside Code Ocean (e.g. on a developer laptop or a
    GitHub Actions runner). Populates the same conceptual provenance fields
    AIND's `Code` object cares about — commit hash and source URL — by
    shelling out to ``git``.

    Returns a dict with keys:

      ``status``        : ``"local_git"`` if a git repo was found, else
                          ``"no_git"``.
      ``commit_hash``   : full SHA of ``HEAD`` (or ``None``).
      ``branch``        : current branch name, or ``"HEAD"`` if detached.
      ``remote_url``    : value of ``remote.origin.url`` as configured.
      ``is_dirty``      : ``True`` if the working tree has uncommitted
                          changes, ``False`` if clean, ``None`` if unknown.
      ``commit_url``    : ``https://github.com/<owner>/<repo>/commit/<sha>``
                          when the remote is parseable as GitHub, else
                          ``None``.
      ``run_timestamp`` : ISO 8601 UTC timestamp of when this call ran.
    """
    commit = _git(["rev-parse", "HEAD"], cwd=cwd)
    if commit is None:
        return {
            "status": "no_git",
            "commit_hash": None,
            "branch": None,
            "remote_url": None,
            "is_dirty": None,
            "commit_url": None,
            "run_timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }

    branch = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd)
    remote_url = _git(["config", "--get", "remote.origin.url"], cwd=cwd)
    dirty_output = _git(["status", "--porcelain"], cwd=cwd)
    is_dirty = bool(dirty_output) if dirty_output is not None else None

    github_repo = None
    if remote_url:
        m = re.search(r"github\.com[:/]([\w.-]+/[\w.-]+?)(?:\.git)?$", remote_url)
        if m:
            github_repo = m.group(1)
    commit_url = (
        f"https://github.com/{github_repo}/commit/{commit}"
        if github_repo
        else None
    )

    return {
        "status": "local_git",
        "commit_hash": commit,
        "branch": branch,
        "remote_url": remote_url,
        "is_dirty": is_dirty,
        "commit_url": commit_url,
        "run_timestamp": datetime.now(tz=timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    import pprint
    pprint.pprint(get_code_ocean_provenance())
