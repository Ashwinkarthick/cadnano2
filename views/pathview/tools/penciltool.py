# The MIT License
#
# Copyright (c) 2011 Wyss Institute at Harvard University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# http://www.opensource.org/licenses/mit-license.php

"""
penciltool
Created by Nick Conway on 2011-06-04.
"""

from selecttool import SelectTool
from forcetool import ForceTool

import util
# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtCore', globals(), ['Qt'])
util.qtWrapImport('QtGui', globals(), [ 'QGraphicsItem', 'QBrush', 'QFont',
                                        'QGraphicsSimpleTextItem', 'QPen',\
                                        'QPolygonF', 'QPainterPath'])

class PencilTool(SelectTool, ForceTool):
    """PencilTool allows for creation of new staple or scaffold strands
    by clicking and dragging on empty bases."""
    # We are just like select tool except we don't enforce drag limits
    limitEndptDragging = False
    disallowClickBreaksStrand = False
    # And we actually use those PathHelixGroup events
    mouseMovePathHelixGroupUnused = False
    mouseReleasePathHelixGroupUnused = False
    mousePressPathHelixGroupUnused = False
    
    def __init__(self, controller):
        super(PencilTool, self).__init__(controller, rightClickOnly=True)

    def mousePressPathHelix(self, pathHelix, event):
        draggingForceCrossover = False
        if pathHelix:
            phg = pathHelix.pathHelixGroup()
            draggingForceCrossover = phg.dragging
        if event.button() & Qt.RightButton or draggingForceCrossover:
            ForceTool.mousePressPathHelix(self, pathHelix, event)
        elif event.buttons() & Qt.LeftButton:
            SelectTool.mousePressPathHelix(self, pathHelix, event)

    def mouseMovePathHelix(self, pathHelix, event):
        if event.buttons() & Qt.LeftButton:
            SelectTool.mouseMovePathHelix(self, pathHelix, event)
        elif event.buttons() & Qt.RightButton:
            ForceTool.mouseMovePathHelix(self, pathHelix, event)

    def mouseReleasePathHelix(self, pathHelix, event):
        SelectTool.mouseReleasePathHelix(self, pathHelix, event)
        ForceTool.mouseReleasePathHelix(self, pathHelix, event)

    def hoverMovePathHelix(self, pathHelix, event):
        ForceTool.hoverMovePathHelix(self, pathHelix, event)

    def hoverMovePathHelixGroup(self, phg, event):
        ForceTool.hoverMovePathHelixGroup(self, phg, event)
