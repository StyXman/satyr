#! /usr/bin/python
# vim: set fileencoding=utf-8 :
# (c) 2009 Marcos Dione <mdione@grulic.org.ar>
# distributed under the terms of the GPLv2.1

# qt/kde related
from PyKDE4.kdecore import KCmdLineArgs, KAboutData, i18n, ki18n, KCmdLineOptions
from PyKDE4.kdeui import KApplication
from PyKDE4.kio import KDirWatch
# from PyKDE4.phonon import Phonon
from PyQt4.phonon import Phonon
from PyQt4.QtCore import SIGNAL, pyqtSignal, QObject, QUrl

# dbus
import dbus
import dbus.mainloop.qt
import dbus.service

# std python
import sys, os, os.path, time, bisect, stat

# local

# globals :|
BUS_NAME= 'org.kde.satyr'

MetaDBusObject= type (dbus.service.Object)
MetaQObject= type (QObject)

class MetaObject (MetaQObject, MetaDBusObject):
    """Dummy metaclass that allows us to inherit from both QObject and d.s.Object"""
    def __init__(cls, name, bases, dct):
        MetaDBusObject.__init__ (cls, name, bases, dct)
        MetaQObject.__init__ (cls, name, bases, dct)

class Player (dbus.service.Object, QObject):
    __metaclass__= MetaObject

    finished= pyqtSignal ()

    def __init__ (self, parent, busName, playlist):
        dbus.service.Object.__init__ (self, busName, "/player")
        QObject.__init__ (self, parent)

        self.playlist= playlist
        # TODO: fix when not DUI
        # self.connect (self.media, SIGNAL("finished ()"), self.next)
        self.filename= None
        self.playing= False
        self.paused= False

        # TypeError: too many arguments to PyKDE4.phonon.MediaObject(), 0 at most expected
        # self.media= Phonon.MediaObject (parent)
        self.media= Phonon.MediaObject ()
        self.connect (self.media, SIGNAL("finished ()"), self.next)

        self.ao= Phonon.AudioOutput (Phonon.MusicCategory, parent)
        Phonon.createPath (self.media, self.ao)

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def prev (self):
        try:
            self.filename= self.playlist.prev ()
            if self.playing:
                self.play ()
        except IndexError:
            print "playlist empty"
            self.stop ()

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def play (self):
        if self.paused:
            self.pause ()
        else:
            self.playing= True
            time.sleep (0.2)
            if self.filename is None:
                self.next ()
            print "playing", self.filename
            self.media.setCurrentSource (Phonon.MediaSource (self.filename))
            # self.media.play ()

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def pause (self):
        """toggle"""
        if self.playing:
            if not self.paused:
                print "pa!..."
                self.media.pause ()
                self.paused= True
            else:
                print "...use!"
                self.media.play ()
                self.paused= False

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def stop (self):
        print "*screeeech*! stoping!"
        self.media.stop ()
        self.playing= False

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def next (self):
        try:
            self.filename= self.playlist.next ()
            if self.playing:
                self.play ()
        except IndexError:
           print "playlist empty"
           self.stop ()

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def quit (self):
        print "bye!"
        self.finished.emit ()

class PlayList (dbus.service.Object, QObject):
    __metaclass__= MetaObject

    finished= pyqtSignal ()

    def __init__ (self, parent, busName, collection):
        dbus.service.Object.__init__ (self, busName, "/playlist")
        QObject.__init__ (self, parent)
        self.collection= collection

    def prev (self):
        print "¡prev",
        return self.collection.prevSong ()

    def next (self):
        print "next!",
        return self.collection.nextSong ()

class ErrorNoDatabase (Exception):
    pass

class Collection (dbus.service.Object, QObject):
    __metaclass__= MetaObject
    """A Collection of Albums"""

    def __init__ (self, parent, path):
        dbus.service.Object.__init__ (self, busName, "/collection")
        QObject.__init__ (self, parent)
        self.path= path
        self.filepaths= []
        self.index= -1

        self.watch= KDirWatch (self)
        self.watch.addDir (self.path,
            KDirWatch.WatchMode (KDirWatch.WatchFiles|KDirWatch.WatchSubDirs))
        self.connect (self.watch, SIGNAL("created (const QString &)"), self.scan)

        try:
            self.load ()
        except ErrorNoDatabase:
            print "no database!"
            self.scan ()

    def load (self):
        raise ErrorNoDatabase

    def scan (self, path=None):
        if path is None:
            path= self.path
        # args.arg (index) is returning something that is not precisely a str
        path= unicode (path)
        print "scanning >%s<" % repr (path)
        mode= os.stat (path).st_mode
        if stat.S_ISDIR (mode):
            for root, dirs, files in os.walk (path):
                for filename in files:
                    filepath= os.path.join (root, filename)
                    self.add (filepath)
        elif stat.S_ISREG (mode):
            self.add (path)

        print "scan finished"

    def add (self, filepath):
        index= bisect.bisect (self.filepaths, filepath)
        # test if it's not already there
        if index==0 or self.filepaths[index-1]!= filepath:
            print "adding %s to the colection" % filepath
            self.filepaths.insert (index, filepath)

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def dump (self):
        for filepath in self.filepaths:
            print filepath

    def prevSong (self):
        self.index-= 1
        filepath= self.filepaths[self.index]
        return filepath

    def nextSong (self):
        self.index+= 1
        filepath= self.filepaths[self.index]
        return filepath


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
busName= dbus.service.BusName (BUS_NAME, bus=bus)


#########################################
# the app itself!

collections= []
for index in xrange (args.count ()):
    collections.append (Collection (app, args.arg (index)))

# TODO: really implement several collections
playlist= PlayList (app, busName, collections[0])
player= Player (app, busName, playlist)
player.finished.connect (app.quit)

# player.play ()
app.exec_ ()

# end
