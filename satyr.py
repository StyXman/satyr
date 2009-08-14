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

# dbus
import dbus
import dbus.mainloop.qt
import dbus.service

# std python
import sys, os, os.path, time

# local

# globals :|
BUS_NAME= 'org.kde.satyr'

MetaQObject= type (QObject)
MetaObject= type (dbus.service.Object)

class MetaPlayer (MetaQObject, MetaObject):
    """Dummy metaclass that allows us to inherit from both QObject and d.s.Object"""
    def __init__(cls, name, bases, dct):
        MetaObject.__init__ (cls, name, bases, dct)
        MetaQObject.__init__ (cls, name, bases, dct)

class Player (dbus.service.Object, QObject):
    __metaclass__= MetaPlayer

    finished= pyqtSignal ()

    def __init__ (self, parent, bus, playlist):
        bus_name= dbus.service.BusName (BUS_NAME, bus=bus)
        dbus.service.Object.__init__ (self, bus_name, "/player")
        QObject.__init__ (self, parent)
        self.playlist= playlist

        # TypeError: too many arguments to PyKDE4.phonon.MediaObject(), 0 at most expected
        # self.media= Phonon.MediaObject (parent)
        self.media= Phonon.MediaObject ()
        self.connect (self.media, SIGNAL("finished ()"), self.play)

        self.ao= Phonon.AudioOutput (Phonon.MusicCategory, parent)
        Phonon.createPath (self.media, self.ao)

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def play (self):
        try:
            time.sleep (0.2)
            filename= self.playlist.next ()
            print "playing", filename
            self.media.setCurrentSource (Phonon.MediaSource (filename))
            self.media.play ()
        except IndexError:
            print "playlist empty"
            self.finished.emit ()

    @dbus.service.method(BUS_NAME, in_signature='', out_signature='')
    def quit (self):
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

dbus.mainloop.qt.DBusQtMainLoop (set_as_default=True)
bus= dbus.SessionBus ()


#########################################
# the app itself!

collections= []
for index in xrange (args.count ()):
    collections.append (Collection (app, args.arg (index)))

# TODO: really implement several collections
playlist= PlayList (app, collections[0])
player= Player (app, bus, playlist)
player.finished.connect (app.quit)

player.play ()
app.exec_ ()

# end
