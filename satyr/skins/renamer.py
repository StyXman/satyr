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

# qt/kde related
from PyKDE4.kio import KIO
from PyKDE4.kdecore import KUrl, KJob
from PyQt4.QtCore import QDir

# std python
import os.path

# local
from satyr.common import ConfigurableObject
from satyr import utils

class Renamer (ConfigurableObject):
    # TODO: move everything to CollAggr
    def __init__ (self, collaggr):
        ConfigurableObject.__init__ (self, 'Renamer')

        self.collaggr= collaggr

        # TODO: ***becareful!*** mixing unicode with paths!
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

    def jobFinished (self, job):
        try:
            self.jobs.remove (job)
        except ValueError:
            print "Renamer.jobFinished()", job, "not found!"

        if job.error()==KJob.NoError:
            # TODO: update iface
            print "Renamer.jobFinished(): success!"
        else:
            # job.errorString () is a QString
            print "Renamer.jobFinished(): ***** error! *****", unicode (job.errorString ())
            # TODO: Renamer.jobFinished(): ***** error! ***** A file named foo already exists.

    def rename (self, songs):
        # TODO: parametrize the main music colleciton
        mainColl= self.collaggr.collections[0]
        base= mainColl.path
        d= QDir ()

        for song in songs:
            dstPath= self.songPath (base, song)
            dstDir= os.path.dirname (dstPath)
            # TODO: QtDir is not net transp. try to make sub jobs creating the missing path
            if d.mkpath (dstDir):
                # HINT: KUrl because KIO.* uses KUrl
                src= KUrl (utils.path2qurl (song.filepath))
                # BUG: Renamer.rename()
                # PyQt4.QtCore.QUrl(u'file:///home/mdione/media/music/new/bandidos rurales/05 - uruguay, uruguay.mp3') ->
                # PyQt4.QtCore.QUrl(u'file:///home/mdione/media/music/Le\xf3n Gieco/2001 - Bandidos rurales/05 - Uruguay, Uruguay.mp3')
                #                                                       ^^^^
                dst= KUrl (dstPath)
                print "Renamer.rename()", src, "->", dst

                # TODO: do not launch them all in parallel
                job= KIO.file_move (src, dst)
                # TODO: emit a finished.

                # print "Renamer.rename()", job
                job.result.connect (self.jobFinished)
                # print "Renamer.rename(): connected"
                self.jobs.append (job)
                # print "Renamer.rename(): next!"
            else:
                print "Renamer.rename(): failed to create", dstDir, ", skipping", dstPath

        # print "Renamer.rename(): finished"

    def delete (self, songs):
        # TODO: parametrize the trash music colleciton
        trashColl= self.collaggr.collections[-1]
        base= trashColl.path

        for song in songs:
            print "Renamer.delete()", song.filepath

# end
