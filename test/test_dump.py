"""
test/test_dump.py

Small, dependency-free test script for wiki_toolkit.dump.

Covers:
  1. extract_title() logic (pure function, no I/O)
  2. A full clone + dump round trip against a throwaway LOCAL git repo
     standing in for a "wiki" - no network access required, since git
     can clone from a local filesystem path just as well as a URL.

Run from the toolkit repo root (with your .venv activated):
    python test/test_dump.py

Exits with status 0 if all tests pass, 1 if any fail.
"""

import shutil
import subprocess
import sys
import json
import tempfile
from pathlib import Path

# Allow running this script directly even if the package isn't pip-installed
# yet (falls back to importing straight from src/).
try:
    from wiki_toolkit.dump import extract_title, dump_wiki
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
    from wiki_toolkit.dump import extract_title, dump_wiki


def run(cmd, cwd):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\n{result.stderr}")
    return result.stdout


def test_extract_title():
    assert extract_title("# Hello World\nSome body text.", "fallback-slug") == "Hello World"
    assert extract_title("No heading here at all.", "My-Page-Slug") == "My Page Slug"
    assert extract_title("#NoSpaceAfterHash\nBody", "Other-Slug") == "Other Slug"
    print("test_extract_title: PASS")


def make_fake_wiki_repo(base_dir: Path) -> Path:
    """Create a small local git repo with a couple of markdown pages,
    standing in for a cloned GitHub wiki."""
    source_repo = base_dir / "fake-wiki-source"
    source_repo.mkdir()

    run(["git", "init"], cwd=source_repo)
    run(["git", "config", "user.email", "test@example.com"], cwd=source_repo)
    run(["git", "config", "user.name", "Test User"], cwd=source_repo)

    (source_repo / "Home.md").write_text(
        "# Home\nWelcome to the fake wiki.\n", encoding="utf-8"
    )
    (source_repo / "Getting-Started.md").write_text(
        "# Getting Started\nSome instructions.\n", encoding="utf-8"
    )
    (source_repo / "_Sidebar.md").write_text(
        "* [Home](Home)\n* [Getting Started](Getting-Started)\n", encoding="utf-8"
    )

    run(["git", "add", "."], cwd=source_repo)
    run(["git", "commit", "-m", "Initial fake wiki content"], cwd=source_repo)

    return source_repo


def test_full_dump_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        source_repo = make_fake_wiki_repo(tmp_path)

        clone_dir = tmp_path / "clone-dest"
        output_path = tmp_path / "output.json"

        # git can clone from a local filesystem path just like a URL
        dump_wiki(str(source_repo), clone_dir, output_path)

        assert output_path.exists(), "Expected output JSON file was not created"
        data = json.loads(output_path.read_text(encoding="utf-8"))

        assert data["page_count"] == 3, f"Expected 3 pages, got {data['page_count']}"

        pages_by_slug = {p["slug"]: p for p in data["pages"]}

        assert "Home" in pages_by_slug
        assert pages_by_slug["Home"]["title"] == "Home"
        assert pages_by_slug["Home"]["is_special"] is True

        assert "Getting-Started" in pages_by_slug
        assert pages_by_slug["Getting-Started"]["title"] == "Getting Started"
        assert pages_by_slug["Getting-Started"]["is_special"] is False

        assert "_Sidebar" in pages_by_slug
        assert pages_by_slug["_Sidebar"]["is_special"] is True

        # Basic git metadata sanity checks
        home_page = pages_by_slug["Home"]
        assert home_page["revision_count"] == 1
        assert home_page["last_author"] == "Test User"
        assert home_page["last_modified"] is not None

        # Re-running should pull instead of re-cloning, and not error out
        dump_wiki(str(source_repo), clone_dir, output_path)

    print("test_full_dump_roundtrip: PASS")


def main():
    tests = [test_extract_title, test_full_dump_roundtrip]
    failures = 0

    for test in tests:
        try:
            test()
        except AssertionError as e:
            failures += 1
            print(f"{test.__name__}: FAIL - {e}")
        except Exception as e:
            failures += 1
            print(f"{test.__name__}: ERROR - {e}")

    if failures:
        print(f"\n{failures} test(s) failed.")
        sys.exit(1)
    else:
        print(f"\nAll {len(tests)} tests passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()