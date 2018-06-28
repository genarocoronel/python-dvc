import os
import uuid
import json
import shutil
import filecmp

from dvc.system import System
from dvc.remote.base import RemoteBase
from dvc.state import State
from dvc.logger import Logger
from dvc.utils import remove, move, copyfile, file_md5
from dvc.config import Config
from dvc.exceptions import DvcException


class RemoteLOCAL(RemoteBase):
    scheme = ''
    REGEX = r'^(?P<path>(/+|.:\\+).*)$'
    PARAM_MD5 = State.PARAM_MD5
    PARAM_RELPATH = State.PARAM_RELPATH

    CACHE_TYPES = ['reflink', 'hardlink', 'symlink', 'copy']
    CACHE_TYPE_MAP = {
        'copy': shutil.copyfile,
        'symlink': System.symlink,
        'hardlink': System.hardlink,
        'reflink': System.reflink,
    }

    def __init__(self, project, config):
        self.project = project
        self.link_state = project.link_state
        storagepath = config.get(Config.SECTION_AWS_STORAGEPATH, None)
        self.cache_dir = config.get(Config.SECTION_REMOTE_URL, storagepath)

        types = config.get(Config.SECTION_CACHE_TYPE, None)
        if types:
            if isinstance(types, str):
                types = [t.strip() for t in types.split(',')]
            self.cache_types = types
        else:
            self.cache_types = self.CACHE_TYPES

        if self.cache_dir != None and not os.path.exists(self.cache_dir):
            os.mkdir(self.cache_dir)

        self.state = State(self.cache_dir)

    @property
    def prefix(self):
        return self.cache_dir

    def all(self):
        clist = []
        for entry in os.listdir(self.cache_dir):
            subdir = os.path.join(self.cache_dir, entry)
            if not os.path.isdir(subdir):
                continue

            for cache in os.listdir(subdir):
                path = os.path.join(subdir, cache)
                clist.append(self.path_to_md5(path))

        return clist

    def get(self, md5):
        if not md5:
            return None

        return os.path.join(self.cache_dir, md5[0:2], md5[2:])

    def path_to_md5(self, path):
        relpath = os.path.relpath(path, self.cache_dir)
        return os.path.dirname(relpath) + os.path.basename(relpath)

    def changed(self, md5):
        cache = self.get(md5)
        if self.state.changed(cache, md5=md5):
            if os.path.exists(cache):
                Logger.warn('Corrupted cache file {}'.format(os.path.relpath(cache)))
                remove(cache)
            return True

        return False

    def link(self, src, link, dump=True):
        dname = os.path.dirname(link)
        if not os.path.exists(dname):
            os.makedirs(dname)

        if self.cache_types != None:
            types = self.cache_types
        else:
            types = self.CACHE_TYPES

        for typ in types:
            try:
                self.CACHE_TYPE_MAP[typ](src, link)
                self.link_state.update(link, dump=dump)
                return
            except Exception as exc:
                msg = 'Cache type \'{}\' is not supported'.format(typ)
                Logger.debug(msg)
                if typ == types[-1]:
                    raise DvcException(msg, cause=exc)

    @staticmethod
    def load_dir_cache(path):
        try:
            with open(path, 'r') as fd:
                d = json.load(fd)
        except Exception as exc:
            msg = u'Failed to load dir cache \'{}\''
            Logger.error(msg.format(os.path.relpath(path)), exc)
            return []

        if not isinstance(d, list):
            msg = u'Dir cache file format error \'{}\': skipping the file'
            Logger.error(msg.format(os.path.relpath(path)))
            return []

        return d

    @staticmethod
    def is_dir_cache(cache):
        return cache.endswith(State.MD5_DIR_SUFFIX)

    def checkout(self, path_info, checksum_info):
        path = path_info['path']
        md5 = checksum_info.get(self.PARAM_MD5, None)
        cache = self.get(md5)

        if not cache or not os.path.exists(cache) or self.changed(md5):
            if cache:
                msg = u'Cache \'{}\' not found. File \'{}\' won\'t be created.'
                Logger.warn(msg.format(md5, os.path.relpath(path)))
            remove(path)
            return

        if os.path.exists(path):
            msg = u'Data \'{}\' exists. Removing before checkout'
            Logger.debug(msg.format(os.path.relpath(path)))
            remove(path)

        msg = u'Checking out \'{}\' with cache \'{}\''
        Logger.debug(msg.format(os.path.relpath(path), os.path.relpath(cache)))

        if not self.is_dir_cache(cache):
            self.link(cache, path, dump=True)
            return

        # Create dir separately so that dir is created
        # even if there are no files in it
        if not os.path.exists(path):
            os.makedirs(path)

        for entry in self.load_dir_cache(cache):
            md5 = entry[self.PARAM_MD5]
            relpath = entry[self.PARAM_RELPATH]
            c = self.get(md5)
            p = os.path.join(path, relpath)
            self.link(c, p, dump=False)
        self.link_state.dump()

    def _move(self, inp, outp):
        # moving in two stages to make last the move atomic in
        # case inp and outp are in different filesystems
        tmp = '{}.{}'.format(outp, str(uuid.uuid4()))
        move(inp, tmp)
        move(tmp, outp)

    def _save_file(self, path_info):
        path = path_info['path']
        md5 = self.state.update(path)
        cache = self.get(md5)
        if self.changed(md5):
            Logger.debug(u'Saving \'{}\' to \'{}\''.format(os.path.relpath(path),
                                                           os.path.relpath(cache)))
            self._move(path, cache)
            self.state.update(cache)

        return {self.PARAM_MD5: md5}

    def _save_dir(self, path_info):
        path = path_info['path']
        md5 = self.state.update(path)
        cache = self.get(md5)
        dname = os.path.dirname(cache)
        dir_info = self.state.collect_dir(path)

        for entry in dir_info:
            relpath = entry[State.PARAM_RELPATH]
            p = os.path.join(path, relpath)

            self._save_file({'scheme': 'local', 'path': p})

        if not os.path.isdir(dname):
            os.makedirs(dname)

        Logger.debug(u'Saving directory \'{}\' to \'{}\''.format(os.path.relpath(path),
                                                                 os.path.relpath(cache)))

        with open(cache, 'w+') as fd:
            json.dump(dir_info, fd, sort_keys=True)

        return {self.PARAM_MD5: md5}

    def save(self, path_info):
        if path_info['scheme'] != 'local':
            raise NotImplementedError

        path = path_info['path']

        if os.path.isdir(path):
            checksum_info = self._save_dir(path_info)
        else:
            checksum_info = self._save_file(path_info)

        self.checkout(path_info, checksum_info)

        return checksum_info

    def save_info(self, path_info):
        if path_info['scheme'] != 'local':
            raise NotImplementedError

        return {self.PARAM_MD5: self.state.update(path_info['path'])}

    def remove(self, path_info):
        if path_info['scheme'] != 'local':
            raise NotImplementedError

        remove(path_info['path'])

    def move(self, from_info, to_info):
        if from_info['scheme'] != 'local' or to_info['scheme'] != 'local':
            raise NotImplementedError

        move(from_info['path'], to_info['path'])

    def cache_file_key(self, path):
        relpath = os.path.relpath(os.path.abspath(path), self.project.cache.local.cache_dir)
        return os.path.join(self.prefix, relpath)

    def _get_path_info(self, path):
        key = self.cache_file_key(path)
        if not os.path.exists(key) or not os.path.isfile(key):
            return None
        return {'scheme': 'local',
                'path': key}

    def _new_path_info(self, path):
        key = self.cache_file_key(path)
        return {'scheme': 'local',
                'path': key}

    def upload(self, path, path_info, name=None):
        if path_info['scheme'] != 'local':
            raise NotImplementedError

        Logger.debug("Uploading '{}' to '{}'".format(path, path_info['path']))

        if not name:
            name = os.path.basename(path)

        self._makedirs(path_info['path'])

        try:
            copyfile(path, path_info['path'], name=name)
        except Exception as exc:
            Logger.error("Failed to upload '{}' tp '{}'".format(path, path_info['path']))
            return None

        return path

    def download(self, path_info, path, no_progress_bar=False, name=None):
        if path_info['scheme'] != 'local':
            raise NotImplementedError

        Logger.debug("Downloading '{}' to '{}'".format(path_info['path'], path))

        if not name:
            name = os.path.basename(path)

        self._makedirs(path)
        tmp_file = self.tmp_file(path)
        try:
            copyfile(path_info['path'], tmp_file, no_progress_bar=no_progress_bar, name=name)
        except Exception as exc:
            Logger.error("Failed to download '{}' to '{}'".format(path_info['path'], path), exc)
            return None

        os.rename(tmp_file, path)

        return path

    def gc(self, checksum_infos):
        used_md5s = [info[self.PARAM_MD5] for info in checksum_infos]

        for md5 in self.all():
            if md5 in used_md5s:
                continue
            remove(self.get(md5))
