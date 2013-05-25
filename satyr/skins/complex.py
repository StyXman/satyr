# vim: set fileencoding=utf-8 :
# (c) 2009, 2010 Marcos Dione <mdione@grulic.org.ar>

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
from PyKDE4.kdeui import KApplication
from PyKDE4.kdeui import KNotification
from PyQt4.QtCore import QSignalMapper, QSize, QFile
from PyQt4.QtGui import QItemSelectionModel, QAbstractItemView, QFontMetrics
from PyQt4.QtGui import QHeaderView, QApplication
from PyQt4 import uic

# we need it before loggin to get the handler
import satyr

# logging
import logging
logger = logging.getLogger(__name__)
logger.addHandler(satyr.loggingHandler)

# local
from satyr.skins import actions
from satyr.common import BUS_NAME
from satyr.skins.renamer import Renamer
from satyr.backend import getBackend
from satyr.models.dbus_table_model import QPlayListModel
from satyr import utils

class MainWindow (KXmlGuiWindow):
    def __init__ (self, parent=None, bus=None):
        KXmlGuiWindow.__init__ (self, parent)

        # load the .ui file
        # !!! __file__ can end with .py[co]!
        uipath= __file__[:__file__.rfind ('.')]+'.ui'
        UIMainWindow, _= uic.loadUiType (uipath)

        self.ui= UIMainWindow ()
        self.ui.setupUi (self)
        self.collectionsAwaited= 0

        self.oldSearchText= ''

        self.setupGUI ()

        self.bus= bus

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
        if ((majV>4) or (majV==4 and minV>3) or (majV==4 and minV==3 and patchL>1) and
            not (majV==4 and minV==6 and patchL==0)):
            # each second
            self.player.media.setTickInterval (1000);
            self.player.media.tick.connect (self.updateTimes)
            self.ui.seekSlider.setMediaObject (self.player.media)
        # TODO: self.ui.volumeSlider

        # TODO: better name?
        self.appModel= QPlayListModel (collaggr=self.playlist.collaggr, view=self)
        # TODO: connect after the collection has been scanned/populated
        self.appModel.dataChanged.connect (self.copyEditToSelection)
        self.copying= False
        self.setModel (self.appModel)

        self.renamer= Renamer (self.model.collaggr)

        # see some lines below
        self.playlist.songChanged.connect (self.showSong)
        self.playlist.queued.connect (self.appModel.dirtyRow)
        self.playlist.dequeued.connect (self.appModel.dirtyRow)
        self.ui.songsList.activated.connect (self.changeSong)
        # HINT: this seems like duplicating code,
        # but is not the same the playlist's current song has changed
        # that the player is playing a new song
        # because you can 'browse' the playlist with prev/next
        # while the player is not playing.
        self.player.songChanged.connect (self.nowPlaying)

        # FIXME: kinda hacky
        self.fontMetrics= QFontMetrics (KGlobalSettings.generalFont ())
        for i, w in enumerate (self.model.columnWidths):
            self.ui.songsList.setColumnWidth (i, self.fontMetrics.width (w))
        # this is much much slower!
        # self.ui.songsList.verticalHeader ().setResizeMode (QHeaderView.ResizeToContents)

        # FIXME: temporarily until I resolve the showSong() at boot time
        self.modelIndex= None
        self.songIndexSelectedByUser= None

        actions.create (self, self.actionCollection ())

    def backendReady (self, backend=None):
        logger.debug ("Complex.backendReady(): got a backend!")
        if backend is None:
            backend= getBackend (self.bus)

        # do I need to store it?
        self.backend= backend
        self.setModel (QPlayListModel (self, backend))

    def setModel (self, model):
        logger.debug ("complex.setModel():", model)
        self.model= model
        self.ui.songsList.setModel (self.model)
        self.ui.songsList.resizeRowsToContents ()

    def log (self, *args):
        print args

    def showSong (self, song):
        # save the old modelIndex so we can update that row and the new one
        oldModelIndex= self.modelIndex
        if self.songIndexSelectedByUser is not None:
            (song, modelIndex)= self.songIndexSelectedByUser
            self.songIndexSelectedByUser= None
        
        index= self.playlist.collaggr.indexForSong (song)
        logger.debug ("complex.showSong()", index)
        # I also have to save it for the same reason
        # but using the other model!
        # BUG: this is getting ugly
        modelIndex= self.modelIndex= self.appModel.index (index, 0)

        # mark data in old song and new song as dirty
        # and let the view update the hightlight
        # FIXME? yes, this could be moved to the model (too many self.appModel's)
        # FIXME: temporarily if'ed until I resolve the showSong() at boot time
        if oldModelIndex is not None:
            self.appModel.dirtyRow (oldModelIndex.row ())
        self.appModel.dirtyRow (self.modelIndex.row ())

        logger.debug ("default.showSong()", song)
        # FIXME? QAbstractItemView.EnsureVisible config?
        self.ui.songsList.scrollTo (modelIndex, QAbstractItemView.PositionAtCenter)
        # move the selection cursor too
        self.ui.songsList.setCurrentIndex (modelIndex)

        # set the window title
        # TODO: also update on tag edition
        self.setCaption (self.playlist.formatSong (song))

    def changeSong (self, modelIndex):
        # FIXME: later we ask for the index... doesn't make sense!
        logger.debug ("default.changeSong()", modelIndex.row ())
        song= self.model.collaggr.songForIndex (modelIndex.row ())
        self.songIndexSelectedByUser= (song, modelIndex)
        self.player.play (song)

    def nowPlaying (self, song):
        logger.debug ("complex.nowPlaying(): %s", self.playlist.formatSong (self.playlist.song))
        # event
        self.notif= KNotification ("nowPlaying", self)
        self.notif.setText ("Now Playing: %s" % self.playlist.formatSong (song))
        self.notif.sendEvent ()

    def scanBegins (self):
        # self.ui.songsList.setEnabled (False)
        # self.ui.songsList.setUpdatesEnabled (False)
        pass

    def scanFinished (self):
        # self.ui.songsList.setEnabled (True)
        # self.ui.songsList.setUpdatesEnabled (True)
        pass

    def search (self, text):
        # TODO: 23:44 < steckmqn> searching w/ the next chr cqn be done only in the qlready found set

        # oST>2 && t>=3 => search
        # (oST>=1 because it can reach that state when the user presses esc)
        # oST>=1 && t==0 => normal
        # otherwise => keep current
        if len (text)>=3 and len (self.oldSearchText)>=2:
            #                            QString->unicode
            songs= self.playlist.search (unicode (text))
            # we have to keep it
            # otherwise it pufs into inexistence after the function ends
            self.setModel (QPlayListModel (songs=songs, view=self))
        elif len (text)==0 and len (self.oldSearchText)>=1:
            self.setModel (self.appModel)
            # ensure the current song is shown
            if self.modelIndex is not None:
                self.showSong (self.modelIndex.row ())
        else:
            # print text, self.oldSearchText
            pass

        self.oldSearchText= text

    def updateTimes (self, tick):
        elapsed= tick/1000 # ms to s
        song= self.appModel.collaggr.songForIndex (self.modelIndex.row ())
        length= int (song.length)
        remaining= elapsed-length
        # print "tick! %d [%d] / %d / %d" % (elapsed, tick, length, remaining)
        
        self.ui.elapsedTime.setText (utils.secondsToTime (elapsed))
        self.ui.remainingTime.setText (utils.secondsToTime (remaining))

    def copyEditToSelection (self, tl, br):
        """copies the outcome of an edition in a cell
        to all the selected cells in the same column which.
        this lets us implement mass tag edition."""

        if len (self.ui.songsList.selectedIndexes ())>1 and self.appModel.edited:
            # more than one cell selected
            # we copy was has just been edited tho the rest of selected cells
            logger.debug ("complex.copyEditToSelection()", self.copying)
            if not self.copying:
                self.copying= True
                # data() already returns QVariant
                value= self.appModel.data (tl, Qt.DisplayRole)
                logger.debug ("complex.copyEditToSelection()", value)
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
            # TODO: fix
            # self.showSong (self.playlist.index)
            pass

    def selectedSongs (self):
        return [self.model.collaggr.songForIndex (modelIndex.row ())
            for modelIndex in self.ui.songsList.selectedIndexes ()]

    ### actions ###
    def queue (self):
        logger.debug ("complex.queue()")
        # so we don't keep (de)queuing if several cells of the same song are selected
        selectedSongs= []
        for modelIndex in self.ui.songsList.selectedIndexes ():
            logger.debug ("complex.queue()", modelIndex.row ())
            if modelIndex.row () not in selectedSongs:
                song= self.model.collaggr.songForIndex (modelIndex.row ())
                index= modelIndex.row ()
                self.playlist.queue (index, song)
                selectedSongs.append (modelIndex.row ())

    def rename (self):
        logger.debug ("complex.rename()")
        songs= self.selectedSongs ()

        self.renamer.rename (songs)

    def toggleVA (self):
        logger.debug ("complex.toggleVA()")
        songs= self.selectedSongs ()
        for song in songs:
            song.variousArtists= not song.variousArtists

    def delete (self):
        # we actually move it to a 'trash' collection
        logger.debug ("complex.delete()")
        songs= self.selectedSongs ()

        self.renamer.delete (songs)

    ### session management ###
    def saveProperties (self, config):
        logger ("saveProperties():")

    def restoreProperties (self, config):
        # not automatically called, add code in main()
        # see http://techbase.kde.org/Development/Tutorials/Session_Management#Add_session_management_support_to_your_main.28.29_function
        logger.debug ("restoreProperties():")

    def queryClose (self):
        logger.debug ("queryClose():")
        # , KApplication.sessionSaving ()
        # self.player.quit ()
        # self.renamer.saveConfig ()
        return True

    def queryExit (self):
        logger.debug ("queryExit():")
        # , KApplication.sessionSaving ()
        return True

# end
