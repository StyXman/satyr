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
from PyKDE4.kdeui import KLineEdit
from PyQt4.QtCore import Qt

# logging
import logging
logger = logging.getLogger(__name__)

class SearchEntry (KLineEdit):

    def keyPressEvent (self, event):
        if event.key ()==Qt.Key_Escape:
            self.setText ('')
        else:
            KLineEdit.keyPressEvent (self, event)

# end
