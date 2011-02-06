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
import styles
from model.virtualhelix import VirtualHelix


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
    rect = QRectF(0, 0, 2 * radius, 2 * radius)

    def __init__(self, row, col, position, parent):
        """
        
        parent: a slice helix group
        """
        super(SliceHelix, self).__init__()
        self.parent = parent
        self.scene = parent.scene
        # data related
        self.row = row
        self.col = col
        self.parity = (row % 2) ^ (col % 2)
        self.p0neighbor = None
        self.p1neighbor = None
        self.p2neighbor = None
        self.number = -1
        self.vhelix = None
        self.label = None
        # drawing related
        self.focusRing = None
        self.beingHoveredOver = False
        self.setAcceptsHoverEvents(True)
        self.setPos(position)

    def paint(self, painter, option, widget=None):
        if self.number >= 0:
            painter.setBrush(self.useBrush)
            painter.setPen(self.usePen)
        else:
            painter.setBrush(self.defBrush)
            painter.setPen(self.defPen)
        if self.beingHoveredOver:
            painter.setPen(self.hovPen)
        painter.drawEllipse(self.rect)
    # end def

    class FocusRingPainter(QGraphicsItem):
        """Draws a focus ring around helix in parent"""
        def __init__(self, helix, scene):
            super(SliceHelix.FocusRingPainter, self).__init__()
            self.scene = scene
            self.helix = helix
            self.setPos(helix.pos())
            scene.addItem(self)

        def paint(self, painter, option, widget=None):
            painter.setPen(SliceHelix.hovPen)
            painter.drawEllipse(self.helix.rect)
            bringToFront(self, self.scene)

        def boundingRect(self):
            return self.helix.rect
    # end class

    def boundingRect(self):
        return self.rect

    def hoverEnterEvent(self, event):
        """hoverEnterEvent changes the SliceHelix brush and pen from default
        to the hover colors if necessary."""
        if self.focusRing == None:
            self.focusRing = SliceHelix.FocusRingPainter(self,\
                                                         self.parent.scene)
        self.update(self.rect)
    # end def

    def hoverLeaveEvent(self, event):
        """hoverEnterEvent changes the SliceHelix brush and pen from hover
        to the default colors if necessary."""
        if self.focusRing != None:
            self.focusRing.setParentItem(None)
            self.focusRing = None
        self.update(self.rect)
    # end def

    def mousePressEvent(self, event):
        self.setUsed(not self.number >= 0)
        QDrag(self.parent.parentWidget())
    # end def

    def dragEnterEvent(self, e):
        self.setUsed(not self.number >= 0)
        e.acceptProposedAction()
        print "dee"
    # end def

    class RenumberCommand(QUndoCommand):
        def __init__(self, helix, fromNum, toNum):
            super(SliceHelix.RenumberCommand, self).__init__()
            self.fromNum = fromNum
            self.toNum = toNum
            self.helix = helix

        def redo(self):
            self.helix.setNumber(self.toNum, pushToUndo=False)

        def undo(self):
            self.helix.setNumber(self.fromNum, pushToUndo=False)
    # end class

    def setNumber(self, n, pushToUndo=True):
        """
        If n!=slice.number the caller should have already reserved n with
        the parent SliceHelixGroup (from self.parent.reserveLabelForHelix).
        The callee tells the SliceHelixGroup to recycle the old value.
        """
        if pushToUndo:
            self.parent.sliceController.mainWindow.undoStack.push(\
                        SliceHelix.RenumberCommand(self, self.number, n))
        self.update(self.rect)
        if n != self.number and self.number >= 0:
            self.parent.recycleLabelForHelix(self.number, self)
        if n < 0:
            if self.label:
                self.label.setParentItem(None)
                self.label = None
            self.number = -1
            return
        self.number = n
        if self.label == None:
            self.label = QGraphicsSimpleTextItem("%d" % self.number)
            self.label.setParentItem(self)
        y_val = self.radius / 2
        if self.number < 10:
            #self.label.setX(self.radius / 1.3)
            self.label.setPos(self.radius / 1.3, y_val)
        elif self.number < 100:
            #self.label.setX(self.radius / 2)
            self.label.setPos(self.radius / 2, y_val)
        else:   # added for bigger than 100 by NC
            #self.label.setX(self.radius / 4)
            self.label.setPos(self.radius / 4, y_val)
        bringToFront(self, self.scene)
    # end def

    def setUsed(self, u):
        """
        Handles user click on SliceHelix in two possible ways:
        
        1. If the SliceHelix has never been used, reserver a new label
        from the parent SliceHelixGroup, create a new VirtualHelix vhelix,
        and notify the PathHelixGroup that it should create a new
        PathHelix that points to vhelix.
        
        2. If the SliceHelix has been used previously, try to add some
        scaffold at the currently selected position in the path view.
        """
        if (self.number >= 0) == u:
            # self.parent.addBasesToDnaPart(self.number)
            pass
        if self.number < 0:  # Use
            self.setNumber(self.parent.reserveLabelForHelix(self))
            part = self.parent.dnaPartInst.part()
            self.vhelix = part.addVirtualHelix(self.number)
            self.parent.addVirtualHelixToPathGroup(self.pos(), self.number)
            # self.parent.addBasesToDnaPart(self.number)
        else:  # Unuse
            # self.setNumber(-1)
            pass
    # end def

    def add(self):
        """docstring for add"""
        pass
    # end def
# end class


def bringToFront(target, scene):
    """collidingItems gets a list of all items that overlap. sets
    this items zValue to one higher than the max."""
    zval = 1
    items = scene.items(target.boundingRect()) # the is a QList
    for item in items:
        temp = item.zValue()
        if temp >= zval:
            zval = item.zValue() + 1
        # end if
    # end for
    target.setZValue(zval)
