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

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtCore import pyqtSignal
from tools.pathtool import PathTool
from tools.looptool import LoopTool
from tools.skiptool import SkipTool
from tools.breaktool import BreakTool
from tools.erasetool import EraseTool
from tools.selecttool import SelectTool


class PathController(QObject):
    """
    Manages the interactions between Path widgets / UI elements and the model
    """
    def __init__(self, win):
        super(PathController, self).__init__()
        self.mainWindow = win
        win.actionPathSelect.triggered.connect(self.chooseSelectTool)
        win.actionPathMove.triggered.connect(self.chooseMoveTool)
        win.actionPathBreak.triggered.connect(self.chooseBreakTool)
        win.actionPathErase.triggered.connect(self.chooseEraseTool)
        win.actionPathInsert.triggered.connect(self.chooseInsertTool)
        win.actionPathSkip.triggered.connect(self.chooseSkipTool)

        self.toolset = set((win.actionPathSelect, win.actionPathMove,\
                            win.actionPathBreak, win.actionPathErase,\
                            win.actionPencil, win.actionPathInsert,\
                            win.actionPathSkip, win.actionPaint))
        ag = QActionGroup(win)
        for a in self.toolset:
            ag.addAction(a)
        ag.setExclusive(True)
        self.currentToolWidget = None
        self.toolUse = False    # flag for using a specfic tool in the scene
        self.selectTool = SelectTool()
        self.eraseTool = EraseTool(pathcontroller=self, parent=None)
        self.insertionTool = LoopTool(pathcontroller=self, parent=None)
        self.skipTool = SkipTool(pathcontroller=self, parent=None)
        self.breakTool = BreakTool(pathcontroller=self, parent=None)
        self.chooseSelectTool()

    # The activeTool is a tool in the style of SelectTool that
    # can handle events forwarded in the style of
    # util.defineEventForwardingMethodsForClass. In other words,
    # the activeTool() gets events from various graphics objects in the
    # path view and then makes the corresponding changes to the
    # model. The displayed content then updates automatically via
    # notifications from the model.
    # * the activeTool gets events from graphics items and
    #        does the work (changes the model). Possible future
    #        configuration of the activeTool() can be done on the
    #        instances of various tools kept in the controller, like
    #        self.selectToo.
    # * the currentToolWidget indicates which activeTool is active
    #        and lets the user change activeTool()
    # * graphics items that make up the view sit back and watch the model,
    #        updating when it changes
    # NEW ACTIVETOOLS SHOULD TAKE ADVANTAGE OF SUBCLASSING, NOT
    # COPY+PASTE CODE DUPLICATON which is a maintainance nightmare.
    def activeTool(self):
        return self._activeTool
    
    activeToolChanged = pyqtSignal()
    def setActiveTool(self, newActiveTool):
        self._activeTool = newActiveTool
        self.activeToolChanged.emit()

    def chooseSelectTool(self):
        widget = self.mainWindow.actionPathSelect
        if self.currentToolWidget is widget:
            return
        else:
            self.currentToolWidget = widget
        # self.toolUse = False
        widget.setChecked(True)
        self.setActiveTool(self.selectTool)

    def chooseMoveTool(self):
        widget = self.mainWindow.actionPathMove
        if self.currentToolWidget is widget:
            return
        else:
            self.currentToolWidget = widget
        widget.setChecked(True)

    def chooseBreakTool(self):
        widget = self.mainWindow.actionPathBreak
        if self.currentToolWidget is widget:
            return
        else:
            self.currentToolWidget = widget
        widget.setChecked(True)

    def chooseEraseTool(self):
        widget = self.mainWindow.actionPathErase
        if self.currentToolWidget is widget:
            return
        else:
            self.currentToolWidget = widget
        widget.setChecked(True)

    def chooseInsertTool(self):
        widget = self.mainWindow.actionPathInsert
        if self.currentToolWidget is widget:
            return
        else:
            self.currentToolWidget = widget
        widget.setChecked(True)

    def chooseSkipTool(self):
        widget = self.mainWindow.actionPathSkip
        if self.currentToolWidget is widget:
            return
        else:
            self.currentToolWidget = widget
        widget.setChecked(True)
    # end def
# end class
