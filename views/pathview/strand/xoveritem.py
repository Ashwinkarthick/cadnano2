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
xoveritem.py
Created by Nick on 2011-05-25.
"""
from exceptions import AttributeError, NotImplementedError
import time
from views import styles

import util, time

# import Qt stuff into the module namespace with PySide, PyQt4 independence
util.qtWrapImport('QtCore', globals(), ['QPointF', 'QRectF', 'Qt', 'QEvent'])
util.qtWrapImport('QtGui', globals(), ['QBrush', 'QFont', 'QGraphicsItem',\
                                'QGraphicsSimpleTextItem', 'QPen',\
                                'QPolygonF', 'QPainterPath', 'QGraphicsRectItem', \
                                'QColor', 'QFontMetrics', 'QGraphicsPathItem'])

_baseWidth = styles.PATH_BASE_WIDTH
_toHelixNumFont = styles.XOVER_LABEL_FONT
# precalculate the height of a number font.  Assumes a fixed font
# and that only numbers will be used for labels
_fm = QFontMetrics(_toHelixNumFont)
_enabbrush = QBrush(Qt.SolidPattern)  # Also for the helix number label
_nobrush = QBrush(Qt.NoBrush)
# _rect = QRectF(0, 0, baseWidth, baseWidth)
_xScale = styles.PATH_XOVER_LINE_SCALE_X  # control point x constant
_yScale = styles.PATH_XOVER_LINE_SCALE_Y  # control point y constant
_rect = QRectF(0, 0, _baseWidth, _baseWidth)

class XoverNode3(QGraphicsRectItem):
    """
    This is a QGraphicsRectItem to allow actions and also a 
    QGraphicsSimpleTextItem to allow a label to be drawn
    """
    def __init__(self, virtualHelixItem, xoverItem, strand3p, idx):
        super(XoverNode3, self).__init__(virtualHelixItem)
        self._vhi = virtualHelixItem
        self._xoverItem = xoverItem
        self._idx = idx
        self._isOnTop = virtualHelixItem.isStrandOnTop(strand3p)
        self._isDrawn5to3 = strand3p.strandSet().isDrawn5to3()
        self._strandType = strand3p.strandSet().strandType()

        self.setPartnerVirtualHelix(strand3p)

        self.setPen(QPen(Qt.NoPen))
        self._label = None
        self.setPen(QPen(Qt.NoPen))
        self.setBrush(_nobrush)
        self.setRect(_rect)
    # end def
    
    def updateForFloat(self, virtualHelixItem, strand3p, idx):
        self._vhi = virtualHelixItem
        self.setParentItem(virtualHelixItem)
        self._idx = idx
        self._isOnTop = virtualHelixItem.isStrandOnTop(strand3p)
        self._strandType = strand3p.strandSet().strandType()
        self.updatePositionAndAppearance()
    # end def
    
    def setFixed(self, virtualHelixItem, xoverItem, strand3p, idx):

    # end def

    def strandType(self):
        return self._strandType
    # end def

    def refreshXover(self):
        self._xoverItem.refreshXover()
    # end def

    def setPartnerVirtualHelix(self,strand):
        if strand.connection5p():
            self._partnerVirtualHelix = strand.connection5p().virtualHelix()
        else:
            self._partnerVirtualHelix = None
    # end def

    def idx(self):
        return self._idx
    # end def

    def virtualHelixItem(self):
        return self._vhi
    # end def

    def point(self):
        return self._vhi.upperLeftCornerOfBaseType(self._idx, self._strandType)
    # end def

    def isOnTop(self):
        return self._isOnTop
    # end def

    def isDrawn5to3(self):
        return self._isDrawn5to3
    # end def

    def updatePositionAndAppearance(self):
        """
        Sets position by asking the VirtualHelixItem
        Sets appearance by choosing among pre-defined painterpaths (from
        normalstrandgraphicsitem) depending on drawing direction.
        """
        self.setPos(*self.point())
        # We can only expose a 5' end. But on which side?
        isLeft = True if self._isDrawn5to3 else False
        self.updateLabel(isLeft)
    # end def

    def updateConnectivity(self):
        isLeft = True if self._isDrawn5to3 else False
        self.updateLabel(isLeft)
    # end def

    def remove(self):
        """
        Clean up this joint
        """
        scene = self.scene()
        scene.removeItem(self._label)
        self._label = None
        scene.removeItem(self)
    # end def

    def updateLabel(self, isLeft):
        """
        Called by updatePositionAndAppearance during init, or later by
        updateConnectivity. Updates drawing and position of the label.
        """
        lbl = self._label
        if self._idx != None:
            if lbl == None:
                bw = _baseWidth
                num = self._partnerVirtualHelix.number()
                tBR = _fm.tightBoundingRect(str(num))
                halfLabelH = tBR.height()/2.0
                halfLabelW = tBR.width()/2.0
                # determine x and y positions
                labelX = bw/2.0 - halfLabelW
                if self._isOnTop:
                    labelY = -0.25*halfLabelH - 0.5 - 0.5*bw
                else:
                    labelY = 2*halfLabelH + 0.5 + 0.5*bw
                # adjust x for left vs right
                labelXoffset = 0.25*bw if isLeft else -0.25*bw
                labelX += labelXoffset
                # adjust x for numeral 1
                if num == 1: labelX -= halfLabelW/2.0
                # create text item
                lbl = QGraphicsSimpleTextItem(str(num), self)
                lbl.setPos(labelX, labelY)
                lbl.setBrush(_enabbrush)
                lbl.setFont(_toHelixNumFont)
                self._label = lbl
            # end if
            lbl.setText( str(self._partnerVirtualHelix.number()) )
        # end if
    # end def

# end class


class XoverNode5(XoverNode3):
    """
    XoverNode5 is the partner of XoverNode3. It dif
    XoverNode3 handles:
    1. Drawing of the 5' end of an xover, and its text label. Drawing style
    is determined by the location of the xover with in a vhelix (is it a top
    or bottom vstrand?).
    2. Notifying XoverStrands in the model when connectivity changes.

    """
    def __init__(self, virtualHelixItem, xoverItem, strand5p, idx):
        super(XoverNode5, self).__init__(virtualHelixItem, xoverItem, strand5p, idx)
    # end def

    def setPartnerVirtualHelix(self, strand):
        if strand.connection3p():
            self._partnerVirtualHelix = strand.connection3p().virtualHelix()
        else:
            self._partnerVirtualHelix = None
    # end def

    def updatePositionAndAppearance(self):
        """Same as XoverItem3, but exposes 3' end"""
        self.setPos(*self.point())
        # # We can only expose a 3' end. But on which side?
        isLeft = False if self._isDrawn5to3 else True
        self.updateLabel(isLeft)
    # end def
