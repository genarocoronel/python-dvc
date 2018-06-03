from dvc.dependency.s3 import DependencyS3


class OutputS3(DependencyS3):
    PARAM_CACHE = 'cache'

    def __init__(self, stage, path, info=None, cache=True):
        super(OutputS3, self).__init__(stage, path, info)
        self.use_cache = cache

    def dumpd(self):
        ret = super(OutputS3, self).dumpd()
        ret[self.PARAM_CACHE] = self.use_cache
        return ret

    def changed(self):
        if super(OutputS3, self).changed():
            return True

        if self.use_cache and self.info != self.project.cache.s3.save_info(self.path_info):
            return True

        return False

    def checkout(self):
        if not self.use_cache:
            return

        self.project.cache.s3.checkout(self.path_info, self.info)

    def save(self):
        super(OutputS3, self).save()

        if not self.use_cache:
            return

        self.info = self.project.cache.s3.save(self.path_info)

    def remove(self):
        self.s3.Object(self.bucket, self.key).delete()
