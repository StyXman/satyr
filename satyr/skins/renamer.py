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

from satyr.common import ConfigurableObject
from satyr import utils

class Renamer (ConfigurableObject):
    def __init__ (self, collaggr):
        ConfigurableObject.__init__ (self, 'Renamer')

        self.collaggr= collaggr

        # TODO: ***becareful!*** mixing unicode with paths!
        self.configValues= (
            ('format', unicode, u"{%artist/}{%4year - }{%album/}{Disk %02disk/}{%02trackno - }{%title}"),
            ('vaFormat', unicode, u"{%4year - }{%album/}{Disk %02disk/}{%02trackno - }{%artist - }{%title}"),
            )
        self.loadConfig ()

    def songPath (self, base, song):
        # TODO: take ext from file format?
        ext= song.filepath[-4:]

        if not song.variousArtists:
            songPath= utils.expandConditionally (self.format, song)
        else:
            songPath= utils.expandConditionally (self.vaFormat, song)

        if songPath!='':
            ans= base+"/"+songPath+ext
        else:
            ans= base+"/"+song.filepath

        return ans

    def rename (self, songs):
        # TODO: parametrize the main music colleciton
        mainColl= self.collaggr.collections[0]
        path= mainColl.path

        for song in songs:
            print "Renamer.rename()", song.filepath, "->", self.songPath (path, song)

# end
