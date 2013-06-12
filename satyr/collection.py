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
from PyQt4.QtCore import pyqtSignal, pyqtSlot, QString

# dbus
import dbus.service

# std python
import os, os.path

# we needed before loggin to get the handler
import satyr

# logging
import logging
logger = logging.getLogger(__name__)

# local
from satyr.common import SatyrObject, BUS_NAME
from satyr.collection_indexer import CollectionIndexer
from satyr.song import Song
from satyr import utils

class ErrorNoDatabase (Exception):
    pass

class Collection (SatyrObject):
    """A Collection of Albums"""
    newSongs= pyqtSignal ()
    scanBegins= pyqtSignal ()
    scanFinished= pyqtSignal ()

    def __init__ (self, parent, path="", relative=False, busName=None, busPath=None):
        SatyrObject.__init__ (self, parent, busName, busPath)


        self.songs= []
        self.songsById= {}
        self.count= 0
        # (re)defined by an aggregator if we're in one of those
        self.offset= 0

        # BUG: path is not reread from the config file!
        # it breaks rescanning
        self.configValues= (
            ('path', str, path),
            )
        self.loadConfig ()

        # if the user requests a new path, use it
        if self.path!=path and path!="":
            path= os.path.abspath (path)
            self.path= path
            self.forceScan= True
            logger.info ("new path, forcing (re)scan")
        else:
            self.forceScan= False
        self.relative= relative
        logger.debug ("Collection(): %s", self.path)

        self.watch= KDirWatch (self)
        self.watch.addDir (self.path,
            KDirWatch.WatchMode (KDirWatch.WatchFiles|KDirWatch.WatchSubDirs))
        self.watch.created.connect (self.newFiles)

        self.scanners= []
        self.scanning= False
        self.loadMetadata= False

        if busPath is not None:
            self.collectionFile= str (KStandardDirs.locateLocal ('data', 'satyr/%s.tdb' % self.dbusName (busPath)))
        else:
            self.collectionFile= str (KStandardDirs.locateLocal ('data', 'satyr/collection.tdb'))

    def loadOrScan (self):
        if self.forceScan or not self.load ():
            self.scan ()

    def load (self):
        logger.info ('loading from', self.collectionFile)
        try:
            # we must remove the trailing newline
            # we could use strip(), but filenames ending with any other whitespace
            # (think of the users!) would be loaded incorrectly
            # this oneliner seems to be the fastest against:
            # * fp= []; f= open(); for line in f.readlines(): fp.append (line)
            # * fp= []; f= open(); for line in f: fp.append (line)
            fileinfos= [ line[:-1].split (',', 1) for line in open (self.collectionFile) ]
            self.add (fileinfos)
            ans= True
        except IOError, e:
            logger.warning ("no database!")
            logger.warning ('FAILED! %s', e)
            ans= False

        return ans

    def save (self):
        if self.count>0:
            utils.makedirs (os.path.dirname (self.collectionFile))
            try:
                logger.debug ('saving collection to', self.collectionFile)
                f= open (self.collectionFile, 'w+')
                # we must add the trailing newline
                for song in self.songs:
                    f.write ("%s,%s\n" %(song.id, song.filepath))
                f.close ()
            except Exception, e:
                # any problem we kill the bastard
                logger.warning (e)
                logger.warning ('FAILED! nuking...')
                os.unlink (self.collectionFile)
        else:
            logger.warning ('no collection to save!')

    def saveConfig (self):
        # reimplement just to also save the collection
        self.save ()
        SatyrObject.saveConfig (self)

    # @pyqtSlot ()
    def newFiles (self, path):
        path= utils.qstring2path (path)
        logger.debug ("C.newFiles(): %s" % path)
        self.scan (path)

    def scan (self, path=None, loadMetadata=False):
        self.scanning= True
        self.loadMetadata= loadMetadata

        if path is None:
            path= self.path

        logger.debug ("C.scan(%s)", path)

        scanner= CollectionIndexer (path)
        scanner.scanning.connect (self.progress)
        scanner.foundSongs.connect (self.add)
        scanner.terminated.connect (self.log)
        # it's a signal
        scanner.finished.connect (self.scanFinished_)

        self.scanBegins.emit ()
        scanner.start ()
        # hold it or it gets destroyed before it finishes
        # BUG: they're never destroyed!
        self.scanners.append (scanner)

    def scanFinished_ (self):
        logger.debug ("C.scanFinished()")
        self.scanning= False
        self.scanFinished.emit ()

    def progress (self, path):
        # TODO: emit a signal?
        pass

    def add (self, filepaths):
        # TODO: emit the list
        self.newSongs_= []
        # we get a QStringList; convert to a list so we can python-iterate it
        for id, filepath in list (filepaths):
            # filepath can be a QString because this method
            # is also connected to a signal and they get converted by ptqt4
            if isinstance (filepath, QString):
                # paths must be bytes, not ascii or utf-8
                filepath= utils.qstring2path (filepath)

            # normalize! this way we avoid this dupes (couldn't find where they're originated)
            # C.add(): [(4081, '/home/mdione/media/music/Poison/2000 - Crack a smile... and more!//01 - Best thing you ever had.ogg')]
            # C.add(): [(4082, '/home/mdione/media/music/Poison/2000 - Crack a smile... and more!/01 - Best thing you ever had.ogg')]
            song= Song (self, os.path.normpath (filepath), id=id)

            # this works because Song.__cmp__() does not compare tags if one song
            # has not loaded them and Song does not do it automatically
            # so only paths are compared.
            index= utils.bisect (self.songs, song)
            s= len (self.songs)
            #  empty list or
            #          index is the last position or
            #                        the new Song's filepath is not the same already in the position (to the left)
            if s==0 or index==s-1 or self.songs[index-1].filepath!=song.filepath:
                self.songs.insert (index, song)
                self.songsById[song.id]= song
                self.count+= 1
                if self.loadMetadata:
                    song.loadMetadata ()
                self.newSongs_.append ((index, filepath))

        logger.debug ("C.add():", self.newSongs_)
        self.newSongs.emit ()

    def indexForSong (self, song):
        # BUG: this is O(n)
        # NOTE: we cannot use Python's bisect now because if the metadata is loaded
        # (and if we're here it is pretty sure the case)
        # the order changes: when we Collection.loadOrScan() it's filepath based
        # and now it's metadata based.
        # is the above no longer true?
        # somehow it is :(
        # NOTE: how does filepath-> id impact this?
        index= utils.bisect (self.songs, song, Song.cmpByFilepath)

        return index

    def log (self, *args):
        log.debug ("logging", args)

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def rescan (self):
        self.scan ()

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def dump (self):
        for song in self.songs:
            logger.info (song.filepath)

# end
