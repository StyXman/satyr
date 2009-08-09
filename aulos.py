#! /usr/bin/python
# (c) 2009 Marcos Dione <mdione@grulic.org.ar>
# distributed under the terms of the GPLv2.1
# a.k.a. Marsyas

# qt/kde related
from PyKDE4.kdecore import KCmdLineArgs, KAboutData, i18n, ki18n, KCmdLineOptions
from PyKDE4.kdeui import KApplication
# from PyKDE4.phonon import Phonon
from PyQt4.phonon import Phonon
from PyQt4.QtCore import SIGNAL

# std python
import sys

# local

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

# TypeError: too many arguments to PyKDE4.phonon.MediaObject(), 0 at most expected
# media= Phonon.MediaObject (app)
media= Phonon.MediaObject ()
ao= Phonon.AudioOutput (Phonon.MusicCategory, app)
print ao.name ()
print ao.outputDevice ().name ()
Phonon.createPath (media, ao)
# player= Phonon.createPlayer (Phonon.MusicCategory, media.currentSource ())

media.setCurrentSource (Phonon.MediaSource (args.arg (0)))
media.play ()

# I whish it were this easy
# app.connect (media.finish, app.quit)
app.connect (media, SIGNAL("finished ()"), app.quit)
app.exec_ ()

# end
