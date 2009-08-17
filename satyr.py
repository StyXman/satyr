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
from PyQt4.QtCore import SIGNAL, pyqtSignal, QObject, QUrl, QByteArray

# dbus
import dbus
import dbus.mainloop.qt
import dbus.service

# std python
import sys, os, os.path, time, bisect, stat, random
import magic

# local
from primes import primes

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

    def __init__ (self, parent, playlist, busName, busPath):
        dbus.service.Object.__init__ (self, busName, busPath)
        QObject.__init__ (self, parent)

        self.playlist= playlist
        # TODO: fix when not DUI
        # self.connect (self.media, SIGNAL("finished ()"), self.next)
        self.filename= None
        self.playing= False
        self.paused= False
        self.stopAfter= False

        # TypeError: too many arguments to PyKDE4.phonon.MediaObject(), 0 at most expected
        # self.media= Phonon.MediaObject (parent)
        self.media= Phonon.MediaObject ()
        self.connect (self.media, SIGNAL("finished ()"), self.next)

        self.ao= Phonon.AudioOutput (Phonon.MusicCategory, parent)
        Phonon.createPath (self.media, self.ao)

        self.mimetypes= [ str (mimetype)
            for mimetype in Phonon.BackendCapabilities.availableMimeTypes ()
                if self.validMimetype (str (mimetype)) ]
        self.magic= magic.open (magic.MAGIC_MIME)
        self.magic.load ()

    def validMimetype (self, mimetype):
        """Phonon.BackendCapabilities.availableMimeTypes() returns a lot of nonsense,
        like image/png or so.
        Filter only interesting mimetypes."""
        valid= False
        valid= valid or mimetype.startswith ('audio')
        valid= valid or mimetype=='application/ogg'

        return valid

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

            print repr (self.filename)
            mimetype_enc= self.magic.file (self.filename)
            mimetype= mimetype_enc.split (';')[0]
            # detect mimetype and play only if it's suppourted
            while mimetype not in self.mimetypes:
                # TODO: remove it from the collection?
                # or should the collection filter them while scaning?
                print "skipping %s; mimetype %s not supported" % (self.filename, mimetype)
                self.next ()
                mimetype= self.magic.file (self.filename).split (';')[0]

            print "playing", self.filename,
            self.media.setCurrentSource (Phonon.MediaSource (self.filename))
            print "!"
            self.media.play ()

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
            if self.stopAfter:
                print "stopping after!"
                # stopAfter is one time only
                self.toggleStopAfter ()
                self.stop ()
            # BUG: this should not be here
            elif self.playing:
                self.play ()
        except IndexError:
            print "playlist empty"
            self.stop ()

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def toggleStopAfter (self):
        """toggle"""
        print "toggle: stopAfter"
        self.stopAfter= not self.stopAfter

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def quit (self):
        print "bye!"
        self.finished.emit ()

class StopAfter (Exception):
    pass

class PlayList (dbus.service.Object, QObject):
    __metaclass__= MetaObject

    finished= pyqtSignal ()

    def __init__ (self, parent, collections, busName=None, busPath=None):
        dbus.service.Object.__init__ (self, busName, busPath)
        QObject.__init__ (self, parent)
        # TODO: support more collections
        self.collection= collections[0]
        self.random= False

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def toggleRandom (self):
        """toggle"""
        print "toggle: random"
        self.random= not self.random

    def prev (self):
        print "¡prev",
        if self.random:
            filepath= self.collection.prevRandomSong ()
        else:
            filepath= self.collection.prevSong ()
        return filepath

    def next (self):
        print "next!",
        if self.random:
            filepath= self.collection.nextRandomSong ()
        else:
            filepath= self.collection.nextSong ()
        return filepath

class ErrorNoDatabase (Exception):
    pass

class Collection (dbus.service.Object, QObject):
    __metaclass__= MetaObject
    """A Collection of Albums"""

    def __init__ (self, parent, path, busName=None, busPath=None):
        dbus.service.Object.__init__ (self, busName, busPath)
        QObject.__init__ (self, parent)
        self.path= path
        self.filepaths= []
        self.index= -1
        self.count= 0
        self.seed= 0
        self.prime= 17

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

    def walk (self, top):
        # TODO: support single filenames
        # if not os.path.isdir (top):
        #     return top
        try:
            # names= [ str (x) for x in os.listdir (top)]
            names= os.listdir (top)
        except Exception, err:
            print err
            return

        dirs, nondirs = [], []
        for name in names:
            try:
                path= top+u'/'+name
            except UnicodeDecodeError:
                print repr (top), repr (name)
                print name, "skipped: bad encoding"
            else:
                if os.path.isdir(path):
                    dirs.append(name)
                else:
                    nondirs.append(name)

        yield top, dirs, nondirs
        for name in dirs:
            try:
                path = top+u'/'+name
            except UnicodeDecodeError:
                print name, "skipped: bad encoding"
            else:
                if not os.path.islink(path):
                    for x in self.walk(path):
                        yield x

    def randomPrime (self):
        # select a random prime based on the amount of songs in the collection
        top= bisect.bisect (primes, self.count)
        # select from the upper 2/3,
        # so in large collections the same artist is not picked consecutively
        self.prime= random.choice (primes[top/3:top])
        print "prime selected:", self.prime

    def newFiles (self, path):
        # BUG: this is ugly
        qba= QByteArray ()
        qba.append (path)
        path= str (qba)
        self.scan (path)

    def scan (self, path=None):
        if path is None:
            path= self.path
        print "scanning >%s<" % repr (path)
        mode= os.stat (path).st_mode
        if stat.S_ISDIR (mode):
            # http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=481795
            for root, dirs, files in self.walk (path):
                for filename in files:
                    filepath= os.path.join (root, filename)
                    self.add (filepath)
        elif stat.S_ISREG (mode):
            self.add (path)

        self.randomPrime ()
        print "scan finished, found %d songs" % self.count

    def add (self, filepath):
        index= bisect.bisect (self.filepaths, filepath)
        # test if it's not already there
        if index==0 or self.filepaths[index-1]!= filepath:
            # print "adding %s to the colection" % filepath
            self.filepaths.insert (index, filepath)
            self.count+= 1

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

    def nextRandomSong (self):
        # TODO: FIX this ugliness
        if self.index==-1:
            self.index= 0
        else:
            self.index= (self.seed+self.prime)%self.count
        self.seed= self.index
        filepath= self.filepaths[self.index]
        return filepath

    def prevRandomSong (self):
        self.index= (self.seed-self.prime)%self.count
        self.seed= self.index
        filepath= self.filepaths[self.index]
        return filepath


if __name__=='__main__':
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
        # paths must be bytes, nos ascii or utf-8
        path= args.arg (index)
        # BUG: this is ugly
        # qba= QByteArray ()
        # qba.append (path)
        # path= str (qba)
        # convert QString to unicode
        path= unicode (path)
        collections.append (Collection (app, path, busName, "/collection_%04d" % index))

    playlist= PlayList (app, collections, busName, '/playlist')
    player= Player (app, playlist, busName, '/player')
    player.finished.connect (app.quit)

    app.exec_ ()

# end
