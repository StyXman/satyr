#! /usr/bin/python
# vim: set fileencoding=utf-8 :
# (c) 2009 Marcos Dione <mdione@grulic.org.ar>
# distributed under the terms of the GPLv2.1

# qt/kde related
from PyKDE4.kdecore import KCmdLineArgs, KAboutData, i18n, ki18n
from PyKDE4.kdecore import KCmdLineOptions, KSharedConfig, KMimeType, KUrl
from PyKDE4.kdecore import KStandardDirs
from PyKDE4.kdeui import KApplication, KMainWindow, KListWidget
from PyKDE4.kio import KDirWatch
# from PyKDE4.phonon import Phonon
from PyQt4.phonon import Phonon
from PyQt4.QtCore import pyqtSignal, QObject, QUrl, QByteArray, QVariant
from PyQt4.QtCore import QThread, QTimer
from PyQt4.QtGui import QListWidget, QWidget, QVBoxLayout

# dbus
import dbus
import dbus.mainloop.qt
import dbus.service

# std python
import sys, os, os.path, time, bisect, stat, random

# local
from primes import primes

# globals :|
BUS_NAME= 'org.kde.satyr'

def configBoolToBool (s):
    return s!='false'

MetaDBusObject= type (dbus.service.Object)
MetaQObject= type (QObject)

class MetaObject (MetaQObject, MetaDBusObject):
    """Dummy metaclass that allows us to inherit from both QObject and d.s.Object"""
    def __init__(cls, name, bases, dct):
        MetaDBusObject.__init__ (cls, name, bases, dct)
        MetaQObject.__init__ (cls, name, bases, dct)


class SatyrObject (dbus.service.Object, QObject):
    __metaclass__= MetaObject

    def __init__ (self, parent, busName, busPath):
        dbus.service.Object.__init__ (self, busName, busPath)
        QObject.__init__ (self, parent)

        self.config= KSharedConfig.openConfig ('satyrrc').group (self.dbusName (busPath))

    def dbusName (self, busPath):
        return busPath[1:].replace ('/', '-')

    def saveConfig (self):
        for k, t, v in self.configValues:
            v= getattr (self, k)
            # print 'writing config entry %s= %s' % (k, v)
            self.config.writeEntry (k, QVariant (v))
        self.config.config ().sync ()

    def loadConfig (self):
        for k, t, v in self.configValues:
            print 'reading config entry %s [%s]' % (k, v),
            s= self.config.readEntry (k, QVariant (v)).toString ()
            v= t (s)
            print s, v
            setattr (self, k, v)

class Player (SatyrObject):
    finished= pyqtSignal ()
    stopAfterChanged= pyqtSignal (bool)

    def __init__ (self, parent, playlist, busName, busPath):
        SatyrObject.__init__ (self, parent, busName, busPath)

        self.configValues= (
            ('playing', configBoolToBool, False),
            ('paused', configBoolToBool, False),
            ('stopAfter', configBoolToBool, False),
            ('quitAfter', configBoolToBool, False),
            )
        self.loadConfig ()

        self.playlist= playlist
        self.filepath= None

        self.media= Phonon.MediaObject ()
        # god bless PyQt4.5
        self.media.finished.connect (self.next)
        self.media.stateChanged.connect (self.stateChanged)

        self.ao= Phonon.AudioOutput (Phonon.MusicCategory, parent)
        Phonon.createPath (self.media, self.ao)

    def stateChanged (self, new, old):
        # print "state changed from %d to %d" % (old, new)
        if new==Phonon.ErrorState:
            print "ERROR: %d: %s" % (self.media.errorType (), self.media.errorString ())
            # just skip it
            self.next ()

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def prev (self):
        try:
            self.playlist.prev ()
            self.filepath= self.playlist.current ()
            if self.playing:
                self.play ()
        except IndexError:
            print "playlist empty"
            self.stop ()

    @dbus.service.method (BUS_NAME, in_signature='i', out_signature='')
    def play (self, index=None):
        if self.paused:
            self.pause ()
        else:
            self.playing= True
            time.sleep (0.2)
            # FIXME: self.filepath should never be None
            # which implies that self.playlist.current () should always point
            # to a filepath (or index, if we change the API)
            if self.filepath is None:
                if self.playlist.current () is None:
                    self.next ()

            if index is not None:
                self.playlist.jumpTo (index)

            self.filepath= self.playlist.current ()

            print "playing", self.filepath
            self.media.setCurrentSource (Phonon.MediaSource (self.filepath))
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
            self.playlist.next ()
            self.filepath= self.playlist.current ()
            # FIXME: this should not be here
            if self.stopAfter:
                print "stopping after!"
                # stopAfter is one time only
                self.toggleStopAfter ()
                self.stop ()
            # FIXME: this should not be here
            if self.quitAfter:
                print "quiting after!"
                # quitAfter is one time only
                self.toggleQuitAfter ()
                self.quit ()
            # FIXME: this should not be here
            elif self.playing:
                self.play ()
        except IndexError:
            print "playlist empty"
            self.stop ()

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def toggleStopAfter (self):
        """toggle"""
        print "toggle: stopAfter",
        self.stopAfter= not self.stopAfter
        print self.stopAfter
        self.stopAfterChanged.emit (self.stopAfter)

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def toggleQuitAfter (self):
        """I need this for debugging"""
        print "toggle: quitAfter",
        self.quitAfter= not self.quitAfter
        print self.quitAfter

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def quit (self):
        self.stop ()
        self.saveConfig ()
        # FIXME: is this the right API?
        self.playlist.saveConfig ()
        self.playlist.collection.saveConfig ()
        print "bye!"
        self.finished.emit ()


