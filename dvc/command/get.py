import argparse
import logging

from .base import append_doc_link
from .base import CmdBaseNoRepo
from dvc.exceptions import DvcException, NotDvcRepoError


logger = logging.getLogger(__name__)


class CmdGet(CmdBaseNoRepo):
    def _show_url(self):
        from dvc.api import get_url

        try:
            url = get_url(
                self.args.path, repo=self.args.url, rev=self.args.rev
            )
            logger.info(url)
        except NotDvcRepoError:
            # NOTE: there's no way to get direct links to files inside
            # git repository.
            logger.exception(
                "Could not show url for '{}' from '{}'. ".format(
                    self.args.path, self.args.url
                )
                + "Only DVC repository is supported currently.",
                exc_info=None,
            )
            return 1
        except DvcException:
            logger.exception(
                "failed to show url for '{}' from '{}'".format(
                    self.args.path, self.args.url
                )
            )
            return 1

        return 0

    def run(self):
        if self.args.show_url:
            return self._show_url()

        return self._get_file_from_repo()

    def _get_file_from_repo(self):
        from dvc.repo import Repo

        try:
            Repo.get(
                self.args.url,
                path=self.args.path,
                out=self.args.out,
                rev=self.args.rev,
            )
            return 0
        except DvcException:
            logger.exception(
                "failed to get '{}' from '{}'".format(
                    self.args.path, self.args.url
                )
            )
            return 1


def add_parser(subparsers, parent_parser):
    GET_HELP = (
        "Download a file or directory from any DVC project or Git repository."
    )
    get_parser = subparsers.add_parser(
        "get",
        parents=[parent_parser],
        description=append_doc_link(GET_HELP, "get"),
        help=GET_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    get_parser.add_argument(
        "url",
        help="Location of DVC project or Git repository to download from",
    )
    get_parser.add_argument(
        "path",
        help="Path to a file or directory within the project or repository",
    )
    get_parser.add_argument(
        "-o", "--out", nargs="?", help="Destination path to download files to"
    )
    get_parser.add_argument(
        "--rev", nargs="?", help="Git revision (e.g. branch, tag, SHA)"
    )
    get_parser.add_argument(
        "--show-url",
        action="store_true",
        help="Returns path/url to the location in remote for specified path",
    )
    get_parser.set_defaults(func=CmdGet)
