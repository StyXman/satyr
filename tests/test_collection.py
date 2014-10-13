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

from common import app

class TestCollection (unittest.TestCase):
    path= 'tests/data'

    def setUp (self):
        app.setApplicationName ("TestCollection")
        makedirs (self.path)

    def tearDown (self):
        rmtree (self.path)

    def common_tests (self, songs, songsById, offset):
        self.assertEqual (self.col.songs, songs)
        self.assertEqual (self.col.songsById, songsById)
        self.assertEqual (self.col.count, len (songs))
        self.assertEqual (self.col.offset, offset)

    def test_creation (self):
        self.col= Collection (None)
        self.common_tests ([], {}, 0)

    def test_creation_with_path (self):
        self.col= Collection (None, self.path)
        self.common_tests ([], {}, 0)

    def test_one_song (self):
        dst= os.path.join (self.path, '01-null.mp3')
        copy ('tests/src/01-null.mp3', dst)

        def end ():
            print "finished"
            app.quit ()

        self.col= Collection (app, self.path)
        QTimer.singleShot (1, self.col.scan)
        self.col.scanFinished.connect (end)
        app.exec_ ()

        s= Song (None, dst)
        self.common_tests ([s], {'406206af9165009e8e423f1965d2b2c9': s}, 0)

if __name__=='__main__':
    unittest.main ()