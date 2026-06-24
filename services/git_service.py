from pathlib import Path

import git

WORKSPACE_DIR = Path("workspace")


def _get_or_clone(repo) -> Path:
    """Clone remote repo to workspace, or fetch latest if already exists."""
    repo_dir = WORKSPACE_DIR / str(repo.id)
    if repo_dir.exists():
        r = git.Repo(repo_dir)
        r.remotes.origin.fetch("--tags", "--prune")
    else:
        repo_dir.mkdir(parents=True, exist_ok=True)
        git.Repo.clone_from(repo.git_url, repo_dir)
    return repo_dir


def get_repo_path(repo) -> Path:
    if repo.source_type == "local":
        return Path(repo.local_path)
    return _get_or_clone(repo)


def checkout_commit(repo_path: Path, commit_sha: str) -> None:
    """Checkout a specific commit (detached HEAD) in the workspace clone."""
    r = git.Repo(repo_path)
    r.git.checkout(commit_sha)


def get_commits(repo_path: Path, limit: int = 50) -> list[dict]:
    r = git.Repo(repo_path)
    commits = []
    for commit in r.iter_commits("--all", max_count=limit):
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
