import tempfile
import unittest
from pathlib import Path

import git

from models import Repository
from routers.builds import _image_name, _validated_build_dir
from services import docker_service, git_service


class BuildValidationTests(unittest.TestCase):
    def test_image_name_is_docker_safe(self):
        self.assertEqual(_image_name("My 中文 App!", "ABCDEF123456"), "my-app:abcdef12")
        self.assertEqual(_image_name("中文", "abcdef123456"), "repo:abcdef12")

    def test_build_context_cannot_escape_repository(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            root.mkdir()
            (root / "backend").mkdir()
            self.assertEqual(_validated_build_dir(root, "backend"), (root / "backend").resolve())
            with self.assertRaises(ValueError):
                _validated_build_dir(root, "../outside")


class EnvironmentFileTests(unittest.TestCase):
    def test_temporary_env_is_removed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with docker_service._temporary_env_file(root, {"TOKEN": "secret"}):
                self.assertEqual((root / ".env").read_text(), "TOKEN=secret\n")
            self.assertFalse((root / ".env").exists())

    def test_existing_env_is_restored(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            env_file = root / ".env"
            env_file.write_text("OWNED=true\n")
            with docker_service._temporary_env_file(root, {"TOKEN": "secret"}):
                self.assertEqual(env_file.read_text(), "TOKEN=secret\n")
            self.assertEqual(env_file.read_text(), "OWNED=true\n")


class GitWorktreeTests(unittest.TestCase):
    def test_each_build_gets_an_isolated_commit(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            source_path = temp_path / "source"
            source = git.Repo.init(source_path)
            source.git.config("user.email", "test@example.com")
            source.git.config("user.name", "Test")

            payload = source_path / "version.txt"
            payload.write_text("one")
            source.index.add(["version.txt"])
            first = source.index.commit("first").hexsha
            payload.write_text("two")
            source.index.add(["version.txt"])
            second = source.index.commit("second").hexsha

            old_workspace = git_service.WORKSPACE_DIR
            old_build_workspace = git_service.BUILD_WORKSPACE_DIR
            git_service.WORKSPACE_DIR = temp_path / "workspace"
            git_service.BUILD_WORKSPACE_DIR = git_service.WORKSPACE_DIR / "builds"
            try:
                repo = Repository(id=42, name="same-name", source_type="local", local_path=str(source_path))
                first_path = git_service.prepare_build_path(repo, 101, first)
                second_path = git_service.prepare_build_path(repo, 102, second)
                self.assertNotEqual(first_path, second_path)
                self.assertEqual((first_path / "version.txt").read_text(), "one")
                self.assertEqual((second_path / "version.txt").read_text(), "two")
            finally:
                git_service.WORKSPACE_DIR = old_workspace
                git_service.BUILD_WORKSPACE_DIR = old_build_workspace


if __name__ == "__main__":
    unittest.main()
