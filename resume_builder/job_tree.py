#!/usr/bin/env python3
"""
job-tree — Job Application Orchestrator 🌳

Each job application "grows a branch" off your resume tree. This tool sequences
the existing resume tooling (exploder / imploder / builder) plus the connective
glue (PDF ingestion, branch setup, tailoring-context assembly) so that starting
and processing a new application is a handful of predictable steps.

Subcommands:
    init      Scaffold the application directory + create the role branch
    ingest    Extract the job-posting PDF -> job_posting.txt (+ metadata)
    checkout  Prepare the editable resume tree on the application branch
    suggest   Assemble the tailoring context (posting + resume + prompt)
    build     implode -> LaTeX -> PDF (delegates to resume-builder / Makefile)
    run       Chain the steps end-to-end

NOTE: This is the Step-1 skeleton. Subcommand handlers are stubs that report
what they *will* do; real logic is layered in one step at a time.
"""

import argparse
import datetime
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

import resume_builder as rb

TAG = "[job-tree]"

# Repo-local directory that marks the root of a job-tree workspace and holds the
# "current application" pointer. Discovered by walking up from the cwd, the same
# way git discovers `.git`.
STATE_DIRNAME = ".job-tree"
CURRENT_FILENAME = "current"

# Global config (resume-repo, default template, ...). Rarely changes.
CONFIG_PATH = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "job-tree" / "config.yaml"


def log(msg: str) -> None:
    """Standardized single-line output for every step."""
    print(f"{TAG} {msg}")


# --------------------------------------------------------------------------- #
# Config + current-application state (repo-local .job-tree/current)
# --------------------------------------------------------------------------- #
def load_config() -> dict:
    """Load the global config (~/.config/job-tree/config.yaml); {} if absent."""
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def find_state_dir(start: Path | None = None) -> Path | None:
    """Walk up from `start` (default cwd) to find an existing `.job-tree/` dir."""
    start = (start or Path.cwd()).resolve()
    for d in (start, *start.parents):
        candidate = d / STATE_DIRNAME
        if candidate.is_dir():
            return candidate
    return None


def workspace_root(start: Path | None = None) -> Path:
    """Return the workspace root (parent of `.job-tree/`), or cwd if none yet."""
    state_dir = find_state_dir(start)
    return state_dir.parent if state_dir else (start or Path.cwd()).resolve()


def read_current(start: Path | None = None) -> Path | None:
    """Return the current application dir recorded in `.job-tree/current`, if any."""
    state_dir = find_state_dir(start)
    if state_dir is None:
        return None
    current_file = state_dir / CURRENT_FILENAME
    if not current_file.exists():
        return None
    raw = current_file.read_text(encoding="utf-8").strip()
    if not raw:
        return None
    p = Path(raw)
    # Stored relative to the workspace root; resolve against it.
    if not p.is_absolute():
        p = state_dir.parent / p
    return p.resolve()


def write_current(app_dir: Path, start: Path | None = None) -> Path:
    """Record `app_dir` as the current application in `.job-tree/current`.

    Creates `.job-tree/` at the workspace root (cwd) if it doesn't exist yet.
    The pointer is stored relative to the workspace root when possible so the
    workspace stays portable.
    """
    state_dir = find_state_dir(start)
    if state_dir is None:
        root = (start or Path.cwd()).resolve()
        state_dir = root / STATE_DIRNAME
        state_dir.mkdir(parents=True, exist_ok=True)
    root = state_dir.parent
    app_dir = app_dir.resolve()
    try:
        value = str(app_dir.relative_to(root))
    except ValueError:
        value = str(app_dir)  # outside the workspace; store absolute
    (state_dir / CURRENT_FILENAME).write_text(value + "\n", encoding="utf-8")
    return state_dir


def resolve_app_dir(flag: str | None) -> Path | None:
    """Resolve the application dir: explicit flag -> current-context pointer.

    Returns None if neither is available (callers emit a helpful hint).
    """
    if flag:
        return Path(flag).expanduser().resolve()
    return read_current()


