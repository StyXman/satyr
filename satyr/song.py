# vim: set fileencoding=utf-8 :
# (c) 2009, 2010 Marcos Dione <mdione@grulic.org.ar>

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
from PyQt4.QtCore import QObject, pyqtSignal

# other libs
import types

# local
import utils

class TagWriteError (Exception):
    pass

class Song (QObject):
    # TODO: do not return int's for year or track?
    # no, we need them as int's so we can %02d
    # updated?
    metadadaChanged= pyqtSignal ()

    def __init__ (self, collection, filepath, onDemand=True, va=False, ro=False):
        QObject.__init__ (self)
        if not isinstance (filepath, str):
            print filepath, "is a", type (filepath), "!"
            traceback.print_stack ()
        self.loaded= False
        self.dirty= False
        self.coll= collection
        self.filepath= filepath
        self.variousArtists= va
        self.readOnly= ro

        if not self.variousArtists:
            self.cmpOrder= ('artist', 'year', 'collection', 'diskno', 'album', 'trackno', 'title', 'length')
        else:
            # note that the year is not used in this case!
            self.cmpOrder= ('album', 'trackno', 'title', 'artist', 'length')

        if not onDemand:
            self.loadMetadata ()

    def formatSeconds (self, seconds):
        """convert length from seconds to mm:ss"""
        if seconds is not None:
            return utils.secondsToTime (float (seconds))
        else:
            return "???"

    def sanitize (self, attr, value):
        value= value.strip ()
        if attr=='diskno':
            # print "Song.sanitize():", value
            # sometimes it's stored as x/N
            pos= value.find ('/')
            if pos>-1:
                value= value[:pos]
            # print "Song.sanitize():", value
            if value!='':
                value= int (value)
            else:
                value= 0

        # print "Song.sanitize():", value
        return value

    def __getitem__ (self, key):
        """dict iface so we can simply % it to a pattern"""
        if not self.loaded:
            self.loadMetadata ()
        val= getattr (self, key)

        if key=='length':
            val= self.formatSeconds (val)
        
        # if it's, then a) it's either year or trackno; b) leave it empty
        if val==0:
            val= ''

        return val

    def __setitem__ (self, key, value):
        if not self.readOnly:
            """dict iface so we don't have to make special case in __setattr__()"""

            # these two must be int()s
            if key in ('diskno', 'trackno', 'year'):
                print "converting from %s to int for %s" % (type (value), key)
                try:
                    value= int (value)
                except ValueError:
                    value= 0

            # we cache; otherwise we could set loaded to False
            # and let other functions to resolve it.
            try:
                print "__setitem__():", key, value
                setattr (self, key, value)
            except AttributeError:
                raise TagWriteError

            self.dirty= True
        # else
            # raise TagWriteError

    def rollbackMetadata (self):
        if not self.readOnly:
            # let the Song reload the metadata from the file
            self.loaded= False
            self.dirty= False

    def __cmp__ (self, other):
        # I don't want to implement the myriad of rich comparison
        ans= cmp (self.filepath, other.filepath)
        # don't load metadata on any comparison
        # this would force it very soon at boot time
        # so use the only reasonable thing: the filepath
        # and only do it if the paths are different
        if ans!=0 and self.loaded and other.loaded:
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

    def relPath (self):
        return self.filepath[len (self.coll.path)+1:]

# end
