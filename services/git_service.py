import re
from pathlib import Path

import git

WORKSPACE_DIR = Path("workspace")


def _repo_dir_name(repo) -> str:
    """Sanitize repo name for use as a directory name."""
    name = re.sub(r"[^a-z0-9]+", "-", repo.name.lower()).strip("-")
    return name or f"repo-{repo.id}"


def _get_or_clone(repo) -> Path:
    """Clone repo to workspace/, or fetch latest if already exists.

    Works for both remote (git_url) and local (local_path) repos.
    Local repos are cloned from their local_path; 'origin' then points
    back to that path so subsequent fetches pick up new commits.
    """
    repo_dir = WORKSPACE_DIR / _repo_dir_name(repo)

    # Migrate from old ID-based path if needed
    old_dir = WORKSPACE_DIR / str(repo.id)
    if old_dir.exists() and not repo_dir.exists():
        old_dir.rename(repo_dir)

    clone_url = repo.git_url if repo.source_type == "remote" else repo.local_path

    if repo_dir.exists():
        r = git.Repo(repo_dir)
        try:
            r.git.fetch("origin", "--tags", "--prune")
        except Exception:
            pass  # local source may have no network; best-effort
    else:
        repo_dir.mkdir(parents=True, exist_ok=True)
        git.Repo.clone_from(clone_url, repo_dir)
    return repo_dir


def get_repo_path(repo, *, fetch: bool = False) -> Path:
    """Return the workspace clone path for any repo (remote or local)."""
    return _get_or_clone(repo)


def checkout_commit(repo_path: Path, commit_sha: str) -> None:
    """Checkout a specific commit (detached HEAD) in the workspace clone."""
    r = git.Repo(repo_path)
    r.git.checkout(commit_sha)


def get_commits(repo_path: Path, limit: int = 50) -> list[dict]:
    r = git.Repo(repo_path)
    commits = []
    for commit in r.iter_commits("--all", max_count=limit, date_order=True):
        commits.append(
            {
                "sha": commit.hexsha,
                "short_sha": commit.hexsha[:8],
                "message": commit.message.strip().split("\n")[0],
                "author": commit.author.name,
                "date": commit.committed_datetime.isoformat(),
                "branch": None,
            }
        )
    return commits


def get_branches(repo_path: Path) -> list[str]:
    r = git.Repo(repo_path)
    branches = [b.name for b in r.branches]
    try:
        for ref in r.remotes.origin.refs:
            name = ref.name.replace("origin/", "")
            if name not in ("HEAD",) and name not in branches:
                branches.append(name)
    except Exception:
        pass
    return branches
