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
slicehelix.py

Created by Shawn on 2010-06-15.
"""

from PyQt4.QtCore import QRectF
from PyQt4.QtGui import QBrush
from PyQt4.QtGui import QGraphicsItem
from PyQt4.QtGui import QGraphicsSimpleTextItem
from PyQt4.QtGui import QPen, QDrag, QUndoCommand
from PyQt4.QtCore import QString, Qt
import ui.styles as styles
from model.virtualhelix import VirtualHelix
from model.enum import Parity, StrandType


class SliceHelix(QGraphicsItem):
    """docstring for SliceHelix"""
    # set up default, hover, and active drawing styles
    defBrush = QBrush(styles.grayfill)
    defPen = QPen(styles.graystroke, styles.SLICE_HELIX_STROKE_WIDTH)
    hovBrush = QBrush(styles.bluefill)
    hovPen = QPen(styles.bluestroke, styles.SLICE_HELIX_HILIGHT_WIDTH)
    useBrush = QBrush(styles.orangefill)
    usePen = QPen(styles.orangestroke, styles.SLICE_HELIX_STROKE_WIDTH)
    radius = styles.SLICE_HELIX_RADIUS
    outOfSlicePen = QPen(styles.lightorangestroke,\
                         styles.SLICE_HELIX_STROKE_WIDTH)
    outOfSliceBrush = QBrush(styles.lightorangefill)
    rect = QRectF(0, 0, 2 * radius, 2 * radius)

    def __init__(self, row, col, parent=None):
        """docstring for __init__"""
        super(SliceHelix, self).__init__(parent)
        self._parent = parent
        self._row = row
        self._col = col
        # drawing related
        self.focusRing = None
        self.beingHoveredOver = False
        self.setAcceptsHoverEvents(True)
        self.undoStack = self._parent.sliceController.mainWindow.undoStack
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setZValue(styles.ZSLICEHELIX)

    def part(self):
        return self._parent.part()

    def virtualHelix(self):
        if not self.part():
            return None
        return self.part().getVirtualHelix((self._row, self._col),\
                                            returnNoneIfAbsent=True)

    def number(self):
        return self.virtualHelix().number()

    def row(self):
        return self._row

    def col(self):
        return self._col

    def selected(self):
        return self.focusRing != None

    def setSelected(self, select):
        if select and not self.focusRing:
            self.focusRing = SliceHelix.FocusRingPainter(self.parentItem())
            self.focusRing.setPos(self.pos())
            self.focusRing.setZValue(styles.ZFOCUSRING)
        if not select and self.focusRing:
            self.focusRing.setParentItem(None)
            self.focusRing = None

    ############################ Painting ############################
    class FocusRingPainter(QGraphicsItem):
        def paint(self, painter, option, widget=None):
            painter.setPen(SliceHelix.hovPen)
            painter.drawEllipse(SliceHelix.rect)

        def boundingRect(self):
            return SliceHelix.rect.adjusted(-1, -1, 2, 2)

    def paint(self, painter, option, widget=None):
        vh = self.virtualHelix()
        if vh:
            if vh.hasBaseAt(StrandType.Scaffold, self.part().activeSlice()):
                painter.setBrush(self.useBrush)
                painter.setPen(self.usePen)
            else:
                painter.setBrush(self.outOfSliceBrush)
                painter.setPen(self.outOfSlicePen)
            painter.drawEllipse(self.rect)
            num = QString(str(self.virtualHelix().number()))
            painter.setPen(Qt.SolidLine)
            painter.setBrush(Qt.NoBrush)
            painter.drawText(0, 0, 2 * self.radius, 2 * self.radius,\
                             Qt.AlignHCenter + Qt.AlignVCenter, num)
        else:  # We are virtualhelix-less
            pass
            painter.setBrush(self.defBrush)
            painter.setPen(self.defPen)
            painter.drawEllipse(self.rect)
        if self.beingHoveredOver:
            painter.setPen(self.hovPen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(self.rect)

    def boundingRect(self):
        return self.rect

    ############################ User Interaction ############################
    def mouseDoubleClickEvent(self, event):
        self.createOrAddBasesToVirtualHelix(\
            addBases=True,\
            addToScaffold=event.modifiers() & Qt.ShiftModifier > 0)

    def mousePressEvent(self, event):
        # self.createOrAddBasesToVirtualHelix()
        self.createOrAddBasesToVirtualHelix(\
            addBases=True,\
            addToScaffold=event.modifiers() & Qt.ShiftModifier > 0)
        if event.modifiers() & Qt.ShiftModifier:
            self.virtualHelix().setSelected(True)
        else:
            self.part().setSelection((self.virtualHelix(),))

    def hoverEnterEvent(self, event):
        # If the selection is configured to always select
        # everything, we don't draw a focus ring around everything,
        # instead we only draw a focus ring around the hovered obj.
        if self.part().selectAllBehavior:
            self.setSelected(True)

    def hoverLeaveEvent(self, event):
        if self.part().selectAllBehavior:
            self.setSelected(False)

    # def createOrAddBasesToVirtualHelix(self, addBasesIfVHExists=False,\
    #                                          addToScaffold=False):
    #     coord = (self._row, self._col)
    #     vh = self.virtualHelix()
    #     index = self.part().activeSlice()
    #     if not vh:
    #         vh = VirtualHelix()
    #         self.part().setVirtualHelixAt(coord, vh)
    #         vh.basesModified.connect(self.update)
    #     elif addBasesIfVHExists:
    #         vh = self.virtualHelix()
    #         nb = vh.numBases()
    #         vh.connectStrand(StrandType.Scaffold\
    #                          if addToScaffold\
    #                          else StrandType.Staple, index - 1, index + 1)

    def createOrAddBasesToVirtualHelix(self, addBases=False,\
                                             addToScaffold=False):
        coord = (self._row, self._col)
        vh = self.virtualHelix()
        index = self.part().activeSlice()
        if not vh:
            vh = VirtualHelix()
            self.part().setVirtualHelixAt(coord, vh)
            vh.basesModified.connect(self.update)
        if addBases and addToScaffold:
            vh.connectStrand(StrandType.Scaffold, index - 1, index + 1)
        elif addBases and not addToScaffold:
            vh.connectStrand(StrandType.Staple, index - 1, index + 1)
    # end def


# end class
