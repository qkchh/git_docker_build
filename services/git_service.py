import re
from pathlib import Path

import git

WORKSPACE_DIR = Path("workspace")


def _repo_dir_name(repo) -> str:
    """Sanitize repo name for use as a directory name."""
    name = re.sub(r"[^a-z0-9]+", "-", repo.name.lower()).strip("-")
    return name or f"repo-{repo.id}"


def _get_or_clone(repo) -> Path:
    """Clone remote repo to workspace, or fetch latest if already exists."""
    repo_dir = WORKSPACE_DIR / _repo_dir_name(repo)

    # Migrate from old ID-based path if needed
    old_dir = WORKSPACE_DIR / str(repo.id)
    if old_dir.exists() and not repo_dir.exists():
        old_dir.rename(repo_dir)

    if repo_dir.exists():
        r = git.Repo(repo_dir)
        r.git.fetch("origin", "--tags", "--prune")
    else:
        repo_dir.mkdir(parents=True, exist_ok=True)
        git.Repo.clone_from(repo.git_url, repo_dir)
    return repo_dir


def _try_fetch_local(repo_path: Path) -> None:
    """If a local repo has a remote, fetch silently to get latest commits."""
    try:
        r = git.Repo(repo_path)
        if r.remotes:
            r.git.fetch("origin", "--tags", "--prune")
    except Exception:
        pass


def get_repo_path(repo, *, fetch: bool = False) -> Path:
    if repo.source_type == "local":
        path = Path(repo.local_path)
        if fetch:
            _try_fetch_local(path)
        return path
    return _get_or_clone(repo)


def create_worktree(repo_path: Path, commit_sha: str) -> Path:
    """Check out a specific commit to a temp directory without touching the main working tree."""
    import time
    worktree_dir = Path(f"/tmp/gdb-{commit_sha[:8]}-{int(time.time() * 1000)}")
    r = git.Repo(repo_path)
    r.git.worktree("add", "--detach", str(worktree_dir), commit_sha)
    return worktree_dir


def remove_worktree(repo_path: Path, worktree_dir: Path) -> None:
    """Remove the temporary worktree created by create_worktree."""
    try:
        r = git.Repo(repo_path)
        r.git.worktree("remove", "--force", str(worktree_dir))
    except Exception:
        import shutil
        shutil.rmtree(worktree_dir, ignore_errors=True)


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
