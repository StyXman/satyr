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
# from PyKDE4.phonon import Phonon
from PyQt4.phonon import Phonon
from PyQt4.QtCore import QByteArray, QUrl

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
    majV, minV, patchL= phononVersion ()
    # older versions need this, at least for the gstreamer backend
    if (majV<4) or (majV==4 and minV<3) or (majV==4 and minV==3 and patchL<51):
        qu.setScheme ('file')

    return qu

def import_ (name):
    # as per __import__'s doc suggestion
    print name
    mod= __import__ (name)
    components= name.split ('.')
    for comp in components[1:]:
        print comp
        mod= getattr (mod, comp)
    return mod

# end
