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
from PyKDE4.phonon import Phonon
# from PyQt4.phonon import Phonon

# dbus
import dbus.service

# std python
import sys, os, os.path, time, bisect, stat, random

# local
from satyr.common import SatyrObject, BUS_NAME
from satyr import utils

mimetypes= None
def initMimetypes ():
    global mimetypes
    # init the mimetypes the first time
    if mimetypes is None:
        available= Phonon.BackendCapabilities.availableMimeTypes ()
        mimetypes= [ str (mimetype)
            for mimetype in available
                if validMimetype (str (mimetype)) ]

    # print "initMimetypes()", mimetypes
    if mimetypes==[]:
        print "No mimetypes! do you have any Phonon backend installed, configured and/or working?"
        # TODO: MessageBox and abort


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

def getMimeType (filepath):
    mimetype, accuracy= KMimeType.findByFileContent (filepath)
    if accuracy<50:
        # try harder?
        # BUG?: (in KMimeType) gets confused by filenames with #'s
        # mimetype, accuracy= KMimeType.findByUrl (KUrl (utils.path2qurl (filepath)), 0, False, True)
        mimetype, accuracy= KMimeType.findByUrl (KUrl (utils.path2qurl (filepath)))

    return str (mimetype.name ())

class CollectionIndexer (QThread):
    # finished= pyqtSignal (QThread)
    scanning= pyqtSignal (unicode)
    foundSongs= pyqtSignal (QStringList)

    def __init__ (self, path, parent=None, relative=False):
        QThread.__init__ (self, parent)
        self.path= path
        self.relative= relative
        initMimetypes ()

    def walk (self, root, subdir='', relative=False):
        print root, subdir
        # TODO: support single filenames
        # if not os.path.isdir (root):
        #     return root
        try:
            names= os.listdir (root+'/'+subdir)
        except Exception, err:
            print err
            return

        # separate directories from files
        dirs, nondirs = [], []
        for name in names:
            # always use the absolute path
            path= root+'/'+subdir+'/'+name

            if os.path.isdir (path):
                dirs.append (name)
            else:
                nondirs.append (name)

        # deliver what we found so far
        if not relative:
            yield root+'/'+subdir, dirs, nondirs
        else:
            yield subdir, dirs, nondirs

        # recurse...
        for name in dirs:
            if subdir=='':
                path= name
            else:
                path= subdir+'/'+name
            # ... on non-symlinked dirs
            if not os.path.islink (path):
                for x in self.walk (root, path, relative=relative):
                    yield x

    def run (self):
        # BUG:
        # Traceback (most recent call last):
        # File "/home/mdione/src/projects/satyr/playlist-listmodel/collection_indexer.py", line 112, in run
        #     mode= os.stat (self.path).st_mode
        # OSError: [Errno 2] No such file or directory: '/home/mdione/media/music/Various Artists/abcde.de10c40e/track01.ogg'
        try:
            mode= os.stat (self.path).st_mode
        except OSError, e:
            print e
        else:
            if stat.S_ISDIR (mode):
                # http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=481795
                for root, dirs, files in self.walk (self.path, relative=self.relative):
                    self.scanning.emit (root)
                    filepaths= []
                    for filename in files:
                        filepath= root+'/'+filename
                        # print root, filename
                        # detect mimetype and add only if it's suppourted
                        mimetype= getMimeType (filepath)
                        if mimetype in mimetypes:
                            filepaths.append (filepath)
                        else:
                            # print mimetype, mimetypes
                            pass

                    # pyqt4 doesn't do this automatically
                    # print "CI.run(): found", filepaths
                    self.foundSongs.emit (QStringList (filepaths))

            elif stat.S_ISREG (mode):
                # HINT: collection_indexer.py:110: Local variable (mimetype) shadows global defined on line 37
                # it's not a global
                mimetype= getMimeType (self.path)
                if mimetype in mimetypes:
                    self.foundSongs.emit (QStringList ([self.path]))

# end
