from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class ManifestLoader:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    def _load_yaml(self, relative_path: str) -> dict[str, Any]:
        path = self.repo_root / relative_path
        if not path.exists():
            raise FileNotFoundError(f'Manifest not found: {relative_path}')
        data = yaml.safe_load(path.read_text(encoding='utf-8'))
        if not isinstance(data, dict):
            raise ValueError(f'Invalid YAML object in {relative_path}')
        return data

    def load_expected_structure(self) -> dict[str, Any]:
        return self._load_yaml('.prgx-ag/manifests/expected_structure.yaml')

    def load_critical_files(self) -> dict[str, Any]:
        return self._load_yaml('.prgx-ag/manifests/critical_files.yaml')

    def load_policy(self) -> dict[str, Any]:
        return self._load_yaml('.prgx-ag/policy/patimokkha.yaml')
