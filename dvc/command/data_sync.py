from dvc.command.base import CmdBase
import dvc.logger as logger


class CmdDataBase(CmdBase):
    def do_run(self, target):
        pass

    def run(self):
        if not self.args.targets:
            return self.do_run()

        ret = 0
        for target in self.args.targets:
            if self.do_run(target):
                ret = 1
        return ret


class CmdDataPull(CmdDataBase):
    def do_run(self, target=None):
        try:
            self.project.pull(target=target,
                              jobs=self.args.jobs,
                              remote=self.args.remote,
                              show_checksums=self.args.show_checksums,
                              all_branches=self.args.all_branches,
                              all_tags=self.args.all_tags,
                              with_deps=self.args.with_deps,
                              force=self.args.force,
                              from_directory=self.args.recursive)
        except Exception:
            logger.error('failed to pull data from the cloud')
            return 1
        return 0


class CmdDataPush(CmdDataBase):
    def do_run(self, target=None):
        try:
            self.project.push(target=target,
                              jobs=self.args.jobs,
                              remote=self.args.remote,
                              show_checksums=self.args.show_checksums,
                              all_branches=self.args.all_branches,
                              all_tags=self.args.all_tags,
                              with_deps=self.args.with_deps,
                              from_directory=self.args.recursive)
        except Exception:
            logger.error('failed to push data to the cloud')
            return 1
        return 0


class CmdDataFetch(CmdDataBase):
    def do_run(self, target=None):
        try:
            self.project.fetch(target=target,
                               jobs=self.args.jobs,
                               remote=self.args.remote,
                               show_checksums=self.args.show_checksums,
                               all_branches=self.args.all_branches,
                               all_tags=self.args.all_tags,
                               with_deps=self.args.with_deps,
                               from_directory=self.args.recursive)
        except Exception:
            logger.error('failed to fetch data from the cloud')
            return 1
        return 0
