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
pathhelixhandle.py
Created by Shawn on 2011-02-05.
"""
from views import styles

import util
# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtCore', globals(), ['QPointF', 'QRectF', 'Qt'])
util.qtWrapImport('QtGui', globals(), ['QBrush', 'QFont', 'QGraphicsItem',\
                                       'QGraphicsSimpleTextItem', 'QPen',\
                                       'QGraphicsTextItem', 'QDrag', \
                                       'QUndoCommand', 'QGraphicsEllipseItem',\
                                       'QTransform', 'QStyle'])

_radius = styles.VIRTUALHELIXHANDLEITEM_RADIUS
_rect = QRectF(0, 0, 2*_radius + styles.VIRTUALHELIXHANDLEITEM_STROKE_WIDTH,\
        2*_radius + styles.VIRTUALHELIXHANDLEITEM_STROKE_WIDTH)
_defBrush = QBrush(styles.grayfill)
_defPen = QPen(styles.graystroke, styles.VIRTUALHELIXHANDLEITEM_STROKE_WIDTH)
_hovBrush = QBrush(styles.bluefill)
_hovPen = QPen(styles.bluestroke, styles.VIRTUALHELIXHANDLEITEM_STROKE_WIDTH)
_useBrush = QBrush(styles.orangefill)
_usePen = QPen(styles.orangestroke, styles.VIRTUALHELIXHANDLEITEM_STROKE_WIDTH)
_font = styles.VIRTUALHELIXHANDLEITEM_FONT


class VirtualHelixHandleItem(QGraphicsEllipseItem):
    """docstring for VirtualHelixHandleItem"""
    def __init__(self, virtualHelix, partItem):
        super(VirtualHelixHandleItem, self).__init__(partItem)
        self._virtualHelix = virtualHelix
        self._partItem = partItem
        self._beingHoveredOver = False
        self.setAcceptsHoverEvents(True)
        # handle the label specific stuff
        self._label = self.createLabel()
        self.setNumber()
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges)
        self.penAndBrushSet(False)
        self.setZValue(styles.ZPATHHELIX)
        self.setRect(_rect)
    # end def

    def penAndBrushSet(self, value):
        if self.number() >= 0:
            if value == True:
                self.setBrush(_hovBrush)
                self.setPen(_hovPen)
            else:
                self.setBrush(_useBrush)
                self.setPen(_usePen)
        else:
            self.setBrush(_defBrush)
            self.setPen(_defPen)
        self.update(self.boundingRect())
    # end def

    def paint(self, painter, option, widget):
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawEllipse(self.rect())
    # end def
    
    def remove(self):
        scene = self.scene()
        scene.removeItem(self._label)
        scene.removeItem(self)
        self._label = None
    # end def

    def someVHChangedItsNumber(self, r, c):
        # If it was our VH, we need to update the number we
        # are displaying!
        if (r,c) == self.vhelix.coord():
            self.setNumber()
    # end def

    def createLabel(self):
        label = QGraphicsSimpleTextItem("%d" % self._virtualHelix.number())
        label.setFont(_font)
        label.setZValue(styles.ZPATHHELIX)
        label.setParentItem(self)
        return label
    # end def

    def setNumber(self):
        """docstring for setNumber"""
        vh = self._virtualHelix
        num = vh.number()
        label = self._label
        radius = _radius

        label.setText("%d" % num)
        y_val = radius / 3
        if num < 10:
            label.setPos(radius / 1.5, y_val)
        elif num < 100:
            label.setPos(radius / 3, y_val)
        else: # _number >= 100
            label.setPos(0, y_val)
        bRect = label.boundingRect()
        posx = bRect.width()/2
        posy = bRect.height()/2
        label.setPos(radius-posx, radius-posy)
    # end def

    def number(self):
        """docstring for number"""
        return self._virtualHelix.number()

    def hoverEnterEvent(self, event):
        """
        hoverEnterEvent changes the PathHelixHandle brush and pen from default
        to the hover colors if necessary.
        """
        if not self.isSelected():
            if self.number() >= 0:
                if self.isSelected():
                    self.setBrush(_hovBrush)
                else:
                    self.setBrush(_useBrush)
            else:
                self.setBrush(_defBrush)
            self.setPen(_hovPen)
            self.update(self.boundingRect())
    # end def

    def hoverLeaveEvent(self, event):
        """
        hoverEnterEvent changes the PathHelixHanle brush and pen from hover
        to the default colors if necessary.
        """
        if not self.isSelected():
            self.penAndBrushSet(False)
            self.update(self.boundingRect())
    # end def

    def mousePressEvent(self, event):
        """
        All mousePressEvents are passed to the group if it's in a group
        """
        selectionGroup = self.group()
        if selectionGroup != None:
            selectionGroup.mousePressEvent(event)
        else:
            QGraphicsItem.mousePressEvent(self, event)
    # end def

    def mouseMoveEvent(self, event):
        """
        All mouseMoveEvents are passed to the group if it's in a group
        """
        selectionGroup = self.group()
        if selectionGroup != None:
            selectionGroup.mousePressEvent(event)
        else:
            QGraphicsItem.mouseMoveEvent(self, event)
    # end def

    def restoreParent(self, pos=None):
        """
        Required to restore parenting and positioning in the partItem
        """

        # map the position
        partItem = self._partItem
        if pos == None:
            pos = self.scenePos()
        self.setParentItem(partItem)
        self.penAndBrushSet(False)

        assert(self.parentItem() == partItem)
        # print "restore", self.number(), self.parentItem(), self.group()
        assert(self.group() == None)
        tempP = partItem.mapFromScene(pos)
        self.setPos(tempP)
        self.setSelected(False)
    # end def

    def itemChange(self, change, value):
        # for selection changes test against QGraphicsItem.ItemSelectedChange
        # intercept the change instead of the has changed to enable features.
        partItem = self._partItem

        if change == QGraphicsItem.ItemSelectedChange and self.scene():
            selectionGroup = partItem.vhiHandleSelectionGroup()
            lock = selectionGroup.partItem().selectionLock()

            # only add if the selectionGroup is not locked out
            if value == True and (lock == None or lock == selectionGroup):
                if self.group() != selectionGroup:
                    # print "preadd", self.number(), self.parentItem(), self.group()
                    # selectionGroup.addToGroup(self)
                    selectionGroup.pendToAdd(self)
                    # print "postadd", self.number(), self.parentItem(), self.group()
                    selectionGroup.partItem().setSelectionLock(selectionGroup)
                    self.penAndBrushSet(True)
                    return True
            # end if
            elif value == True:
                self.setSelected(False)
            else:
                # print "deselect", self.number(), self.parentItem(), self.group()
                selectionGroup.pendToRemove(self)
                self.penAndBrushSet(False)
                return False
            # end else
        # end if
        return QGraphicsEllipseItem.itemChange(self, change, value)
    # end def
# end class
