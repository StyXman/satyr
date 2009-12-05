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
from PyQt4.QtCore import QObject, QSignalMapper

class CollectionAggregator (QObject):
    def __init__ (self, collections= None, songs=None):
        QObject.__init__ (self)

        if collections is None:
            collections= []
        self.collections= collections

        if songs is None:
            self.songs= []
            self.count= 0
        else:
            self.songs= songs
            self.count= len (songs)

        self.signalMapper= QSignalMapper ()
        for collNo, collection in enumerate (self.collections):
            collection.newSongs.connect (self.signalMapper.map)
            self.signalMapper.setMapping (collection, collNo)
            collection.scanFinished.connect (self.updateIndexes)

        self.signalMapper.mapped.connect (self.addSongs)
        self.updateIndexes ()

    def indexToCollection (self, index):
        """Selects the collection that contains the index"""
        for collection in self.collections:
            if index < collection.offset:
                break
            prevCollection= collection

        return prevCollection

    def indexToCollectionIndex (self, index):
        """Converts a global index to a index in a collection"""
        collection= self.indexToCollection (index)
        collectionIndex= index-collection.offset

        return collection, collectionIndex

    def songForIndex (self, index):
        if len (self.songs)==0:
            # we're not a queue PLM, so we use the collections
            collection, collectionIndex= self.indexToCollectionIndex (index)
            song= collection.songs[collectionIndex]
        else:
            song= self.songs[index]

        return song

    def indexForSong (self, song):
        print "PLM.indexForSong", song
        index= None
        if len (self.songs)>0:
            index= self.songs.index (song)
        else:
            collection= song.collection
            collectionIndex= collection.indexForSong (song)
            if collectionIndex is not None:
                index= collection.offset+collectionIndex

        return index

    def addSongs (self, collNo):
        collection= self.collections[collNo]
        # BUG? shouldn't we call updateIndexes?
        # HINT: we call it when scanFinished()
        self.count+= len (collection.newSongs_)

    def updateIndexes (self):
        # recalculate the count and the offsets
        # only if we don't hols the songs ourselves
        if len (self.songs)==0:
            # HINT: yes, self.count==offset, but the semantic is different
            # otherwise the update of offsets will not be so clear
            self.count= 0
            offset= 0

            for collection in self.collections:
                collection.offset= offset
                offset+= collection.count
                self.count+= collection.count

        print "PLM: count:", self.count

# end
