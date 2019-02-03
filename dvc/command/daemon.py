from __future__ import unicode_literals

from dvc.command.base import CmdBase, fix_subparsers


class CmdDaemonBase(CmdBase):
    def __init__(self, args):
        self.args = args
        self.config = None
        self.set_loglevel(args)

    def run_cmd(self):
        return self.run()


class CmdDaemonUpdater(CmdDaemonBase):
    def run(self):
        import os
        from dvc.project import Project
        from dvc.updater import Updater

        root_dir = Project.find_root()
        dvc_dir = os.path.join(root_dir, Project.DVC_DIR)
        updater = Updater(dvc_dir)
        updater.fetch(detach=False)

        return 0


class CmdDaemonAnalytics(CmdDaemonBase):
    def run(self):
        from dvc.analytics import Analytics

        analytics = Analytics.load(self.args.target)
        analytics.send()

        return 0


def add_parser(subparsers, parent_parser):
    DAEMON_HELP = "Service daemon."
    daemon_parser = subparsers.add_parser(
        "daemon",
        parents=[parent_parser],
        description=DAEMON_HELP,
        help=DAEMON_HELP,
    )

    daemon_subparsers = daemon_parser.add_subparsers(
        dest="cmd", help="Use dvc daemon CMD --help for command-specific help."
    )

    fix_subparsers(daemon_subparsers)

    DAEMON_UPDATER_HELP = "Fetch latest available version."
    daemon_updater_parser = daemon_subparsers.add_parser(
        "updater",
        parents=[parent_parser],
        description=DAEMON_UPDATER_HELP,
        help=DAEMON_UPDATER_HELP,
    )
    daemon_updater_parser.set_defaults(func=CmdDaemonUpdater)

    DAEMON_ANALYTICS_HELP = "Send dvc usage analytics."
    daemon_analytics_parser = daemon_subparsers.add_parser(
        "analytics",
        parents=[parent_parser],
        description=DAEMON_ANALYTICS_HELP,
        help=DAEMON_ANALYTICS_HELP,
    )
    daemon_analytics_parser.add_argument("target", help="Analytics file.")
    daemon_analytics_parser.set_defaults(func=CmdDaemonAnalytics)