# end class

class XoverItem(QGraphicsPathItem):
    """
    This class handles:
    1. Drawing the spline between the XoverNode3 and XoverNode5 graphics
    items in the path view.

    XoverItem should be a child of a PartItem.
    """

    def __init__(self, virtualHelixItem):
        """
        strandItem is a the model representation of the 5prime most strand
        of a Xover
        """
        super(XoverItem, self).__init__(virtualHelixItem.partItem())
        self._virtualHelixItem = virtualHelixItem
        self._strand5p = None
        self._node5 = None
        self._node3 = None
        self.hide()
    # end def

    ### SLOTS ###

    ### METHODS ###
    def remove(self):
        scene = self.scene()
        if self._node3:
            scene.removeItem(self._node3)
            scene.removeItem(self._node5)
        scene.removeItem(self)
    # end def

    def hideIt(self):
        self.hide()
        if self._node3:
            self._node3.hide()
            self._node5.hide()
    # end def

    def showIt(self):
        self.show()
        if self._node3:
            self._node3.show()
            self._node5.show()
    # end def

    def refreshXover(self):
        if self._strand5p:
            self.update(self._strand5p)
    # end def

    def update(self, strand5p, idx=None):
        """
        Pass idx to this method in order to install a floating
        Xover for the forced xover tool
        """
        self._strand5p = strand5p
        strand3p = strand5p.connection3p()
        vhi5p = self._virtualHelixItem
        partItem = vhi5p.partItem()
        
        # This condition is for floating xovers
        idx3Prime = idx if idx else strand5p.idx3Prime()
        
        if self._node5 == None:
            self._node5 = XoverNode5(vhi5p, self, strand5p, idx3Prime)
        if strand3p != None:
            if self._node3 == None:
                vhi3p = partItem.itemForVirtualHelix(strand3p.virtualHelix())
                self._node3 = XoverNode3(vhi3p, self, strand3p, strand3p.idx5Prime())

            self._node5.setPartnerVirtualHelix(strand5p)
            self._updatePath(strand5p)
        # end if
    # end def
    
    def updateFloating(self, virtualHelixItem, strand3p, idx):
        # floating Xover!
        if self._node3 == None: 
            self._node3 = XoverNode3(None, self, None, None)
        # end if
        self._node3.updateForFloat(virtualHelixItem, strand3p, idx)
    # end def

    def _updatePath(self, strand5p):
        """
        Draws a quad curve from the edge of the fromBase
        to the top or bottom of the toBase (q5), and
        finally to the center of the toBase (toBaseEndpoint).

        If floatPos!=None, this is a floatingXover and floatPos is the
        destination point (where the mouse is) while toHelix, toIndex
        are potentially None and represent the base at floatPos.

        """
        # print "updating xover curve", self.parentObject()
        node3 = self._node3
        node5 = self._node5

        bw = _baseWidth
        
        vhi5 = self._virtualHelixItem
        partItem = vhi5.partItem()
        pt5 = vhi5.mapToItem(partItem, *node5.point())
                            
        fiveIsTop = node5.isOnTop()
        fiveIs5to3 = node5.isDrawn5to3()
        
        if node3.idx() == None: # is it a floating Xover?
            pt3 = strand.pt3()  # NEED TO UPDATE THIS FLOATING POINT
            vhi3 = None
            threeIsTop = True
            threeIs5to3 = True
            isFloating = True
            sameStrand = False
            sameParity = False
        else:
            vhi3 = node3.virtualHelixItem()
            pt3 = vhi3.mapToItem(partItem, *node3.point())

            threeIsTop = node3.isOnTop()
            threeIs5to3 = node3.isDrawn5to3()
            isFloating = False
            sameStrand = (node5.strandType() == node3.strandType()) and vhi3 == vhi5
            sameParity = fiveIs5to3 == threeIs5to3

        # Null source / dest => don't paint ourselves => no painterpath
        if pt3 == None or pt5 == None:
            self.hide()
            return None
        else:
            self.show()

        # Enter/exit are relative to the direction that the path travels
        # overall.
        fiveEnterPt = pt5 + QPointF(0 if fiveIs5to3 else 1, .5)*bw
        fiveCenterPt = pt5 + QPointF(.5, .5)*bw
        fiveExitPt = pt5 + QPointF(.5, 0 if fiveIsTop else 1)*bw
        if isFloating:
            threeEnterPt = threeCenterPt = threeEnterPt = pt3
        else:
            threeEnterPt = pt3 + QPointF(.5, 0 if threeIsTop else 1)*bw
            threeCenterPt = pt3 + QPointF(.5, .5)*bw
            threeExitPt = pt3 + QPointF(1 if threeIs5to3 else 0, .5)*bw

        c1 = QPointF()
        # case 1: same strand
        if sameStrand:
            dx = abs(threeEnterPt.x() - fiveExitPt.x())
            c1.setX(0.5 * (fiveExitPt.x() + threeEnterPt.x()))
            if fiveIsTop:
                c1.setY(fiveExitPt.y() - _yScale * dx)
            else:
                c1.setY(fiveExitPt.y() + _yScale * dx)
        # case 2: same parity
        elif sameParity:
            dy = abs(threeEnterPt.y() - fiveExitPt.y())
            c1.setX(fiveExitPt.x() + _xScale * dy)
            c1.setY(0.5 * (fiveExitPt.y() + threeEnterPt.y()))
        # case 3: different parity
        else:
            if fiveIsTop and fiveIs5to3:
                c1.setX(fiveExitPt.x() - _xScale *\
                        abs(threeEnterPt.y() - fiveExitPt.y()))
            else:
                c1.setX(fiveExitPt.x() + _xScale *\
                        abs(threeEnterPt.y() - fiveExitPt.y()))
            c1.setY(0.5 * (fiveExitPt.y() + threeEnterPt.y()))

        # Construct painter path
        painterpath = QPainterPath()
        if strand5p.connection5p() != None:
            # The xover5's non-crossing-over end (5') has a connection
            painterpath.moveTo(fiveEnterPt)
            painterpath.lineTo(fiveCenterPt)
            painterpath.lineTo(fiveExitPt)
        else:
            painterpath.moveTo(fiveCenterPt)
            painterpath.lineTo(fiveExitPt)
        if strand5p.connection3p().connection3p() != None:
            # The xover5's non-crossing-over end (3') has a connection
            painterpath.quadTo(c1, threeEnterPt)
            painterpath.lineTo(threeCenterPt)
            painterpath.lineTo(threeExitPt)
        else:
            painterpath.quadTo(c1, threeEnterPt)
            painterpath.lineTo(threeCenterPt)
            
        node3.updatePositionAndAppearance()
        node5.updatePositionAndAppearance()
        self.setPath(painterpath)
        self._updatePen(strand5p)
    # end def

    def _updatePen(self, strand5p):
        oligo = strand5p.oligo()
        color = QColor(oligo.color())
        penWidth = styles.PATH_STRAND_STROKE_WIDTH
        if oligo.shouldHighlight():
            penWidth = styles.PATH_STRAND_HIGHLIGHT_STROKE_WIDTH
            color.setAlpha(128)
        pen = QPen(color, penWidth)
        pen.setCapStyle(Qt.FlatCap)
        self.setPen(pen)
    # end def
# end class XoverItem