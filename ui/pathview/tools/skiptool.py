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
skiptool.py
Created by Nick on 2011-05-03.
"""
from exceptions import AttributeError, NotImplementedError
from PyQt4.QtCore import QPointF, QRectF, Qt
from PyQt4.QtGui import QBrush, QFont
from PyQt4.QtGui import QGraphicsItem, QGraphicsSimpleTextItem
from PyQt4.QtGui import QPainterPath
from PyQt4.QtGui import QPen
from model.enum import HandleOrient
import ui.styles as styles
from ui.pathview.pathhelix import PathHelix
from pathtool import PathTool
from ui.pathview.handles.skiphandle import SkipItem, SkipHandle


class SkipTool(PathTool):
    def __init__(self, pathcontroller=None, parent=None):
        """
        This class inherits from the PathTool class for the majority of 
        methods/behaviours.  Essentially it adds merely decorator graphics
        custimazation of behaviour and data structure access particular to
        skip insertion on a mouseclick
    
        it's parent should be *always* be a PathHelix
        """
        super(SkipTool, self).__init__(parent)
        self._skipItem = SkipItem(parent=self)
        _pen = QPen(styles.redstroke, 2)
        self.baseWidth = styles.PATH_BASE_WIDTH
        self.hide()
        self.setZValue(styles.ZPATHTOOL)
    # end def
    
    def toolPress(self, item, event):
        posScene = event.scenePos()
        posItem = self.parentItem().mapFromScene(posScene)
        indexp = self.helixIndex(posItem)
        print "SkipTool clicked at: (%d, %d) on helix %d" % \
            (indexp[0], indexp[1], self.parentItem().number())
        # create a new SkipHandle by adding through the parentItem
    # end def
# end class