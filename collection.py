# vim: set fileencoding=utf-8 :
# (c) 2009 Marcos Dione <mdione@grulic.org.ar>
# distributed under the terms of the GPLv2.1

# qt/kde related
from PyKDE4.kdecore import KStandardDirs
from PyKDE4.kio import KDirWatch
from PyQt4.QtCore import pyqtSignal, QObject, QUrl, QByteArray, QVariant

# dbus
import dbus.service

# std python
import os, bisect

# local
from common import SatyrObject, BUS_NAME
from collection_indexer import CollectionIndexer

class ErrorNoDatabase (Exception):
    pass

class Collection (SatyrObject):
    """A Collection of Albums"""
    newSong= pyqtSignal (int, unicode)
    filesAdded= pyqtSignal ()

    def __init__ (self, parent, path, busName=None, busPath=None):
        SatyrObject.__init__ (self, parent, busName, busPath)
        self.filepaths= []
        self.count= 0

        self.configValues= (
            ('path', str, path),
            )
        self.loadConfig ()

        # if the user requests a new path, use it
        if self.path!=path:
            self.path= path

        self.watch= KDirWatch (self)
        self.watch.addDir (self.path,
            KDirWatch.WatchMode (KDirWatch.WatchFiles|KDirWatch.WatchSubDirs))
        self.watch.created.connect (self.newFiles)

        self.scanners= []
        self.collectionFile= str (KStandardDirs.locateLocal ('data', 'saryr/%s.tdb' % self.dbusName (busPath)))

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
            print "load finished, found %d songs" % self.count
            self.filesAdded.emit ()
        except IOError, e:
            print 'FAILED!', e
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
        print "scan finished, found %d songs" % self.count
        self.filesAdded.emit ()

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def rescan (self):
        self.filepaths= []
        self.scan ()

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def dump (self):
        for filepath in self.filepaths:
            print filepath

# end
