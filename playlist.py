# vim: set fileencoding=utf-8 :
# (c) 2009 Marcos Dione <mdione@grulic.org.ar>
# distributed under the terms of the GPLv2.1

# qt/kde related
from PyKDE4.kdecore import KStandardDirs
from PyQt4.QtCore import pyqtSignal

# dbus
import dbus.service

# std python

# local
from common import SatyrObject, BUS_NAME, configBoolToBool

class StopAfter (Exception):
    pass

class PlayList (SatyrObject):
    finished= pyqtSignal ()
    randomChanged= pyqtSignal (bool)
    songChanged= pyqtSignal (int)

    def __init__ (self, parent, collections, busName=None, busPath=None):
        SatyrObject.__init__ (self, parent, busName, busPath)
        self.collections= collections
        self.collectionStartIndexes= [ (0, self.collections[0]) ]
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

    def indexToCollection (self, index):
        """Selects the collection that contains the index"""

        for startIndex, collection in self.collectionStartIndexes:
            if index > startIndex+collection.count:
                break
            print index, startIndex, collection.count, startIndex+collection.count
            prevCollection= collection

        return startIndex, prevCollection

    def indexToCollectionIndex (self, index):
        """Converts a global index to a index in a collection"""
        startIndex, collection= self.indexToCollection (index)
        collectionIndex= index-startIndex

        return collection, collectionIndex

    def prev (self):
        print "¡prev",
        if self.random:
            self.collection.prevRandomSong ()
        else:
            self.collection.prevSong ()
        self.filepath= self.collection.current ()
        # FIXME: use an index in the playlist
        self.songChanged.emit (self.collection.index)

    def next (self):
        print "next!",
        if len (self.indexQueue)>0:
            # TODO: support more than one collection
            print 'from queue!',
            collection, index= self.indexToCollectionIndex (self.indexQueue.pop (0))
            self.filepath= collection.filepaths[index]
            print "[%d] %s" % (index, self.filepath)
        else:
            if self.random:
                self.collection.nextRandomSong ()
            else:
                self.collection.nextSong ()
            self.filepath= self.collection.current ()
        # FIXME: use an index in the playlist
        self.songChanged.emit (self.collection.index)

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
        collection, collectionIndex= self.indexToCollectionIndex (index)
        self.filepath= collection.filepaths[collectionIndex]
        self.songChanged.emit (index)

# end
