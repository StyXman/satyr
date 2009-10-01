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
from PyQt4.QtCore import pyqtSignal
# QAbstractListModel
# QAbstractItemModel for when we can model albums and group them that way
from PyQt4.QtCore import QAbstractListModel, QModelIndex, QVariant, Qt

# dbus
import dbus.service

# std python
import random, bisect

# local
from common import SatyrObject, BUS_NAME, configBoolToBool
from primes import primes

class PlayListModel (QAbstractListModel):
    def __init__ (self, collection, parent= None):
        QAbstractListModel.__init__ (self, parent)
        self.songs= []

    def rowCount (self, index= QModelIndex ()):
        return len (self.songs)

    def data (self, index, role):
        if not index.isValid ():
            return QVariant ()

        if index.row ()>=len (self.songs.size):
            return QVariant ()

        if role==Qt.DisplayRole:
            return self.songs[index.row ()]
        else:
            return QVariant ()

    # def index (self, row, column, parent):

class StopAfter (Exception):
    pass

class PlayList (SatyrObject):
    finished= pyqtSignal ()
    randomChanged= pyqtSignal (bool)
    songChanged= pyqtSignal (int)

    def __init__ (self, parent, collections, busName=None, busPath=None):
        SatyrObject.__init__ (self, parent, busName, busPath)

        self.collections= collections
        for collection in self.collections:
            collection.scanFinished.connect (self.filesAdded)
            # FIXME: this should be redundant
            collection.filesAdded.connect (self.filesAdded)
        self.collectionStartIndexes= []

        # self.model= PlayListModel (self.collections)
        self.indexQueue= []
        self.filepath= None
        self.count= 0

        self.configValues= (
            ('random', configBoolToBool, False),
            ('seed', int, 0),
            ('prime', int, -1),
            ('index', int, 0),
            )
        self.loadConfig ()
        # self.setCurrent ()

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
            # FIXME: I still don't think this is right
            # if index > startIndex+collection.count:
            if index < startIndex:
                break
            # print index, startIndex, collection.count, startIndex+collection.count
            prevCollection= collection

        return startIndex, prevCollection

    def indexToCollectionIndex (self, index):
        """Converts a global index to a index in a collection"""
        startIndex, collection= self.indexToCollection (index)
        collectionIndex= index-startIndex

        return collection, collectionIndex

    def setCurrent (self):
        # BUG: this doesn't take into account changes in the collections sizes
        collection, collectionIndex= self.indexToCollectionIndex (self.index)
        # print self.index, collectionIndex, collection.count
        try:
            self.filepath= collection.filepaths[collectionIndex]
        except IndexError:
            # the index saved in the config is bigger than the current collection
            # fall back to 0
            self.index= 0
            self.filepath= self.collections.filepaths[0]
        # print "PL.setCurrent: [%d] %s" % (self.index, self.filepath)
        self.songChanged.emit (self.index)

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

        self.setCurrent ()

    def next (self):
        print "next!",
        if len (self.indexQueue)>0:
            print 'from queue!',
            self.index= self.indexQueue.pop (0)
        else:
            if self.random:
                random= (self.seed+self.prime) % self.count
                self.index= (self.index+random) % self.count
                # print random, self.index
                self.seed= random
            else:
                self.index+= 1

        self.setCurrent ()

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

        self.setCurrent ()

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
    def search (self, searchSpec):
        # print "searching %s" % words
        def predicate (s):
            foundAny= False
            for words in searchSpec.split ('+'):
                if words=='':
                    # the first or last char is +, so the words at its right is ''
                    foundWords= False
                else:
                    foundWords= True
                    wordList= words.lower ().split ()
                    for word in wordList:
                        foundWords= foundWords and word in s
                foundAny= foundAny or foundWords
            return foundAny

        songs= []
        for collection in self.collections:
            songs+= [ (index, path)
                for (index, path) in enumerate (collection.filepaths)
                    if predicate (path.lower ()) ]

        return songs

    @dbus.service.method (BUS_NAME, in_signature='i', out_signature='')
    def jumpTo (self, index):
        # print 'jU..'
        self.index= index
        self.setCurrent ()
        # print 'Mp!'

# end
