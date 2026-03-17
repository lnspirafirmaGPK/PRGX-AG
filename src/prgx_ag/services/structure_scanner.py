from __future__ import annotations

from pathlib import Path

import yaml


def detect_structure_issues(root: Path) -> list[str]:
    issues: list[str] = []
    expected_manifest = root / '.prgx-ag/manifests/expected_structure.yaml'
    expected_paths: list[str] = []
    if expected_manifest.exists():
        data = yaml.safe_load(expected_manifest.read_text(encoding='utf-8')) or {}
        expected_paths = data.get('paths', [])
    for rel in expected_paths:
        if not (root / rel).exists():
            issues.append(f'Missing expected path: {rel}')
    for package_dir in [p for p in (root / 'src').glob('**') if p.is_dir()] if (root / 'src').exists() else []:
        if any(child.suffix == '.py' for child in package_dir.glob('*.py')) and not (package_dir / '__init__.py').exists():
            issues.append(f'Missing __init__.py in {package_dir.relative_to(root)}')
    for critical in ['README.md', 'pyproject.toml', 'src', 'tests']:
        if not (root / critical).exists():
            issues.append(f'Missing critical path: {critical}')
    return issues
