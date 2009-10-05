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
from PyQt4.QtCore import QObject
# from PyQt4.phonon import Phonon
# QAbstractItemModel for when we can model albums and group them that way
from PyQt4.QtCore import QAbstractListModel, QModelIndex, QVariant, Qt
# QAbstractTableModel if we ever change to a table
from PyQt4.QtCore import QAbstractTableModel

# std python
# import traceback

# other libs
from kaa import metadata

class PlayListTableModel (QAbstractTableModel):
    """Do not use until finished"""
    def __init__ (self, collection, parent= None):
        QAbstractListModel.__init__ (self, parent)
        self.songs= []
        self.lastIndex= 0
        self.count= 0
        # FIXME? hardcoded
        self.attrNames= ('index', 'artist', 'album', 'trackno', 'title', 'length', 'filepath')

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
    def __init__ (self, songs=None, parent= None):
        QAbstractListModel.__init__ (self, parent)
        if songs is None:
            self.songs= []
            self.lastIndex= 0
            self.count= 0
        else:
            self.songs= songs
            self.lastIndex= self.count= len (songs)
        # print self.songs

        # self.attrNames= ('index', 'artist', 'album', 'trackno', 'title', 'length', 'filepath')
        # HINT: attrs from kaa-metadata are all strings
        # TODO: config
        # TODO: optional parts
        self.format= "[%(index)d] %(artist)s/%(album)s: %(trackno)s - %(title)s [%(length)s]"
        self.altFormat= "%(filepath)s [%(length)s]"

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

    def data (self, index, role):
        if not index.isValid ():
            return QVariant ()

        elif index.row ()>=self.count:
            return QVariant ()

        elif role==Qt.DisplayRole:
            song= self.songs[index.row ()]
            # print song
            if song.metadataNotNull ():
                return QVariant (self.format % song)
            else:
                return QVariant (self.altFormat % song)
        else:
            return QVariant ()

    def addSong (self, filepath):
        # convert QString to unicode
        filepath= unicode (filepath)
        row= index= self.lastIndex
        self.lastIndex+= 1

        self.beginInsertRows (QModelIndex (), row, row)
        self.songs.append (SongModel (index, filepath))
        self.endInsertRows ()

        # again, I know that count and lastIndex are equal,
        # but again, it's better for the intiutive semantics of the code
        # (readability, they call it)
        self.count+= 1

        modelIndex= self.index (row, 0)
        self.dataChanged.emit (modelIndex, modelIndex)

    def rowCount (self, parent=None):
        return self.count


class SongModel (QObject):
    def __init__ (self, index, filepath, onDemand=True):
        # sigsegv :(
        # KCrash: Application 'satyr.py' crashing...
        # sock_file=/home/mdione/.kde/socket-mustang/kdeinit4__0
        # satyr.py: Fatal IO error: client killed
        # ms= Phonon.MediaSource (filepath)
        # mo= Phonon.MediaObject ()
        # mo.setCurrentSource (ms)
        # print mo.metadata ()

        self.loaded= False
        self.index= index
        self.filepath= filepath
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
        # traceback.print_stack ()
        try:
            info= metadata.parse (self.filepath)
            # print info.artist, info.album, info.trackno, info.title
        except Exception, e:
            print self.filepath
            print e
            print '-----'

        for attr in ('artist', 'album', 'trackno', 'title', 'length'):
            setattr (self, attr, getattr (info, attr, None))
        self.length= self.formatSeconds (self.length)
        self.loaded= True

    # dict iface so we can simply % it to a pattern
    def __getitem__ (self, key):
        if not self.loaded:
            self.loadMetadata ()
        return getattr (self, key)

    def metadataNotNull (self):
        if not self.loaded:
            self.loadMetadata ()

        # we could do it more complex, but I think this is enough
        return self.title is not None

# end