def slugify(text: str) -> str:
    """Lowercase, hyphenate: 'Acme Corp!' -> 'acme-corp'."""
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def default_branch_name(company: str) -> str:
    """YYYY-MM-DD-<company-slug> using today's date."""
    today = datetime.date.today().isoformat()
    return f"{today}-{slugify(company)}"


def run_git(repo: Path, *git_args: str) -> subprocess.CompletedProcess:
    """Run a git command in `repo`, capturing output; raises on failure."""
    return subprocess.run(
        ["git", "-C", str(repo), *git_args],
        check=True, capture_output=True, text=True,
    )


def read_application(app_dir: Path) -> dict:
    """Load metadata.yaml from an app dir; returns {} if absent."""
    app_yaml = app_dir / "metadata.yaml"
    if not app_yaml.exists():
        return {}
    with open(app_yaml, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from a PDF: prefer `pdftotext`, fall back to `pdfplumber`."""
    # Preferred: poppler's pdftotext (fast, reliable). "-" writes to stdout.
    if shutil.which("pdftotext"):
        result = subprocess.run(
            ["pdftotext", "-layout", str(pdf_path), "-"],
            check=True, capture_output=True, text=True,
        )
        return result.stdout

    # Fallback: pure-Python pdfplumber.
    try:
        import pdfplumber  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "No PDF text extractor available: install poppler's `pdftotext` "
            "or `pdfplumber`."
        ) from exc

    pages = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    return "\n\n".join(pages)


# --------------------------------------------------------------------------- #
# Subcommand handlers (Step-1 stubs)
# --------------------------------------------------------------------------- #
def cmd_init(args: argparse.Namespace) -> int:
    """Structural scaffold: app dir + git init + clone resume repo + branch + metadata.

    Idempotent: safe to re-run. Existing pieces are reused rather than recreated.
    """
    if not args.resume_repo:
        log("init — error: --resume-repo is required (or set it in config)")
        return 1
    if not args.company:
        log("init — error: --company is required")
        return 1
    if not args.url:
        log("init — error: --url is required")
        return 1
    if not args.role:
        log("init — error: --role is required")
        return 1

    # 1. Create the branch dir from the parameters passed
    company_slug = slugify(args.company)
    role_slug = slugify(args.role)
    branch_dir = Path(f'{datetime.date.today().isoformat()}-{company_slug}-{role_slug}')
    branch_dir.mkdir(parents=True, exist_ok=True)

    # 2. Create the yaml file storing necessary information
    metadata = {
        "company": args.company,
        "role": args.role,
        "url": args.url,
        "branch": str(branch_dir),
        "created": datetime.date.today().isoformat(),
        "resume-repo": args.resume_repo,
        "status": "draft",
    }

    app_yaml_file = branch_dir / "metadata.yaml"
    with open(app_yaml_file, "w", encoding="utf-8") as f:
        yaml.dump(metadata, f, sort_keys=False, allow_unicode=True)
    log(f"init — wrote metadata: {app_yaml_file}")

    # 3. Clone the git repository
    resume_clone = branch_dir / "resume-repo"
    if resume_clone.exists():
        log(f"init — resume-repo/ already present, skipping clone")
    else:
        subprocess.run(
            ["git", "clone", str(args.resume_repo), str(resume_clone)],
            check=True, capture_output=True, text=True,)
        log(f"init — cloned resume repo -> {resume_clone}")

    # 4. Create/checkout the role branch inside the clone (idempotent).
    existing = run_git(resume_clone, "branch", "--list", branch_dir).stdout.strip()
    if existing:
        run_git(resume_clone, "checkout", branch_dir)
        log(f"init — checked out existing branch: {branch_dir}")
    else:
        run_git(resume_clone, "checkout", "-b", branch_dir)
        log(f"init — created + checked out branch: {branch_dir}")

    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    """Acquire the posting content: PDF -> job_posting.txt.

    Exit-and-re-run model:
      * If no PDF exists, open the posting URL in the browser and instruct the
        user to Print -> Save as PDF at <app-dir>/job_posting.pdf, then re-run.
      * If a PDF exists, extract it to job_posting.txt.
    """
    app_dir = resolve_app_dir(args.app_dir)
    if app_dir is None:
        log("ingest — error: no current application set "
            "(run `job-tree checkout <app-dir>` or pass --app-dir)")
        return 1

    if not app_dir.exists():
        log(f"ingest — error: app dir not found: {app_dir} (run `job-tree init` first)")
        return 1

    meta = read_application(app_dir)
    url = args.url or meta.get("url")
    pdf_path = app_dir / "job-posting.pdf"
    txt_path = app_dir / "job-posting.txt"

    # Optional: copy an already-saved PDF into place.
    if args.pdf:
        src = Path(args.pdf).expanduser().resolve()
        if not src.exists():
            log(f"ingest — error: --pdf not found: {src}")
            return 1
        shutil.copyfile(src, pdf_path)
        log(f"ingest — copied {src} -> {pdf_path}")

    # No PDF yet: assist the user, then exit for a re-run.
    if not pdf_path.exists():
        if url:
            subprocess.run(["open", url], check=False)
            log(f"ingest — opened posting in browser: {url}")
        else:
            log("ingest — no URL recorded and no PDF present")
        log(f"ingest — Print -> Save as PDF to: {pdf_path}")
        log("ingest — then re-run `job-tree ingest` to extract the text.")
        return 0

    # PDF present: extract to text.
    text = extract_pdf_text(pdf_path)
    txt_path.write_text(text, encoding="utf-8")
    log(f"ingest — extracted {len(text)} chars, "
        f"{text.count(chr(10)) + 1} lines -> {txt_path}")
    log("ingest — done 🌳")

    return 0


def cmd_checkout(args: argparse.Namespace) -> int:
    """Set the current application (git-style): record it in `.job-tree/current`.

    With no argument, re-affirms / prints the current application. With an
    app-dir, validates it looks like a real application (has metadata.yaml)
    and records it as current so later commands can omit --app-dir.
    """
    # No target given: report the current context.
    if not args.app_dir:
        current = read_current()
        if current is None:
            log("checkout — no current application set "
                "(run `job-tree checkout <app-dir>`)")
            return 1
        log(f"checkout — current application: {current}")
        return 0

    app_dir = Path(args.app_dir).expanduser().resolve()
    if not app_dir.exists():
        log(f"checkout — error: app dir not found: {app_dir} "
            "(run `job-tree init` first)")
        return 1
    if not (app_dir / "metadata.yaml").exists():
        log(f"checkout — error: {app_dir} has no metadata.yaml "
            "(is this a job-tree application dir?)")
        return 1

    state_dir = write_current(app_dir)
    meta = read_application(app_dir)
    desc = f"{meta.get('company', '?')} — {meta.get('role', '?')}"
    log(f"checkout — current application set: {app_dir} ({desc})")
    log(f"checkout — state recorded in {state_dir / CURRENT_FILENAME}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Show the current application and its metadata."""
    root = workspace_root()
    current = read_current()
    log(f"status — workspace root: {root}")
    if current is None:
        log("status — no current application set "
            "(run `job-tree checkout <app-dir>`)")
        return 0
    if not current.exists():
        log(f"status — current application missing on disk: {current}")
        return 1

    meta = read_application(current)
    log(f"status — current application: {current}")
    for key in ("company", "role", "status", "url", "branch", "created"):
        if key in meta:
            log(f"status —   {key}: {meta[key]}")
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    """Build the resume and pdf from the git repository."""

    # No target given: report the current context.
    if not args.app_dir:
        current = read_current()
        if current is None:
            log("checkout — no current application set "
                "(run `job-tree checkout <app-dir>`)")
        log(f"checkout — current application: {current}")

    # build file paths for calls
    # TODO: Update file path names to be in line with resume parameters
    app_dir = resolve_app_dir(args.app_dir)
    resume_yaml = app_dir / "resume.yaml"
    pdf = app_dir / "resume.pdf"

    # if pdf exist remove
    pdf.unlink(missing_ok=True)

    # if resume.yaml doesn't exist call resume imploder
    if not resume_yaml.exists():
        # TODO: build piping to pass in a resume rep
        repo_dir = app_dir / 'resume-repo'
        manifest = repo_dir / 'manifest.yaml'
        resume_dir = repo_dir / 'resume'
        imploder = rb.ResumeImploder(str(resume_dir), str(manifest), resume_yaml)
        imploder.write_resume()

    # build the resume latex file and pdf
    # TODO: make file paths implicit in buid call. Little tedium here
    builder = rb.Jinja2ResumeBuilder()
    builder.load_resume_data(resume_yaml)
    latex_content = builder.generate_latex(args.template)
    builder.save_latex(latex_content, app_dir)
    builder.compile_pdf(app_dir)

    # run cleanup -- remove build files
    builder.cleanup_files(pdf, tex_file = True)

    return 0


def cmd_commit(args: argparse.Namespace) -> int:
    """Save the current application and its metadata."""
    root = workspace_root()
    current = read_current()
    log(f"status — workspace root: {root}")
    if current is None:
        log("status — no current application set "
            "(run `job-tree checkout <app-dir>`)")
        return 0
    if not current.exists():
        log(f"status — current application missing on disk: {current}")
        return 1

    meta = read_application(current)
    log(f"status — current application: {current}")
    for key in ("company", "role", "status", "url", "branch", "created"):
        if key in meta:
            log(f"status —   {key}: {meta[key]}")
    return 0

# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="job-tree",
        description="Orchestrate a job application: ingest a posting, grow a "
                    "resume branch, tailor it, and build the PDF.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # Default resume-repo comes from global config (~/.config/job-tree/config.yaml),
    # falling back to the current application's metadata if we're inside one.
    config = load_config()
    resume_repo = config.get("resume-repo")
    if resume_repo is None:
        current = read_current()
        if current is not None:
            resume_repo = read_application(current).get("resume-repo")

    # init
    p_init = sub.add_parser("init", help="Scaffold app dir + create role branch")
    p_init.add_argument("--resume-repo",
        default=resume_repo,
        help="Path to your private resume repo. Falls back to config / default.")
    p_init.add_argument("--company", help="Company name (for the branch/metadata)")
    p_init.add_argument("--role", help="Role title (for metadata)")
    p_init.add_argument("--url", help="Job-posting website URL (recorded; fetched in ingest)")
    p_init.add_argument("--branch", help="Override the derived branch name")
    p_init.set_defaults(func=cmd_init)

    # ingest
    p_ingest = sub.add_parser("ingest", help="PDF -> job_posting.txt (+ metadata)")
    p_ingest.add_argument("--app-dir",
        default=None,
        help="Application dir (defaults to the current application via `checkout`)")
    p_ingest.add_argument("--pdf", help="Path to an already-saved PDF to copy into place")
    p_ingest.add_argument("--url", help="Posting URL (overrides metadata.yaml)")
    p_ingest.set_defaults(func=cmd_ingest)

    # checkout — set (or show) the current application
    p_checkout = sub.add_parser(
        "checkout",
        help="Set the current application (git-style); omit arg to show current")
    p_checkout.add_argument("app_dir", nargs="?",
        help="Application dir to make current. Omit to print the current one.")
    p_checkout.set_defaults(func=cmd_checkout)

    # status — show the current application + metadata
    p_status = sub.add_parser("status", help="Show the current application")
    p_status.set_defaults(func=cmd_status)

    # status — show the current application + metadata
    p_build = sub.add_parser("build", help="Build the current application")
    p_build.add_argument("--app-dir",
        default=None,
        help="Application dir (defaults to the current application via `checkout`)")
    p_build.add_argument("--template",
        default='classic.tex',
        help="Template to use to build the resume (defaults to classic.tex)")
    p_build.set_defaults(func=cmd_build)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
