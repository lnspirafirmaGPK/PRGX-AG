from pathlib import Path

from prgx_ag.services.dependency_scanner import scan_dependency_anomalies


def test_dependency_scanner_allows_environment_marker_spacing(tmp_path: Path) -> None:
    manifest = tmp_path / 'requirements.txt'
    manifest.write_text(
        'requests>=2.0 ; python_version < "3.12"\n'
        'uvicorn[standard]>=0.30 ; platform_system != "Windows"\n',
        encoding='utf-8',
    )

    anomalies = scan_dependency_anomalies(tmp_path)

    assert anomalies == []


def test_dependency_scanner_flags_invalid_requirement_line(tmp_path: Path) -> None:
    manifest = tmp_path / 'requirements.txt'
    manifest.write_text('requests => 2.0\n', encoding='utf-8')

    anomalies = scan_dependency_anomalies(tmp_path)

    assert anomalies == ['Malformed requirement entries in requirements.txt']
