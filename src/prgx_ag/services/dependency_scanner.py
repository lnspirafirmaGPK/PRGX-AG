from __future__ import annotations

from pathlib import Path


def find_dependency_manifests(root: Path) -> list[Path]:
    manifests: list[Path] = []
    for name in ('pyproject.toml', 'requirements.txt', 'requirements-dev.txt'):
        path = root / name
        if path.exists():
            manifests.append(path)
    manifests.extend(sorted(root.glob('requirements*.txt')))
    return list(dict.fromkeys(manifests))


def scan_dependency_anomalies(root: Path) -> list[str]:
    anomalies: list[str] = []
    manifests = find_dependency_manifests(root)
    if not manifests:
        return ['No dependency manifest detected.']
    for manifest in manifests:
        lines = manifest.read_text(encoding='utf-8').splitlines()
        if manifest.name.startswith('requirements'):
            clean = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]
            if len(clean) != len(set(clean)):
                anomalies.append(f'Duplicate requirement entries in {manifest.name}')
            malformed = [line for line in clean if ' ' in line and ' @ ' not in line]
            if malformed:
                anomalies.append(f'Malformed requirement entries in {manifest.name}')
        if manifest.name == 'pyproject.toml' and 'dependencies' not in '\n'.join(lines):
            anomalies.append('pyproject.toml missing dependencies section')
    return anomalies
