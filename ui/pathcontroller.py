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


class PathController():
    """
    Manages the interactions between widgets / UI elements and the path model
    """

    def __init__(self, win):
        self.mainWindow = win
        self.toolset = set((win.actionPathSelect, win.actionPathMove,\
                            win.actionPathBreak, win.actionPathErase,\
                            win.actionPathForce, win.actionPathInsertion,\
                            win.actionPathSkip))
        win.connect(win.actionPathSelect,\
                    SIGNAL("triggered()"),\
                    self.chooseSelectTool)
        win.connect(win.actionPathMove,\
                    SIGNAL("triggered()"),\
                    self.chooseMoveTool)
        win.connect(win.actionPathBreak,\
                    SIGNAL("triggered()"),\
                    self.chooseBreakTool)
        win.connect(win.actionPathErase,\
                    SIGNAL("triggered()"),\
                    self.chooseEraseTool)
        win.connect(win.actionPathForce,\
                    SIGNAL("triggered()"),\
                    self.chooseForceTool)
        win.connect(win.actionPathInsertion,\
                    SIGNAL("triggered()"),\
                    self.chooseInsertTool)
        win.connect(win.actionPathSkip,\
                    SIGNAL("triggered()"),\
                    self.chooseSkipTool)
        self.currentTool = None
        ag = QActionGroup(win)
        for a in self.toolset:
            ag.addAction(a)
        ag.setExclusive(True)
        self.chooseSelectTool()

    def chooseSelectTool(self):
        widget = self.mainWindow.actionPathSelect
        if self.currentTool is widget:
            return
        else:
            self.currentTool = widget
        widget.setChecked(True)
        print "path select"

    def chooseMoveTool(self):
        widget = self.mainWindow.actionPathMove
        if self.currentTool is widget:
            return
        else:
            self.currentTool = widget
        widget.setChecked(True)
        print "path move"

    def chooseBreakTool(self):
        widget = self.mainWindow.actionPathBreak
        if self.currentTool is widget:
            return
        else:
            self.currentTool = widget
        widget.setChecked(True)
        print "path break"

    def chooseEraseTool(self):
        widget = self.mainWindow.actionPathErase
        if self.currentTool is widget:
            return
        else:
            self.currentTool = widget
        widget.setChecked(True)
        print "path erase"

    def chooseForceTool(self):
        widget = self.mainWindow.actionPathForce
        if self.currentTool is widget:
            return
        else:
            self.currentTool = widget
        widget.setChecked(True)
        print "path force"

    def chooseInsertTool(self):
        widget = self.mainWindow.actionPathInsertion
        if self.currentTool is widget:
            return
        else:
            self.currentTool = widget
        widget.setChecked(True)
        print "path insert"

    def chooseSkipTool(self):
        widget = self.mainWindow.actionPathSkip
        if self.currentTool is widget:
            return
        else:
            self.currentTool = widget
        widget.setChecked(True)
        print "path skip"
