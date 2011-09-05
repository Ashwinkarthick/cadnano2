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

import util, sys
util.qtWrapImport('QtCore', globals(), ['QObject'])
from model.strands.normalstrand import NormalStrand
import model.oligo
from operation import Operation
from model.strands.vbase import VBase
from model.strands.xoverstrand import XOverStrand3, XOverStrand5

class PencilToolOperation(Operation):
    """
    Handles interactive strand creation / destruction in the manner of the
    Pencil Tool.
    """
    imposeDragBounds = True
    allowBreakingByClickInsideStrands = True
    logger = None

    def __init__(self, startVBase, useLeft, undoStack):
        """ Begin a session of pencil-tool interaction """
        Operation.__init__(self, undoStack)
        self.newStrand = NormalStrand(startVBase, startVBase)
        self.startVStrand = self.newStrand.vStrand()
        self.startVBase = startVBase
        self.useLeft = useLeft
        self.lastDestVBase = None
        self.newStrandInVfbPool = False
        self.newOligoProvider = model.oligo.DragOperationOligoProvider()
        if self.imposeDragBounds:  # calculate drag boundaries
            self.setDragBounds()
        self.updateDestination(startVBase)
        if self.logger:
            self.logger.write('PencilToolOperation.init(%s)\n'%startVBase)

    def setDragBounds(self):
        # prevent dragging outside the grid
        self.dragBoundL = 0
        self.dragBoundR = self.startVBase.part().dimensions()[2]-1

    def updateDestination(self, newDestVBase):
        """ Looks at self.startVBase and newDestVBase then calls the appropriate
        actionWhatever method on self. """
        if isinstance(newDestVBase, (int, long)):
            newDestVBase = VBase(self.startVBase.vStrand(), newDestVBase)
        if newDestVBase == self.lastDestVBase:
            return
        else:
            self.lastDestVBase = newDestVBase
        self.rewind()
        self.newOligoProvider.rewind()
        dragStartBase, dragEndBase = self.startVBase, newDestVBase
        dragStartExposedEnds = dragStartBase.exposedEnds()
        # special case: single-base strand
        if 'L' in dragStartExposedEnds and 'R' in dragStartExposedEnds:
            dragStartExposedEnds = 'L' if self.useLeft else 'R'
        dragStartStrand = dragStartBase.strand()
        dragEndStrand = dragEndBase.strand()
        startIdx, endIdx = dragStartBase.vIndex(), dragEndBase.vIndex()
        vStrand = dragStartBase.vStrand()

        if not isinstance(newDestVBase, VBase):
            return

        if self.imposeDragBounds:
            if endIdx < self.dragBoundL:
                endIdx = self.dragBoundL
            elif endIdx > self.dragBoundR:
                endIdx = self.dragBoundR

        if 'R' in dragStartExposedEnds:
            if endIdx < startIdx:  # Dragging a right-facing endpoint left
                vStrand.clearStrand(endIdx + 1, startIdx + 1,\
                                   useUndoStack=True, undoStack=self.undoStack,\
                                   newOligoProvider=self.newOligoProvider)
            elif startIdx < endIdx:  # Dragging a right-facing endpoint right
                vStrand.connectStrand(startIdx, endIdx,\
                                   useUndoStack=True, undoStack=self.undoStack,\
                                   newOligoProvider=self.newOligoProvider)
            else:  # Click on an endpoint
                pass
        elif 'L' in dragStartExposedEnds:
            if endIdx < startIdx:  # Dragging a left-facing endpoint left
                vStrand.connectStrand(startIdx, endIdx,\
                                   useUndoStack=True, undoStack=self.undoStack,\
                                   newOligoProvider=self.newOligoProvider)
            elif startIdx < endIdx:  # Dragging a left-facing endpoint right
                vStrand.clearStrand(startIdx, endIdx,\
                                   useUndoStack=True, undoStack=self.undoStack,\
                                   newOligoProvider=self.newOligoProvider)
            else:
                pass  # Click on an endpoint
        elif dragStartStrand != None and self.allowBreakingByClickInsideStrands:
            if endIdx < startIdx:  # Dragging left inside a strand
                vStrand.clearStrand(endIdx + 1, startIdx,\
                                useUndoStack=True, undoStack=self.undoStack,\
                                keepLeft=True, newOligoProvider=self.newOligoProvider)
            elif startIdx < endIdx:  # Dragging right inside a strand
                vStrand.clearStrand(startIdx, endIdx,\
                               useUndoStack=True, undoStack=self.undoStack,\
                               keepLeft=False, newOligoProvider=self.newOligoProvider)
            else: # Click inside a strand
                vStrand.clearStrand(startIdx, startIdx,\
                               useUndoStack=True, undoStack=self.undoStack,\
                               keepLeft=False, newOligoProvider=self.newOligoProvider)
        else:
            vStrand.connectStrand(startIdx, endIdx,\
                                 useUndoStack=True, undoStack=self.undoStack,\
                                 newOligoProvider=self.newOligoProvider)

    def end(self):
        """ Make the changes displayed by the last call to
        updateDestination permanent. Mostly, cause trouble for a user who
        erroneously tries to use the same PencilToolOperation twice.
        Also perform special mouseup behavior. """
        if self.logger:
            self.logger.write('PencilToolOperation.end\n')
        if self.startVBase == self.lastDestVBase:
            strand = self.startVBase.strand()
            if isinstance(strand, (XOverStrand3, XOverStrand5)):
                self.rewind()
                self.newOligoProvider.rewind()
                idx = self.startVBase.vIndex()
                self.startVBase.vStrand().clearStrand(idx, idx + 1,\
                                   useUndoStack=True, undoStack=self.undoStack)
        del self.newStrand
        del self.startVBase
        del self.newStrandInVfbPool
        del self.lastDestVBase
