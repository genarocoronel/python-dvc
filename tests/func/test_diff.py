import hashlib
import os
import pytest


def digest(text):
    return hashlib.md5(bytes(text, "utf-8")).hexdigest()


def test_no_scm(tmp_dir, dvc):
    tmp_dir.dvc_gen("file", "text")

    pytest.skip("TODO: define behavior, should it fail?")


def test_added(tmp_dir, scm, dvc):
    tmp_dir.dvc_gen("file", "text")

    result = {
        "added": [{"filename": "file", "checksum": digest("text")}],
        "deleted": [],
        "modified": [],
    }

    assert result == dvc.diff()


def test_deleted(tmp_dir, scm, dvc):
    tmp_dir.dvc_gen("file", "text", commit="add file")
    (tmp_dir / "file.dvc").unlink()

    result = {
        "added": [],
        "deleted": [{"filename": "file", "checksum": digest("text")}],
        "modified": [],
    }

    assert result == dvc.diff()


def test_modified(tmp_dir, scm, dvc):
    tmp_dir.dvc_gen("file", "first", commit="first version")
    tmp_dir.dvc_gen("file", "second")

    result = {
        "added": [],
        "deleted": [],
        "modified": [
            {
                "filename": "file",
                "checksum": {"old": digest("first"), "new": digest("second")},
            }
        ],
    }

    assert result == dvc.diff()


def test_refs(tmp_dir, scm, dvc):
    tmp_dir.dvc_gen("file", "first", commit="first version")
    tmp_dir.dvc_gen("file", "second", commit="second version")
    tmp_dir.dvc_gen("file", "third", commit="third version")

    HEAD_2 = digest("first")
    HEAD_1 = digest("second")
    HEAD = digest("third")

    assert dvc.diff("HEAD~1") == {
        "added": [],
        "deleted": [],
        "modified": [
            {"filename": "file", "checksum": {"old": HEAD_1, "new": HEAD}}
        ],
    }

    assert dvc.diff("HEAD~2", "HEAD~1") == {
        "added": [],
        "deleted": [],
        "modified": [
            {"filename": "file", "checksum": {"old": HEAD_2, "new": HEAD_1}}
        ],
    }

    pytest.skip('TODO: test dvc.diff("missing")')


def test_target(tmp_dir, scm, dvc):
    tmp_dir.dvc_gen("foo", "foo")
    tmp_dir.dvc_gen("bar", "bar")
    scm.add([".gitignore", "foo.dvc", "bar.dvc"])
    scm.commit("lowercase")

    tmp_dir.dvc_gen("foo", "FOO")
    tmp_dir.dvc_gen("bar", "BAR")
    scm.add(["foo.dvc", "bar.dvc"])
    scm.commit("uppercase")

    assert dvc.diff("HEAD~1", target="foo") == {
        "added": [],
        "deleted": [],
        "modified": [
            {
                "filename": "foo",
                "checksum": {"old": digest("foo"), "new": digest("FOO")},
            }
        ],
    }

    assert dvc.diff("HEAD~1", target="missing") == {
        "added": [],
        "deleted": [],
        "modified": [],
    }


def test_directories(tmp_dir, scm, dvc):
    tmp_dir.dvc_gen({"dir": {"1": "1", "2": "2"}}, commit="add a directory")
    tmp_dir.dvc_gen({"dir": {"3": "3"}}, commit="add a file")
    tmp_dir.dvc_gen({"dir": {"2": "two"}}, commit="modify a file")

    (tmp_dir / "dir" / "2").unlink()
    dvc.add("dir")
    scm.add("dir.dvc")
    scm.commit("delete a file")

    assert dvc.diff(":/init", ":/directory") == {
        "added": [
            {
                "filename": "dir/",
                "checksum": "5fb6b29836c388e093ca0715c872fe2a.dir",
            },
            {"filename": os.path.join("dir", "1"), "checksum": digest("1")},
            {"filename": "dir/2", "checksum": digest("2")},
        ],
        "deleted": [],
        "modified": [],
    }

    assert dvc.diff(":/directory", ":/modify") == {
        "added": [
            {"filename": os.path.join("dir", "3"), "checksum": digest("3")}
        ],
        "deleted": [],
        "modified": [
            {
                "filename": os.path.join("dir", ""),
                "checksum": {
                    "old": "5fb6b29836c388e093ca0715c872fe2a.dir",
                    "new": "9b5faf37366b3370fd98e3e60ca439c1.dir",
                },
            },
            {
                "filename": os.path.join("dir", "2"),
                "checksum": {"old": digest("2"), "new": digest("two")},
            },
        ],
    }

    assert dvc.diff(":/modify", ":/delete") == {
        "added": [],
        "deleted": [
            {"filename": os.path.join("dir", "2"), "checksum": digest("two")}
        ],
        "modified": [
            {
                "filename": os.path.join("dir", ""),
                "checksum": {
                    "old": "9b5faf37366b3370fd98e3e60ca439c1.dir",
                    "new": "83ae82fb367ac9926455870773ff09e6.dir",
                },
            }
        ],
    }


def test_cli(tmp_dir, scm, dvc):
    tmp_dir.dvc_gen("file", "text")
    # main(["diff"])
    pytest.skip("TODO: define output structure")


def test_json(tmp_dir, scm, dvc):
    # result = {
    #     "added": {...},
    #     "renamed": {...},
    #     "modified": {...},
    #     "deleted": {...},
    # }

    # main(["diff", "--json"])
    pytest.skip("TODO: define output structure")
