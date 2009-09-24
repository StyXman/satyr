#! /usr/bin/python
# vim: set fileencoding=utf-8 :
# (c) 2009 Marcos Dione <mdione@grulic.org.ar>
# distributed under the terms of the GPLv2.1

# qt/kde related
from PyKDE4.kdecore import KCmdLineArgs, KAboutData, i18n, ki18n
from PyKDE4.kdecore import KCmdLineOptions, KMimeType, KUrl
from PyKDE4.kdecore import KStandardDirs
from PyKDE4.kdeui import KApplication, KMainWindow
from PyQt4.QtCore import pyqtSignal, QObject, QByteArray, QTimer

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

    def connectUi (self, player, playlist):
        self.player= player
        self.playlist= playlist
        # connect buttons!
        self.ui.prevButton.clicked.connect (player.prev)
        self.ui.playButton.clicked.connect (player.play)
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
        self.ui.songsList.itemActivated.connect (self.changeSong)

        # self.ui.searchEntry.

    def addSong (self, index, filepath):
        self.ui.songsList.insertItem (index, filepath)

    def showSong (self, index):
        item= self.ui.songsList.item (index)
        self.ui.songsList.scrollToItem (item)
        self.ui.songsList.setCurrentItem (item)

    def changeSong (self, item):
        index= self.ui.songsList.row (item)
        self.player.play (index)


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
    options.add ("+file", ki18n ("file to play"))
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
