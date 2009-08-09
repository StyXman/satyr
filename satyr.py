#! /usr/bin/python
# (c) 2009 Marcos Dione <mdione@grulic.org.ar>
# distributed under the terms of the GPLv2.1
# a.k.a. Marsyas

# qt/kde related
from PyKDE4.kdecore import KCmdLineArgs, KAboutData, i18n, ki18n, KCmdLineOptions
from PyKDE4.kdeui import KApplication
# from PyKDE4.phonon import Phonon
from PyQt4.phonon import Phonon
from PyQt4.QtCore import SIGNAL, pyqtSignal, QObject, QUrl

# std python
import sys, os, os.path

# local

class Player (QObject):
    finished= pyqtSignal ()

    def __init__ (self, parent, playlist):
        QObject.__init__ (self, parent)
        self.playlist= playlist

        # TypeError: too many arguments to PyKDE4.phonon.MediaObject(), 0 at most expected
        # self.media= Phonon.MediaObject (parent)
        self.media= Phonon.MediaObject ()
        self.connect (self.media, SIGNAL("finished ()"), self.play)

        self.ao= Phonon.AudioOutput (Phonon.MusicCategory, parent)
        Phonon.createPath (self.media, self.ao)

    def play (self):
        try:
            filename= self.playlist.next ()
            print "playing", filename
            self.media.setCurrentSource (Phonon.MediaSource (filename))
            self.media.play ()
        except IndexError:
            print "playlist empty"
            self.finished.emit ()

class PlayList (QObject):
    finished= pyqtSignal ()

    def __init__ (self, parent, collection):
        QObject.__init__ (self, parent)
        self.collection= collection

    def next (self):
        print "next!",
        filename= self.collection.nextSong ()
        return filename

class ErrorNoDatabase (Exception):
    pass

class Collection (QObject):
    """A Collection of Albums"""

    def __init__ (self, parent, path):
        QObject.__init__ (self, parent)
        self.path= path
        self.filepaths= []

        try:
            self.load ()
        except ErrorNoDatabase:
            print "no database!"
            self.scan ()

    def load (self):
        raise ErrorNoDatabase

    def scan (self):
        print "scanning >%s<" % self.path
        # args.arg (index) is returning something that ois not precisely a str
        for root, dirs, files in os.walk (str (self.path)):
            for filename in files:
                filepath= os.path.join (root, filename)
                print "adding %s to the colection" % filepath
                self.filepaths.append (filepath)
        print "scan finished"

    def nextSong (self):
        return self.filepaths.pop (0)


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

#########################################
# the app itself!

collections= []
for index in xrange (args.count ()):
    collections.append (Collection (app, args.arg (index)))

# TODO: really implement several collections
playlist= PlayList (app, collections[0])
player= Player (app, playlist)
player.finished.connect (app.quit)

player.play ()
app.exec_ ()

# end
