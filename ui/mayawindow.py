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
mayawindow.py
"""

import maya.OpenMayaUI as mui
import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui
import sip

import ui_mainwindow
import slicehelixgroup
import pathcontroller
import slicecontroller
from cadnanomaya import app

def getMayaWindow():
	#Get the maya main window as a QMainWindow instance
    ptr = mui.MQtUtil.mainWindow()
    return sip.wrapinstance(long(ptr), QtCore.QObject)
# end def

class DocumentWindow(QtGui.QMainWindow, ui_mainwindow.Ui_MainWindow):
    '''docstring for DocumentWindow'''
    def __init__(self, parent=getMayaWindow(), docCtrlr=None):
        super(DocumentWindow, self).__init__(parent)
        self.controller = docCtrlr
        self.setupUi(self)
        # Slice setup
        self.slicescene = QtGui.QGraphicsScene()
        self.sliceGraphicsView.setScene(self.slicescene)
        self.sliceController = slicecontroller.SliceController(self)
        # Path setup
        self.pathscene = QtGui.QGraphicsScene()
        self.pathGraphicsView.setScene(self.pathscene)
        self.pathController = pathcontroller.PathController(self)
        # Edit menu setup
        self.undoStack = docCtrlr.undoStack
        self.editMenu = self.menuBar().addMenu("Edit")
        self.undoAction = docCtrlr.undoStack.createUndoAction(self)
        self.redoAction = docCtrlr.undoStack.createRedoAction(self)
        self.editMenu.addAction(self.undoAction)
        self.editMenu.addAction(self.redoAction)
    def focusInEvent(self):
       app().undoGroup.setActiveStack(self.controller.undoStack)
# end class
