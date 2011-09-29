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

from controllers.itemcontrollers.strand.abstractstranditemcontroller \
     import AbstractStrandItemController


class StrandItemController(AbstractStrandItemController):
    def __init__(self, strandItem, modelStrand):
        super(StrandItemController, self).__init__(strandItem, modelStrand)
        self.connectSignals()
    # end def

    def reconnectOligoSignals(self, newOligo):
        AbstractStrandItemController.disconnectOligoSignals(self)
        self.disconnectOligoSignals()
        self._modelOligo = newOligo
        AbstractStrandItemController.connectOligoSignals(self)
        self.connectOligoSignals()
    # end def

    def connectSignals(self):
        AbstractStrandItemController.connectSignals(self)
        mS = self._modelStrand
        sI = self._strandItem
        mS.strandResizedSignal.connect(sI.strandResizedSlot)
        self.connectOligoSignals()
    # end def

    def connectOligoSignals(self):
        mO = self._modelOligo
        sI = self._strandItem
        mO.sequenceAddedSignal.connect(sI.sequenceAddedSlot)
        mO.sequenceClearedSignal.connect(sI.sequenceClearedSlot)
    # end def

    def disconnectSignals(self):
        AbstractStrandItemController.disconnectSignals(self)
        mS = self._modelStrand
        sI = self._strandItem
        mS.strandResizedSignal.disconnect(sI.strandResizedSlot)
        self.disconnectOligoSignals()
    # end def

    def disconnectOligoSignals(self):
        mO = self._modelOligo
        sI = self._strandItem
        mO.sequenceAddedSignal.disconnect(sI.sequenceAddedSlot)
        mO.sequenceClearedSignal.disconnect(sI.sequenceClearedSlot)
    # end def