class StopAfter (Exception):
    pass

class PlayList (SatyrObject):
    finished= pyqtSignal ()
    randomChanged= pyqtSignal (bool)

    def __init__ (self, parent, collections, busName=None, busPath=None):
        SatyrObject.__init__ (self, parent, busName, busPath)
        # TODO: support more collections
        self.collection= collections[0]
        self.indexQueue= []
        self.filepath= None

        self.configValues= (
            ('random', configBoolToBool, False),
            )
        self.loadConfig ()

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def toggleRandom (self):
        """toggle"""
        print "toggle: random",
        self.random= not self.random
        print self.random
        self.randomChanged.emit (self.random)

    def prev (self):
        print "¡prev",
        if self.random:
            self.collection.prevRandomSong ()
        else:
            self.collection.prevSong ()
        self.filepath= self.collection.current ()

    def next (self):
        print "next!",
        if len (self.indexQueue)>0:
            # TODO: support more than one collection
            print 'from queue!',
            index= self.indexQueue.pop (0)
            self.filepath= self.collection.filepaths[index]
            print "[%d] %s" % (index, self.filepath)
        else:
            if self.random:
                self.collection.nextRandomSong ()
            else:
                self.collection.nextSong ()
            self.filepath= self.collection.current ()

    def current (self):
        return self.filepath

    @dbus.service.method (BUS_NAME, in_signature='i', out_signature='')
    def queue (self, collectionIndex):
        try:
            listIndex= self.indexQueue.index (collectionIndex)
            # esists; dequeue
            print 'dequeuing index [%d, %d] %s' % (listIndex, collectionIndex, self.collection.filepaths[collectionIndex])
            self.indexQueue.pop (listIndex)
        except ValueError:
            # doesn't exist; append
            print 'queuing [%d] %s' % (collectionIndex, self.collection.filepaths[collectionIndex])
            self.indexQueue.append (collectionIndex)

    @dbus.service.method (BUS_NAME, in_signature='s', out_signature='a(is)')
    def search (self, words):
        print "searching %s" % words
        wordList= words.lower ().split ()
        def predicate (s):
            found= True
            for word in wordList:
                found= found and word in s
            return found

        songs= [ (index, path)
            for (index, path) in enumerate (self.collection.filepaths)
                if predicate (path.lower ()) ]

        print songs
        return songs

    @dbus.service.method (BUS_NAME, in_signature='i', out_signature='')
    def jumpTo (self, index):
        self.filepath= self.collection.filepaths[index]


def validMimetype (mimetype):
    """Phonon.BackendCapabilities.availableMimeTypes() returns a lot of nonsense,
    like image/png or so.
    Filter only interesting mimetypes."""

    valid= False
    valid= valid or mimetype.startswith ('audio')
    # we can play the sound of video files :|
    # also some wma files are detected as video :|
    # skipping /home/mdione/media/music//N/Noir Desir/Album inconnu (13-07-2004 01:59:07)/10 - Piste 10.wma;
    # mimetype video/x-ms-asf not supported
    valid= valid or mimetype.startswith ('video')
    valid= valid or mimetype=='application/ogg'

    return valid

