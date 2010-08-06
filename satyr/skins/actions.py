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
from PyKDE4.kdeui import KAction
from PyQt4.QtCore import Qt

def create (parent, ac):
    """here be common actions for satyr skins"""
    actions= (
        ("queue",     Qt.CTRL+Qt.Key_Q),
        ("rename",    Qt.CTRL+Qt.Key_R),
        ("toggleVA",  Qt.CTRL+Qt.Key_V),
        )

    for name, shortcut in actions:
        action= KAction (parent)
        action.setShortcut (shortcut)
        ac.addAction (name, action)

        # the skin can decide to not implement an action!
        method= getattr (parent, name, None)
        if method is not None:
            action.triggered.connect (method)
        else:
            print "actions.create(): no method", name

# end
