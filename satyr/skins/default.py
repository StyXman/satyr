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
from PyKDE4.kdeui import KMainWindow, KGlobalSettings
from PyQt4.QtCore import QAbstractListModel, QModelIndex, QVariant, Qt
from PyQt4.QtCore import QSignalMapper
from PyQt4.QtGui import QItemSelectionModel, QAbstractItemView, QFontMetrics
from PyQt4 import uic

# local
from satyr.collaggr import CollectionAggregator

class MainWindow (KMainWindow):
    def __init__ (self, parent=None):
        KMainWindow.__init__ (self, parent)

        # load the .ui file
        # !!! __file__ can end with .py[co]!
        uipath= __file__[:__file__.rfind ('.')]+'.ui'
        UIMainWindow, _= uic.loadUiType (uipath)

        self.ui= UIMainWindow ()
        self.ui.setupUi (self)
        self.collectionsAwaited= 0

    def connectUi (self, player):
        self.player= player
        self.playlist= player.playlist

        # connect buttons!
        self.ui.prevButton.clicked.connect (self.player.prev)
        # the QPushButton.clicked() emits a bool,
        # and it's False on normal (non-checkable) buttons
        # no, it's not false, it's 0, which is indistinguishable from play(0)
        # so lambda the 'bool' away
        self.ui.playButton.clicked.connect (lambda b: self.player.play ())
        self.ui.pauseButton.clicked.connect (self.player.pause)
        self.ui.stopButton.clicked.connect (self.player.stop)
        self.ui.nextButton.clicked.connect (self.player.next)

        self.ui.randomCheck.setChecked (self.playlist.random)
        self.ui.randomCheck.clicked.connect (self.playlist.toggleRandom)
        self.playlist.randomChanged.connect (self.ui.randomCheck.setChecked)

        self.ui.stopAfterCheck.setChecked (self.player.stopAfter)
        self.ui.stopAfterCheck.clicked.connect (self.player.toggleStopAfter)
        self.player.stopAfterChanged.connect (self.ui.stopAfterCheck.setChecked)

        self.playlist.songChanged.connect (self.showSong)
        self.ui.songsList.setSelectionMode (QAbstractItemView.NoSelection)
        self.ui.songsList.activated.connect (self.changeSong)

        self.ui.searchEntry.textChanged.connect (self.search)

        # TODO: better name?
        self.appModel= QPlayListModel (aggr=self.playlist.aggr, parent=self)
        self.setModel (self.appModel)

        self.songIndexSelectedByUser= None

    def setModel (self, model):
        self.model= model
        self.ui.songsList.setModel (self.model)
        self.selection= self.ui.songsList.selectionModel ()

    def log (self, *args):
        print args

    def showSong (self, index):
        if self.songIndexSelectedByUser is None:
            print "default.showSong()", index
            # we use the playlist model because the index is *always* refering
            # to that model
            song= self.playlist.aggr.songForIndex (index)
            # we save the modelindex in the instance so we can show it
            # when we come back from searching
            modelIndex= self.modelIndex= self.model.index (index, 0)
        else:
            (song, modelIndex)= self.songIndexSelectedByUser
            # I also have to save it for the same reason
            # but using the other model!
            # BUG: this is getting ugly
            self.modelIndex= self.appModel.index (index, 0)
            # we uesd it so we discard it
            # it will be set again by changeSong()
            self.songIndexSelectedByUser= None

        print "default.showSong()", song
        self.selection.select (modelIndex, QItemSelectionModel.SelectCurrent)
        # FIXME? QAbstractItemView.EnsureVisible config?
        self.ui.songsList.scrollTo (modelIndex, QAbstractItemView.PositionAtCenter)
        # move the selection cursor too
        self.ui.songsList.setCurrentIndex (modelIndex)

        # set the window title
        self.setCaption (self.model.formatSong (song))

    def changeSong (self, modelIndex):
        # FIXME: later we ask for the index... doesn't make sense!
        print "default.changeSong()", modelIndex.row ()
        song= self.model.aggr.songForIndex (modelIndex.row ())
        self.songIndexSelectedByUser= (song, modelIndex)
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
            self.setModel (QPlayListModel (songs=songs))
        else:
            self.setModel (self.appModel)
            # ensure the current song is shown
            self.showSong (self.modelIndex.row ())

    def collectionAdded (self):
        self.collectionsAwaited+= 1

    def collectionLoaded (self):
        # TODO: locking here, for data race's sake!
        # really? signals get emited from threads,
        # but processed from the main loop, isn't it?
        self.collectionsAwaited-= 1
        if self.collectionsAwaited==0:
            self.showSong (self.playlist.index)

class QPlayListModel (QAbstractListModel):
    def __init__ (self, aggr=None, songs=None, parent=None):
        QAbstractListModel.__init__ (self, parent)

        if songs is None:
            self.aggr= aggr
            self.collections= self.aggr.collections

            self.signalMapper= QSignalMapper ()
            for collNo, collection in enumerate (self.collections):
                collection.newSongs.connect (self.signalMapper.map)
                self.signalMapper.setMapping (collection, collNo)

            self.signalMapper.mapped.connect (self.addRows)
        else:
            self.aggr= CollectionAgregator (songs=songs)

        # TODO: config
        # TODO: optional parts
        # TODO: unify unicode/str
        self.format= u"%(artist)s/%(year)s-%(album)s: %(trackno)s - %(title)s [%(length)s]"
        # this must NOT be unicode, 'cause the filepaths might have any vegetable
        self.altFormat= "%(filepath)s [%(length)s]"

        # FIXME: kinda hacky
        self.fontMetrics= QFontMetrics (KGlobalSettings.generalFont ())

    def formatSong (self, song):
        if song.metadataNotNull ():
            formatted= self.format % song
        else:
            # I choose latin1 because it's the only one I know
            # which is full 256 chars
            # FIXME: I think (this is not needed|we're not in kansas) anymore
            try:
                s= (self.altFormat % song).decode ('latin1')
            except UnicodeDecodeError:
                print song.filepath
                fp= song.filepath.decode ('iso-8859-1')
                s= u"%s [%s]" % (fp, song.length)

            formatted= s

        return formatted

    def data (self, modelIndex, role):
        if modelIndex.isValid () and modelIndex.row ()<self.aggr.count:
            song= self.aggr.songForIndex (modelIndex.row ())

            if role==Qt.DisplayRole:
                data= QVariant (self.formatSong (song))
            elif role==Qt.SizeHintRole:
                # calculate something based on the filepath
                data= QVariant (self.fontMetrics.size (Qt.TextSingleLine, song.filepath))
            else:
                data= QVariant ()
        else:
            data= QVariant ()

        return data

    def addRows (self, collNo):
        collection= self.collections[collNo]

        for index, filepath in collection.newSongs_:
            self.beginInsertRows (QModelIndex (), index, index)
            self.endInsertRows ()

            modelIndex= self.index (index, 0)
            self.dataChanged.emit (modelIndex, modelIndex)

    def rowCount (self, parent=None):
        return self.aggr.count

# end
