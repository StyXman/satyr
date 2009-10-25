# vim: set fileencoding=utf-8 :
# (c) 2009 Marcos Dione <mdione@grulic.org.ar>

# This file is part of satyr.

# satyr is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.

# satyr is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with satyr.  If not, see <http://www.gnu.org/licenses/>.


# qt/kde related
from PyKDE4.kdecore import KStandardDirs
from PyKDE4.kio import KDirWatch
from PyQt4.QtCore import pyqtSignal, QString, QByteArray

# dbus
import dbus.service

# std python
import os, bisect
import pdb

# local
from common import SatyrObject, BUS_NAME
from collection_indexer import CollectionIndexer
from models import Song
import utils

class ErrorNoDatabase (Exception):
    pass

class Collection (SatyrObject):
    """A Collection of Albums"""
    newSong= pyqtSignal (unicode)
    filesAdded= pyqtSignal ()
    scanBegins= pyqtSignal ()
    scanFinished= pyqtSignal ()

    def __init__ (self, parent, path, busName=None, busPath=None):
        SatyrObject.__init__ (self, parent, busName, busPath)

        self.songs= []
        self.count= 0

        self.configValues= (
            ('path', str, path),
            )
        self.loadConfig ()

        # if the user requests a new path, use it
        if self.path!=path:
            self.path= path
            self.forceScan= True
            print "new path, forcing (re)scan"
        else:
            self.forceScan= False

        self.watch= KDirWatch (self)
        self.watch.addDir (self.path,
            KDirWatch.WatchMode (KDirWatch.WatchFiles|KDirWatch.WatchSubDirs))
        self.watch.created.connect (self.newFiles)

        self.scanners= []
        if busPath is not None:
            self.collectionFile= str (KStandardDirs.locateLocal ('data', 'satyr/%s.tdb' % self.dbusName (busPath)))
        else:
            self.collectionFile= str (KStandardDirs.locateLocal ('data', 'satyr/collection.tdb'))

    def loadOrScan (self):
        # FIXME: ugly
        try:
            if self.forceScan:
                self.scan ()
            else:
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
            filepaths= []
            for line in f.readlines ():
                filepaths.append (line[:-1])
            f.close ()
            self.add (filepaths)
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
                for song in self.songs:
                    f.write (song.filepath+'\n')
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
        path= utils.qstring2str (path)
        self.scan (path)

    def scan (self, path=None):
        if path is None:
            path= self.path
        scanner= CollectionIndexer (path)
        scanner.scanning.connect (self.progress)
        scanner.foundSongs.connect (self.add)
        scanner.terminated.connect (self.log)
        scanner.finished.connect (self.scanFinished)

        self.scanBegins.emit ()
        scanner.start ()
        # hold it or it gets destroyed before it finishes
        self.scanners.append (scanner)

    def progress (self, path):
        # print 'scanning', path
        # TODO: emit a signal?
        pass

    def add (self, filepaths):
        # we get a QStringList; convert to a list so we can python-iterate it
        for filepath in list (filepaths):
            # filepath can be a QString because this method
            # is also connected to a signal and they get converted by ptqt4
            if isinstance (filepath, QString):
                # paths must be bytes, not ascii or utf-8
                filepath= utils.qstring2str (filepath)

            song= Song (self, filepath)

            index= bisect.bisect (self.songs, song)
            # test if it's not already there
            # FIXME: use another sorting method?
            if index==0 or self.songs[index-1]!=song:
                self.songs.insert (index, song)
                self.count+= 1

                self.newSong.emit (filepath)

    def indexForSong (self, song):
        index= bisect.bisect (self.songs, song)
        # test if it's not already there
        if index==0 or self.songs[index-1]!=song:
            # 404 not found
            index= None

        return index

    def log (self, *args):
        print "logging", args

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def rescan (self):
        self.scan ()

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def dump (self):
        for filepath in self.filepaths:
            print filepath

# end
