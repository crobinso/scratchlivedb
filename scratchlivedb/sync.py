
from scratchlivedb.scratchdb import log


class SyncBase(object):
    """
    Base class for sync plugins, which read data from some source
    and sync with a SeratoFile instance
    """
    def __init__(self, source=None):
        self.source = source


    ###################
    # Private methods #
    ###################

    def _find_shared_root(self, paths):
        """
        Given a list of paths, find the shared root path
        """
        ret = paths[0]

        for key in paths:
            tmpbase = ret
            while not key.startswith(tmpbase):
                log.debug("key=%s doesn't start with base=%s, shrinking it",
                          key, tmpbase)
                tmpbase = tmpbase[:-1]

            ret = tmpbase
        return ret


    ##############
    # Public API #
    ##############

    def sync(self, db):
        raise NotImplementedError("Must be implemented in subclass")
