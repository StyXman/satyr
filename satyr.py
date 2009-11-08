#! /usr/bin/python
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
from PyKDE4.kdecore import KCmdLineArgs, KAboutData, i18n, ki18n
from PyKDE4.kdecore import KCmdLineOptions, KMimeType, KUrl, KStandardDirs
from PyKDE4.kdeui import KApplication, KMainWindow
from PyQt4.QtCore import pyqtSignal, QTimer, QStringList, QVariant
from PyQt4.QtGui import QStringListModel, QItemSelectionModel, QAbstractItemView

# dbus
import dbus
import dbus.mainloop.qt
import dbus.service

# std python
import sys, os, os.path, time, bisect, stat, random

# local
from primes import primes
from common import SatyrObject, BUS_NAME
from player import Player
from playlist import PlayList
from collection import Collection
from models import PlayListModel
import utils

# ui
from default import Ui_MainWindow

#   PID USER     PRI  NI  VIRT   RES   SHR S CPU% MEM%   TIME+  Command
# 24979 mdione    20   0  216M 46132 17380 S  1.0  2.2  4:01.62 python satyr.py /home/mdione/media/music/
#  7300 mdione    20   0  171M 52604 20004 S  0.0  2.5  0:18.42 python satyr.py /home/mdione/media/music/

class MainWindow (KMainWindow):
    def __init__ (self, parent=None):
        KMainWindow.__init__ (self, parent)

        self.ui= Ui_MainWindow ()
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
            self.ui.songsList.scrollTo (self.modelIndex, QAbstractItemView.PositionAtCenter)


def createApp ():
    #########################################
    # all the bureaucratic init of a KDE App
    # the appName must not contain any chars besides a-zA-Z0-9_
    # because KMainWindowPrivate::polish() calls QDBusConnection::sessionBus().registerObject()
    # see QDBusUtil::isValidCharacterNoDash()
    appName     = "satyr"
    catalog     = ""
    programName = ki18n ("satyr")                 #ki18n required here
    version     = "0.1a"
    description = ki18n ("I need a media player that thinks about music the way I think about it. This is such a program.")         #ki18n required here
    license     = KAboutData.License_GPL
    copyright   = ki18n ("(c) 2009 Marcos Dione")    #ki18n required here
    text        = ki18n ("none")                    #ki18n required here
    homePage    = "http://savannah.nongnu.org/projects/satyr/"
    bugEmail    = "mdione@grulic.org.ar"

    aboutData   = KAboutData (appName, catalog, programName, version, description,
                                license, copyright, text, homePage, bugEmail)

    # ki18n required for first two addAuthor () arguments
    aboutData.addAuthor (ki18n ("Marcos Dione"), ki18n ("design and implementation"))
    aboutData.addAuthor (ki18n ("Sebastián Álvarez"), ki18n ("features and bugfixes"))

    KCmdLineArgs.init (sys.argv, aboutData)
    options= KCmdLineOptions ()
    options.add ("+path", ki18n ("paths to your music collections"))
    KCmdLineArgs.addCmdLineOptions (options)

    app= KApplication ()
    args= KCmdLineArgs.parsedArgs ()

    return app, args

def main ():
    app, args= createApp ()

    dbus.mainloop.qt.DBusQtMainLoop (set_as_default=True)
    bus= dbus.SessionBus ()
    busName= dbus.service.BusName (BUS_NAME, bus=bus)

    #########################################
    # the app itself!
    mw= MainWindow ()

    collections= []
    for index in xrange (args.count ()):
        path= args.arg (index)

        # paths must be bytes, not ascii or utf-8
        path= utils.qstring2str (path)

        collection= Collection (app, path, busName, "/collection_%04d" % index)
        collections.append (collection)
        collection.scanBegins.connect (mw.scanBegins)
        collection.scanFinished.connect (mw.scanFinished)
        # we need to fire the load/scan after the main loop has started
        # otherwise the signals emited from it are not sent to the connected slots
        # FIXME? I'm not sure I want it this way
        QTimer.singleShot (100, collection.loadOrScan)

    playlist= PlayList (app, collections, busName, '/playlist')
    player= Player (app, playlist, busName, '/player')
    player.finished.connect (app.quit)

    mw.connectUi (player, playlist)
    mw.show ()

    return app.exec_ ()

if __name__=='__main__':
    sys.exit (main ())

# end
