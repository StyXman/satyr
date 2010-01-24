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
from PyKDE4.kdeui import KXmlGuiWindow, KGlobalSettings, KActionCollection
from PyQt4.QtCore import QAbstractTableModel, QModelIndex, QVariant, Qt
from PyQt4.QtCore import QSignalMapper, QSize, QFile
from PyQt4.QtGui import QItemSelectionModel, QAbstractItemView, QFontMetrics
from PyQt4.QtGui import QHeaderView, QApplication
from PyQt4 import uic

# local
from satyr.collaggr import CollectionAggregator
from satyr.song import TagWriteError
from satyr.skins import actions
from satyr import utils

class MainWindow (KXmlGuiWindow):
    def __init__ (self, parent=None):
        KXmlGuiWindow.__init__ (self, parent)

        # load the .ui file
        # !!! __file__ can end with .py[co]!
        uipath= __file__[:__file__.rfind ('.')]+'.ui'
        UIMainWindow, _= uic.loadUiType (uipath)

        self.ui= UIMainWindow ()
        self.ui.setupUi (self)
        self.collectionsAwaited= 0

        self.ac= KActionCollection (self)
        actions.create (self, self.actionCollection ())
        self.setupGUI ()

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

        self.ui.searchEntry.textChanged.connect (self.search)
        majV, minV, patchL= utils.phononVersion ()
        if (majV>4) or (majV==4 and minV>3) or (majV==4 and minV==3 and patchL>1):
            self.ui.timeSlider.setMediaObject (self.player.media)

        # TODO: better name?
        self.appModel= QPlayListModel (aggr=self.playlist.aggr, view=self)
        self.appModel.dataChanged.connect (self.copyEditToSelection)
        self.copying= False
        self.setModel (self.appModel)

        self.playlist.songChanged.connect (self.showSong)
        self.playlist.queued.connect (self.appModel.dirtyRow)
        self.playlist.dequeued.connect (self.appModel.dirtyRow)
        self.ui.songsList.activated.connect (self.changeSong)

        # FIXME: kinda hacky
        self.fontMetrics= QFontMetrics (KGlobalSettings.generalFont ())
        for i, w in enumerate (self.model.columnWidths):
            self.ui.songsList.setColumnWidth (i, self.fontMetrics.width (w))
        # this is much much slower!
        # self.ui.songsList.verticalHeader ().setResizeMode (QHeaderView.ResizeToContents)

        # FIXME: temporarily until I resolve the showSong() at boot time
        self.modelIndex= None
        self.songIndexSelectedByUser= None

    def setModel (self, model):
        print "complex.setModel():", model
        self.model= model
        self.ui.songsList.setModel (self.model)
        self.ui.songsList.resizeRowsToContents ()

    def log (self, *args):
        print args

    def showSong (self, index):
        # save the old modelIndex so we can update that row and the new one
        oldModelIndex= self.modelIndex
        if self.songIndexSelectedByUser is None:
            print "complex.showSong()", index
            # we use the playlist model because the index is *always* refering
            # to that model
            song= self.playlist.aggr.songForIndex (index)
            # we save the new modelIndex in self so we can show it
            # when we come back from searching
            modelIndex= self.modelIndex= self.model.index (index, 0)
        else:
            (song, modelIndex)= self.songIndexSelectedByUser
            # I also have to save it for the same reason
            # but using the other model!
            # BUG: this is getting ugly
            self.modelIndex= self.appModel.index (index, 0)
            # we used it so we discard it
            # it will be set again by changeSong()
            self.songIndexSelectedByUser= None

        # mark data in old song and new song as dirty
        # and let the view update the hightlight
        # FIXME? yes, this could be moved to the model (too many self.appModel's)
        # FIXME: temporarily if'ed until I resolve the showSong() at boot time
        if oldModelIndex is not None:
            self.appModel.dirtyRow (oldModelIndex.row ())
        self.appModel.dirtyRow (self.modelIndex.row ())

        print "default.showSong()", song
        # FIXME? QAbstractItemView.EnsureVisible config?
        self.ui.songsList.scrollTo (modelIndex, QAbstractItemView.PositionAtCenter)
        # move the selection cursor too
        self.ui.songsList.setCurrentIndex (modelIndex)

        # set the window title
        self.setCaption (self.playlist.formatSong (song))

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
            self.setModel (QPlayListModel (songs=songs, view=self))
        else:
            self.setModel (self.appModel)
            # ensure the current song is shown
            self.showSong (self.modelIndex.row ())

    def queue (self):
        print "complex.queue()"
        # so we don't keep (de)queuing if several cells of the same song are selected
        selectedSongs= []
        for modelIndex in self.ui.songsList.selectedIndexes ():
            print "complex.queue()", modelIndex.row ()
            if modelIndex.row () not in selectedSongs:
                # self.playlist.queue (modelIndex.row ())
                # not so fast, cowboy. PlayList.queue() spects 'global' indexes
                # TODO: this is not very efficient
                song= self.model.aggr.songForIndex (modelIndex.row ())
                index= self.appModel.aggr.indexForSong (song)
                self.playlist.queue (index)
                selectedSongs.append (modelIndex.row ())

    def copyEditToSelection (self, tl, br):
        """copies the outcome of an edition in a cell
        to all the selected cells in the same column which.
        this lets us implement mass tag edition."""
        print "complex.copyEditToSelection()", len (self.ui.songsList.selectedIndexes ()), self.appModel.edited
        if len (self.ui.songsList.selectedIndexes ())>1 and self.appModel.edited:
            # more than one cell selected
            # we copy was has just been edited tho the rest of selected cells
            print "complex.copyEditToSelection()", self.copying
            if not self.copying:
                self.copying= True
                # data() already returns QVariant
                value= self.appModel.data (tl, Qt.DisplayRole)
                print "complex.copyEditToSelection()", value
                # just copy the column that has been edited...
                column= tl.column ()
                for modelIndex in self.ui.songsList.selectedIndexes ():
                    # ... in the selected cells in the same column
                    if modelIndex.column ()==column:
                        # copy the value
                        self.appModel.setData (modelIndex, value, Qt.EditRole)

                # we finished copying
                self.copying= False

    def collectionAdded (self):
        self.collectionsAwaited+= 1

    def collectionLoaded (self):
        # TODO: locking here, for data race's sake!
        # really? signals get emited from threads,
        # but processed from the main loop, isn't it?
        self.collectionsAwaited-= 1
        if self.collectionsAwaited==0:
            self.showSong (self.playlist.index)


