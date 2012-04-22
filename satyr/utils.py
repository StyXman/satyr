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
# from PyKDE4.phonon import Phonon
from PyQt4.phonon import Phonon
from PyQt4.QtCore import QByteArray, QUrl

import re
import types
import os.path
from datetime import time

# logging
import logging
logger = logging.getLogger(__name__)

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
    qba= QByteArray (path)
    qu= QUrl.fromEncoded (qba.toPercentEncoding ("/ "))
    # older versions need this, at least for the gstreamer backend
    if qu.scheme ()=='':
        qu.setScheme ('file')

    return qu

def import_ (name):
    # as per __import__'s doc suggestion
    # print name
    mod= __import__ (name)
    components= name.split ('.')
    for comp in components[1:]:
        # print comp
        mod= getattr (mod, comp)
    return mod

expansion= re.compile ("(\{(.*?)\%([0-9]*)([a-z]+)([^a-z}]*)\})")

def expandConditionally (format, values):
    expansions= expansion.findall (format)
    ans= format
    logger.debug ("xpandCond(): %s", ans)
    for complete, pre, digits, var, post in expansions:
        try:
            value= values[var]
        except (KeyError, AttributeError):
            value= ''

        if value!='' and value!=0:
            logger.debug ("%s: >%s<", type (value), value)
            # year and trackno are int's
            if type (value)==types.IntType:
                value= (u"%"+digits+"d") % value
            else:
                # / is not valid in filenames
                # in our case it creates a subdir
                value= value.replace ('/', '-')
                logger.debug ("%s: >%s<", type (value), value)

            ans= ans.replace (complete, pre+value+post)
        else:
            if var=='title':
                # don't let the title to be empty; at least copy the old file name
                ans= ans.replace (complete, os.path.basename (values['filepath']))
            else:
                ans= ans.replace (complete, '')

        logger.debug ("xpandCond(): %s" % ans)

    return ans

def secondsToTime (seconds):
    minutes= int (seconds/60.0)
    seconds= abs (seconds-minutes*60)
    return u"%02d:%02d" % (minutes, seconds)

# end
