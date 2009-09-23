# vim: set fileencoding=utf-8 :
# (c) 2009 Marcos Dione <mdione@grulic.org.ar>
# distributed under the terms of the GPLv2.1

# qt/kde related
from PyKDE4.kdecore import KStandardDirs
from PyQt4.QtCore import pyqtSignal

# dbus
import dbus.service

# std python
import random, bisect

# local
from common import SatyrObject, BUS_NAME, configBoolToBool
from primes import primes

class StopAfter (Exception):
    pass

class PlayList (SatyrObject):
    finished= pyqtSignal ()
    randomChanged= pyqtSignal (bool)
    songChanged= pyqtSignal (int)

    def __init__ (self, parent, collections, busName=None, busPath=None):
        SatyrObject.__init__ (self, parent, busName, busPath)

        print collections
        self.collections= collections
        for collection in self.collections:
            collection.filesAdded.connect (self.filesAdded)
        # FIXME: fix search to get rid of this
        self.collection= self.collections[0]

        self.indexQueue= []
        self.filepath= None
        self.count= 0

        self.configValues= (
            ('random', configBoolToBool, False),
            ('seed', int, 0),
            ('prime', int, -1),
            ('index', int, -1),
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
            random= self.seed
            self.index= (self.index-random) % self.count
            random= (self.seed-self.prime) % self.count
            # print random, self.index
            self.seed= random
        else:
            self.index-= 1

        collection, collectionIndex= self.indexToCollectionIndex (self.index)
        self.filepath= collection.filepaths[collectionIndex]
        print "[%d] %s" % (self.index, self.filepath)
        self.songChanged.emit (self.index)

    def next (self):
        print "next!",
        if len (self.indexQueue)>0:
            print 'from queue!',
            self.index= self.indexQueue.pop (0)
        else:
            if self.random:
                # TODO: FIX this ugliness
                if self.index==-1:
                    # HACK: ugly
                    random= 1
                else:
                    random= (self.seed+self.prime) % self.count
                self.index= (self.index+random) % self.count
                # print random, self.index
                self.seed= random
            else:
                self.index+= 1

        collection, collectionIndex= self.indexToCollectionIndex (self.index)
        self.filepath= collection.filepaths[collectionIndex]
        print "[%d] %s" % (self.index, self.filepath)
        self.songChanged.emit (self.index)

    def filesAdded (self):
        # recalculate the count and the startIndexes
        # HINT: yes, self.count==startIndex, but the semantic is different
        # otherwise the update of startIndexes will not be so clear
        self.count= 0
        startIndex= 0
        self.collectionStartIndexes= []

        for collection in self.collections:
            self.collectionStartIndexes.append ((startIndex, self.collections[0]))
            startIndex+= collection.count
            self.count+= collection.count
        print "count:", self.count

        # we must recompute the prime too
        if self.count>0:
            self.prime= self.randomPrime ()
            print "prime selected:", self.prime

    def randomPrime (self):
        # select a random prime based on the amount of songs in the playlist
        top= bisect.bisect (primes, self.count)
        # select from the upper 2/3,
        # so in large playlists the same artist is not picked consecutively
        prime= random.choice (primes[top/3:top])

        return prime

    @dbus.service.method (BUS_NAME, in_signature='i', out_signature='')
    def queue (self, collectionIndex):
        try:
            listIndex= self.indexQueue.index (collectionIndex)
            # exists; dequeue
            # print 'dequeuing index [%d, %d] %s' % (listIndex, collectionIndex, self.collection.filepaths[collectionIndex])
            print 'dequeuing index [%d, %d]' % (listIndex, collectionIndex)
            self.indexQueue.pop (listIndex)
        except ValueError:
            # doesn't exist; append
            # print 'queuing [%d] %s' % (collectionIndex, self.collection.filepaths[collectionIndex])
            print 'queuing [%d]' % (collectionIndex)
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
        self.index= index
        self.songChanged.emit (self.index)

# end
