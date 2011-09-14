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

# other libs
import tagpy
import types

# local
import satyr.song

class TagWriteError (Exception):
    pass

class Song (satyr.song.Song):
    def __init__ (self, collection, filepath, onDemand=True, va=False):
        # tagpy presents trackno as track, so we map them
        # no, I don't want to change everything to match this
        self.tagForAttr= dict (artist='artist', year='year', album='album', trackno='track', title='title')

        satyr.song.Song.__init__ (self, collection, filepath, onDemand, va)

    def loadMetadata (self):
        try:
            # tagpy doesn't handle unicode filepaths (somehow makes sense)
            # we cannot keep the FileRef or the Tag because the file stays open.
            fr= tagpy.FileRef (self.filepath)

            props= fr.audioProperties ()
            # incredibly enough, tagpy also express length as a astring
            # even when taglib uses an int (?!?)
            # BUG: this is wrong, the internal repr should be in seconds
            # and the visual part shoould ask for the visual repr
            # no, we need it for % it to the pattern. see __getitem__()
            # HINT: props has string attrs, not unicode
            self.length= int (props.length)

            # HINT: info has unicode attrs
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


        # 'faked' tags; must be handled file type by file type
        for attr in ('collection', 'diskno'):
            setattr (self, attr, '')

        if type (info)==tagpy._tagpy.ogg_XiphComment:
            # with Xiph comments we're free to set our own
            # names must(?) be uppercase
            d= info.fieldListMap ()
            # TODO: make it a class attr
            # print 'Song.loadMetadata():', self.filepath, info.fieldCount (), info.fieldListMap ().keys ()
            for attr in ('collection', 'diskno'):
                tag= attr.upper ()
                try:
                    value= self.sanitize (attr, d[tag][0]) # TODO: support a real list
                except KeyError:
                    value= ''

                setattr (self, attr, value)

        elif type (info)==tagpy._tagpy.Tag:
            # this is somewhat generic, so we try guessing different types
            # mpeg first
            f= fr.file ()
            if type (f)==tagpy._tagpy.mpeg_File:
                t1= f.ID3v1Tag ()
                t2= f.ID3v2Tag ()
                if not t1.isEmpty () and t2.isEmpty ():
                    # TODO: convert to v2
                    # TODO: strip?
                    pass

                if not t2.isEmpty ():
                    d= t2.frameListMap ()
                    # 4.2.1   TOAL    [#TOAL Original album/movie/show title] <-- we (ab)use this one for collection
                    # 4.2.1   TPOS    [#TPOS Part of a set]
                    # ['TALB', 'TCON', 'TDRC', 'TIT2', 'TPE1', 'TRCK']
                    # print "Song.loadMetadata():", d.keys ()
                    for attr, tag in dict (collection='TOAL', diskno='TPOS').items ():
                        try:
                            value= self.sanitize (attr, d[tag][0].toString ()) # TODO: support a real list
                        except KeyError:
                            value= ''

                        setattr (self, attr, value)
                else:
                    # TODO: else?
                    # if we convert to v2 above, there's no else :)
                    pass
            else:
                print '**** loadMetadata(): file type not supported yet', type (f)

        else:
            print '**** loadMetadata(): file type not supported yet', type (info)

        self.metadadaChanged.emit ()
        self.loaded= True

        return fr

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

                # BUG:
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

                # 'faked' tags; must be handled file type by file type
                if type (info)==tagpy._tagpy.ogg_XiphComment:
                    # http://www.xiph.org/vorbis/doc/v-comment.html
                    # with Xiph comments we're free to set our own
                    # names must(?) be uppercase
                    # TODO: make it a class attr
                    for attr in ('collection', 'diskno'):
                        tag= attr.upper ()
                        value= getattr (self, attr)
                        if value!='' and value!=0:
                            # the conversion to unicode is because the values are int
                            info.addField (tag, unicode (value), True) # yes, replace
                        else:
                            info.removeField (tag)

                    # print 'Song.saveMetadata():', info.fieldCount (), info.fieldListMap ().keys ()

                elif type (info)==tagpy._tagpy.Tag:
                    # this is somewhat generic, so we try guessing different types
                    # mpeg first
                    f= fr.file ()
                    if type (f)==tagpy._tagpy.mpeg_File:
                        t1= f.ID3v1Tag ()
                        t2= f.ID3v2Tag ()
                        if t1 is not None and not t1.isEmpty ():
                            # TODO: strip?
                            pass

                        if t2 is not None and not t2.isEmpty ():
                            # http://www.id3.org/id3v2.3.0
                            # 4.2.1   TOAL    [#TOAL Original album/movie/show title] <-- we (ab)use this one for collection
                            # 4.2.1   TPOS    [#TPOS Part of a set]
                            # ['TALB', 'TCON', 'TDRC', 'TIT2', 'TPE1', 'TRCK']
                            d= t2.frameListMap ()
                            # print "Song.saveMetadata():", d.keys ()
                            for attr, tag in dict (collection='TOAL', diskno='TPOS').items ():
                                # BUG? why
                                value= unicode (getattr (self, attr))
                                # convert to ByteVector
                                # value= value.encode ('utf-16')

                                if value not in (u'', u'0'):
                                    try:
                                        frame= d[tag][0]
                                        # frame= tagpy._tagpy.id3v2_TextIdentificationFrame (tag)
                                        t2.removeFrame (frame, False)
                                    except KeyError:
                                        pass
                                    finally:
                                        frame= tagpy._tagpy.id3v2_TextIdentificationFrame (tag)
                                        frame.setText (value)
                                        t2.addFrame (frame)

                        else:
                            # TODO: else?
                            pass
                    else:
                        print '**** loadMetadata(): file type not supportd yet', type (f)

                else:
                    print '**** loadMetadata(): file type not supportd yet', type (info)

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
