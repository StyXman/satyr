#! /usr/bin/python
# vim: set fileencoding=utf-8 :
# (c) 2011 Marcos Dione <mdione@grulic.org.ar>

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

# dbus
import dbus.service

# local
from satyr.common import SatyrObject, BUS_NAME
from satyr.player import Player
from satyr.playlist import PlayList
from satyr.collection import Collection
from satyr.collaggr import CollectionAggregator
from satyr import utils

# logging
import logging
logger = logging.getLogger(__name__)
logger.addHandler(satyr.loggingHandler)

def getBackend (bus):
    try:
        proxy= bus.get_object (BUS_NAME, '/backend')
        logger.debug ("backend.ping(): %s", proxy.ping ())
    except dbus.DBusException:
        proxy= None

    return proxy

class Backend (SatyrObject):
    def __init__ (self, app, args, busName=None, busPath=None):
        SatyrObject.__init__ (self, app, busName, busPath)
        
        collaggr= CollectionAggregator (app, busName=busName, busPath='/collaggr')
        if collaggr.collsNo==0:
            print "no collections, picking from args"
            for index in xrange (args.count ()):
                path= args.arg (index)

                # paths must be bytes, not ascii or utf-8
                path= utils.qstring2path (path)

                collection= Collection (app, path, busName=busName, busPath="/collection_%04d" % index)
                collaggr.append (collection)

        for collection in collaggr.collections:
            # collection.scanBegins.connect (mw.scanBegins)
            # collection.scanFinished.connect (mw.scanFinished)
            # they're loaded by the CollAggr
            # collection.loadOrScan ()
            # mw.collectionAdded ()
            pass

        playlist= PlayList (app, collaggr, busName=busName, busPath='/playlist')
        player= Player (app, playlist, busName, '/player')
        player.finished.connect (app.quit)

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='s')
    def ping (self):
        return 'pong'

# end
