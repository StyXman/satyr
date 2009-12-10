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
from PyKDE4.kdeui import KAction
from PyQt4.QtCore import Qt

def create (parent, ac):
    """here be common actions for satyr skins"""
    # queueAction= actionCollection ().addAction ("queue")
    queueAction= KAction (parent)
    queueAction.setShortcut (Qt.CTRL + Qt.Key_Q)
    ac.addAction ("queue", queueAction)
    # FIXME? if we don't do this then the skin will be able to choose whether it
    # wants the action or not. with this it will still be able to do it, but via
    # implementing empty slots
    queueAction.triggered.connect (parent.queue)
    print "actions created"

# end
