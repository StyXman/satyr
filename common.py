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
from PyKDE4.kdecore import KSharedConfig
from PyQt4.QtCore import QObject, QVariant

# dbus
import dbus.service

# globals :|
BUS_NAME= 'org.kde.satyr'

def configBoolToBool (s):
    return s!='false'


MetaDBusObject= type (dbus.service.Object)
MetaQObject= type (QObject)

class MetaObject (MetaQObject, MetaDBusObject):
    """Dummy metaclass that allows us to inherit from both QObject and d.s.Object"""
    def __init__(cls, name, bases, dct):
        MetaDBusObject.__init__ (cls, name, bases, dct)
        MetaQObject.__init__ (cls, name, bases, dct)

class SatyrObject (dbus.service.Object, QObject):
    """A QObject with a DBus interface and a section in the config file"""
    __metaclass__= MetaObject

    def __init__ (self, parent, busName=None, busPath=None):
        dbus.service.Object.__init__ (self, busName, busPath)
        QObject.__init__ (self, parent)

        # HINT: please redefine in inheriting classes
        self.configValues= ()
        if busPath is not None:
            self.config= KSharedConfig.openConfig ('satyrrc').group (self.dbusName (busPath))
        else:
            self.config= None

    def dbusName (self, busPath):
        return busPath[1:].replace ('/', '-')

    def saveConfig (self):
        if not self.config is None:
            for k, t, v in self.configValues:
                v= getattr (self, k)
                # print 'writing config entry %s= %s' % (k, v)
                self.config.writeEntry (k, QVariant (v))
            self.config.config ().sync ()

    def loadConfig (self):
        for k, t, v in self.configValues:
            if not self.config is None:
                print 'reading config entry %s [%s]' % (k, v),
                s= self.config.readEntry (k, QVariant (v)).toString ()
                v= t (s)
                print s, v

            setattr (self, k, v)

# end
