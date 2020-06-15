import pytest

from dvc.remote import get_cloud_tree
from dvc.remote.gs import GSRemoteTree
from dvc.remote.s3 import S3RemoteTree


def test_remote_with_checksum_jobs(dvc):
    dvc.config["remote"]["with_checksum_jobs"] = {
        "url": "s3://bucket/name",
        "checksum_jobs": 100,
    }
    dvc.config["core"]["checksum_jobs"] = 200

    tree = get_cloud_tree(dvc, name="with_checksum_jobs")
    assert tree.checksum_jobs == 100


def test_remote_without_checksum_jobs(dvc):
    dvc.config["remote"]["without_checksum_jobs"] = {"url": "s3://bucket/name"}
    dvc.config["core"]["checksum_jobs"] = 200

    tree = get_cloud_tree(dvc, name="without_checksum_jobs")
    assert tree.checksum_jobs == 200


def test_remote_without_checksum_jobs_default(dvc):
    dvc.config["remote"]["without_checksum_jobs"] = {"url": "s3://bucket/name"}

    tree = get_cloud_tree(dvc, name="without_checksum_jobs")
    assert tree.checksum_jobs == tree.CHECKSUM_JOBS


@pytest.mark.parametrize("tree_cls", [GSRemoteTree, S3RemoteTree])
def test_makedirs_not_create_for_top_level_path(tree_cls, dvc, mocker):
    url = f"{tree_cls.scheme}://bucket/"
    tree = tree_cls(dvc, {"url": url})
    mocked_client = mocker.PropertyMock()
    # we use remote clients with same name as scheme to interact with remote
    mocker.patch.object(tree_cls, tree.scheme, mocked_client)

    tree.makedirs(tree.path_info)
    assert not mocked_client.called
