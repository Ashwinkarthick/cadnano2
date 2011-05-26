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
paintertool
Created by Jonathan deWerd on 2011-05-26.
"""

class PainterTool(object):
    def mousePressPathHelix(self, ph, event):
        """Activate this item as the current helix"""
        self._mouseDownBase = ph.baseAtLocation(event.pos().x(), event.pos().y())
        if self._mouseDownBase:
            ph.vhelix().setSandboxed(True)
            self.painterToolApply(self._mouseDownBase, self._mouseDownBase)
        self.updateAsActiveHelix(self._mouseDownBase[1])
        # QGraphicsItem.mousePressEvent(self,event)
    
    def mouseMovePathHelix(self, ph, event):
        vh = ph.vhelix()
        newBase = ph.baseAtLocation(event.pos().x(), event.pos().y())
        if self._mouseDownBase and newBase:
            self._lastValidBase = newBase
            vh.undoStack().undo()
            self.painterToolApply(self._mouseDownBase, newBase)
    
    def mouseReleasedPathHelix(self, ph, event):
        vh = ph.vhelix()
        if self._mouseDownBase and self._lastValidBase:
            vh.undoStack().undo()
            vh.setSandoxed(False)  # vhelix should now use the document undo stack
            self.painterToolApply(self._mouseDownBase, newBase)

    def painterToolApply(self, vHelix, fr, to):
        """PainterTool is the default tool that lets one
        create scaffold and staple by dragging starting on
        an empty or endpoint base or destroy scaffold/staple
        by dragging from a connected base. from and to take the
        format of (strandType, base)"""
        fr = vHelix.validatedBase(*fr, raiseOnErr=False)
        to = vHelix.validatedBase(*to, raiseOnErr=False)
        if (None, None) in (fr, to):
            return False
        startOnSegment = vHelix.hasStrandAt(*fr)
        startOnBreakpoint = vHelix.hasEndAt(*fr)
        adj = vHelix.validatedBase(fr[0], fr[1]+direction, raiseOnErr=False)
        direction = 1 if to[1]>fr[1] else -1
        useClearMode = vHelix.hasStrandAt(*adj)
        # adj: the base adjacent to fr in the same direction as to
        if adj and startOnBreakpoint and vHelix.hasStrandAt(*adj):
            useClearMode = True
        if useClearMode:
            self.vhelix().clearStrand(fr[0], fr[1], to[1])
        else:
            self.vhelix().connectStrand(fr[0], fr[1], to[1])        



