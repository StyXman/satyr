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
from PyQt4.QtCore import QObject, pyqtSignal, QSignalMapper

# other libs
import tagpy

class CollectionAgregator (object):
    def __init__ (self, collections= None, songs=None):
        object.__init__ (self)

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
        self.collectionStartIndexes= []
        for collNo, collection in enumerate (self.collections):
            collection.newSongs.connect (self.signalMapper.map)
            self.signalMapper.setMapping (collection, collNo)
            collection.scanFinished.connect (self.updateIndexes)

        self.signalMapper.mapped.connect (self.addSongs)
        self.updateIndexes ()

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

    def songForIndex (self, index):
        if len (self.songs)==0:
            # we're not a queue PLM, so we use the collections
            collection, collectionIndex= self.indexToCollectionIndex (index)
            # print collection, collectionIndex, len (collection.songs)
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
            for startIndex, collection in self.collectionStartIndexes:
                collectionIndex= collection.indexForSong (song)
                if collectionIndex is not None:
                    index= startIndex+collectionIndex

        return index

    def addSongs (self, collNo):
        # sender= QObject.sender ()
        # print sender
        collection= self.collections[collNo]
        # BUG? shouldn't we call updateIndexes?
        # HINT: we call it when scanFinished()
        self.count+= len (collection.newSongs_)

    def updateIndexes (self):
        # recalculate the count and the startIndexes
        # only if we don't hols the songs ourselves
        if len (self.songs)==0:
            # HINT: yes, self.count==startIndex, but the semantic is different
            # otherwise the update of startIndexes will not be so clear
            self.count= 0
            startIndex= 0
            self.collectionStartIndexes= []

            for collection in self.collections:
                self.collectionStartIndexes.append ((startIndex, collection))
                startIndex+= collection.count
                self.count+= collection.count

        print "PLM: count:", self.count


class Song (QObject):
    def __init__ (self, collection, filepath, onDemand=True, va=False):
        if not isinstance (filepath, str):
            print filepath, "is a", type (filepath), "!"
            traceback.print_stack ()
        self.loaded= False
        self.collection= collection
        self.filepath= filepath
        self.variousArtists= va
        if not self.variousArtists:
            self.cmpOrder= ('artist', 'year', 'album', 'trackno', 'title', 'length')
        else:
            # note that the year is not used in this case!
            self.cmpOrder= ('album', 'trackno', 'title', 'artist', 'length')

        if not onDemand:
            self.loadMetadata ()

    def formatSeconds (self, seconds):
        """convert length from seconds to mm:ss"""
        if seconds is not None:
            s= float (seconds)
            seconds= int (s) % 60
            minutes= int (s) / 60
            return "%02d:%02d" % (minutes, seconds)
        else:
            return "???"

    def loadMetadata (self):
        try:
            # tagpy doesn't handle unicode filepaths (somehow makes sense)
            fr= tagpy.FileRef (self.filepath)

            props= fr.audioProperties ()
            # incredibly enough, tagpy also express lenght as a astring
            # even when taglib uses an int (?!?)
            self.length= self.formatSeconds (props.length)

            info= fr.tag ()
        except Exception, e:
            print '----- loadMetadata()'
            print self.filepath
            print e
            print '----- loadMetadata()'
            self.length= 0
            # we must define info so getattr() works
            info= None

        # tagpy presents trackno as track, so we map them
        # no, I don't want to change everything to match this
        for tag, attr in zip (
                ('artist', 'year', 'album', 'track',   'title'),
                ('artist', 'year', 'album', 'trackno', 'title')):
            datum= getattr (info, tag, None)
            if isinstance (datum, basestring):
                datum= datum.strip ()
            setattr (self, attr, datum)

        self.loaded= True

    def __getitem__ (self, key):
        """dict iface so we can simply % it to a pattern"""
        # print self.filepath, key,
        if not self.loaded:
            self.loadMetadata ()
        val= getattr (self, key)
        # print val
        return val

    def metadataNotNull (self):
        if not self.loaded:
            self.loadMetadata ()

        # we could do it more complex, but I think this is enough
        # tagpy returns u'' or 0 instead of not defining the attr at all
        # so we see that indeed it reurns unicode. see comment in loadMetadata()
        return (self.title is not None and self.title!=u'')

    def __cmp__ (self, other):
        # I don't want to implement the myriad of rich comparison
        if not self.loaded:
            # don't load metadata on any comparison
            # this would force it very soon at boot time
            # so use the only reasonable thing: the filepath
            ans= cmp (self.filepath, other.filepath)
        elif not other.loaded:
            # (is this a) BUG?
            print '===== cmp()'
            print other.filepath
            print '===== cmp()'
            # this is not so much a lie as a decision
            ans= -1
        else:
            try:
                for attr1, attr2 in zip (self.cmpOrder, other.cmpOrder):
                    val1= getattr (self, attr1)
                    val2= getattr (other, attr2)
                    ans= cmp (val1, val2)
                    if ans!=0:
                        break

            except Exception, e:
                print '----- cmp()'
                print self.filepath
                print e
                print '----- cmp()'
                # any lie is good as any
                ans= -1

        return ans

    def __repr__ (self):
        return "Song: "+self.filepath

# end
