#! /usr/bin/python
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
from PyKDE4.kdecore import KCmdLineArgs, KAboutData, i18n, ki18n
from PyKDE4.kdecore import KCmdLineOptions
from PyKDE4.kdeui import KApplication

# dbus
import dbus
import dbus.mainloop.qt
import dbus.service

# std python
import sys

# local
from common import BUS_NAME
from player import Player
from playlist import PlayList
from collection import Collection
import utils

#   PID USER     PRI  NI  VIRT   RES   SHR S CPU% MEM%   TIME+  Command
# 24979 mdione    20   0  216M 46132 17380 S  1.0  2.2  4:01.62 python satyr.py /home/mdione/media/music/
#  7300 mdione    20   0  171M 52604 20004 S  0.0  2.5  0:18.42 python satyr.py /home/mdione/media/music/
# 19204 mdione    20   0  249M 42828 12084 S  0.0  2.1  0:22.61 python satyr.py /home/mdione/media/music/

def createApp (args=sys.argv):
    #########################################
    # all the bureaucratic init of a KDE App
    # the appName must not contain any chars besides a-zA-Z0-9_
    # because KMainWindowPrivate::polish() calls QDBusConnection::sessionBus().registerObject()
    # see QDBusUtil::isValidCharacterNoDash()
    appName     = "satyr"
    catalog     = ""
    programName = ki18n ("satyr")                 #ki18n required here
    version     = "0.1a"
    description = ki18n ("I need a media player that thinks about music the way I think about it. This is such a program.")         #ki18n required here
    license     = KAboutData.License_GPL
    copyright   = ki18n ("(c) 2009 Marcos Dione")    #ki18n required here
    text        = ki18n ("none")                    #ki18n required here
    homePage    = "http://savannah.nongnu.org/projects/satyr/"
    bugEmail    = "mdione@grulic.org.ar"

    aboutData   = KAboutData (appName, catalog, programName, version, description,
                                license, copyright, text, homePage, bugEmail)

    # ki18n required for first two addAuthor () arguments
    aboutData.addAuthor (ki18n ("Marcos Dione"), ki18n ("design and implementation"))
    aboutData.addAuthor (ki18n ("Sebastián Álvarez"), ki18n ("features and bugfixes"))

    KCmdLineArgs.init (args, aboutData)
    options= KCmdLineOptions ()
    options.add ("s").add ("skin <skin-name>", ki18n ("skin"), "default")
    options.add ("+path", ki18n ("paths to your music collections"))
    KCmdLineArgs.addCmdLineOptions (options)

    app= KApplication ()
    args= KCmdLineArgs.parsedArgs ()

    return app, args

def main ():
    app, args= createApp ()

    dbus.mainloop.qt.DBusQtMainLoop (set_as_default=True)
    bus= dbus.SessionBus ()
    busName= dbus.service.BusName (BUS_NAME, bus=bus)

    # TODO: add the app dir to sys.path so we can load skins
    skin= str (args.getOption ("skin"))
    # do the import magic
    parent= __import__ ('skins.'+skin)
    # print mod.__file__
    # pdb.set_trace ()
    # When the name variable is of the form package.module, normally,
    # the top-level package (the name up till the first dot) is returned,
    # not the module named by name
    mod= getattr (parent, skin)
    mw= mod.MainWindow ()

    collections= []
    for index in xrange (args.count ()):
        path= args.arg (index)

        # paths must be bytes, not ascii or utf-8
        path= utils.qstring2path (path)

        collection= Collection (app, path, busName, "/collection_%04d" % index)
        collections.append (collection)
        collection.scanBegins.connect (mw.scanBegins)
        collection.scanFinished.connect (mw.scanFinished)
        # we need to fire the load/scan after the main loop has started
        # otherwise the signals emited from it are not sent to the connected slots
        # FIXME? I'm not sure I want it this way
        # QTimer.singleShot (100, collection.loadOrScan)

        # ? seems to be fixed
        collection.loadOrScan ()
        mw.collectionAdded ()

    playlist= PlayList (app, collections, busName, '/playlist')
    player= Player (app, playlist, busName, '/player')
    player.finished.connect (app.quit)

    mw.connectUi (player, playlist)
    mw.show ()

    return app.exec_ ()

if __name__=='__main__':
    sys.exit (main ())

# end