mimetypes= [ str (mimetype)
    for mimetype in Phonon.BackendCapabilities.availableMimeTypes ()
        if validMimetype (str (mimetype)) ]

def getMimeType (filepath):
    mimetype, accuracy= KMimeType.findByFileContent (filepath)
    # print mimetype.name (), accuracy,
    if accuracy<50:
        # try harder?
        mimetype, accuracy= KMimeType.findByUrl (KUrl (filepath))
        # print mimetype.name (), accuracy,
    # print
    return str (mimetype.name ())

class CollectionIndexer (QThread):
    # finished= pyqtSignal (QThread)
    scanning= pyqtSignal (unicode)
    foundSong= pyqtSignal (unicode)

    def __init__ (self, path, parent=None):
        QThread.__init__ (self, parent)
        self.path= path

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

    def run (self):
        # print "scanning >%s<" % repr (path)
        mode= os.stat (self.path).st_mode
        if stat.S_ISDIR (mode):
            # http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=481795
            for root, dirs, files in self.walk (self.path):
                self.scanning.emit (root)
                songs= []
                for filename in files:
                    filepath= os.path.join (root, filename)
                    # detect mimetype and add only if it's suppourted
                    mimetype= getMimeType (filepath)
                    if mimetype in mimetypes:
                        self.foundSong.emit (filepath)

        elif stat.S_ISREG (mode):
            mimetype= getMimeType (path)
            if mimetype in mimetypes:
                self.foundSong.emit (path)


class ErrorNoDatabase (Exception):
    pass

