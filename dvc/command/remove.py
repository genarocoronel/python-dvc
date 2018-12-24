import dvc.prompt as prompt
import dvc.logger as logger
from dvc.exceptions import DvcException
from dvc.command.base import CmdBase


class CmdRemove(CmdBase):
    def _is_outs_only(self, target):
        if not self.args.purge:
            return True

        if self.args.force:
            return False

        msg = (
            u'Are you sure you want to remove {} with its outputs?'
            .format(target)
        )

        if prompt.confirm(msg):
            return False

        raise DvcException(
            u'Cannot purge without a confirmation from the user.'
            u" Use '-f' to force."
        )

    def run(self):
        for target in self.args.targets:
            try:
                outs_only = self._is_outs_only(target)
                self.project.remove(target, outs_only=outs_only)
            except DvcException:
                logger.error('failed to remove {}'.format(target))
                return 1
        return 0
