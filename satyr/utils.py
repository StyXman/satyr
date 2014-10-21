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
from PyKDE4.kdecore import KMimeType, KUrl
from PyQt4.phonon import Phonon
from PyQt4.QtCore import QByteArray, QUrl

import re
import types
import os.path
from datetime import time
from urllib import pathname2url
from os import mkdir

# logging
import logging
logger = logging.getLogger(__name__)
# logger.setLevel (logging.DEBUG)

def phononVersion ():
    return map (int, Phonon.phononVersion ().split ('.'))

def qstring2path (qs):
    # BUG: this is ugly; might be properly handled w/PyQt4.6/Python2.6
    qba= QByteArray ()
    qba.append (qs)
    s= str (qba)

    return s

def path2qurl (path):
    # path= '/home/mdione/media/music/Patricio Rey Y Sus Redonditos De Ricota/\xc3\x9altimo bondi a Finisterre/07- La peque\xf1a novia del carioca.wav'
    # qba= QByteArray (path)
    qu= QUrl.fromEncoded (pathname2url (path))
    # older versions need this, at least for the gstreamer backend
    if qu.scheme ()=='':
        qu.setScheme ('file')

    return qu

def import_ (name):
    # as per __import__'s doc suggestion
    mod= __import__ (name)
    components= name.split ('.')
    for comp in components[1:]:
        mod= getattr (mod, comp)
    return mod

expansion= re.compile ("(\{(.*?)\%([0-9]*)([a-z]+)([^a-z}]*)\})")

def expandConditionally (format, values):
    expansions= expansion.findall (format)
    ans= format
    logger.debug ("xpandCond(): %r", ans)
    for complete, pre, digits, var, post in expansions:
        try:
            value= values[var]
        except (KeyError, AttributeError):
            value= ''

        if value!='' and value!=0:
            logger.debug ("%s: >%r<", type (value), value)
            # year and trackno are int's
            if type (value)==types.IntType:
                value= (u"%"+digits+"d") % value
            else:
                # / is not valid in filenames
                # in our case it creates a subdir
                value= value.replace ('/', '-')
                logger.debug ("%s: >%r<", type (value), value)

            ans= ans.replace (complete, pre+value+post)
        else:
            if var=='title':
                # don't let the title to be empty; at least copy the old file name
                ans= ans.replace (complete, os.path.basename (values['filepath']))
            else:
                ans= ans.replace (complete, '')

        logger.debug ("xpandCond(): %r" % ans)

    return ans

def secondsToTime (seconds):
    minutes= int (seconds/60.0)
    seconds= abs (seconds-minutes*60)
    return u"%02d:%02d" % (minutes, seconds)

def bisect (a, x, f=cmp):
    # shamelessly taken from python's bisect.py
    # TODO: check license
    lo= 0
    hi= len (a)

    while lo < hi:
        mid = (lo+hi)//2
        # cmp (a, b)==-1 \eq a < b
        if f (a[mid], x)==-1:
            lo = mid+1
        else:
            hi = mid

    return lo

def makedirs(_dirname):
    """
    Better replacement for os.makedirs():
    it doesn't fails if some intermediate dir already exists.
    """

    dirs = _dirname.split('/')
    i = u''
    while len(dirs):
        i += dirs.pop(0)+'/'
        try:
            mkdir(i.encode ('utf-8'))
        except OSError, e:
            logger.debug ('make dir %r failed: %s' % (i.encode ('utf-8'), e))
        else:
            logger.debug ('make dir %r' % i.encode ('utf-8'))

mimetypes= None
def initMimetypes ():
    global mimetypes
    # init the mimetypes the first time
    if mimetypes is None:
        available= Phonon.BackendCapabilities.availableMimeTypes ()
        mimetypes= [ str (mimetype)
            for mimetype in available
                if validMimetype (str (mimetype)) ]

    if mimetypes==[]:
        logger.warning ("No mimetypes! Do you have any Phonon backend installed, configured and/or working?")
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
    # TODO: filter out playlists (.m3u)

    return valid

def getMimeType (filepath):
    mimetype, accuracy= KMimeType.findByFileContent (filepath)
    if accuracy<50:
        # try harder?
        # BUG?: (in KMimeType) gets confused by filenames with #'s
        # mimetype, accuracy= KMimeType.findByUrl (KUrl (utils.path2qurl (filepath)), 0, False, True)
        mimetype, accuracy= KMimeType.findByUrl (KUrl (path2qurl (filepath)))

    return str (mimetype.name ())

# end
