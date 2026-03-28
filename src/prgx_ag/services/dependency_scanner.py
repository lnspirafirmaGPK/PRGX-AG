from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

from packaging.requirements import InvalidRequirement, Requirement


DIRECTIVE_PREFIXES = ('-r', '--requirement', '-c', '--constraint', '--index-url', '--extra-index-url', '-f', '--find-links')
EDITABLE_PREFIXES = ('-e ', '--editable ')
VCS_PREFIXES = ('git+', 'hg+', 'svn+', 'bzr+')
URL_SCHEMES = {'http', 'https', 'ftp', 'ftps', 'file'}
ARCHIVE_SUFFIXES = ('.whl', '.zip', '.tar.gz', '.tgz', '.tar.bz2', '.tar.xz')


def find_dependency_manifests(root: Path) -> list[Path]:
    manifests: list[Path] = []
    for name in ('pyproject.toml', 'requirements.txt', 'requirements-dev.txt'):
        path = root / name
        if path.exists():
            manifests.append(path)
    manifests.extend(sorted(root.glob('requirements*.txt')))
    return list(dict.fromkeys(manifests))


def _is_requirement_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped or stripped.startswith('#'):
        return False
    if stripped.startswith(DIRECTIVE_PREFIXES) or stripped.startswith(EDITABLE_PREFIXES):
        return False
    if stripped.startswith(('--', '-')):
        return False
    return True


def _is_malformed_requirement(line: str) -> bool:
    requirement_text = line.split('#', maxsplit=1)[0].strip()
    try:
        Requirement(requirement_text)
    except InvalidRequirement:
        if _is_valid_pip_reference(requirement_text):
            return False
        return True
    return False


def _is_valid_pip_reference(requirement_text: str) -> bool:
    lowered = requirement_text.lower()
    if lowered.startswith(VCS_PREFIXES):
        return True
    if lowered.endswith(ARCHIVE_SUFFIXES):
        return True
    if requirement_text.startswith(('./', '../', '/', '~')) or re.match(r'^[A-Za-z]:[\\/]', requirement_text):
        return True

    parsed = urlparse(requirement_text)
    if parsed.scheme.lower() in URL_SCHEMES:
        return True
    return False


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
            malformed = [line for line in clean if _is_requirement_line(line) and _is_malformed_requirement(line)]
            if malformed:
                anomalies.append(f'Malformed requirement entries in {manifest.name}')
        if manifest.name == 'pyproject.toml' and 'dependencies' not in '\n'.join(lines):
            anomalies.append('pyproject.toml missing dependencies section')
    return anomalies
