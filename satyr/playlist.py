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
import bisect
from collections import deque
from random import randint

# local
from satyr.common import SatyrObject, BUS_NAME, ConfigEntry
from satyr.collaggr import CollectionAggregator

class StopAfter (Exception):
    pass

class PlayList (SatyrObject):
    # TODO: get rid of primes, use normal random and a bounded list
    finished= pyqtSignal ()
    randomChanged= pyqtSignal (bool)
    songChanged= pyqtSignal (int)
    queued= pyqtSignal (int)
    dequeued= pyqtSignal (int)

    def __init__ (self, parent, collaggr, busName=None, busPath=None):
        SatyrObject.__init__ (self, parent, busName, busPath)

        self.collaggr= collaggr
        self.collections= collaggr.collections
        for collection in self.collections:
            collection.scanFinished.connect (self.filesAdded)

        self.song= None
        self.filepath= None

        self.configValues= (
            ConfigEntry ('random', bool, False),
            ConfigEntry ('index', int, 0),
            ConfigEntry ('shrinkPlayed', bool, True),
            ConfigEntry ('played', deque, deque ([], 100)),
            ConfigEntry ('playedIndex', int, -1),
            ConfigEntry ('indexQueue', list, [], subtype=int)
            )
        self.loadConfig ()
        print self.played, self.playedIndex

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
        if song is None:
            try:
                print "playlist.setCurrent()", self.index
                self.song= self.collaggr.songForIndex (self.index)
                self.filepath= self.song.filepath
            # IndexError when we're out of bounds, TypeError when index is None
            except (IndexError, TypeError):
                # the index saved in the config is bigger than the current collection
                # fall back to 0
                try:
                    self.index= 0
                    self.song= self.collaggr.songForIndex (self.index)
                    self.filepath= self.song.filepath
                except IndexError:
                    # we cannot even select the first song
                    # which means there are no songs
                    self.index= None
                    self.song= None
                    self.filepath= None
        else:
            print "playlist.setCurrent()", song
            self.song= song
            self.filepath= song.filepath
            self.index= self.collaggr.indexForSong (song)
            print "playlist.setCurrent()", self.index

        # we cannot emit the song because Qt (and I don't mean PyQt4 here)
        # knows nothing about it, so (with the help of, yes this time, PyQt4)
        # it basically emits its id(), which is useless
        self.songChanged.emit (self.index)

    def prev (self):
        print "¡prev", self.playedIndex, self.played,
        # HINT: yes, they might be equivalent,
        # but I keep them for clarity's sake
        if len (self.played)==0 or self.playedIndex==0:
            if self.random:
                print 'random'
                self.index= randint (0, self.collaggr.count-1)
            else:
                print 'sequential'
                self.index-= 1

            # append and appendleft are equivalent here
            # but appendleft is conceptualy more accurate
            self.played.appendleft (self.index)
            self.playedIndex= 0
        else:
            # HINT: this has an ugly collateral damage
            # when switching from random to sequential and then hitting prev
            # the song is picked from the played list and does not select
            # the song sequentially previous in the collection
            print 'from played'
            if self.shrinkPlayed:
                self.played.pop ()
            self.playedIndex-= 1
            self.index= self.played[self.playedIndex]

        print "¡prev", self.playedIndex, self.played,
        self.song= self.collaggr.songForIndex (self.index)
        self.setCurrent ()

    def next (self):
        print "next!", self.playedIndex, self.played,
        if self.playedIndex==len (self.played)-1:
            if len (self.indexQueue)>0:
                print 'from queue!',
                # BUG: this is destructive, so we can't go back properly
                # TODO: also, users want semi-ephemeral queues
                self.index= self.indexQueue.pop (0)
            elif self.random:
                print 'random'
                self.index= randint (0, self.collaggr.count-1)
            else:
                print 'sequential'
                self.index+= 1

            self.played.append (self.index)
            self.playedIndex+= 1
        else:
            # HINT: this has an ugly collateral damage
            # when switching from random to sequential and then hitting prev
            # the song is picked from the played list and does not select
            # the song sequentially previous in the collection
            print 'from played'
            self.playedIndex+= 1
            self.index= self.played[self.playedIndex]

        print "next!", self.playedIndex, self.played
        self.song= self.collaggr.songForIndex (self.index)
        self.setCurrent ()

    def filesAdded (self):
        self.setCurrent ()

    @dbus.service.method (BUS_NAME, in_signature='i', out_signature='')
    def queue (self, collectionIndex):
        try:
            listIndex= self.indexQueue.index (collectionIndex)
            # exists; dequeue
            print 'PL.queue(): dequeuing index [%d, %d]' % (listIndex, collectionIndex)
            self.indexQueue.pop (listIndex)
            self.dequeued.emit (collectionIndex)
        except ValueError:
            # doesn't exist; append
            print 'PL.queue(): queuing [%d]' % (collectionIndex)
            self.indexQueue.append (collectionIndex)
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

    @dbus.service.method (BUS_NAME, in_signature='i', out_signature='')
    def jumpToIndex (self, index):
        # print 'jU..'
        print "playlist.jumpToIndex()", index
        self.index= index
        self.setCurrent ()
        # print 'Mp!'

    # we can't export this through dbus because it's a Song
    def jumpToSong (self, song):
        self.setCurrent (song)

# end
