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
from PyQt4.QtCore import QObject, QVariant, QStringList

# dbus
import dbus.service

# std python
from collections import deque

# globals :|
BUS_NAME= 'org.kde.satyr'

# v is a QVariant
def configEntryToBool (v):
    return v.toString ()!='false'

def configEntryToStr (v):
    return str (v.toString ())

def configEntryToUnicode (v):
    return unicode (v.toString ())

def configEntryToInt (v):
    return v.toInt ()[0]

def configEntryToStrList (v):
    return list (v.toStringList ())

def configEntryToIntList (v):
    return [int (x) for x in configEntryToStrList (v)]

def configEntryToDeque (v):
    l= configEntryToIntList (v)
    v= deque (l, 100)
    # print "cETD:", l, v,
    return v

def listToConfigEntry (l):
    return QStringList (map (str, l))

class ConfigEntry (object):
    def __init__ (self, key, _type, default, subtype=None):
        self.key= key
        self.type= _type
        self.default= default
        self.subtype= subtype

readFunctions= {
    bool: configEntryToBool,
    int:  configEntryToInt,
    str:  configEntryToStr,
    unicode: configEntryToUnicode,
    list: {
        str: configEntryToStrList,
        int: configEntryToIntList,
        },
    # we could do it more generic, but we don't use it
    deque: configEntryToDeque,
    }

writeFunctions= {
    list: listToConfigEntry,
    deque: listToConfigEntry,
    }

class ConfigurableObject (object):
    def __init__ (self, groupName=None):
        # HINT: please redefine in inheriting classes
        self.configValues= ()
        if groupName is not None:
            self.config= KSharedConfig.openConfig ('satyrrc').group (groupName)
        else:
            self.config= None

    def saveConfig (self):
        if not self.config is None:
            for configEntry in self.configValues:
                k= configEntry.key
                v= getattr (self, k)
                print 'writing config entry %s= %s' % (k, v)
                w= writeFunctions.get (configEntry.type, QVariant)
                # use the write function
                v= w (v)
                self.config.writeEntry (k, v)
            self.config.config ().sync ()

    def loadConfig (self):
        for configEntry in self.configValues:
            k= configEntry.key
            if not self.config is None:
                w= writeFunctions.get (configEntry.type, QVariant)
                v= configEntry.default
                print 'reading config entry %s.%s [%s:%s]' % (unicode (self.config.name ()), k, v, type (v)),
                # use the write function to give a default that KConfig can understand
                v= w (v)
                a= self.config.readEntry (k, v)
                # we always have a read function, otherwise they're all QVariants
                r= readFunctions[configEntry.type]
                if configEntry.subtype is not None:
                    r= r[configEntry.subtype]
                v= r (a)
                print a.toString (), v
            else:
                v= configEntry.default

            setattr (self, k, v)


MetaDBusObject= type (dbus.service.Object)
MetaQObject= type (QObject)
MetaCObject= type (ConfigurableObject)


class MetaObject (MetaQObject, MetaDBusObject, MetaCObject):
    """Dummy metaclass that allows us to inherit from both QObject and d.s.Object"""
    def __init__(cls, name, bases, dct):
        MetaDBusObject.__init__ (cls, name, bases, dct)
        MetaQObject.__init__ (cls, name, bases, dct)
        MetaCObject.__init__ (cls, name, bases, dct)


class SatyrObject (dbus.service.Object, QObject, ConfigurableObject):
    """A QObject with a DBus interface and a section in the config file"""
    __metaclass__= MetaObject

    def __init__ (self, parent, busName=None, busPath=None):
        # print busName, busPath
        dbus.service.Object.__init__ (self, busName, busPath)
        QObject.__init__ (self, parent)
        ConfigurableObject.__init__ (self, self.dbusName (busPath))

    def dbusName (self, busPath):
        if busPath is None:
            ans= None
        else:
            ans= busPath[1:].replace ('/', '-')
        return ans

# end
