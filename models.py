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


from PyQt4.QtCore import QObject
# from PyQt4.phonon import Phonon
from kaa import metadata

class Song (QObject):
    def __init__ (self, filepath):
        # sigsegv :(
        # KCrash: Application 'satyr.py' crashing...
        # sock_file=/home/mdione/.kde/socket-mustang/kdeinit4__0
        # satyr.py: Fatal IO error: client killed
        # ms= Phonon.MediaSource (filepath)
        # mo= Phonon.MediaObject ()
        # mo.setCurrentSource (ms)
        # print mo.metadata ()

        try:
            info= metadata.parse (filepath)
            # print info.artist, info.album, info.trackno, info.title
        except Exception, e:
            print filepath
            print e
            print '-----'

        for attr in ('artist', 'album', 'trackno', 'title'):
            setattr (self, attr, getattr (info, attr, None))
        self.filepath= filepath

# end
