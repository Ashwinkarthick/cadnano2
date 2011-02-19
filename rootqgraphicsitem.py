#!/usr/bin/env python
# encoding: utf-8

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
rootqgraphicsitem.py

Created by Nick Conway on 2011-01-17.
Copyright (c) 2010 . All rights reserved.
"""
from PyQt4.QtCore import Qt
from PyQt4 import QtGui


class RootQGraphicsItem(QtGui.QGraphicsItem):
    """
    Base class for QGraphicsViews with Mouse Zoom and Pan support via the
    Control/Command shortcut key.

    A QGraphics View stores info on the view and handles mouse events for
    zooming and panning

    Ctrl-MidMouseButton = Pan
    Ctrl-RightMouseButton = Dolly Zoom
    MouseWheel = Zoom

    Parameters
    ----------
    parent: type of QWidget, such as QWidget.splitter() for the type of
    View its has

    See Also
    --------

    Examples
    --------

    For details on these and other miscellaneous methods, see below.
    """
    def __init__(self,rectsource=None, parent = None, scene=None):
        """
        on initialization we need to bind the Ctrl/command key to
        enable manipulation of the view

        Parameters
        ----------
        parent: type of QWidget, such as QWidget.splitter() for the type of
        View its has

        See Also
        --------

        Examples
        --------
        """
        
        super(RootQGraphicsItem, self).__init__()
        self.parent = parent 
        self.scene = scene
        # this sets the rect of itself to the QGraphicsScene bounding volume
        self.rect = rectsource.sceneRect()

        self.draggable = False
        
        self.transformEnable = False
        self.dollyZoomEnable = False
        #print self.transformationAnchor()
        #self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

        self.x0 = 0
        self.y0 = 0
        self.scale_size = 1.0
        self.scale_limit_max = 3.0
        self.scale_limit_min = .41
        self.last_scale_factor = 0.0
        self.key_mod = Qt.Key_Control
        self.key_pan = Qt.LeftButton #Qt.MidButton
        self.key_zoom = Qt.RightButton
        
    # end def

    def setKeyPan(self, button):
        """
        Set the class pan button remotely
        Parameters
        ----------
        button: QtGui.Qt Namespace button identifier

        See Also
        --------

        Examples
        --------
        """
        self.key_pan = button
    # end def

    def keyPressEvent(self, event):
        """
        Parameters
        ----------
        event: type of QKeyEvent

        See Also
        --------

        Examples
        --------
        """
        if event.key() == self.key_mod:
            #event.accept()
            self.transformEnable = True
        else:
            QtGui.QGraphicsItem.keyPressEvent(self, event)
        # end else
    # end def

    def keyReleaseEvent(self, event):
        """
        Parameters
        ----------
        event: type of QKeyEvent

        See Also
        --------

        Examples
        --------
        """
        if event.key() == self.key_mod:
            #event.accept()
            self.transformEnable = False
            self.dollyZoomEnable = False
            self.panDisable()
        # end if
        else:
            QtGui.QGraphicsItem.keyReleaseEvent(self, event)
        # end else
    # end def

    def mouseMoveEvent(self, event):
        """
            Must reimplement mouseMoveEvent of QGraphicsView to allow
            ScrollHandDrag due to the fact that events are intercepted
            breaks this feature.

            Parameters
            ----------
            event: type of QMouseEvent

            See Also
            --------

            Examples
            --------
        """
        if self.transformEnable == True:
            if self.draggable == True:
                """
                Add stuff to handle the pan event
                """
                xf = event.x()
                yf = event.y()
                self.translate(xf - self.x0, yf - self.y0)
                self.x0 = xf
                self.y0 = yf
            elif self.dollyZoomEnable == True:
                self.dollyZoom(event)
            #else:
                #QGraphicsView.mouseMoveEvent(self, event)
        #else:
        # adding this allows events to be passed to items underneath
        QtGui.QGraphicsItem.mouseMoveEvent(self, event)
    # end def

    def mousePressEvent(self, event):
        """
        This takes a QMouseEvent for the event

        Parameters
        ----------
        event: type of QMouseEvent

        See Also
        --------

        Examples
        --------
        """
        if self.transformEnable == True:
            #event.accept()
            which_buttons = event.buttons()
            if which_buttons == self.key_pan:
                self.panEnable()
                self.setCursor(Qt.ClosedHandCursor)
                self.x0 = event.scenePos().x()
                self.y0 = event.scenePos().y()
            elif which_buttons == self.key_zoom:
                self.dollyZoomEnable = True
                self.last_scale_factor = 0
                # QMouseEvent.y() returns the position of the mouse cursor
                # relative to the widget
                self.y0 = event.scenePos().y()
            else:
                QtGui.QGraphicsItem.mousePressEvent(self, event)
        else:
            QtGui.QGraphicsItem.mousePressEvent(self, event)
    #end def

    def mouseReleaseEvent(self, event):
        """
        This takes a QMouseEvent for the event

        Parameters
        ----------
        event: type of QMouseEvent

        See Also
        --------

        Examples
        --------
        """
        if self.transformEnable == True:
            # QMouseEvent.button() returns the button that triggered the event
            which_button = event.button()
            if which_button == self.key_pan:
                self.setCursor(Qt.ArrowCursor)
                self.panDisable()
            elif which_button == self.key_zoom:
                self.dollyZoomEnable = False
            else:
                QtGui.QGraphicsItem.mouseReleaseEvent(self, event)
        # end if
        else:
            QtGui.QGraphicsItem.mouseReleaseEvent(self, event)
    #end def

    def panEnable(self):
        """Enable ScrollHandDrag Mode in QGraphicsView (displays a hand
        pointer)"""
        self.draggable = True
    # end def

    def panDisable(self):
        """Disable ScrollHandDrag Mode in QGraphicsView (displays a hand
        pointer)"""
        self.draggable = False
    # end def

    

    def wheelEvent(self, event):
        """
        This takes a QMouseEvent for the event

        Parameters
        ----------
        event: type of QMouseEvent

        See Also
        --------

        Examples
        --------
        """
        self.wheelZoom(event)
    #end def

    def wheelZoom(self, event):
        """
        This takes a QMouseEvent for the event

        Parameters
        ----------
        event: type of QMouseEvent

        See Also
        --------

        Examples
        --------
        """
        if event.delta() > 0:  # rotated away from the user
            if self.scale_limit_max > self.scale_size:
                dx = event.pos().x()
                dy = event.pos().y()
                self.setScale(1.25, 1.25,dx,dy)
                self.scale_size *= 1.25
            # end if
        # end if
        else:
            if self.scale_limit_min < self.scale_size:
                dx = event.pos().x()
                dy = event.pos().y()
                self.setScale(.8, .8,dx,dy)
                self.scale_size *= 0.8
            # end if
        # end else
    # end def

    def dollyZoom(self, event):
        """
        This takes a QMouseEvent for the event

        Parameters
        ----------
        event: type of QMouseEvent

        See Also
        --------

        Examples
        --------
        """
        # QMouseEvent.y() returns the position of the mouse cursor relative
        # to the widget
        yf = event.scenePos().y()
        denom = abs(yf - self.y0)
        if denom > 0:
            scale_factor = (self.height() / 2) % denom
            if self.last_scale_factor != scale_factor:
                self.last_scale_factor = scale_factor
                # zoom in if mouse y position is getting bigger
                if yf - self.y0 > 0:
                    if self.scale_limit_max > self.scale_size:
                        self.setScale(1.25, 1.25)
                        self.scale_size *= 1.25
                    # end if
                # end else
                else:  # else if smaller zoom out
                    if self.scale_limit_min < self.scale_size:
                        self.setScale(.8, .8)
                        self.scale_size *= 0.8
                    # end if
                # end else
        # end if
    # end def
    
    def paint(self, painter, option, widget):
        pass
        
    def boundingRect(self):
        return self.rect
        
    def height(self):
        return self.boundingRect().height()
    # end def
        
    def setScale(self,sx,sy, dx=0,dy=0):
        """ 
        required for less than Qt 4.6
        tries to translate based on scaling to keep item
        centered overthe point passed in
        """
        r = QtGui.QTransform()
        r.translate(dx*(1-sx),dy*(1-sy))
        r.scale(sx,sy)
        self.setTransform(r, combine=True)
    # end def
#end class
