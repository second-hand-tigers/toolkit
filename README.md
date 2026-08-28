# toolkit

Public, reusable command-line toolkits for running a Second Hand Tigers–style
educational GitHub org. Clone it, take what you need, reuse it on your own
site.

This repo is meant to grow: each tool lives as its own package under `src/`,
installed together from one clone. See [Adding a new toolkit](#adding-a-new-toolkit)
below.

## Toolkits in this repo

| Toolkit | What it does | Entry point |
|---|---|---|
| [`wiki_toolkit`](src/wiki_toolkit/) | Dumps every page of a GitHub wiki into a single structured JSON file — raw markdown plus per-page git metadata (last author, last modified, revision count) | `wiki-dump` |

## Installation

```bash
git clone https://github.com/second-hand-tigers/toolkit.git
cd toolkit
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows PowerShell — macOS/Linux: source .venv/bin/activate
pip install -e .
```

No third-party dependencies — just the Python standard library and the `git`
binary on your PATH. `pip install -e .` registers the console-script entry
points (`wiki-dump`, and any future ones) for every package under `src/`.

## Usage: `wiki-dump`

A GitHub wiki is itself a separate git repo (`<repo>.wiki.git`), so
`wiki-dump` works by cloning it locally and reading it directly — no GitHub
API calls, no auth or rate limits for public wikis. Re-running it just
`git pull`s the existing local clone, so it doubles as a refresh command.

```bash
# by org + repo name
wiki-dump --org second-hand-tigers --repo chem-eng-projects

# or a full wiki URL
wiki-dump --wiki-url https://github.com/second-hand-tigers/badocter-career-learnings.wiki.git

# custom output filename
wiki-dump --org second-hand-tigers --repo chem-eng-projects-MogasDebenz --output mogasdebenz-wiki.json
```

Optional flags: `--clone-dir` (where the local wiki clone lives, default
`wiki-clones/`) and `--output` (output JSON filename, default derived from
the repo name).

### Output format

```json
{
  "organization": "...",
  "repository": "...",
  "wiki_url": "...",
  "generated_at": "ISO timestamp",
  "page_count": 0,
  "pages": [
    {
      "slug": "...",
      "filename": "....md",
      "title": "... (from first # heading, else derived from slug)",
      "is_special": false,
      "content": "raw markdown",
      "word_count": 0,
      "last_modified": "ISO timestamp",
      "last_author": "...",
      "revision_count": 0
    }
  ]
}
```

Because every page's raw markdown and metadata end up in one place, the dump
is useful well beyond human browsing — feeding a search index, a static
site generator, or a RAG pipeline, and it also tends to surface content bugs
(dead links, inconsistent link styles, stray Unicode look-alike characters
in filenames) that are easy to miss paging through the wiki UI one page at
a time.

## Repo structure

```
toolkit/
├── README.md
├── LICENSE                    # MIT
├── .gitignore                 # wiki-clones/, *.json outputs, __pycache__/, etc.
├── pyproject.toml             # src-layout; setuptools auto-discovers new packages under src/
├── Fix_unicode_hyphens.py     # one-off cleanup script, see below
├── test/
│   └── dump_test.py
└── src/
    └── wiki_toolkit/
        ├── __init__.py
        └── dump.py
```

## Testing

Plain `assert`-based scripts, no test-framework dependency — consistent
with the rest of this repo's dependency-light approach:

```bash
python test/dump_test.py
```

`wiki_toolkit`'s test suite exercises the real `dump_wiki()` logic against a
throwaway local git repo standing in for a wiki, so it needs no network
access and never touches a real GitHub wiki.

## Utility scripts

**`Fix_unicode_hyphens.py`** — a standalone cleanup script for a specific
class of bug: smart-punctuation tools (e.g. a PowerPoint→markdown export
pipeline) sometimes substitute the Unicode HYPHEN (U+2010) for a plain
ASCII hyphen (`-`, U+002D) in page titles. The two are visually
indistinguishable in almost any font, but GitHub wiki page matching is
exact on the slug, so a link typed with an ordinary hyphen 404s against a
filename that secretly contains U+2010.

Run it against a local wiki clone (e.g. the one `wiki-dump` leaves under
`wiki-clones/`):

1. Rewrites all `.md` file **contents**, replacing any U+2010 with `-`
   (fixes internal links first).
2. Renames any **filenames** containing U+2010 via `git mv`, so git history
   and blame are preserved.
3. Leaves `git add` / `commit` / `push` to you, so you can review the diff
   before it goes live.

Not installed as a console script — run it directly with
`python Fix_unicode_hyphens.py <path-to-wiki-clone>`, review with
`git status`/`git diff` inside that clone, then commit and push from there.
Re-run `wiki-dump` afterward to confirm no U+2010 remains anywhere in the
dump.

## Adding a new toolkit

This repo is organized to hold more than one tool. To add another:

1. Create a new package under `src/`, e.g. `src/my_toolkit/`.
2. Add its console-script entry point to `pyproject.toml` under
   `[project.scripts]`.
3. Add a row to the **Toolkits in this repo** table above.
4. `pip install -e .` picks it up with no other config changes.

## License

MIT — see [LICENSE](LICENSE). Code in this repo is MIT licensed; content
produced by the org (wiki pages, docs) is separately CC BY 4.0.
