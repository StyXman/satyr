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
from PyQt4.QtCore import QObject, pyqtSignal

# other libs
import tagpy
# import Boost.Python

class TagWriteError (Exception):
    pass

class Song (QObject):
    metadadaChanged= pyqtSignal ()

    def __init__ (self, collection, filepath, onDemand=True, va=False):
        QObject.__init__ (self)
        if not isinstance (filepath, str):
            print filepath, "is a", type (filepath), "!"
            traceback.print_stack ()
        self.loaded= False
        self.dirty= False
        self.collection= collection
        self.filepath= filepath

        self.variousArtists= va
        if not self.variousArtists:
            self.cmpOrder= ('artist', 'year', 'album', 'trackno', 'title', 'length')
        else:
            # note that the year is not used in this case!
            self.cmpOrder= ('album', 'trackno', 'title', 'artist', 'length')

        # tagpy presents trackno as track, so we map them
        # no, I don't want to change everything to match this
        self.tagForAttr= dict (artist='artist', year='year', album='album', trackno='track', title='title')

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
            # we cannot keep the FileRef or the Tag because the file stays open.
            fr= tagpy.FileRef (self.filepath)

            props= fr.audioProperties ()
            # incredibly enough, tagpy also express lenght as a astring
            # even when taglib uses an int (?!?)
            self.length= self.formatSeconds (props.length)

            info= fr.tag ()
        except Exception, e:
            print '----- loadMetadata()'
            print self.filepath
            print type (e), e
            fr= None
            info= None
            self.length= 0

        for attr, tag in self.tagForAttr.items ():
            value= getattr (info, tag, None)
            if isinstance (value, basestring):
                value= value.strip ()
            setattr (self, attr, value)

        self.metadadaChanged.emit ()
        self.loaded= True

        return fr

    def __getitem__ (self, key):
        """dict iface so we can simply % it to a pattern"""
        # print self.filepath, key,
        if not self.loaded:
            self.loadMetadata ()
        val= getattr (self, key)
        # if it's, then a) it's either year or trackno; b) leave it empty
        if val==0:
            val= ''
        # print val
        return val

    def __setitem__ (self, key, value):
        """dict iface so we don't have to make special case in __setattr__()"""

        # these two must be int()s
        if key in ('trackno', 'year'):
            print "converting from %s to int for %s" % (type (value), key)
            value= int (value)

        # we cache; otherwise we could set loaded to False
        # and let other functions to resolve it.
        try:
            setattr (self, key, value)
        except AttributeError:
            raise TagWriteError

        self.dirty= True

    def rollbackMetadata (self):
        # let the Song reload the metadata from the file
        self.loaded= False
        self.dirty= False

    def saveMetadata (self):
        # otherwise it doesn't make sense
        if self.dirty:
            if not self.loaded:
                # BUG: makes no fucking sense! what was I drinking?
                # we loose all the changes we want to save!
                print "*** ERROR: loadMetadata() while saveMetadata()!!!"
                fr= self.loadMetadata ()
            else:
                try:
                    fr= tagpy.FileRef (self.filepath)
                except Exception, e:
                    print '----- saveMetadata()'
                    print self.filepath
                    print type (e), e
                    fr= None

            if fr is None:
                raise TagWriteError
            else:
                info= fr.tag ()

                #Traceback (most recent call last):
                #File "/home/mdione/src/projects/satyr/collection-agregator/satyr/skins/complex.py", line 327, in setData
                    #song.saveMetadata ()
                #File "/home/mdione/src/projects/satyr/collection-agregator/satyr/song.py", line 154, in saveMetadata
                    #setattr (info, tag, value)
                #Boost.Python.ArgumentError: Python argument types in
                    #None.None(Tag, unicode)
                #did not match C++ signature:
                    #None(TagLib::Tag {lvalue}, unsigned int)
                for attr, tag in self.tagForAttr.items ():
                    value= getattr (self, attr, None)
                    # print
                    try:
                        setattr (info, tag, value)
                    except Exception, e:
                        print type (e)
                        print "ValueError: %s= (%s)%s" % (tag, type (value), value)

                if not fr.save ():
                    raise TagWriteError

                self.dirty= False

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
            # print '===== cmp()'
            # print other.filepath
            # print '===== cmp()'
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

    def relPath (self):
        return self.filepath[len (self.collection.path)+1:]

# end
