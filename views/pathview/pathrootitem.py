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

from controllers.viewrootcontroller import ViewRootController
from partitem import PartItem

import util
util.qtWrapImport('QtCore', globals(), ['pyqtSignal', 'QObject'])
util.qtWrapImport('QtGui', globals(), ['QGraphicsRectItem'])


class PathRootItem(QGraphicsRectItem):
    """
    PathRootItem is the root item in the PathView. It gets added directly
    to the pathscene by DocumentWindow. It receives two signals
    (partAddedSignal and documentSelectedPartChangedSignal)
    via its ViewRootController.

    PathRootItem must instantiate its own controller to receive signals
    from the model.
    """
    def __init__(self, rect, parent, window, document):
        super(PathRootItem, self).__init__(rect, parent)
        self._window = window
        self._document = document
        self._controller = ViewRootController(self, document)
        self._modelPart = None
        self._partItems = []

    ### SIGNALS ###

    ### SLOTS ###
    def partAddedSlot(self, modelPart):
        """
        Receives notification from the model that a part has been added.
        The Pathview doesn't need to do anything on part addition, since
        the Sliceview handles setting up the appropriate lattice.
        """
        print "PathRootItem.partAddedSlot!"
        self._modelPart = modelPart
        win = self._window
        partItem = PartItem(modelPart,\
                            activeTool=win.pathToolManager.activeTool,\
                            parent=win.pathroot)
        self._partItems.append(partItem)
        win.pathToolManager.setActivePart(partItem)

    def selectedPartChangedSlot(self, modelPart):
        """Given a newly selected modelPart, update the scene to indicate
        that modelPart is selected and the previously selected part is
        deselected."""
        pass
        
        # if partItem in self._partItems:
        #     self._window.setActivePart(partItem)

    ### METHODS ###
