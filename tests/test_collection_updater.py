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

import unittest
from shutil import rmtree, copy
from satyr.utils import makedirs
from os import getcwd
import os.path

from PyQt4.QtGui import QApplication
from PyQt4.QtCore import QTimer, QEventLoop

from satyr.collection_updater import CollectionUpdater

from common import app, test_path

class TestCollectionUpdater (unittest.TestCase):

    def setUp (self):
        app.setApplicationName ("TestCollectionUpdater")
        makedirs (test_path)
        self.n= 0

    def tearDown (self):
        self.col.stop ()
        rmtree (test_path)

    def count (self, l):
        self.n+= len (l)

    def test_new_file (self):
        dst= os.path.join (test_path, '01-null.mp3')

        def copy_file ():
            copy ('tests/src/01-null.mp3', dst)

        self.col= CollectionUpdater (test_path)
        QTimer.singleShot (0, copy_file)
        self.col.foundSongs.connect (self.count)
        QTimer.singleShot (1000, app.quit)
        app.exec_ ()

        self.assertEqual (self.n, 1)

    def test_new_wrong_file (self):
        dst= os.path.join (test_path, '03-do_not_index.txt')

        def copy_file ():
            copy ('tests/src/03-do_not_index.txt', dst)

        self.col= CollectionUpdater (test_path)
        QTimer.singleShot (0, copy_file)
        self.col.foundSongs.connect (self.count)
        QTimer.singleShot (1000, app.quit)
        app.exec_ ()

        self.assertEqual (self.n, 0)

if __name__=='__main__':
    unittest.main ()
