import re
import shutil
import threading
from pathlib import Path

import git

WORKSPACE_DIR = Path("workspace")
_repo_locks: dict[int, threading.Lock] = {}
_locks_guard = threading.Lock()


def _repo_lock(repo_id: int) -> threading.Lock:
    with _locks_guard:
        return _repo_locks.setdefault(repo_id, threading.Lock())


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

    # Migrate from the two layouts used by earlier versions.
    old_dir = WORKSPACE_DIR / str(repo.id)
    newer_slug = re.sub(r"[^a-z0-9]+", "-", repo.name.lower()).strip("-") or "repo"
    newer_layout_dir = WORKSPACE_DIR / "repos" / f"{repo.id}-{newer_slug}"
    for legacy_dir in (old_dir, newer_layout_dir):
        if legacy_dir and legacy_dir.exists() and not repo_dir.exists():
            legacy_dir.rename(repo_dir)
            break

    clone_url = repo.git_url if repo.source_type == "remote" else repo.local_path

    with _repo_lock(repo.id):
        if repo_dir.exists():
            r = git.Repo(repo_dir)
            try:
                r.git.fetch("origin", "--tags", "--prune")
            except Exception:
                pass  # local source may have no network; best-effort
        else:
            git.Repo.clone_from(clone_url, repo_dir)
    return repo_dir


def get_repo_path(repo, *, fetch: bool = False) -> Path:
    """Return the workspace clone path for any repo (remote or local)."""
    return _get_or_clone(repo)


def checkout_commit(repo_path: Path, commit_sha: str) -> None:
    """Checkout a specific commit (detached HEAD) in the workspace clone."""
    r = git.Repo(repo_path)
    r.git.checkout(commit_sha)


def prepare_build_path(repo, build_id: int, commit_sha: str) -> Path:
    """Checkout the requested commit in the project's named workspace."""
    repo_path = _get_or_clone(repo)
    with _repo_lock(repo.id):
        source = git.Repo(repo_path)
        try:
            commit = source.commit(commit_sha)
        except Exception as exc:
            raise ValueError(f"Unknown commit: {commit_sha}") from exc
        source.git.checkout("--force", commit.hexsha)
    return repo_path


def delete_repo_workspace(repo) -> None:
    """Remove the repository cache. Build worktrees are removed by build id separately."""
    repo_path = WORKSPACE_DIR / _repo_dir_name(repo)
    shutil.rmtree(repo_path, ignore_errors=True)


def delete_build_workspace(build_id: int) -> None:
    # Builds share the repository workspace; deleting one build must not remove it.
    return None


def get_commits(repo_path: Path, limit: int = 50) -> list[dict]:
    r = git.Repo(repo_path)
    commits = []
    for commit in r.iter_commits("--all", max_count=limit, date_order=True):
        branches = []
        for ref in r.git.branch("--all", "--contains", commit.hexsha).splitlines():
            name = ref.strip().lstrip("* ")
            if " -> " in name or name.endswith("/HEAD"):
                continue
            name = name.removeprefix("remotes/").removeprefix("origin/")
            if name and name not in branches:
                branches.append(name)
        commits.append(
            {
                "sha": commit.hexsha,
                "short_sha": commit.hexsha[:8],
                "message": commit.message.strip().split("\n")[0],
                "author": commit.author.name,
                "date": commit.committed_datetime.isoformat(),
                "branch": branches[0] if branches else None,
                "branches": branches,
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
