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
from PyKDE4.kdeui import KGlobalSettings
from PyQt4.QtCore import QObject
# from PyQt4.phonon import Phonon
# QAbstractItemModel for when we can model albums and group them that way
from PyQt4.QtCore import QAbstractListModel, QModelIndex, QVariant, Qt
# QAbstractTableModel if we ever change to a table
from PyQt4.QtCore import QAbstractTableModel
from PyQt4.QtGui import QFontMetrics

# std python
import traceback

# other libs
# from kaa import metadata
import tagpy

class PlayListTableModel (QAbstractTableModel):
    """Do not use until finished"""
    def __init__ (self, collection, parent= None):
        QAbstractListModel.__init__ (self, parent)
        self.songs= []
        self.lastIndex= 0
        self.count= 0
        # FIXME? hardcoded
        self.attrNames= ('index', 'artist', 'year', 'album', 'trackno', 'title', 'length', 'filepath')

    def data (self, index, role):
        if not index.isValid ():
            return QVariant ()

        if index.row ()>=self.count:
            return QVariant ()

        if role==Qt.DisplayRole:
            # this defines the order of the data
            attrName= [index.column ()]
            data= getattr (self.songs[index.row ()], attrName, None)
            return QVariant (data)
        else:
            return QVariant ()

    #def insertRow (self, row, count, parent=None):
        #if parent is None:
            #parent= QModelIndex ()

        #if count<1 or row<0 or row>self.rowCount(parent):
            #return False

        #for (int r = 0; r < count; ++r)
            #lst.insert(row, QString());

        #return true;

    def addSong (self, filepath):
        row= index= self.lastIndex
        self.lastIndex+= 1

        self.beginInsertRows (QModelIndex (), row, row)
        self.songs.append (SongModel (index, filepath))
        self.endInsertRows ();

        # again, I know that count and lastIndex are equal,
        # but again, it's better for the intiutive semantics of the code
        # (readability, they call it)
        self.count+= 1

        # FIXME? this sucks?
        for column in xrange (7):
            modelIndex= self.index (row, column)
            self.dataChanged.emit (modelIndex, modelIndex)

    def rowCount (self, parent=None):
        return self.count

    def columnCount (self, parent=None):
        return len (self.attrNames)

    def headerData (self, section, orientation, role=Qt.DisplayRole):
        if orientation==Qt.Horizontal:
            return self.attrNames[section]
        else:
            return section


class PlayListModel (QAbstractListModel):
    def __init__ (self, collections= None, songs=None, parent= None):
        QAbstractListModel.__init__ (self, parent)

        if collections is None:
            collections= []
        self.collections= collections

        # print songs
        if songs is None:
            self.songs= []
            self.lastIndex= 0
            self.count= 0
        else:
            self.songs= songs
            self.lastIndex= self.count= len (songs)

        self.collectionStartIndexes= []
        for collection in self.collections:
            collection.scanFinished.connect (self.updateIndexes)
            # FIXME: this should be redundant
            collection.filesAdded.connect (self.updateIndexes)
        self.updateIndexes ()

        # self.attrNames= ('index', 'artist', 'year', 'album', 'trackno', 'title', 'length', 'filepath')
        # HINT: attrs from kaa-metadata are all strings
        # TODO: config
        # TODO: optional parts
        self.format= u"%(artist)s/%(year)s-%(album)s: %(trackno)s - %(title)s [%(length)s]"
        self.altFormat= u"%(filepath)s [%(length)s]"

        # FIXME: kinda hacky
        self.fontMetrics= QFontMetrics (KGlobalSettings.generalFont ())

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

    def formatSong (self, song):
        if song.metadataNotNull ():
            formatted= self.format % song
        else:
            formatted= self.altFormat % song

        return formatted

    def song (self, index):
        if len (self.songs)==0:
            collection, collectionIndex= self.indexToCollectionIndex (index)
            song= collection.songs[collectionIndex]
        else:
            song= self.songs[index]

        return song

    def data (self, modelIndex, role):
        song= self.song (modelIndex.row ())

        if not modelIndex.isValid ():
            data= QVariant ()
        elif modelIndex.row ()>=self.count:
            data= QVariant ()
        elif role==Qt.DisplayRole:
            # print song
            data= QVariant (self.formatSong (song))
        elif role==Qt.SizeHintRole:
            # calculate something based on the filepath
            data= QVariant (self.fontMetrics.size (Qt.TextSingleLine, song.filepath))
        else:
            data= QVariant ()

        return data

    def addSong (self):
        # convert QString to unicode
        # filepath= unicode (filepath)
        row= index= self.lastIndex
        self.lastIndex+= 1

        self.beginInsertRows (QModelIndex (), row, row)
        # self.songs.append ()
        self.endInsertRows ()

        # again, I know that count and lastIndex are equal,
        # but again, it's better for the intiutive semantics of the code
        # (readability, they call it)
        self.count+= 1

        modelIndex= self.index (row, 0)
        self.dataChanged.emit (modelIndex, modelIndex)

    def rowCount (self, parent=None):
        return self.count

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
        # self.index= index
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
            # print info.artist, info.album, info.trackno, info.title
            # print repr (info.title)
        except Exception, e:
            print self.filepath
            print e
            print '-----'
            # we must define info so getattr() works
            self.length= 0
            info= None

        # tagpy presents trackno as track, so we map them
        for tag, attr in zip (
                ('artist', 'year', 'album', 'track', 'title'),
                ('artist', 'year', 'album', 'trackno', 'title')):
            datum= getattr (info, tag, None)
            if isinstance (datum, basestring):
                datum= datum.strip ()
            setattr (self, attr, datum)

        self.loaded= True

    def __getitem__ (self, key):
        """dict iface so we can simply % it to a pattern"""
        if not self.loaded:
            self.loadMetadata ()
        return getattr (self, key)

    def metadataNotNull (self):
        if not self.loaded:
            self.loadMetadata ()

        # we could do it more complex, but I think this is enough
        # tagpy returns u'' or 0 instead of not defining the attr at all
        # so we see that indeed it reurns unicode. see comment in loadMetadata()
        return (self.title is not None or self.title!=u'')

    def __cmp__ (self, other):
        # I don't want to implement the myriad of rich comparison
        if not self.loaded:
            # don't load metadata on any comparison
            # this would force it very soon at boot time
            # so use the only reasonable thing: the filepath
            ans= cmp (self.filepath, other.filepath)
        else:
            try:
                for attr1, attr2 in zip (self.cmpOrder, other.cmpOrder):
                    val1= getattr (self, attr1)
                    val2= getattr (other, attr2)
                    ans= cmp (val1, val2)
                    if ans!=0:
                        break

            except Exception, e:
                print self.filepath
                print e
                print '-----'
                # any lie is good as any
                ans= -1

        return ans

# end
