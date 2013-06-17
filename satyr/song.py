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

# std python
import types
from md5 import md5
from os import stat

# other libs
import tagpy

# we needed before loggin to get the handler
import satyr

# logging
import logging
logger = logging.getLogger(__name__)
# logger.setLevel (logging.DEBUG)

# local
from satyr import utils

class TagWriteError (Exception):
    pass

# TODO: create a database, store everything, including last modif date,
# update only when the date on disk is newer than the one in the db

class Song (QObject):
    # TODO: metadata potentially updated in file if mtime is newer than stored one
    # TODO: store mtime
    metadadaChanged= pyqtSignal ()

    def __init__ (self, collection, filepath, id=None, onDemand=True, va=False):
        QObject.__init__ (self)
        if not isinstance (filepath, str):
            logger.debug (filepath, "is a", type (filepath), "!")
            traceback.print_stack ()
        self.loaded= False
        self.dirty= False
        self.coll= collection
        self.filepath= filepath
        if id is None:
            self.id= md5 (filepath).hexdigest ()
        else:
            self.id= id

        # artist, year, collection, diskno, album, trackno, title, length
        self.variousArtists= va
        if not self.variousArtists:
            self.cmpOrder= ('artist', 'year', 'collection', 'diskno', 'album', 'trackno', 'title', 'length')
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
            return utils.secondsToTime (float (seconds))
        else:
            return "???"

    def loadMetadata (self):
        # do not even try if the file does not exist
        # NOTE: this was added because at some point tagpy crashed horribly if the file didn't exist
        fr= None
        info= None
        f= None
        self.length= 0
        try:
            stat (self.filepath)
        except OSError as e:
            logger.warning ("sta()'ing file %r failed: %s", self.filepath, e)
        else:
            try:
                # tagpy doesn't handle unicode filepaths (somehow makes sense)
                # we cannot keep the FileRef or the Tag because the file stays open.
                fr= tagpy.FileRef (self.filepath)
                f= fr.file ()

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

                if type (info)==tagpy._tagpy.Tag and type (f)==tagpy._tagpy.flac_File:
                    # flac files use xiph comments
                    # grab the original tagset
                    info= f.xiphComment ()
            except Exception, e:
                logger.debug ('----- loadMetadata()')
                logger.debug (self.filepath)
                logger.debug ("%s: %s", type (e), e)

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
            d= info.fieldListMap ()
            # TODO: make it a class attr
            for attr in ('collection', 'diskno'):
                # names must(?) be uppercase
                # «It is case insensitive, so artist and ARTIST are the same field»
                tag= attr.upper ()
                try:
                    value= self.sanitize (attr, d[tag][0]) # TODO: support a real list
                except KeyError:
                    value= ''

                setattr (self, attr, value)

        elif type (info)==tagpy._tagpy.Tag:
            # this is somewhat generic, so we try guessing different types
            # mpeg first
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
            elif f is not None:
                logger.warning ('**** loadMetadata(): file type not supported yet: %s', type (f))

        elif info is not None:
            logger.warning ('**** loadMetadata(): tagset type not supported yet: %s', type (info))

        self.metadadaChanged.emit ()
        self.loaded= True

        return fr

    def sanitize (self, attr, value):
        value= value.strip ()
        if attr=='diskno':
            # sometimes it's stored as x/N
            pos= value.find ('/')
            if pos>-1:
                value= value[:pos]
            if value!='':
                value= int (value)
            else:
                value= 0

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
        """dict iface so we don't have to make special case in __setattr__()"""

        # these two must be int()s
        if key in ('diskno', 'trackno', 'year'):
            logger.debug ("converting from %s to int for %s", type (value), key)
            try:
                value= int (value)
            except ValueError:
                value= 0

        # we cache; otherwise we could set loaded to False
        # and let other functions to resolve it.
        try:
            logger.debug ("__setitem__(): %s >%r<", key, value)
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
                logger.warning ("*** ERROR: loadMetadata() while saveMetadata()!!!")
                # fr= self.loadMetadata ()
            else:
                try:
                    fr= tagpy.FileRef (self.filepath)
                    f= fr.file ()
                except Exception, e:
                    logger.debug ('----- saveMetadata()')
                    logger.debug (self.filepath)
                    logger.debug ("%s: %s", type (e), e)
                    fr= None

            if fr is None:
                raise TagWriteError
            else:
                info= fr.tag ()

                logger.debug ("%r", info)

                if type (info)==tagpy._tagpy.Tag and type (f)==tagpy._tagpy.flac_File:
                    # flac files use xiph comments
                    # grab the original tagset
                    info= f.xiphComment ()

                for attr, tag in self.tagForAttr.items ():
                    value= getattr (self, attr, None)
                    try:
                        logger.debug ("%s-> %r", tag, value)
                        setattr (info, tag, value)
                    except Exception, e:
                        logger.warning (type (e))
                        logger.warning ("ValueError: %s= (%s)%s", tag, type (value), value)

                logger.debug ("%r", info)
                
                # 'faked' tags; must be handled file type by file type
                if type (info)==tagpy._tagpy.ogg_XiphComment:
                    # http://www.xiph.org/vorbis/doc/v-comment.html
                    # with Xiph comments we're free to set our own
                    # TODO: make the list a class attr
                    for attr in ('collection', 'diskno'):
                        # names must(?) be uppercase
                        # «It is case insensitive, so artist and ARTIST are the same field»
                        tag= attr.upper ()
                        value= getattr (self, attr)
                        if value!='' and value!=0:
                            # the conversion to unicode is because the values are int
                            info.addField (tag, unicode (value), True) # yes, replace
                            logger.debug ("%s-> %r", tag, unicode (value))
                        else:
                            info.removeField (tag)
                            logger.debug ("removed %s", tag)


                elif type (info)==tagpy._tagpy.Tag:
                    # this is somewhat generic, so we try guessing different types
                    # mpeg first
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
                            for attr, tag in dict (collection='TOAL', diskno='TPOS').items ():
                                # BUG? why
                                value= unicode (getattr (self, attr))

                                try:
                                    frame= d[tag][0]
                                    if value not in (u'', u'0'):
                                        logger.debug ("%s-> %r", tag, unicode (value))
                                        frame= tagpy._tagpy.id3v2_TextIdentificationFrame (tag)
                                        frame.setText (value)
                                        t2.addFrame (frame)
                                    else:
                                        t2.removeFrame (frame, False)
                                        logger.debug ("removed %s", tag)
                                except KeyError:
                                    logger.debug ("cannot find frame for %s", tag)

                        else:
                            # TODO: else?
                            logger.debug ("else! %r, %r", t1, t2)
                    else:
                        logger.warning ('**** saveMetadata(): file type not supportd yet', type (f))

                else:
                    logger.warning ('**** saveMetadata(): file type not supportd yet', type (info))

                if not fr.save ():
                    raise TagWriteError

                self.dirty= False
        else:
            logger.debug ('not dirty! %s', self)

    def metadataNotNull (self):
        if not self.loaded:
            self.loadMetadata ()

        # we could do it more complex, but I think this is enough
        # tagpy returns u'' or 0 instead of not defining the attr at all
        # so we see that indeed it reurns unicode. see comment in loadMetadata()
        return (self.title is not None and self.title!=u'')

    def cmpByMetadata (self, other):
        try:
            for attr1, attr2 in zip (self.cmpOrder, other.cmpOrder):
                val1= getattr (self, attr1)
                val2= getattr (other, attr2)
                ans= cmp (val1, val2)
                if ans!=0:
                    break

        except Exception, e:
            logger.debug ('>>>>> cmp()')
            logger.debug (self.filepath)
            logger.debug (e)
            logger.debug ('<<<<< cmp()')
            # any lie is good as any
            ans= -1

        return ans

    def cmpByFilepath (self, other):
        return cmp (self.filepath, other.filepath)

    def __cmp__ (self, other):
        # I don't want to implement the myriad of rich comparison
        # don't load metadata on any comparison
        # this would force it very soon at boot time
        # so use the only reasonable thing: the filepath
        ans= self.cmpByFilepath (other)
        # and only do it if the paths are different
        if ans!=0 and self.loaded and other.loaded:
            ans= self.cmpByMetadata (other)

        return ans

    def __repr__ (self):
        return "Song: "+self.filepath

    def relPath (self):
        return self.filepath[len (self.coll.path)+1:]

# end
