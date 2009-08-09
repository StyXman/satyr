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
import sys

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
        self.files= []

    def append (self, path):
        self.files.append (path)

    def next (self):
        print "next!",
        filename= self.files.pop (0)
        return filename


#########################################
# all the bureaucratic init of a KDE App
appName     = "aulos.py"
catalog     = ""
programName = ki18n ("aulos")                 #ki18n required here
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

playlist= PlayList (app, None)
player= Player (app, playlist)
player.finished.connect (app.quit)

for index in xrange (args.count ()):
    playlist.append (args.arg (index))

player.play ()
app.exec_ ()

# end
