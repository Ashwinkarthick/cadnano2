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

from views import styles
import util
util.qtWrapImport('QtGui', globals(), [ 'QBrush', 'QGraphicsLineItem', 'QPen',\
                                        'QColor', 'QPainterPath', 'QPolygonF',\
                                        'QGraphicsPathItem'])
util.qtWrapImport('QtCore', globals(), [ 'QPointF', 'Qt' ])

baseWidth = styles.PATH_BASE_WIDTH
NoPen = QPen(Qt.NoPen)
ppL5 = QPainterPath()  # Left 5' PainterPath
ppR5 = QPainterPath()  # Right 5' PainterPath
ppL3 = QPainterPath()  # Left 3' PainterPath
ppR3 = QPainterPath()  # Right 3' PainterPath
pp53 = QPainterPath()  # Left 5', Right 3' PainterPath
pp35 = QPainterPath()  # Left 5', Right 3' PainterPath
# set up ppL5 (left 5' blue square)
ppL5.addRect(0.25*baseWidth, 0.125*baseWidth,0.75*baseWidth, 0.75*baseWidth)
# set up ppR5 (right 5' blue square)
ppR5.addRect(0, 0.125*baseWidth, 0.75*baseWidth, 0.75*baseWidth)
# set up ppL3 (left 3' blue triangle)
l3poly = QPolygonF()
l3poly.append(QPointF(baseWidth, 0))
l3poly.append(QPointF(0.25*baseWidth, 0.5*baseWidth))
l3poly.append(QPointF(baseWidth, baseWidth))
ppL3.addPolygon(l3poly)
# set up ppR3 (right 3' blue triangle)
r3poly = QPolygonF()
r3poly.append(QPointF(0, 0))
r3poly.append(QPointF(0.75*baseWidth, 0.5*baseWidth))
r3poly.append(QPointF(0, baseWidth))
ppR3.addPolygon(r3poly)
# single base left 5'->3'
pp53.addRect(0, 0.125*baseWidth, 0.5*baseWidth, 0.75*baseWidth)
poly53 = QPolygonF()
poly53.append(QPointF(0.5*baseWidth, 0))
poly53.append(QPointF(baseWidth, 0.5*baseWidth))
poly53.append(QPointF(0.5*baseWidth, baseWidth))
pp53.addPolygon(poly53)
# single base left 3'<-5'
pp35.addRect(0.50*baseWidth, 0.125*baseWidth, 0.5*baseWidth, 0.75*baseWidth)
poly35 = QPolygonF()
poly35.append(QPointF(0.5*baseWidth, 0))
poly35.append(QPointF(0, 0.5*baseWidth))
poly35.append(QPointF(0.5*baseWidth, baseWidth))
pp35.addPolygon(poly35)


class NormalStrandGraphicsItem(QGraphicsLineItem):
    """
    Handles drawing of 'normal' strands (i.e. not xover, loop, or skip).
    """
    def __init__(self, normalStrand, pathHelix):
        QGraphicsLineItem.__init__(self, pathHelix)
        self.normalStrand = normalStrand
        self.pathHelix = pathHelix
        normalStrand.didMove.connect(self.update)
        normalStrand.apparentConnectivityChanged.connect(self.update)
        normalStrand.willBeRemoved.connect(self.remove)
        drawn5To3 = normalStrand.drawn5To3()
        self.leftCap = QGraphicsPathItem(ppL5 if drawn5To3 else ppL3, self)
        self.leftCap.setPen(NoPen)
        self.rightCap = QGraphicsPathItem(ppR3 if drawn5To3 else ppR5, self)
        self.rightCap.setPen(NoPen)
        self.dualCap = QGraphicsPathItem(pp53 if drawn5To3 else pp35, self)
        self.dualCap.setPen(NoPen)
        self.update(normalStrand)

    def update(self, strand):
        """
        Prepare NormalStrand for drawing:
        1. Show or hide caps depending on L and R connectivity.
        2. Determine line coordinates.
        3. Apply paint styles.
        """
        # 0. Setup
        ph = self.pathHelix
        halfBaseWidth = ph.baseWidth / 2.0
        vbL, vbR = strand.vBaseL, strand.vBaseR
        lUpperLeftX, lUpperLeftY = ph.upperLeftCornerOfVBase(vbL)
        rUpperLeftX, rUpperLeftY = ph.upperLeftCornerOfVBase(vbR)
        # 1. Cap visibilty
        if strand.apparentlyConnectedL():  # hide left cap if L-connected
            lx = lUpperLeftX
            self.leftCap.hide()
        else:  # otherwise show left cap
            lx = lUpperLeftX + halfBaseWidth
            self.leftCap.setPos(lUpperLeftX, lUpperLeftY)
            self.leftCap.show()
        if strand.apparentlyConnectedR():  # hide right cap if R-connected
            rx = rUpperLeftX + ph.baseWidth
            self.rightCap.hide()
        else:  # otherwise show it
            rx = rUpperLeftX + halfBaseWidth
            self.rightCap.setPos(rUpperLeftX, rUpperLeftY)
            self.rightCap.show()
        # special case: single-base strand with no L or R connections,
        # (unconnected caps were made visible in previous block of code)
        if strand.numBases() == 1 and \
                  (self.leftCap.isVisible() and self.rightCap.isVisible()):
            self.leftCap.hide()  # hide 
            self.rightCap.hide()
            self.dualCap.setPos(lUpperLeftX, lUpperLeftY)
            self.dualCap.show()
        else:
            self.dualCap.hide()
        # 2. Line drawing
        ry = ly = lUpperLeftY + halfBaseWidth
        self.setLine(lx, ly, rx, ry)
        if vbL.vStrand().isScaf():
            pen = QPen(styles.scafstroke, styles.PATH_STRAND_STROKE_WIDTH)
            brush = QBrush(styles.handlefill)
        else:
            pen = QPen(QColor(), styles.PATH_STRAND_STROKE_WIDTH)
            brush = QBrush(self.normalStrand.color())
        # 3. Apply paint styles
        pen.setCapStyle(Qt.FlatCap)
        self.setPen(pen)
        self.leftCap.setBrush(brush)
        self.rightCap.setBrush(brush)
        self.dualCap.setBrush(brush)

    def remove(self, strand):
        ns = self.normalStrand
        ns.didMove.disconnect(self.update)
        ns.apparentConnectivityChanged.disconnect(self.update)
        ns.willBeRemoved.disconnect(self.remove)
        scene = self.scene()
        scene.removeItem(self.rightCap)
        self.scene().removeItem(self.leftCap)
        self.rightCap = None
        self.leftCap = None
        scene.removeItem(self)