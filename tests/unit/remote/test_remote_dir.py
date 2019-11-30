# -*- coding: utf-8 -*-
import pytest

from dvc.remote.s3 import RemoteS3

from tests.remotes import GCP, S3Mocked

remotes = [GCP, S3Mocked]

FILE_WITH_CONTENTS = {
    "empty_dir/": "",
    "empty_file": "",
    "foo": "foo",
    "data/alice": "alice",
    "data/alpha": "alpha",
    "data/subdir/1": "1",
    "data/subdir/2": "2",
    "data/subdir/3": "3",
    "data/subdir/empty_dir/": "",
    "data/subdir/empty_file": "",
}


@pytest.fixture
def remote(request):
    if not request.param.should_test():
        raise pytest.skip()
    with request.param.remote() as remote:
        with request.param.put_objects(remote, FILE_WITH_CONTENTS):
            yield remote


@pytest.mark.parametrize("remote", remotes, indirect=True)
def test_isdir(remote):
    test_cases = [
        (True, "data"),
        (True, "data/"),
        (True, "data/subdir"),
        (True, "empty_dir"),
        (False, "foo"),
        (False, "data/alice"),
        (False, "data/al"),
        (False, "data/subdir/1"),
    ]

    for expected, path in test_cases:
        assert remote.isdir(remote.path_info / path) == expected


@pytest.mark.parametrize("remote", remotes, indirect=True)
def test_exists(remote):
    test_cases = [
        (True, "data"),
        (True, "data/"),
        (True, "data/subdir"),
        (True, "empty_dir"),
        (True, "empty_file"),
        (True, "foo"),
        (True, "data/alice"),
        (True, "data/subdir/1"),
        (False, "data/al"),
        (False, "foo/"),
    ]

    for expected, path in test_cases:
        assert remote.exists(remote.path_info / path) == expected


@pytest.mark.parametrize("remote", remotes, indirect=True)
def test_walk_files(remote):
    files = [
        remote.path_info / "data/alice",
        remote.path_info / "data/alpha",
        remote.path_info / "data/subdir/1",
        remote.path_info / "data/subdir/2",
        remote.path_info / "data/subdir/3",
        remote.path_info / "data/subdir/empty_file",
    ]

    assert list(remote.walk_files(remote.path_info / "data")) == files


@pytest.mark.parametrize("remote", [S3Mocked], indirect=True)
def test_copy_preserve_etag_across_buckets(remote):
    s3 = remote.s3
    s3.create_bucket(Bucket="another")

    another = RemoteS3(None, {"url": "s3://another", "region": "us-east-1"})

    from_info = remote.path_info / "foo"
    to_info = another.path_info / "foo"

    remote.copy(from_info, to_info)

    from_etag = RemoteS3.get_etag(s3, from_info.bucket, from_info.path)
    to_etag = RemoteS3.get_etag(s3, "another", "foo")

    assert from_etag == to_etag


@pytest.mark.parametrize("remote", remotes, indirect=True)
def test_makedirs(remote):
    empty_dir = remote.path_info / "empty_dir" / ""
    remote.remove(empty_dir)
    assert not remote.exists(empty_dir)
    remote.makedirs(empty_dir)
    assert remote.exists(empty_dir)
    assert remote.isdir(empty_dir)
