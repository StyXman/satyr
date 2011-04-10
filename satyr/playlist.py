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
from PyQt4.QtCore import pyqtSignal, QModelIndex, QStringList

# dbus
import dbus.service

# std python
import random, bisect, collections

# local
from satyr.common import SatyrObject, BUS_NAME, configEntryToBool, configEntryToIntList
from satyr.primes import primes
from satyr.collaggr import CollectionAggregator

class StopAfter (Exception):
    pass

class PlayList (SatyrObject):
    # TODO: get rid of primes, use normal random and a bounded list
    finished= pyqtSignal ()
    randomChanged= pyqtSignal (bool)
    # songChanged= pyqtSignal (int)
    songChanged= pyqtSignal (str)
    queued= pyqtSignal (int)
    dequeued= pyqtSignal (int)

    def __init__ (self, parent, collaggr, busName=None, busPath=None):
        SatyrObject.__init__ (self, parent, busName, busPath)

        self.collaggr= collaggr
        self.collections= collaggr.collections
        for collection in self.collections:
            collection.scanFinished.connect (self.filesAdded)

        self.songQueue= []
        # TODO: save this?
        # self.played= collections.deque (100)
        self.song= None
        self.filepath= None

        self.configValues= (
            ('random', configEntryToBool, False),
            ('seed', int, 0),
            ('prime', int, -1),
            # TODO: make the current song to be savable again
            # ('index', int, 0),
            ('filepath', str, None)
            # ('indexQueue', configEntryToIntList, QStringList ())
            # TODO: make songQueue to be saved again
            # ('songQueue', configEntryToIntList, QStringList ())
            )
        self.loadConfig ()

        # TODO: config
        # TODO: optional parts
        # TODO: unify unicode/str
        # ** DO NOT REMOVE ** we're still using it for setting the window title
        self.format= u"%(artist)s/%(year)s-%(album)s: %(trackno)s - %(title)s [%(length)s]"
        # this must NOT be unicode, 'cause the filepaths might have any vegetable
        self.altFormat= "%(filepath)s [%(length)s]"

        # BUG: loading for the first time
        # File "/home/mdione/src/projects/satyr/playlist-listmodel/models.py", line 180, in songForIndex
        #     song= collection.songs[collectionIndex]
        # IndexError: list index out of range
        self.setCurrent ()

    # ** DO NOT REMOVE ** we're still using it for setting the window title
    def formatSong (self, song):
        if song.metadataNotNull ():
            formatted= self.format % song
        else:
            # I choose latin1 because it's the only one I know
            # which is full 256 chars
            # FIXME: I think (this is not needed|we're not in kansas) anymore
            # or in any case trying with the system's encoding first shoud give better results
            try:
                s= (self.altFormat % song).decode ('latin1')
            except UnicodeDecodeError:
                print song.filepath
                fp= song.filepath.decode ('iso-8859-1')
                s= u"%s [%s]" % (fp, song.length)

            formatted= s

        return formatted

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='')
    def toggleRandom (self):
        """toggle"""
        print "toggle: random",
        self.random= not self.random
        print self.random
        self.randomChanged.emit (self.random)

    def setCurrent (self, song=None):
        print "playlist.setCurrent()", song
        if song is not None:
            # self.index= self.collaggr.indexForSong (song)
            self.song= song
            self.filepath= song.filepath
        else:
            # take the current from saved status
            print "playlist.setCurrent()", self.filepath
            # self.song= self.collaggr.songForIndex (self.index)
            if self.filepath is None:
                # none saved, use first
                self.song= self.collaggr.songForIndex (0)
                self.filepath= self.song.filepath
            else:
                song= self.collaggr.songForFilepath (self.filepath)
                if song is not None:
                    self.song= song
                else:
                    # sorry, we don't have that song anymore
                    self.song= self.collaggr.songForIndex (0)
                    self.filepath= self.song.filepath

        # we cannot emit the song because Qt (and I don't mean PyQt4 here)
        # knows nothing about it, so (with the help of, yes this time, PyQt4)
        # it basically emits its id(), which is useless
        # self.songChanged.emit (self.index)
        self.songChanged.emit (self.filepath)

    def prev (self):
        print "¡prev",
        if self.random:
            # random= self.seed
            # self.index= (self.index-random) % self.collaggr.count
            # random= (self.seed-self.prime) % self.collaggr.count
            # self.seed= random
            # TODO: implement played
            index= random.randint (0, self.collaggr.count)
            song= self.collaggr.songForIndex (index)
        else:
            # self.index= (self.index-1) % self.collaggr.count
            song= self.collaggr.prev (self.song)

        self.setCurrent (song)

    def next (self):
        print "next!",
        song= None
        if len (self.songQueue)>0:
            print 'from queue!',
            # BUG: this is destructive, so we can't go back properly
            # TODO: also, users want semi-ephemeral queues
            # self.index= self.indexQueue.pop (0)
            song= self.songQueue.pop (0)
        else:
            if self.random:
                # random= (self.seed+self.prime) % self.collaggr.count
                # self.index= (self.index+random) % self.collaggr.count
                # self.seed= random
                index= random.randint (0, self.collaggr.count)
                song= self.collaggr.songForIndex (index)
            else:
                # self.index= (self.index+1) % self.collaggr.count
                song= self.collaggr.next (self.song)

        # self.lastPlayed.append ()
        self.setCurrent (song)

    def filesAdded (self):
        # we must recompute the prime
        if self.collaggr.count>2:
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
        top= bisect.bisect (primes, self.collaggr.count)
        # select from the upper 2/3,
        # so in large playlists the same artist is not picked consecutively
        prime= random.choice (primes[top/3:top])

        return prime

    # TODO: reenable this dbus method?
    # @dbus.service.method (BUS_NAME, in_signature='i', out_signature='')
    # def queue (self, collectionIndex):
    def queue (self, collectionIndex, song):
        # song= self.collaggr.songForIndex (collectionIndex)
        try:
            listIndex= self.songQueue.index (song)
            # exists; dequeue
            print 'PL.queue(): dequeuing [%d, %s]' % (listIndex, song)
            self.songQueue.pop (listIndex)
            self.dequeued.emit (collectionIndex)
        except ValueError:
            # doesn't exist; append
            print 'PL.queue(): queuing [%s]' % (song)
            self.songQueue.append (song)
            self.queued.emit (collectionIndex)

    @dbus.service.method (BUS_NAME, in_signature='s', out_signature='a(is)')
    def search (self, searchSpec):
        # encode to utf-8, so we can match str against str
        searchSpec= searchSpec.encode ('utf-8')
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
            songs+= [ song
                for song in collection.songs
                    if predicate (song.filepath.lower ()) ]

        return songs

# end