class QPlayListModel (QAbstractTableModel):
    def __init__ (self, aggr=None, songs=None, view=None):
        QAbstractTableModel.__init__ (self, view)
        # TODO: different delegate for editing tags: one with completion
        self.view_= view
        self.playlist= view.playlist
        self.edited= False

        if songs is None:
            self.aggr= aggr
            self.collections= self.aggr.collections

            self.signalMapper= QSignalMapper ()
            for collNo, collection in enumerate (self.collections):
                collection.newSongs.connect (self.signalMapper.map)
                self.signalMapper.setMapping (collection, collNo)

            self.signalMapper.mapped.connect (self.addRows)
        else:
            self.aggr= CollectionAggregator (songs=songs)

        self.attrNames= ('artist', 'year', 'album', 'trackno', 'title', 'length', 'filepath')

        self.headers= (u'Artist', u'Year', u'Album', u'Track', u'Title', u'Length', u'Path')
        # FIXME: kinda hacky
        self.fontMetrics= QFontMetrics (KGlobalSettings.generalFont ())
        # FIXME: (even more) hackish
        self.columnWidths= ("M"*15, "M"*4, "M"*20, "M"*3, "M"*25, "M"*5, "M"*100)
        print "QPLM: ", self

    def data (self, modelIndex, role):
        if modelIndex.isValid () and modelIndex.row ()<self.aggr.count:
            song= self.aggr.songForIndex (modelIndex.row ())

            if role==Qt.DisplayRole or role==Qt.EditRole:
                attr= self.attrNames [modelIndex.column ()]
                rawData= song[attr]
                if attr=='filepath':
                    rawData= QFile.decodeName (rawData)
                elif attr=='title':
                    try:
                        queueIndex= self.playlist.indexQueue.index (modelIndex.row ())
                        # make it show as starting in 1, otherwise it's confusing
                        rawData= "[%d] %s" % (queueIndex+1, rawData)
                    except ValueError:
                        pass
                data= QVariant (rawData)

            elif role==Qt.SizeHintRole:
                size= self.fontMetrics.size (Qt.TextSingleLine, self.columnWidths[modelIndex.column ()])
                data= QVariant (size)

            elif role==Qt.BackgroundRole and self.view_.modelIndex is not None:
                if modelIndex.row ()==self.view_.modelIndex.row ():
                    # highlight the current song
                    # must return a QBrush
                    data= QVariant (QApplication.palette ().dark ())
                else:
                    try:
                        queueIndex= self.playlist.indexQueue.index (modelIndex.row ())
                        data= QVariant (QApplication.palette ().mid ())
                    except ValueError:
                        data= QVariant ()

            elif role==Qt.ForegroundRole and self.view_.modelIndex is not None:
                if modelIndex.row ()==self.view_.modelIndex.row ():
                    # highlight the current song
                    # must return a QBrush
                    data= QVariant (QApplication.palette ().brightText ())
                else:
                    data= QVariant ()

            else:
                data= QVariant ()
        else:
            data= QVariant ()

        return data

    def flags (self, modelIndex):
        ans= QAbstractTableModel.flags (self, modelIndex)
        if modelIndex.column ()<5: # length or filepath are not editable
            ans= ans|Qt.ItemIsEditable|Qt.ItemIsEditable

        return ans

    def match (self, start, role, value, hits=1, flags=None):
        # when you press a key on an uneditable cell, QTableView tries to search
        # calling this function for matching. we already have a way for searching
        # and it loads the metadata of all the songs anyways
        # so we disable it by constantly returning an empty list
        return []

    def setData (self, modelIndex, variant, role=Qt.EditRole):
        # not length or filepath and editing
        print "QPLM.setData()", modelIndex.row (), modelIndex.column(), role
        if modelIndex.column ()<5 and role==Qt.EditRole:
            song= self.aggr.songForIndex (modelIndex.row ())
            attr= self.attrNames[modelIndex.column ()]
            try:
                song[attr]= unicode (variant.toString ())
                # TODO: make a list of dirty songs and commit them later
                song.saveMetadata ()
            except TagWriteError:
                # it failed
                ans= False
            else:
                self.edited= True
                self.dataChanged.emit (modelIndex, modelIndex)
                ans= True
        else:
            ans= QAbstractTableModel.setData (self, modelIndex, variant, role)

        print "QPLM.setData():", modelIndex.row(), modelIndex.column (), role, ans
        return ans

    def headerData (self, section, direction, role=Qt.DisplayRole):
        if direction==Qt.Horizontal and role==Qt.DisplayRole:
            data= QVariant (self.headers[section])
        elif direction==Qt.Vertical:
            if role==Qt.SizeHintRole:
                # again, hacky. 5 for enough witdh for 5 digits
                size= self.fontMetrics.size (Qt.TextSingleLine, "X"*5)
                data= QVariant (size)
            elif role==Qt.TextAlignmentRole:
                data= QVariant (Qt.AlignRight|Qt.AlignVCenter)
            else:
                data= QAbstractTableModel.headerData (self, section, direction, role)
        else:
            data= QAbstractTableModel.headerData (self, section, direction, role)

        return data

    def addRows (self, collNo):
        collection= self.collections[collNo]

        for index, filepath in collection.newSongs_:
            self.beginInsertRows (QModelIndex (), index, index)
            self.endInsertRows ()

            modelIndex= self.index (index, 0)
            self.dataChanged.emit (modelIndex, modelIndex)

    def dirtyRow (self, index):
        print "QLMP.dirtyRow():", index
        columns= self.columnCount ()
        start= self.index (index, 0)
        end=   self.index (index, columns)
        self.edited= False
        self.dataChanged.emit (start, end)

    def rowCount (self, parent=None):
        return self.aggr.count

    def columnCount (self, parent=None):
        return len (self.attrNames)

# end
