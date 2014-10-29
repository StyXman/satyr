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
from os import getcwd, rename, unlink
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
        self.col= Collection (None, test_path)

    def tearDown (self):
        self.col.updater.stop ()
        rmtree (test_path)

    def common_tests (self, songs, songsById, offset):
        self.assertEqual (self.col.songs, songs)
        self.assertEqual (self.col.songsById, songsById)
        self.assertEqual (self.col.count, len (songs))
        self.assertEqual (self.col.offset, offset)

    def test_creation_with_path (self):
        self.common_tests ([], {}, 0)

    def test_scan_one_song (self):
        dst= os.path.join (test_path, '01-null.mp3')
        copy ('tests/src/01-null.mp3', dst)

        QTimer.singleShot (1, self.col.scan)
        self.col.scanFinished.connect (app.quit)
        app.exec_ ()

        s= Song (None, os.path.abspath (dst))
        self.common_tests ([s], {s.id: s}, 0)

    def test_scan_one_file (self):
        dst= os.path.join (test_path, '03-do_not_index.txt')
        copy ('tests/src/03-do_not_index.txt', dst)

        QTimer.singleShot (1, self.col.scan)
        self.col.scanFinished.connect (app.quit)
        app.exec_ ()

        self.common_tests ([], {}, 0)

    def test_new_song (self):
        dst= os.path.join (test_path, '01-null.mp3')

        def copy_file ():
            copy ('tests/src/01-null.mp3', dst)

        QTimer.singleShot (0, copy_file)
        QTimer.singleShot (1000, app.quit)
        app.exec_ ()

        s= Song (None, os.path.abspath (dst))
        self.common_tests ([s], {s.id: s}, 0)

    def test_new_file (self):
        dst= os.path.join (test_path, '03-do_not_index.txt')

        def copy_file ():
            copy ('tests/src/03-do_not_index.txt', dst)

        QTimer.singleShot (0, copy_file)
        QTimer.singleShot (1000, app.quit)
        app.exec_ ()

        self.common_tests ([], {}, 0)

    def test_new_del_song (self):
        dst= os.path.join (test_path, '01-null.mp3')

        def copy_file ():
            copy ('tests/src/01-null.mp3', dst)
            QTimer.singleShot (500, del_file)

        def del_file ():
            s= Song (None, os.path.abspath (dst))
            self.common_tests ([s], {s.id: s}, 0)
            unlink (dst)

        QTimer.singleShot (0, copy_file)
        QTimer.singleShot (1000, app.quit)
        app.exec_ ()

        self.common_tests ([], {}, 0)

    def test_move_in_song (self):
        dst= os.path.join (test_path, '04-null-copy.mp3')

        def move_file ():
            copy ('tests/src/01-null.mp3', 'tests/src/04-null-copy.mp3')
            rename ('tests/src/04-null-copy.mp3', dst)

        QTimer.singleShot (0, move_file)
        QTimer.singleShot (1000, app.quit)
        app.exec_ ()

        s= Song (None, os.path.abspath (dst))
        self.common_tests ([s], {s.id: s}, 0)

    def test_move_around_song (self):
        dst1= os.path.join (test_path, '04-null-copy.mp3')
        dst2= os.path.join (test_path, '06-null-copy.mp3')

        def move_in_file ():
            copy ('tests/src/01-null.mp3', 'tests/src/04-null-copy.mp3')
            rename ('tests/src/04-null-copy.mp3', dst1)
            QTimer.singleShot (500, move_around_file)

        def move_around_file ():
            s= Song (None, os.path.abspath (dst1))
            self.common_tests ([s], {s.id: s}, 0)
            rename (dst1, dst2)

        QTimer.singleShot (0, move_in_file)
        QTimer.singleShot (1000, app.quit)
        app.exec_ ()

        s= Song (None, os.path.abspath (dst2))
        self.common_tests ([s], {s.id: s}, 0)

if __name__=='__main__':
    unittest.main ()