class Collection (SatyrObject):
    """A Collection of Albums"""
    newSong= pyqtSignal (int, unicode)

    def __init__ (self, parent, path, busName=None, busPath=None):
        SatyrObject.__init__ (self, parent, busName, busPath)
        self.filepaths= []
        self.count= 0

        self.configValues= (
            ('path', str, path),
            ('index', int, -1),
            ('seed', int, 0),
            ('prime', int, -1),
            # even if we could recalculate the filepath given the filelist
            # and the index, we save it anyways
            # just in case they become out of sync
            # BUG: reading any path gives ''
            ('filepath', str, None)
            )
        self.loadConfig ()
        print self.filepath

        # if the user requests a new path, use it
        if self.path!=path:
            self.path= path

        self.watch= KDirWatch (self)
        self.watch.addDir (self.path,
            KDirWatch.WatchMode (KDirWatch.WatchFiles|KDirWatch.WatchSubDirs))
        self.watch.created.connect (self.newFiles)

        self.scanners= []
        self.collectionFile= str (KStandardDirs.locateLocal ('data', 'saryr/%s.tdb' % self.dbusName (busPath)))
        # but if the filepath empty, calculate anyways (as good as any?)
        if self.filepath in ('', None):
            try:
                self.filepath= self.filepaths[self.index]
            except IndexError:
                self.filepath= None
            # print self.filepath

    def loadOrScan (self):
        try:
            self.load ()
        except ErrorNoDatabase:
            print "no database!"
            self.scan ()

    def load (self):
        print 'loading from', self.collectionFile
        try:
            f= open (self.collectionFile)
            # we must remove the trailing newline
            # we could use strip(), but filenames ending with any other whitespace
            # (think of the users!) would be loaded incorrectly
            for line in f.readlines ():
                # self.filepaths=  ([ path[:-1].decode ('utf-8') for path in  ])
                self.add (line[:-1].decode ('utf-8'))
            f.close ()
            # self.count= len (self.filepaths)
        except IOError, e:
            print 'FAILED!'
            raise ErrorNoDatabase
        print

    def save (self):
        if self.count>0:
            try:
                print 'saving collection to', self.collectionFile
                f= open (self.collectionFile, 'w+')
                # we must add the trailing newline
                # f.writelines ([ path.encode ('utf-8')+'\n' for path in self.filepaths ])
                for filepath in self.filepaths:
                    f.write (filepath.encode ('utf-8')+'\n')
                f.close ()
            except Exception, e:
                # any problem we kill the bastard
                print e
                print 'FAILED! nuking...'
                os.unlink (self.collectionFile)
        else:
            print 'no collection to save!'

    def saveConfig (self):
        # reimplement just to also save the collection
        self.save ()
        SatyrObject.saveConfig (self)

    def randomPrime (self):
        # select a random prime based on the amount of songs in the collection
        top= bisect.bisect (primes, self.count)
        # select from the upper 2/3,
        # so in large collections the same artist is not picked consecutively
        prime= random.choice (primes[top/3:top])

        return prime

    def newFiles (self, path):
        # BUG: this is ugly
        # qba= QByteArray ()
        # qba.append (path)
        # path= str (qba)

        # convert QString to unicode
        path= unicode (path)
        self.scan (path)

    def scan (self, path=None):
        if path is None:
            path= self.path
        scanner= CollectionIndexer (path)
        scanner.scanning.connect (self.progress)
        scanner.foundSong.connect (self.add)
        scanner.terminated.connect (self.log)
        scanner.finished.connect (self.scanFinished)
        scanner.start ()
        # hold it or it gets destroyed before it finishes
        self.scanners.append (scanner)

    def progress (self, path):
        print 'scanning', path

    def add (self, filepath):
        # the unidocde gets converted to QString by the signal/slot processing
        # so we convert it back
        filepath= unicode (filepath)
        index= bisect.bisect (self.filepaths, filepath)
        # test if it's not already there
        # FIXME: use another sorting method?
        if index==0 or self.filepaths[index-1]!= filepath:
            # print "adding %s to the colection" % filepath
            self.filepaths.insert (index, filepath)
            # FIXME: make a proper Song implementation
            self.newSong.emit (index, filepath)
            self.count+= 1

    def log (self, *args):
        print "logging", args

    def scanFinished (self):
        # self.scanners.remove (scanner)
        # FIXME: you know this is wrong
        if self.path is not None or self.prime==-1:
            # we're adding files,
            # or we hadn't set the prime yet
            # so we must recompute the prime.
            self.prime= self.randomPrime ()
            print "prime selected:", self.prime

        print "scan finished, found %d songs" % self.count

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def rescan (self):
        self.filepaths= []
        self.scan ()

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def dump (self):
        for filepath in self.filepaths:
            print filepath

    def prevSong (self):
        self.index-= 1
        self.filepath= self.filepaths[self.index]

    def nextSong (self):
        self.index+= 1
        self.filepath= self.filepaths[self.index]

    def nextRandomSong (self):
        # TODO: FIX this ugliness
        if self.index==-1:
            # HACK: ugly
            random= 1
        else:
            random= (self.seed+self.prime) % self.count
        self.index= (self.index+random) % self.count
        # print random, self.index
        self.seed= random
        self.filepath= self.filepaths[self.index]

    def prevRandomSong (self):
        random= self.seed
        self.index= (self.index-random) % self.count
        random= (self.seed-self.prime) % self.count
        # print random, self.index
        self.seed= random
        self.filepath= self.filepaths[self.index]

    def current (self):
        return self.filepath

from default import Ui_MainWindow

class MainWindow (KMainWindow):
    def __init__ (self, parent=None):
        KMainWindow.__init__ (self, parent)

        self.ui= Ui_MainWindow ()
        self.ui.setupUi (self)

    def connectUi (self, player, playlist):
        # connect buttons!
        self.ui.prevButton.clicked.connect (player.prev)
        self.ui.playButton.clicked.connect (player.play)
        self.ui.pauseButton.clicked.connect (player.pause)
        self.ui.stopButton.clicked.connect (player.stop)
        self.ui.nextButton.clicked.connect (player.next)

        self.ui.randomCheck.setChecked (playlist.random)
        self.ui.randomCheck.clicked.connect (playlist.toggleRandom)
        playlist.randomChanged.connect (self.ui.randomCheck.setChecked)

        self.ui.stopAfterCheck.setChecked (player.stopAfter)
        self.ui.stopAfterCheck.clicked.connect (player.toggleStopAfter)
        player.stopAfterChanged.connect (self.ui.stopAfterCheck.setChecked)

    def addSong (self, index, filepath):
        self.ui.songsList.insertItem (index, filepath)


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
        # paths must be bytes, nos ascii or utf-8
        path= args.arg (index)

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
