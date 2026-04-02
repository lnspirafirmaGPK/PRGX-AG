"""Tests for the CLI argument parsing changes introduced in main.py."""
from __future__ import annotations

import sys

import pytest

# Import parse_args directly from main module
from prgx_ag.main import parse_args


def test_parse_args_runtime_profile_development(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, 'argv', ['prgx-ag', '--runtime-profile', 'development'])
    args = parse_args()
    assert args.runtime_profile == 'development'


def test_parse_args_runtime_profile_staging(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, 'argv', ['prgx-ag', '--runtime-profile', 'staging'])
    args = parse_args()
    assert args.runtime_profile == 'staging'


def test_parse_args_runtime_profile_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, 'argv', ['prgx-ag', '--runtime-profile', 'production'])
    args = parse_args()
    assert args.runtime_profile == 'production'


def test_parse_args_runtime_profile_default_is_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """When --runtime-profile is not provided, args.runtime_profile must be None."""
    monkeypatch.setattr(sys, 'argv', ['prgx-ag'])
    args = parse_args()
    assert args.runtime_profile is None


def test_parse_args_runtime_profile_invalid_raises_systemexit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, 'argv', ['prgx-ag', '--runtime-profile', 'invalid-profile'])
    with pytest.raises(SystemExit):
        parse_args()


def test_parse_args_runtime_profile_combined_with_dry_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sys, 'argv', ['prgx-ag', '--runtime-profile', 'production', '--dry-run']
    )
    args = parse_args()
    assert args.runtime_profile == 'production'
    assert args.dry_run is True


def test_parse_args_runtime_profile_combined_with_scan_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sys, 'argv', ['prgx-ag', '--runtime-profile', 'staging', '--scan-only']
    )
    args = parse_args()
    assert args.runtime_profile == 'staging'
    assert args.scan_only is True