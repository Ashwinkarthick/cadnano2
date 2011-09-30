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
helixitem.py
Created by Nick on 2011-09-28.
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

#from .src.graphicsellipseitem import GraphicsEllipseItem

class HelixItem(QGraphicsEllipseItem):
    """docstring for HelixItem"""
    
    # set up default, hover, and active drawing styles
    _defaultBrush = QBrush(styles.grayfill)
    _defaultPen = QPen(styles.graystroke, styles.SLICE_HELIX_STROKE_WIDTH)
    _hoverBrush = QBrush(styles.bluefill)
    _hoverPen = QPen(styles.bluestroke, styles.SLICE_HELIX_HILIGHT_WIDTH)
    _radius = styles.SLICE_HELIX_RADIUS
    temp = styles.SLICE_HELIX_STROKE_WIDTH
    _rectDefault = QRectF(0, 0, 2 * _radius, 2 * _radius)
    temp = (styles.SLICE_HELIX_HILIGHT_WIDTH - temp)/2
    _rectHovered = _rectDefault.adjusted(-temp, -temp, temp, temp)
    _ZDefault = styles.ZSLICEHELIX 
    _ZHovered = _ZDefault+1 
    temp /= 2
    _adjustmentPlus = (temp, temp)
    _adjustmentMinus = (-temp, -temp)

    def __init__(self, row, column, partItem):
        """
        row, column is a coordinate in Lattice terms
        partItem is a PartItem that will act as a QGraphicsItem parent
        """
        super(HelixItem, self).__init__(parent=partItem)
        self._partItem = partItem
        self.hide()
        self._isHovered = False
        self.setAcceptsHoverEvents(True)
        
        self.setNotHovered()
        
        x, y = partItem.part().latticeToSpatial(row, column, partItem.scaleFactor())
        self.setPos(x, y)
        self._coord = (row, column)
        self.show()
    # end def
    
    def virtualHelix(self):
        """
        virtualHelixItem should be the HelixItems only child if it exists
        and virtualHelix should be it member
        """
        temp = self.virtualHelixItem()
        if temp:
            return temp.virtualHelix()
        else:
            return None
    # end def
    
    def virtualHelixItem(self):
        """
        virtualHelixItem should be the HelixItems only child if it exists
        and virtualHelix should be it member
        """
        temp = self.childItems()
        if len(temp) > 0:
            return temp[0]
        else:
            return None
    # end def
    
    def part(self):
        return self._partItem.part()
    # end def
    
    def translateVH(self, delta):
        """
        used to update a child virtual helix position on a hover event
        delta is a tuple of x and y values to translate
        
        positive delta happens when hover happens
        negative delta when something unhovers
        """
        temp = self.virtualHelixItem()
        
        # xor the check to translate, 
        # convert to a QRectF adjustment if necessary
        check = (delta > 0) ^ self._isHovered
        if temp and check:
            pass
            # temp.translate(*delta)
    # end def
    
    def setHovered(self):
        # self.setFlag(QGraphicsItem.ItemHasNoContents, False)  
        self.setBrush(self._hoverBrush)
        self.setPen(self._hoverPen)
        self.update(self.boundingRect())
        # self.translateVH(self._adjustmentPlus)
        self._isHovered = True
        self.setZValue(self._ZHovered)
        self.setRect(self._rectHovered)
    # end def
    
    def hoverEnterEvent(self, event):
        """
        hoverEnterEvent changes the HelixItem brush and pen from default
        to the hover colors if necessary.
        """
        self.setHovered()
    # end def
    
    def setNotHovered(self):
        """
        """
        # drawMe = False if self.virtualHelixItem() else True
        # self.setFlag(QGraphicsItem.ItemHasNoContents, drawMe)  
        self.setBrush(self._defaultBrush)
        self.setPen(self._defaultPen)
        # self.translateVH(self._adjustmentMinus)
        self._isHovered = False
        self.setZValue(self._ZDefault)
        self.setRect(self._rectDefault)
    # end def

    def hoverLeaveEvent(self, event):
        """
        hoverEnterEvent changes the HelixItem brush and pen from hover
        to the default colors if necessary.
        """
        self.setNotHovered()
    # end def
    
    def mousePressEvent(self, event):
        action = self.decideAction(event.modifiers())
        action(self)
        self.dragSessionAction = action
    # end def

    def mouseMoveEvent(self, event):
        partItem = self._partItem
        posInParent = partItem.mapFromItem(self, QPointF(event.pos()))
        # Qt doesn't have any way to ask for graphicsitem(s) at a
        # particular position but it *can* do intersections, so we
        # just use those instead
        partItem.probe.setPos(posInParent)
        for ci in partItem.probe.collidingItems():
            if isinstance(ci, HelixItem):
                self.dragSessionAction(ci)
    # end def

    # def mouseReleaseEvent(self, event):
    #     self.part().partNeedsFittingToViewSignal.emit()
    # # end def 

    def decideAction(self, modifiers):
        """ On mouse press, an action (add scaffold at the active slice, add
        segment at the active slice, or create virtualhelix if missing) is
        decided upon and will be applied to all other slices happened across by
        mouseMoveEvent. The action is returned from this method in the form of a
        callable function."""
        vh = self.virtualHelix()
        part = self.part()
        
        if vh == None: 
            return HelixItem.addVHIfMissing
            
        idx = part.activeBaseIndex()
        scafSSet, stapSSet = vh.getStrandSets()
        if modifiers & Qt.ShiftModifier:
            if not stapSSet.hasStrandAt(idx-1, idx+1):
                print "add a staple strand"
                return HelixItem.addStapAtActiveSliceIfMissing
            else:
                return HelixItem.nop
        if not scafSSet.hasStrandAt(idx-1, idx+1):
            print "add a scaffold strand"
            return HelixItem.addScafAtActiveSliceIfMissing
        return HelixItem.nop
    # end def

    def nop(self):
        pass
    
    def addScafAtActiveSliceIfMissing(self):
        vh = self.virtualHelix()
        part = self.part()
        if vh == None: 
            return
            
        idx = part.activeBaseIndex()
        startIdx = max(0,idx-1)
        endIdx = min(idx+1, part.dimensions()[1]-1)
        vh.scaffoldStrandSet().createStrand(startIdx, endIdx)
    # end def

    def addStapAtActiveSliceIfMissing(self):
        vh = self.virtualHelix()
        part = self.part()
        
        if vh == None: 
            return
            
        idx = part.activeBaseIndex()
        if vh.scaf().get(idx) != None: 
            return
            
        startIdx = max(0,idx-1)
        endIdx = min(idx+1, part.dimensions()[1]-1)
        vh.scaffoldStrandSet().createStrand(startIdx, endIdx)
    # end def

    def addVHIfMissing(self):
        vh = self.virtualHelix()
        coord = self._coord
        part = self.part()
        
        if vh != None: 
            return
        uS = part.undoStack()
        uS.beginMacro("Slice Click")
        part.createVirtualHelix(*coord)
        # vh.scaffoldStrandSet().createStrand(startIdx, endIdx)
        uS.endMacro()
    # end def
    
    