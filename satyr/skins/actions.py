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
from PyKDE4.kdeui import KAction, KShortcut
from PyQt4.QtCore import Qt

# we needed before loggin to get the handler
import satyr

# logging
import logging
logger = logging.getLogger(__name__)
logger.addHandler(satyr.loggingHandler)

def traverseObjects (root, fqn):
    components= fqn.split ('.')
    name= components.pop ()

    for c in components:
        root= getattr (root, c)

    return root, name

def create (parent, ac):
    """here be common actions for satyr skins"""
    actions= (
        ('queue',    Qt.CTRL+Qt.Key_Q, False, "Queue songs"),
        ('rename',   Qt.CTRL+Qt.Key_R, False, "Arrange songs"),
        ('toggleVA', Qt.CTRL+Qt.Key_V, False, "Toggle 'Various Artists' flag"),
        ('delete',   Qt.CTRL+Qt.Key_D, False, "Delete songs"),

        # globals
        ('player.prev',  KShortcut (Qt.Key_MediaPrevious),  True, "Previous song"),
        ('player.stop',  KShortcut (Qt.Key_MediaStop),      True, "Stop"),
        ('player.play',  KShortcut (Qt.Key_MediaPlay),      True, "Play"),
        ('player.pause', KShortcut (Qt.Key_Pause),     True, "Toggle Pause"),
        ('player.play_pause', KShortcut (Qt.Key_MediaPlay), True, "Switch between Play and Pause"),
        ('player.next',  KShortcut (Qt.Key_MediaNext),      True, "Next song"),
        ('player.toggleStopAfter', KShortcut (Qt.Key_Eject), True, "Stop after playing current song"),
        # TODO: S-Play/Pause -> cycle random
        # TODO: S-|<</>>| -> beginning/prev album, next album
        )

    for fqn, shortcut, globalSC, text in actions:
        try:
            obj, name= traverseObjects (parent, fqn)
        except AttributeError, e:
            logger.warning ("actions.create(): %s, shortcut for %s not set", e.args[0], fqn)
        else:
            fqn= "satyr."+fqn
            action= KAction (text, parent)
            action.setObjectName (fqn)
            if globalSC:
                action.setGlobalShortcut (shortcut)
            else:
                action.setShortcut (shortcut)
            ac.addAction (fqn, action)

            # the skin can decide to not implement an action!
            method= getattr (obj, name, None)
            if method is not None:
                action.triggered.connect (method)
            else:
                logger.warning ("actions.create(): no method %s, shortcut for %s not set", name, fqn)

# end
