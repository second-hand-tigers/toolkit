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
├── LICENSE
├── pyproject.toml        # src-layout; setuptools auto-discovers new packages under src/
├── test/
│   └── test_dump.py
└── src/
    └── wiki_toolkit/
        ├── __init__.py
        └── dump.py
```

## Testing

Plain `assert`-based scripts, no test-framework dependency — consistent
with the rest of this repo's dependency-light approach:

```bash
python test/test_dump.py
```

`wiki_toolkit`'s test suite exercises the real `dump_wiki()` logic against a
throwaway local git repo standing in for a wiki, so it needs no network
access and never touches a real GitHub wiki.

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
