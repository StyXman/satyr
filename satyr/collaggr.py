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
from PyQt4.QtCore import QSignalMapper, QStringList

# local
from satyr.common import SatyrObject, BUS_NAME
# from satyr.collection import Collection
from satyr import utils

class CollectionAggregator (SatyrObject):
    def __init__ (self, parent, songs=None, busName=None, busPath=None):
        SatyrObject.__init__ (self, parent, busName, busPath)

        self.configValues= (
            # ('collsNo', int, 0),
            ('collTypes', list, list ()), # TBFixed with the merge of work from branch lastplayed
            )
        self.loadConfig ()
        self.collsNo= len (self.collTypes)

        self.signalMapper= QSignalMapper ()
        self.collections= []

        if songs is None:
            self.songs= []
            self.count= 0
        else:
            self.songs= songs
            self.count= len (songs)

        # if collections is not None we it means the may have changed
        if self.collsNo>0:
            for index, module in enumerate (self.collTypes):
                print "CollectionAggregator(): ", index, module
                try:
                    mod= utils.import_ (str (module))
                except ImportError:
                    print "no support for %s, skipping collection" % module
                else:
                    collection= mod.Collection (self, busName=busName, busPath="/collection_%04d" % index)
                    print "CollectionAggregator(): %s" % collection
                    self.append (collection)

        self.signalMapper.mapped.connect (self.addSongs)

    def append (self, collection, collType=None):
        print "adding collection", collection
        collection.loadOrScan ()
        self.collections.append (collection)
        self.collsNo= len (self.collections)
        if collType is not None:
            self.collTypes.append (collType)
        
        index= len (self.collections)-1
        collection.newSongs.connect (self.signalMapper.map)
        self.signalMapper.setMapping (collection, index)
        collection.scanFinished.connect (self.updateIndexes)
        self.updateIndexes ()

    def indexToCollection (self, index):
        """Selects the collection that contains the index"""
        prevCollection= self.collections[0]
        for collection in self.collections[1:]:
            # print index, collection.offset
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
            collection= song.coll
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
