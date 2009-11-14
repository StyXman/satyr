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
from PyKDE4.kdeui import KMainWindow
from PyQt4 import uic

class MainWindow (KMainWindow):
    def __init__ (self, parent=None):
        KMainWindow.__init__ (self, parent)

        # load the .ui file
        # !!! __file__ can end with .py[co]!
        uipath= __file__[:__file__.rfind ('.')]+'.ui'
        (UIMainWindow, buh)= uic.loadUiType (uipath)

        self.ui= UIMainWindow ()
        self.ui.setupUi (self)

    def connectUi (self, player, playlist):
        self.player= player
        self.playlist= playlist

        # connect buttons!
        self.ui.prevButton.clicked.connect (player.prev)
        # the QPushButton.clicked() emits a bool,
        # and it's False on normal (non-checkable) buttons
        # no, it's not false, it's 0, which is indistinguishable from play(0)
        # so lambda the 'bool' away
        self.ui.playButton.clicked.connect (lambda b: player.play ())
        self.ui.pauseButton.clicked.connect (player.pause)
        self.ui.stopButton.clicked.connect (player.stop)
        self.ui.nextButton.clicked.connect (player.next)

        self.setModel (self.playlist.model)

    def setModel (self, model):
        self.model= model

    # BUG?
    # Traceback (most recent call last):
    # File "satyr.py", line 124, in <module>
    #     sys.exit (main ())
    # File "satyr.py", line 103, in main
    #     collection.scanBegins.connect (mw.scanBegins)
    # AttributeError: 'MainWindow' object has no attribute 'scanBegins'
    def scanBegins (self):
        # self.ui.songsList.setEnabled (False)
        # self.ui.songsList.setUpdatesEnabled (False)
        pass

    def scanFinished (self):
        # self.ui.songsList.setEnabled (True)
        # self.ui.songsList.setUpdatesEnabled (True)
        pass

    # BUG
    # Traceback (most recent call last):
    # File "satyr.py", line 124, in <module>
    #     sys.exit (main ())
    # File "satyr.py", line 112, in main
    #     mw.collectionAdded ()
    # AttributeError: 'MainWindow' object has no attribute 'collectionAdded'
    def collectionAdded (self):
        pass

    def queryClose (self):
        self.player.quit ()
        return True

# end
