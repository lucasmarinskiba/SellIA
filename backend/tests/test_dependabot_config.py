"""`.github/dependabot.yml` must stay valid and keep covering every dependency manifest in the repo.

A broken dependabot.yml fails silently (GitHub just stops raising updates), and a folder missing from it never gets
security PRs. This pins both. It reads files only; it never contacts GitHub.
"""

import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / ".github" / "dependabot.yml"

MANIFEST_BY_ECOSYSTEM = {"pip": ("requirements.txt",), "npm": ("package.json",), "github-actions": ()}


@pytest.fixture(scope="module")
def updates() -> list[dict]:
    data = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert data["version"] == 2
    return data["updates"]


def _tracked() -> list[str]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=False)
    return out.stdout.splitlines() if out.returncode == 0 else []


def test_every_listed_folder_exists_and_has_its_manifest(updates):
    for u in updates:
        folder = ROOT / u["directory"].lstrip("/")
        assert folder.is_dir(), f"{u['directory']} no existe"
        for manifest in MANIFEST_BY_ECOSYSTEM[u["package-ecosystem"]]:
            assert (folder / manifest).exists(), f"{u['directory']} no tiene {manifest}"
    if any(u["package-ecosystem"] == "github-actions" for u in updates):
        assert (ROOT / ".github" / "workflows").is_dir()


def test_security_updates_are_grouped_and_version_updates_are_off(updates):
    for u in updates:
        label = f"{u['package-ecosystem']} {u['directory']}"
        assert u["open-pull-requests-limit"] == 0, f"{label}: las actualizaciones de versión inundarían de PRs"
        groups = u["groups"]
        assert groups, f"{label}: sin grupo, cada paquete vulnerable abriría su propio PR"
        assert all(g["applies-to"] == "security-updates" and g["patterns"] == ["*"] for g in groups.values()), label


def test_no_folder_is_listed_twice_for_the_same_ecosystem(updates):
    keys = [(u["package-ecosystem"], u["directory"]) for u in updates]
    assert len(keys) == len(set(keys))


def test_every_tracked_python_and_npm_manifest_folder_is_covered(updates):
    tracked = _tracked()
    if not tracked:
        pytest.skip("no es un checkout de git")
    covered = {(u["package-ecosystem"], u["directory"]) for u in updates}
    missing = []
    for path in tracked:
        if "node_modules/" in path:
            continue
        name = Path(path).name
        folder = "/" + str(Path(path).parent).replace("\\", "/")
        folder = "/" if folder == "/." else folder
        if name.startswith("requirements") and name.endswith(".txt") and ("pip", folder) not in covered:
            missing.append(("pip", folder))
        if name == "package.json" and ("npm", folder) not in covered:
            missing.append(("npm", folder))
    assert not missing, f"carpetas con dependencias sin cubrir en dependabot.yml: {sorted(set(missing))}"
