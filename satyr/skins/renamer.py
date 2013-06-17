# (c) 2010 Marcos Dione <mdione@grulic.org.ar>

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

# std python
import os.path
import os

# we needed before loggin to get the handler
import satyr

# logging
import logging
logger= logging.getLogger(__name__)
logger.setLevel (logging.DEBUG)

# local
from satyr.common import ConfigurableObject
from satyr import utils

class Renamer (ConfigurableObject):
    # TODO: move everything to CollAggr
    def __init__ (self, collaggr):
        ConfigurableObject.__init__ (self, 'Renamer')

        self.collaggr= collaggr

        # unicode is ok here because we're going to create the pathname in unicode and later encode it
        # artist, year, collection, diskno, album, trackno, title, length
        self.configValues= (
            # ('format', unicode, u"{%artist/}{%4year - }{%collection/}{%02diskno - }{%album/}{Disk %02disk/}{%02trackno - }{%title}"),
            ('format', unicode, u"{%artist}/{%4year - }{%album}/{Disk %02diskno}/{%02trackno - }{%title}"),
            ('vaFormat', unicode, u"{%4year - }{%album}/{Disk %02diskno}/{%02trackno - }{%artist - }{%title}"),
            ('collection', unicode, u"{%artist}/{%4year - }{%collection}/{%02diskno - }{%album}/{%02trackno - }{%title}"),
            )
        self.loadConfig ()

        self.jobs= []

    # TODO: make this a method of Song called properPath()
    def songPath (self, base, song):
        # TODO: take ext from file format?
        lastDot= song.filepath.rfind ('.')
        if lastDot==-1:
            ext= ''
        else:
            ext= song.filepath[lastDot:]

        if not song.variousArtists:
            if song.collection==u'':
                songPath= utils.expandConditionally (self.format, song)
            else:
                songPath= utils.expandConditionally (self.collection, song)
        else:
            songPath= utils.expandConditionally (self.vaFormat, song)

        if songPath!='':
            ans= base+"/"+songPath+ext
        else:
            ans= base+"/"+song.filepath

        return ans

    def rename (self, songs):
        self.collaggr.rename (self, songs)

    def delete (self, songs):
        # TODO: parametrize the trash music collection
        trashColl= self.collaggr.collections[-1]
        base= trashColl.path

        for song in songs:
            logger.debug ("Renamer.delete()", song.filepath)

# end
