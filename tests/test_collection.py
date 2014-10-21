# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :
# (c) 2009-2012 Marcos Dione <mdione@grulic.org.ar>

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
from PyQt4.QtCore import QTimer

from satyr.collection import Collection
from satyr.song import Song

from common import app, test_path

class TestCollection (unittest.TestCase):

    def setUp (self):
        app.setApplicationName ("TestCollection")
        makedirs (test_path)

    def tearDown (self):
        rmtree (test_path)

    def common_tests (self, col, songs, songsById, offset):
        self.assertEqual (col.songs, songs)
        self.assertEqual (col.songsById, songsById)
        self.assertEqual (col.count, len (songs))
        self.assertEqual (col.offset, offset)

    def test_creation (self):
        col= Collection (None)
        self.common_tests (col, [], {}, 0)

    def test_creation_with_path (self):
        col= Collection (None, test_path)
        self.common_tests (col, [], {}, 0)

    def test_scan_one_song (self):
        dst= os.path.join (test_path, '01-null.mp3')
        copy ('tests/src/01-null.mp3', dst)

        col= Collection (app, test_path)
        QTimer.singleShot (1, col.scan)
        col.scanFinished.connect (app.quit)
        app.exec_ ()

        s= Song (None, os.path.abspath (dst))
        self.common_tests (col, [s], {s.id: s}, 0)
        col.updater.stop ()

    def test_scan_one_file (self):
        dst= os.path.join (test_path, '03-do_not_index.txt')
        copy ('tests/src/03-do_not_index.txt', dst)

        col= Collection (app, test_path)
        QTimer.singleShot (1, col.scan)
        col.scanFinished.connect (app.quit)
        app.exec_ ()

        self.common_tests (col, [], {}, 0)
        col.updater.stop ()

    def test_new_song (self):
        dst= os.path.join (test_path, '01-null.mp3')

        def copy_file ():
            copy ('tests/src/01-null.mp3', dst)

        col= Collection (app, test_path)
        QTimer.singleShot (0, copy_file)
        QTimer.singleShot (1000, app.quit)
        app.exec_ ()

        s= Song (None, os.path.abspath (dst))
        self.common_tests (col, [s], {s.id: s}, 0)
        col.updater.stop ()

    def test_new_wrong_file (self):
        dst= os.path.join (test_path, '03-do_not_index.txt')

        def copy_file ():
            copy ('tests/src/03-do_not_index.txt', dst)

        col= Collection (app, test_path)
        QTimer.singleShot (0, copy_file)
        QTimer.singleShot (1000, app.quit)
        app.exec_ ()

        self.common_tests (col, [], {}, 0)
        col.updater.stop ()

if __name__=='__main__':
    unittest.main ()
