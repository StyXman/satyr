# vim: set fileencoding=utf-8 :
# (c) 2009 Marcos Dione <mdione@grulic.org.ar>

# This file is part of satyr.

# satyr is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.

# satyr is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with satyr.  If not, see <http://www.gnu.org/licenses/>.


# qt/kde related
from PyQt4.QtCore import pyqtSignal, QThread, QObject

# misc utils
import dbus.service
# TODO: IN_DELETE, IN_DELETE_SELF,
from pyinotify import WatchManager, ThreadedNotifier, ProcessEvent, IN_CREATE

# we needed before logging to get the handler
import satyr

# logging
import logging
logger= logging.getLogger(__name__)
# logger.setLevel (logging.DEBUG)

class CollectionUpdater (QObject, ProcessEvent):
    scanning= pyqtSignal (unicode)
    foundSongs= pyqtSignal (list)
    wm= WatchManager ()

    def __init__ (self, path):
        QObject.__init__ (self)
        ProcessEvent.__init__ (self)
        self.notifier= ThreadedNotifier (self.wm, self)
        self.notifier.start ()
        self.watch= self.wm.add_watch (path, IN_CREATE, rec=True)
        logger.debug ("watch: %r", self.watch)

    def __delete__ (self):
        self.notifier.stop ()
        for fd in self.watch.values ():
            try:
                self.wm.del_watch (fd)
            except OSError as e:
                # closes #12
                if not e.errno==errno.EBADFD:
                    raise e

    def process_IN_CREATE (self, event):
        logger.debug ("%s, %s", event, event.name)
        self.foundSongs.emit ([event.name])
