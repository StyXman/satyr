#! /usr/bin/python
# vim: set fileencoding=utf-8 :
# (c) 2009 Marcos Dione <mdione@grulic.org.ar>
# distributed under the terms of the GPLv2.1

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

# ui
from default import Ui_MainWindow

class MainWindow (KMainWindow):
    def __init__ (self, parent=None):
        KMainWindow.__init__ (self, parent)

        self.ui= Ui_MainWindow ()
        self.ui.setupUi (self)

        self.songsList= QStringList ()
        self.model= QStringListModel (self.songsList)
        self.searchModel= QStringListModel ()
        self.ui.songsList.setModel (self.model)
        self.selection= self.ui.songsList.selectionModel ()

    def connectUi (self, player, playlist):
        self.player= player
        self.playlist= playlist
        # connect buttons!
        self.ui.prevButton.clicked.connect (player.prev)
        # the QPushButton.clicked() emits a bool,
        # and it's False on normal (non-checkable) buttons
        # BUG: it's not false, it's 0, which is indistinguishable from play(0)
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

    def log (self, *args):
        print args

    def addSong (self, index, filepath):
        # add the song via the model, so the views realize of the changes
        self.model.insertRow (index)
        modelIndex= self.model.index (index, 0)
        self.model.setData (modelIndex, QVariant (filepath))

    def showSong (self, index):
        modelIndex= self.model.index (index, 0)
        print "showSong()", modelIndex.row ()
        self.selection.select (modelIndex, QItemSelectionModel.SelectCurrent)
        # TODO? QAbstractItemView.EnsureVisible
        self.ui.songsList.scrollTo (modelIndex, QAbstractItemView.PositionAtCenter)
        # TODO: move the selection cursor too

    def changeSong (self, modelIndex):
        # FIXME: this should be fixed in a better way
        # once the Song includes the index
        # print modelIndex.model (), self.model
        filepath= modelIndex.data ().toString ()
        # FIXME: support multiple collections (and counting...)
        index= self.playlist.collections[0].filepaths.index (filepath)
        print "[%d] %s" % (index, filepath)
        self.player.play (index)

    def scanBegins (self):
        # self.ui.songsList.setEnabled (False)
        self.ui.songsList.setUpdatesEnabled (False)

    def scanFinished (self):
        # self.ui.songsList.setEnabled (True)
        self.ui.songsList.setUpdatesEnabled (True)

    def queryClose (self):
        self.player.quit ()
        return True

    def search (self, text):
        # below 3 chars is too slow (and with big playlists, useless)
        if len (text)>2:
            filepaths= [ filepath
                for index, filepath in self.playlist.search (unicode (text)) ]
            self.searchModel.setStringList (QStringList (filepaths))
            self.ui.songsList.setModel (self.searchModel)
            self.selection= self.ui.songsList.selectionModel ()
        else:
            self.ui.songsList.setModel (self.model)
            self.selection= self.ui.songsList.selectionModel ()


def createApp ():
    #########################################
    # all the bureaucratic init of a KDE App
    appName     = "satyr.py"
    catalog     = ""
    programName = ki18n ("satyr")                 #ki18n required here
    version     = "0.1a"
    description = ki18n ("I need a media player that thinks about music the way I think about it. This is such a program.")         #ki18n required here
    license     = KAboutData.License_GPL
    copyright   = ki18n ("(c) 2009 Marcos Dione")    #ki18n required here
    text        = ki18n ("none")                    #ki18n required here
    homePage    = ""
    bugEmail    = "mdione@grulic.org.ar"

    aboutData   = KAboutData (appName, catalog, programName, version, description,
                                license, copyright, text, homePage, bugEmail)

    # ki18n required for first two addAuthor () arguments
    aboutData.addAuthor (ki18n ("Marcos Dione"), ki18n ("design and implementation"))

    KCmdLineArgs.init (sys.argv, aboutData)
    options= KCmdLineOptions ()
    options.add ("+path", ki18n ("path to your music collection"))
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
        # BUG: this is ugly
        # qba= QByteArray ()
        # qba.append (path)
        # path= str (qba)

        # convert QString to unicode
        path= unicode (path)
        collection= Collection (app, path, busName, "/collection_%04d" % index)
        collections.append (collection)
        collection.newSong.connect (mw.addSong)
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

    app.exec_ ()

if __name__=='__main__':
    main ()

# end
