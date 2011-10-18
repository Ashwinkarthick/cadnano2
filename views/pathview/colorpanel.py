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
util.qtWrapImport('QtCore', globals(), ['QRectF', 'Qt'])
util.qtWrapImport('QtGui', globals(),  ['QBrush', 'QColorDialog', 'QGraphicsItem'])


class ColorPanel(QGraphicsItem):
    _scafColors = styles.scafColors
    _stapColors = styles.stapColors
    _pen = Qt.NoPen

    def __init__(self, parent=None):
        super(ColorPanel, self).__init__(parent)
        self.rect = QRectF(0, 0, 20, 20)
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.colordialog = QColorDialog()
        self.colordialog.setOption(QColorDialog.DontUseNativeDialog)
        self._scafColorIndex = -1  # init on -1, painttool will cycle to 0
        self._stapColorIndex = -1  # init on -1, painttool will cycle to 0
        self._scafColor = self._scafColors[self._scafColorIndex]
        self._stapColor = self._stapColors[self._stapColorIndex]
        self._scafBrush = QBrush(self._scafColor)
        self._stapBrush = QBrush(self._stapColor)
        self.hide()

    def boundingRect(self):
        return self.rect

    def paint(self, painter, option, widget=None):
        painter.setPen(self._pen)
        painter.setBrush(self._scafBrush)
        painter.drawRect(0, 0, 20, 10)
        painter.setBrush(self._stapBrush)
        painter.drawRect(0, 10, 20, 10)

    def nextColor(self):
        self._scafColorIndex += 1
        self._stapColorIndex += 1
        if self._scafColorIndex == len(self._scafColors):
            self._scafColorIndex = 0
        if self._stapColorIndex == len(self._stapColors):
            self._stapColorIndex = 0
        self._scafColor = self._scafColors[self._scafColorIndex]
        self._stapColor = self._stapColors[self._stapColorIndex]
        self._scafBrush.setColor(self._scafColor)
        self._stapBrush.setColor(self._stapColor)
        self.update()

    def color(self):
        return self._stapColor

    def scafColorName(self):
        return self._scafColor.name()

    def stapColorName(self):
        return self._stapColor.name()

    def mousePressEvent(self, event):
        if event.pos().y() < 10:
            self._scafColor = self.colordialog.getColor(self._scafColor)
            self._scafBrush = QBrush(self._scafColor)
        else:
            self._stapColor = self.colordialog.getColor(self._stapColor)
            self._stapBrush = QBrush(self._stapColor)
        self.update()