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
from PyKDE4.kdecore import KMimeType, KUrl
from PyQt4.QtCore import pyqtSignal, QThread, QStringList
# from PyKDE4.phonon import Phonon
from PyQt4.phonon import Phonon

# dbus
import dbus.service

# std python
import sys, os, os.path, time, bisect, stat, random

# local
from common import SatyrObject, BUS_NAME

def validMimetype (mimetype):
    """Phonon.BackendCapabilities.availableMimeTypes() returns a lot of nonsense,
    like image/png or so.
    Filter only interesting mimetypes."""

    valid= False
    valid= valid or mimetype.startswith ('audio')
    # we can play the sound of video files :|
    # also some wma files are detected as video :|
    # skipping /home/mdione/media/music//N/Noir Desir/Album inconnu (13-07-2004 01:59:07)/10 - Piste 10.wma;
    # mimetype video/x-ms-asf not supported
    valid= valid or mimetype.startswith ('video')
    valid= valid or mimetype=='application/ogg'

    return valid

mimetypes= [ str (mimetype)
    for mimetype in Phonon.BackendCapabilities.availableMimeTypes ()
        if validMimetype (str (mimetype)) ]

def getMimeType (filepath):
    mimetype, accuracy= KMimeType.findByFileContent (filepath)
    # print mimetype.name (), accuracy,
    if accuracy<50:
        # try harder?
        mimetype, accuracy= KMimeType.findByUrl (KUrl (filepath))
        # print mimetype.name (), accuracy,
    # print
    return str (mimetype.name ())

class CollectionIndexer (QThread):
    # finished= pyqtSignal (QThread)
    scanning= pyqtSignal (unicode)
    foundSongs= pyqtSignal (QStringList)

    def __init__ (self, path, parent=None):
        QThread.__init__ (self, parent)
        self.path= path

    def walk (self, top, relative=False):
        # TODO: return relative paths
        # TODO: support single filenames
        # if not os.path.isdir (top):
        #     return top
        try:
            # names= [ str (x) for x in os.listdir (top)]
            names= os.listdir (top)
        except Exception, err:
            print err
            return

        dirs, nondirs = [], []
        for name in names:
            try:
                path= top+'/'+name
            except UnicodeDecodeError:
                print repr (top), repr (name)
                print name, "skipped: bad encoding"
            else:
                if os.path.isdir(path):
                    dirs.append(name)
                else:
                    nondirs.append(name)

        yield top, dirs, nondirs
        for name in dirs:
            try:
                path = top+'/'+name
            except UnicodeDecodeError:
                print name, "skipped: bad encoding"
            else:
                if not os.path.islink(path):
                    for x in self.walk(path):
                        yield x

    def run (self):
        # print "scanning >%s<" % repr (path)
        mode= os.stat (self.path).st_mode
        if stat.S_ISDIR (mode):
            # http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=481795
            for root, dirs, files in self.walk (self.path):
                self.scanning.emit (root)
                filepaths= []
                for filename in files:
                    # filepath= os.path.join (root, filename)
                    filepath= root+'/'+filename
                    print root, filename
                    # detect mimetype and add only if it's suppourted
                    mimetype= getMimeType (filepath)
                    if mimetype in mimetypes:
                        # Song (filepath)
                        filepaths.append (filepath)

                # pyqt4 cannot make this automatically
                self.foundSongs.emit (QStringList (filepaths))

        elif stat.S_ISREG (mode):
            # HINT: collection_indexer.py:110: Local variable (mimetype) shadows global defined on line 37
            # it's not a global
            mimetype= getMimeType (self.path)
            if mimetype in mimetypes:
                self.foundSongs.emit (QStringList ([self.path]))

# end
