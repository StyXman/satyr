#! /usr/bin/python
# (c) 2009 Marcos Dione <mdione@grulic.org.ar>
# distributed under the terms of the GPLv2.1
# a.k.a. Marsyas

# qt/kde related
from PyKDE4.kdecore import KCmdLineArgs, KAboutData, i18n, ki18n, KCmdLineOptions
from PyKDE4.kdeui import KApplication
# from PyKDE4.phonon import Phonon
from PyQt4.phonon import Phonon
from PyQt4.QtCore import SIGNAL, pyqtSignal, QObject

# std python
import sys

# local

class Player (QObject):
    finished= pyqtSignal ()

    def __init__ (self, parent):
        QObject.__init__ (self, parent)
        # TypeError: too many arguments to PyKDE4.phonon.MediaObject(), 0 at most expected
        # self.media= Phonon.MediaObject (parent)
        self.media= Phonon.MediaObject ()
        self.ao= Phonon.AudioOutput (Phonon.MusicCategory, parent)
        print self.ao.name ()
        print self.ao.outputDevice ().name ()
        Phonon.createPath (self.media, self.ao)
        # player= Phonon.createPlayer (Phonon.MusicCategory, self.media.currentSource ())
        self.files= []
        self.connect (self.media, SIGNAL("finished ()"), self.play)

    def append (self, path):
        self.files.append (path)

    def play (self):
        try:
            file= self.files.pop (0)
            print "playing", file
            self.media.setCurrentSource (Phonon.MediaSource (file))
            self.media.play ()
        except IndexError:
            print "playlist empty; bailing out"
            self.finished.emit ()

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

player= Player (app)
player.finished.connect (app.quit)

for index in xrange (args.count ()):
    player.append (args.arg (index))

player.play ()
app.exec_ ()

# end
