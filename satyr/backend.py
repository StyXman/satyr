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
from satyr.models.table_model import QPlayListModel
from satyr.models.dbus_table_model import 
from satyr import utils

# we need it before loggin to get the handler
import satyr

# logging
import logging
logger = logging.getLogger(__name__)
logger.addHandler(satyr.loggingHandler)

# TODO: we're mixing everything here. these functions should go somewhere else
def getProxy (bus, path):
    try:
        proxy= bus.get_object (BUS_NAME, path)
    except dbus.DBusException:
        proxy= None

    return proxy

def getBackend (bus):
    proxy= getProxy (bus, '/backend')
    if proxy is not None:
        logger.debug ("backend.ping(): %s", proxy.ping ())

    return proxy

def getModel (bus):
    return getProxy (bus, '/model')

class Backend (SatyrObject):
    """This object creates all the objects exported via dbus."""
    def __init__ (self, app, args, busName=None, busPath=None):
        SatyrObject.__init__ (self, app, busName, busPath)
        
        self.collaggr= CollectionAggregator (app, busName=busName, busPath='/collaggr')
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

        self.playlist= PlayList (app, collaggr, busName=busName, busPath='/playlist')
        self.player= Player (app, playlist, busName, '/player')
        player.finished.connect (app.quit)

        self.model= QPlaListModel (self, self.playlist, busName=busName, busPath='/model')

    @dbus.service.method (BUS_NAME, in_signature='', out_signature='s')
    def ping (self):
        return 'pong'

# end
