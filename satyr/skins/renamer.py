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

from PyKDE4.kio import KIO
from PyKDE4.kdecore import KUrl, KJob

from satyr.common import ConfigurableObject
from satyr import utils

class Renamer (ConfigurableObject):
    def __init__ (self, collaggr):
        ConfigurableObject.__init__ (self, 'Renamer')

        self.collaggr= collaggr

        # TODO: ***becareful!*** mixing unicode with paths!
        # artist, year, collection, diskno, album, trackno, title, length
        self.configValues= (
            # ('format', unicode, u"{%artist/}{%4year - }{%collection/}{%02diskno - }{%album/}{Disk %02disk/}{%02trackno - }{%title}"),
            ('format', unicode, u"{%artist/}{%4year - }{%album/}{Disk %02diskno/}{%02trackno - }{%title}"),
            ('vaFormat', unicode, u"{%4year - }{%album/}{Disk %02diskno/}{%02trackno - }{%artist - }{%title}"),
            )
        self.loadConfig ()

        self.jobs= []

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

    def jobFinished (self, job):
        try:
            self.jobs.remove (job)
        except ValueError:
            print "Renamer.jobFinished()", job, "not found!"

        if job.error()==KJob.NoError:
            # TODO: update iface
            print "Renamer.jobFinished(): success!"

    def rename (self, songs):
        # TODO: parametrize the main music colleciton
        mainColl= self.collaggr.collections[0]
        base= mainColl.path

        for song in songs:
            print "Renamer.rename()", song.filepath, "->", self.songPath (base, song)
            src= KUrl (song.filepath)
            dst= KUrl (self.songPath (base, song))

            # TODO: do not launch them all in parallel
            job= KIO.move (src, dst)
            # TODO: emit a finished.

            print "Renamer.rename()", job
            job.result.connect (self.jobFinished)
            self.jobs.append (job)

    def delete (self, songs):
        # TODO: parametrize the trash music colleciton
        trashColl= self.collaggr.collections[-1]
        path= trashColl.path

        for song in songs:
            print "Renamer.rename()", song.filepath, "->", self.songPath (path, song)

# end
