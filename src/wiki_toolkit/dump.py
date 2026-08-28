"""
wiki_toolkit.dump

Clones (or updates) a GitHub wiki repo and dumps every page into a single
structured JSON file, including basic git metadata per page.

A GitHub wiki is itself a git repo, reachable at:
    https://github.com/<org>/<repo>.wiki.git

CLI usage (after `pip install -e .`):
    wiki-dump --org second-hand-tigers --repo chem-eng-projects
    wiki-dump --wiki-url https://github.com/second-hand-tigers/badocter-career-learnings.wiki.git
    wiki-dump --org second-hand-tigers --repo chem-eng-projects-MogasDebenz --output mogasdebenz-wiki.json

Requirements:
    - git installed and on PATH
    - network access to github.com (public wiki, or credentials configured
      for git if the repo is private)

Output shape:
    {
      "organization": "...",
      "repository": "...",
      "wiki_url": "...",
      "generated_at": "2026-08-28T12:00:00Z",
      "page_count": 12,
      "pages": [
        {
          "slug": "Who-is-Dr-Docter",
          "filename": "Who-is-Dr-Docter.md",
          "title": "Who is Dr. Docter?",
          "is_special": false,
          "content": "raw markdown ...",
          "word_count": 842,
          "last_modified": "2026-08-20T14:03:11Z",
          "last_author": "William Docter",
          "revision_count": 4
        },
        ...
      ]
    }
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SPECIAL_PAGES = {"_Sidebar", "_Footer", "Home"}


def run_git(args, cwd=None):
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{result.stderr}")
    return result.stdout.strip()


def clone_or_update_wiki(wiki_url: str, clone_dir: Path) -> Path:
    if clone_dir.exists() and (clone_dir / ".git").exists():
        print(f"Updating existing clone at {clone_dir} ...")
        run_git(["pull"], cwd=clone_dir)
    else:
        print(f"Cloning {wiki_url} into {clone_dir} ...")
        clone_dir.parent.mkdir(parents=True, exist_ok=True)
        run_git(["clone", wiki_url, str(clone_dir)])
    return clone_dir


def extract_title(content: str, fallback_slug: str) -> str:
    """Use the first level-1 markdown heading if present, else derive from slug."""
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return fallback_slug.replace("-", " ")


def get_page_git_metadata(repo_dir: Path, filename: str):
    """Return (last_modified_iso, last_author, revision_count) for a file."""
    log_out = run_git(
        ["log", "--follow", "--format=%aI\t%an", "--", filename],
        cwd=repo_dir,
    )
    lines = [l for l in log_out.splitlines() if l.strip()]
    if not lines:
        return None, None, 0
    last_date, last_author = lines[0].split("\t", 1)
    return last_date, last_author, len(lines)


def dump_wiki(wiki_url: str, clone_dir: Path, output_path: Path):
    repo_dir = clone_or_update_wiki(wiki_url, clone_dir)

    md_files = sorted(repo_dir.glob("*.md"))
    if not md_files:
        print("Warning: no .md files found in the wiki repo.", file=sys.stderr)

    pages = []
    for md_file in md_files:
        slug = md_file.stem
        content = md_file.read_text(encoding="utf-8")
        last_modified, last_author, revision_count = get_page_git_metadata(
            repo_dir, md_file.name
        )

        pages.append(
            {
                "slug": slug,
                "filename": md_file.name,
                "title": extract_title(content, slug),
                "is_special": slug in SPECIAL_PAGES,
                "content": content,
                "word_count": len(content.split()),
                "last_modified": last_modified,
                "last_author": last_author,
                "revision_count": revision_count,
            }
        )

    # Parse org/repo back out of the wiki URL for the manifest header
    org, repo = None, None
    try:
        trimmed = wiki_url.rstrip("/")
        if trimmed.endswith(".wiki.git"):
            trimmed = trimmed[: -len(".wiki.git")]
        parts = trimmed.split("/")
        org, repo = parts[-2], parts[-1]
    except Exception:
        pass

    manifest = {
        "organization": org,
        "repository": repo,
        "wiki_url": wiki_url,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "page_count": len(pages),
        "pages": pages,
    }

    output_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Wrote {len(pages)} pages to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Dump a GitHub wiki to JSON.")
    parser.add_argument("--org", help="GitHub org/user, e.g. second-hand-tigers")
    parser.add_argument("--repo", help="Repo name, e.g. chem-eng-projects")
    parser.add_argument(
        "--wiki-url",
        help="Full wiki git URL, e.g. https://github.com/ORG/REPO.wiki.git "
        "(overrides --org/--repo)",
    )
    parser.add_argument(
        "--clone-dir",
        default=None,
        help="Where to clone/update the wiki repo locally "
        "(default: ./wiki-clones/<repo>.wiki)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path (default: <repo>-wiki.json)",
    )
    args = parser.parse_args()

    if args.wiki_url:
        wiki_url = args.wiki_url
        repo_name = wiki_url.rstrip("/").removesuffix(".wiki.git").split("/")[-1]
    elif args.org and args.repo:
        wiki_url = f"https://github.com/{args.org}/{args.repo}.wiki.git"
        repo_name = args.repo
    else:
        parser.error("Provide either --wiki-url, or both --org and --repo.")

    clone_dir = (
        Path(args.clone_dir) if args.clone_dir else Path("wiki-clones") / f"{repo_name}.wiki"
    )
    output_path = Path(args.output) if args.output else Path(f"{repo_name}-wiki.json")

    dump_wiki(wiki_url, clone_dir, output_path)


if __name__ == "__main__":
    main()