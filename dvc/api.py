import os
import importlib.util
from contextlib import contextmanager

try:
    from contextlib import _GeneratorContextManager as GCM
except ImportError:
    from contextlib import GeneratorContextManager as GCM

import ruamel.yaml

from dvc.utils.compat import urlparse
from dvc.repo import Repo
from dvc.external_repo import external_repo


def get_url(path, repo=None, rev=None, remote=None):
    """Returns an url of a resource specified by path in repo"""
    with _make_repo(repo, rev=rev) as _repo:
        abspath = os.path.join(_repo.root_dir, path)
        out, = _repo.find_outs_by_path(abspath)
        remote_obj = _repo.cloud.get_remote(remote)
        return str(remote_obj.checksum_to_path_info(out.checksum))


def open(path, repo=None, rev=None, remote=None, mode="r", encoding=None):
    """Opens a specified resource as a file descriptor"""
    args = (path,)
    kwargs = {
        "repo": repo,
        "remote": remote,
        "rev": rev,
        "mode": mode,
        "encoding": encoding,
    }
    return _OpenContextManager(_open, args, kwargs)


class _OpenContextManager(GCM):
    def __init__(self, func, args, kwds):
        self.gen = func(*args, **kwds)
        self.func, self.args, self.kwds = func, args, kwds

    def __getattr__(self, name):
        raise AttributeError(
            "dvc.api.open() should be used in a with statement"
        )


def _open(path, repo=None, rev=None, remote=None, mode="r", encoding=None):
    with _make_repo(repo, rev=rev) as _repo:
        abspath = os.path.join(_repo.root_dir, path)
        with _repo.open(
            abspath, remote=remote, mode=mode, encoding=encoding
        ) as fd:
            yield fd


def read(path, repo=None, rev=None, remote=None, mode="r", encoding=None):
    """Read a specified resource into string"""
    with open(
        path, repo=repo, rev=rev, remote=remote, mode=mode, encoding=encoding
    ) as fd:
        return fd.read()


@contextmanager
def _make_repo(repo_url, rev=None):
    if not repo_url or urlparse(repo_url).scheme == "":
        assert rev is None, "Custom revision is not supported for local repo"
        yield Repo(repo_url)
    else:
        with external_repo(url=repo_url, rev=rev) as repo:
            yield repo


def summon(name, repo=None, rev=None):
    # 1. Read grimoire.yaml
    # 2. Pull dependencies (TODO)
    # 3. Get the call and parameters
    # 4. Invoke the call with the given parameters
    # 5. Return the result

    with _make_repo(repo, rev=rev) as _repo:
        grimoire_path = os.path.join(_repo.root_dir, "grimoire.yaml")

        with open(grimoire_path, "r") as fobj:
            spells = ruamel.yaml.load(fobj.read()).get("spells")

        spell = next(spell for spell in spells if spell.get("name") == name)
        spell_path = os.path.join(_repo.root_dir, spell.get("file"))
        spec = importlib.util.spec_from_file_location(name, spell_path)
        module = importlib.util.module_from_spec(spec)

        spec.loader.exec_module(module)

        method = getattr(module, spell.get("method"))

        return method(**spell.get("params"))
