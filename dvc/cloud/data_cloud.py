import re
from multiprocessing.pool import ThreadPool

from dvc.cloud.instance_manager import CloudSettings
from dvc.logger import Logger
from dvc.exceptions import DvcException
from dvc.config import ConfigError
from dvc.utils import map_progress
from dvc.config import Config

from dvc.cloud.aws import DataCloudAWS
from dvc.cloud.gcp import DataCloudGCP
from dvc.cloud.local import DataCloudLOCAL
from dvc.cloud.base import DataCloudBase


class DataCloud(object):
    """ Generic class to do initial config parsing and redirect to proper DataCloud methods """

    CLOUD_MAP = {
        'aws'   : DataCloudAWS,
        'gcp'   : DataCloudGCP,
        'local' : DataCloudLOCAL,
    }

    SCHEME_MAP = {
        's3'    : 'aws',
        'gs'    : 'gcp',
        None    : 'local',
    }

    def __init__(self, cache, config):
        self._cache = cache
        self._config = config

        remote = self._config[Config.SECTION_CORE].get(Config.SECTION_CORE_REMOTE, '')
        if remote == '':
            if config[Config.SECTION_CORE].get(Config.SECTION_CORE_CLOUD, None):
                # backward compatibility
                Logger.warn('Using obsoleted config format. Consider updating.')
                self._cloud = self.__init__compat()
            else:
                self._cloud = None
            return

        self._cloud = self._init_remote(remote)

    def _init_remote(self, remote):
        section = Config.SECTION_REMOTE_FMT.format(remote)
        cloud_config = self._config.get(section, None)
        if not cloud_config:
            raise ConfigError("Can't find remote section '{}' in config".format(section))

        url = cloud_config[Config.SECTION_REMOTE_URL]
        res = re.match(Config.SECTION_REMOTE_URL_REGEX, url)
        if not res:
            raise ConfigError("Unknown format of url '{}'".format(url))

        scheme = res.group('scheme')
        cloud_type = self.SCHEME_MAP.get(scheme, None)
        if not cloud_type:
            raise ConfigError("Unsupported scheme '{}' in '{}'".format(scheme, url))

        return self._init_cloud(self._cache, cloud_config, cloud_type)

    def __init__compat(self):
        cloud_type = self._config[Config.SECTION_CORE].get(Config.SECTION_CORE_CLOUD, '').strip().lower()
        if cloud_type == '':
            self._cloud = None
            return
        elif cloud_type not in self.CLOUD_MAP.keys():
            raise ConfigError('Wrong cloud type %s specified' % cloud_type)

        cloud_config = self._config.get(cloud_type, None)
        if not cloud_config:
            raise ConfigError('Can\'t find cloud section \'[%s]\' in config' % cloud_type)

        return self._init_cloud(self._cache, cloud_config, cloud_type)

    def _init_cloud(self, cache, cloud_config, cloud_type):
        cloud_settings = self.get_cloud_settings(cache,
                                                 self._config,
                                                 cloud_config)

        cloud = self.CLOUD_MAP[cloud_type](cloud_settings)
        cloud.sanity_check()
        return cloud

    @staticmethod
    def get_cloud_settings(cache, config, cloud_config):
        """
        Obtain cloud settings from config.
        """
        global_storage_path = config[Config.SECTION_CORE].get(Config.SECTION_CORE_STORAGEPATH, None)
        if global_storage_path:
            Logger.warn('Using obsoleted config format. Consider updating.')

        cloud_settings = CloudSettings(cache, global_storage_path, cloud_config)
        return cloud_settings

    def _collect(self, cloud, targets, jobs, local):
        collected = set()
        pool = ThreadPool(processes=jobs)
        args = zip(targets, [local]*len(targets))
        ret = pool.map(cloud.collect, args)

        for r in ret:
            collected |= set(r)

        return collected

    def _map_targets(self, func, targets, jobs, collect_local=False, collect_cloud=False, remote=None):
        """
        Process targets as data items in parallel.
        """

        if not remote:
            cloud = self._cloud
        else:
            cloud = self._init_remote(remote)

        if not cloud:
            return

        cloud.connect()

        collected = set()
        if collect_local:
            collected |= self._collect(cloud, targets, jobs, True)
        if collect_cloud:
            collected |= self._collect(cloud, targets, jobs, False)

        return map_progress(getattr(cloud, func), list(collected), jobs)

    def push(self, targets, jobs=1, remote=None):
        """
        Push data items in a cloud-agnostic way.
        """
        return self._map_targets('push', targets, jobs, collect_local=True, remote=remote)

    def pull(self, targets, jobs=1, remote=None):
        """
        Pull data items in a cloud-agnostic way.
        """
        return self._map_targets('pull', targets, jobs, collect_cloud=True, remote=remote)

    def status(self, targets, jobs=1, remote=None):
        """
        Check status of data items in a cloud-agnostic way.
        """
        return self._map_targets('status', targets, jobs, True, True, remote=remote)
