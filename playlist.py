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
from PyQt4.QtCore import pyqtSignal, QModelIndex

# dbus
import dbus.service

# std python
import random, bisect

# local
from common import SatyrObject, BUS_NAME, configBoolToBool
from primes import primes
from models import PlayListModel

class StopAfter (Exception):
    pass

class PlayList (SatyrObject):
    finished= pyqtSignal ()
    randomChanged= pyqtSignal (bool)
    songChanged= pyqtSignal (int)

    def __init__ (self, parent, collections, busName=None, busPath=None):
        SatyrObject.__init__ (self, parent, busName, busPath)

        self.model= PlayListModel (collections)
        self.collections= collections
        for collection in self.collections:
            collection.newSong.connect (self.model.addSong)
            collection.scanFinished.connect (self.filesAdded)

        self.indexQueue= []
        self.filepath= None

        self.configValues= (
            ('random', configBoolToBool, False),
            ('seed', int, 0),
            ('prime', int, -1),
            ('index', int, 0),
            )
        self.loadConfig ()

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def toggleRandom (self):
        """toggle"""
        print "toggle: random",
        self.random= not self.random
        print self.random
        self.randomChanged.emit (self.random)

    def setCurrent (self, song=None):
        if song is None:
            try:
                song= self.model.song (self.index)
                self.filepath= song.filepath
            except IndexError:
                # the index saved in the config is bigger than the current collection
                # fall back to 0
                self.index= 0
                song= self.model.song (self.index)
                self.filepath= song.filepath
        else:
            self.filepath= song.filepath
            # yes, this is O(n), but hookers!
            # FIXME: maybe we can get it from the modelIndex
            # (we're using it elsewhere anyways)
            # FIXME: this os O(n)
            # BUG: this is the Collection index, not the global one
            self.index= song.collection.songs.index (song)
        self.songChanged.emit (self.index)

    def prev (self):
        print "¡prev",
        if self.random:
            random= self.seed
            self.index= (self.index-random) % self.model.count
            random= (self.seed-self.prime) % self.model.count
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
                random= (self.seed+self.prime) % self.model.count
                self.index= (self.index+random) % self.model.count
                # print random, self.index
                self.seed= random
            else:
                self.index+= 1

        self.setCurrent ()

    def filesAdded (self):
        # we must recompute the prime
        if self.model.count>2:
            # if count is 1, it make no sense to select a prime
            # if it's 2, the prime selected would be 2
            # if you turn on random and hit next
            # you get the same song over and over again...
            self.prime= self.randomPrime ()
            print "prime selected:", self.prime
        else:
            # so instead we hadrcode it to 1
            self.prime= 1

        self.setCurrent ()

    def randomPrime (self):
        # select a random prime based on the amount of songs in the playlist
        top= bisect.bisect (primes, self.model.count)
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
        # print "searching %s" % searchSpec
        def predicate (s):
            foundAny= False
            for words in searchSpec.split ('+'):
                # print words
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
            songs+= [ song
                for song in collection.songs
                    if predicate (song.filepath.lower ()) ]

        # print songs
        return songs

    @dbus.service.method (BUS_NAME, in_signature='i', out_signature='')
    def jumpToIndex (self, index):
        # print 'jU..'
        self.index= index
        self.setCurrent ()
        # print 'Mp!'

    # we can't export this through dbus because it's a Song
    def jumpToSong (self, song):
        self.setCurrent (song)

# end
