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
from PyQt4.QtCore import QTimer, QEventLoop

from satyr.collection_indexer import CollectionIndexer

from common import app

class TestCollectionIndexer (unittest.TestCase):
    path= 'tests/data'

    def setUp (self):
        app.setApplicationName ("TestCollectionIndexer")
        makedirs (self.path)
        self.n= 0

    def tearDown (self):
        rmtree (self.path)

    def count (self):
        self.n+= 1

    def test_scan (self):
        dst= os.path.join (self.path, '01-null.mp3')
        copy ('tests/src/01-null.mp3', dst)

        self.col= CollectionIndexer (self.path)
        QTimer.singleShot (1, self.col.start)
        self.col.foundSongs.connect (self.count)
        self.col.finished.connect (app.quit)
        app.exec_ ()

        self.assertEqual (self.n, 1)

    def test_new_file (self):
        dst= os.path.join (self.path, '01-null.mp3')

        def copy_file ():
            copy ('tests/src/01-null.mp3', dst)

        self.col= CollectionIndexer (self.path)
        QTimer.singleShot (0, copy_file)
        self.col.foundSongs.connect (self.count)
        QTimer.singleShot (5000, app.quit)
        app.exec_ ()

        self.assertEqual (self.n, 1)

if __name__=='__main__':
    unittest.main ()
