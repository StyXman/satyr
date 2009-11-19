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
from PyQt4.QtGui import QItemSelectionModel, QAbstractItemView
from PyQt4 import uic

# local
from satyr.models import PlayListModel

class MainWindow (KMainWindow):
    def __init__ (self, parent=None):
        KMainWindow.__init__ (self, parent)

        # load the .ui file
        # !!! __file__ can end with .py[co]!
        uipath= __file__[:__file__.rfind ('.')]+'.ui'
        # print uipath
        (UIMainWindow, buh)= uic.loadUiType (uipath)
        # print UIMainWindow, buh

        self.ui= UIMainWindow ()
        self.ui.setupUi (self)
        self.collectionsAwaited= 0

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

        self.ui.randomCheck.setChecked (playlist.random)
        self.ui.randomCheck.clicked.connect (playlist.toggleRandom)
        self.playlist.randomChanged.connect (self.ui.randomCheck.setChecked)

        self.ui.stopAfterCheck.setChecked (player.stopAfter)
        self.ui.stopAfterCheck.clicked.connect (player.toggleStopAfter)
        self.player.stopAfterChanged.connect (self.ui.stopAfterCheck.setChecked)

        self.playlist.songChanged.connect (self.showSong)
        self.ui.songsList.setSelectionMode (QAbstractItemView.NoSelection)
        self.ui.songsList.activated.connect (self.changeSong)

        self.ui.searchEntry.textChanged.connect (self.search)

        self.setModel (self.playlist.model)

    def setModel (self, model):
        self.model= model
        self.ui.songsList.setModel (self.model)
        self.selection= self.ui.songsList.selectionModel ()

    def log (self, *args):
        print args

    def showSong (self, index):
        print "satyr.showSong()", index
        # index= self.model.indexForSong (song)
        # we use the playlist model because the index is *always* refering
        # to that model
        song= self.playlist.model.songForIndex (index)
        print "satyr.showSong()", song
        self.modelIndex= self.model.index (index, 0)
        self.selection.select (self.modelIndex, QItemSelectionModel.SelectCurrent)
        # FIXME? QAbstractItemView.EnsureVisible config?
        self.ui.songsList.scrollTo (self.modelIndex, QAbstractItemView.PositionAtCenter)
        # move the selection cursor too
        self.ui.songsList.setCurrentIndex (self.modelIndex)

        # set the window title
        self.setCaption (self.playlist.model.formatSong (song))

    def changeSong (self, modelIndex):
        # FIXME: later we ask for the index... doesn't make sense!
        print "satyr.changeSong()", modelIndex.row ()
        song= self.model.songForIndex (modelIndex.row ())
        self.player.play (song)

    def scanBegins (self):
        # self.ui.songsList.setEnabled (False)
        # self.ui.songsList.setUpdatesEnabled (False)
        pass

    def scanFinished (self):
        # self.ui.songsList.setEnabled (True)
        # self.ui.songsList.setUpdatesEnabled (True)
        pass

    def queryClose (self):
        self.player.quit ()
        return True

    def search (self, text):
        # below 3 chars is too slow (and with big playlists, useless)
        if len (text)>2:
            #                            QString->unicode
            songs= self.playlist.search (unicode (text))
            # we have to keep it
            # otherwise it pufs into inexistence after the function ends
            self.setModel (PlayListModel (songs=songs))
        else:
            self.setModel (self.playlist.model)
            # ensure the current song is shown
            # BUG:
            # Traceback (most recent call last):
            # File "satyr.py", line 145, in search
            #     self.ui.songsList.scrollTo (self.modelIndex, QAbstractItemView.PositionAtCenter)
            # AttributeError: 'MainWindow' object has no attribute 'modelIndex'
            self.ui.songsList.scrollTo (self.modelIndex, QAbstractItemView.PositionAtCenter)

    def collectionAdded (self):
        self.collectionsAwaited+= 1

    def collectionLoaded (self):
        # TODO: locking here, for data race's sake!
        # really? signals get emited from threads,
        # but processed from the main loop, isn't it?
        self.collectionsAwaited-= 1
        if self.collectionsAwaited==0:
            self.showSong (self.playlist.index)
