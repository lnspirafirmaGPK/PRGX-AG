from pathlib import Path

import json


def test_readme_excludes_completed_suggestion_sections() -> None:
    readme = Path('README.md').read_text(encoding='utf-8')
    assert 'completed suggestions' not in readme.lower()
    assert 'ข้อเสนอแนะที่ทำเสร็จแล้ว' not in readme


def test_repository_metadata_is_not_demo_content() -> None:
    package = json.loads(Path('package.json').read_text(encoding='utf-8'))
    html = Path('index.html').read_text(encoding='utf-8').lower()

    assert package['name'] == 'prgx-ag'
    assert 'sample package.json' not in package['description'].lower()
    assert 'demo repository' not in html
    assert 'prgx-ag repository overview' in html
