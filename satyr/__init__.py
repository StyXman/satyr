# vim: set fileencoding=utf-8 :
# (c) 2009, 2012 Marcos Dione <mdione@grulic.org.ar>

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

# std python
import sys

# logging
import logging
loggingHandler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s %(name)30s:%(lineno)-4d "
                              "%(levelname)-8s %(message)s",
                              '%Y-%m-%d %H:%M:%S')
loggingHandler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(loggingHandler)

# local
from satyr.app import App

def createApp (args=sys.argv):
    #########################################
    # all the bureaucratic init of a KDE App
    # the appName must not contain any chars besides a-zA-Z0-9_
    # because KMainWindowPrivate::polish() calls QDBusConnection::sessionBus().registerObject()
    # see QDBusUtil::isValidCharacterNoDash()
    appName     = "satyr"
    catalog     = ""
    programName = ki18n ("satyr")
    version     = "0.5.0"
    description = ki18n ("I need a media player that thinks about music the way I think about it. This is such a program.")
    license     = KAboutData.License_GPL
    copyright   = ki18n ("(c) 2009, 2010, 2011, 2012 Marcos Dione")
    text        = ki18n ("none")
    homePage    = "http://savannah.nongnu.org/projects/satyr/"
    bugEmail    = "mdione@grulic.org.ar"

    aboutData   = KAboutData (appName, catalog, programName, version, description,
                                license, copyright, text, homePage, bugEmail)

    aboutData.addAuthor (ki18n ("Marcos Dione"), ki18n ("design and implementation"))
    aboutData.addAuthor (ki18n ("Sebastián Álvarez"), ki18n ("features, bugfixes and testing"))

    KCmdLineArgs.init (args, aboutData)
    options= KCmdLineOptions ()
    options.add ("s").add ("skin <skin-name>", ki18n ("set the skin to use"), "")
    # options.add ("d").add ("debug", ki18n ("turn on debug"), "")
    options.add ("+path", ki18n ("paths to your music collections"))
    KCmdLineArgs.addCmdLineOptions (options)

    app= App ()
    args= KCmdLineArgs.parsedArgs ()

    return app, args

# end
