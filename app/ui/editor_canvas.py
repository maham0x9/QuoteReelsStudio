"""Canva-style center canvas built on QGraphicsScene.

Shows the current background's first frame as a 1080x1920 (scaled) page,
plus a draggable / resizable / rotatable text item bound to the active
``TextLayer``. Geometry is normalized to 0..1 for portable storage.
"""
from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QImage,
    QPainter,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
)

from app.models import Quote, TextLayer

LOG = logging.getLogger(__name__)


class _TextItem(QGraphicsSimpleTextItem):
    def __init__(self, parent_box: _TextBox):
        super().__init__(parent_box)
        self.parent_box = parent_box
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations, False)


class _TextBox(QGraphicsRectItem):
    """Draggable / resizable container for a TextLayer."""

    HANDLE_SIZE = 12

    def __init__(self, layer: TextLayer, on_change):
        super().__init__()
        self.layer = layer
        self.on_change = on_change
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setPen(QPen(QColor("#5C7CFA"), 1, Qt.DashLine))
        self.setBrush(QBrush(Qt.NoBrush))
        self._suppress_change = False
        self._resizing = False
        self._press_pos = None
        self._press_rect = None
        self._handle = QGraphicsRectItem(self)
        self._handle.setBrush(QBrush(QColor("#5C7CFA")))
        self._handle.setPen(QPen(Qt.NoPen))
        self._handle.setCursor(Qt.SizeFDiagCursor)
        self._handle.setAcceptHoverEvents(True)
        self._handle.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self._text_item = QGraphicsSimpleTextItem(self)
        self._text_item.setBrush(QBrush(QColor(layer.color)))
        self._text_item.setAcceptedMouseButtons(Qt.NoButton)

    # -------------------------------------------- geometry sync
    def apply_layer(self, scene_size: tuple[float, float]) -> None:
        self._suppress_change = True
        sw, sh = scene_size
        x = self.layer.x * sw
        y = self.layer.y * sh
        w = max(40.0, self.layer.width * sw)
        h = max(40.0, self.layer.height * sh)
        self.setRect(0, 0, w, h)
        self.setPos(x, y)
        self.setRotation(self.layer.rotation)
        self._refresh_handle()
        self._refresh_text()
        self._suppress_change = False

    def _refresh_handle(self) -> None:
        r = self.rect()
        s = self.HANDLE_SIZE
        self._handle.setRect(r.right() - s / 2, r.bottom() - s / 2, s, s)

    def _refresh_text(self) -> None:
        self._text_item.setText(self.layer.text or "")
        font = QFont(self.layer.font_family or "Arial",
                     max(6, int(self.layer.font_size * 0.5)))
        font.setBold(self.layer.bold)
        font.setItalic(self.layer.italic)
        self._text_item.setFont(font)
        self._text_item.setBrush(QBrush(QColor(self.layer.color)))
        # rough centering inside box
        br = self._text_item.boundingRect()
        r = self.rect()
        if self.layer.alignment == "left":
            x = 8
        elif self.layer.alignment == "right":
            x = r.width() - br.width() - 8
        else:
            x = (r.width() - br.width()) / 2
        y = (r.height() - br.height()) / 2
        self._text_item.setPos(x, y)

    # -------------------------------------------- events
    def mousePressEvent(self, ev):
        if self._handle.contains(self._handle.mapFromScene(ev.scenePos())):
            self._resizing = True
            self._press_pos = ev.scenePos()
            self._press_rect = QRectF(self.rect())
            ev.accept()
            return
        super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        if self._resizing and self._press_rect is not None:
            delta = ev.scenePos() - self._press_pos
            new_w = max(40.0, self._press_rect.width() + delta.x())
            new_h = max(40.0, self._press_rect.height() + delta.y())
            self.setRect(0, 0, new_w, new_h)
            self._refresh_handle()
            self._refresh_text()
            ev.accept()
            return
        super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev):
        if self._resizing:
            self._resizing = False
            self._notify_change()
            ev.accept()
            return
        super().mouseReleaseEvent(ev)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged and not self._suppress_change:
            self._notify_change()
        return super().itemChange(change, value)

    def _notify_change(self) -> None:
        if self._suppress_change:
            return
        scene = self.scene()
        if not scene:
            return
        sw = scene.width()
        sh = scene.height()
        if sw <= 0 or sh <= 0:
            return
        self.layer.x = float(self.pos().x() / sw)
        self.layer.y = float(self.pos().y() / sh)
        self.layer.width = float(self.rect().width() / sw)
        self.layer.height = float(self.rect().height() / sh)
        self.layer.rotation = float(self.rotation())
        if self.on_change:
            self.on_change(self.layer)


class EditorCanvas(QGraphicsView):
    """Center preview canvas."""
    layer_changed = Signal(object)  # TextLayer

    def __init__(self, canvas_size: tuple[int, int] = (1080, 1920), parent=None):
        super().__init__(parent)
        self.canvas_w, self.canvas_h = canvas_size
        self._scene = QGraphicsScene(0, 0, self.canvas_w, self.canvas_h)
        self.setScene(self._scene)
        self.setRenderHints(
            QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.TextAntialiasing
        )
        self.setBackgroundBrush(QBrush(QColor("#0E0F12")))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._bg_item: QGraphicsPixmapItem | None = None
        self._text_box: _TextBox | None = None
        self._safe_zone: QGraphicsRectItem | None = None
        self._draw_safe_zone()
        self._fit()

    # -------------------------------------------- safe zone
    def _draw_safe_zone(self) -> None:
        if self._safe_zone:
            self._scene.removeItem(self._safe_zone)
        margin_x = self.canvas_w * 0.05
        margin_y_top = self.canvas_h * 0.18    # avoid TikTok username
        margin_y_bot = self.canvas_h * 0.22    # avoid caption
        rect = QRectF(margin_x, margin_y_top,
                      self.canvas_w - 2 * margin_x,
                      self.canvas_h - margin_y_top - margin_y_bot)
        self._safe_zone = self._scene.addRect(
            rect, QPen(QColor(255, 255, 255, 40), 2, Qt.DotLine), QBrush(Qt.NoBrush)
        )
        self._safe_zone.setZValue(-1)

    # -------------------------------------------- background
    def set_background_thumb(self, path: str) -> None:
        if self._bg_item:
            self._scene.removeItem(self._bg_item)
            self._bg_item = None
        if not path or not Path(path).exists():
            self._scene.setBackgroundBrush(QBrush(QColor("#1B1D22")))
            return
        pm = QPixmap(path)
        if pm.isNull():
            return
        pm = pm.scaled(self.canvas_w, self.canvas_h,
                       Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        self._bg_item = QGraphicsPixmapItem(pm)
        self._bg_item.setZValue(-2)
        # center
        x = (self.canvas_w - pm.width()) / 2
        y = (self.canvas_h - pm.height()) / 2
        self._bg_item.setPos(x, y)
        self._scene.addItem(self._bg_item)

    def set_background_image(self, image: QImage) -> None:
        self.set_background_pixmap(QPixmap.fromImage(image))

    def set_background_pixmap(self, pm: QPixmap) -> None:
        if self._bg_item:
            self._scene.removeItem(self._bg_item)
            self._bg_item = None
        if pm.isNull():
            return
        pm = pm.scaled(self.canvas_w, self.canvas_h,
                       Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        self._bg_item = QGraphicsPixmapItem(pm)
        self._bg_item.setZValue(-2)
        x = (self.canvas_w - pm.width()) / 2
        y = (self.canvas_h - pm.height()) / 2
        self._bg_item.setPos(x, y)
        self._scene.addItem(self._bg_item)

    # -------------------------------------------- text
    def bind_quote(self, quote: Quote) -> None:
        if self._text_box:
            self._scene.removeItem(self._text_box)
        layer = quote.text_layer
        if not layer.text:
            layer.text = quote.text
        self._text_box = _TextBox(layer, on_change=self.layer_changed.emit)
        self._scene.addItem(self._text_box)
        self._text_box.apply_layer((self.canvas_w, self.canvas_h))

    def refresh_text(self) -> None:
        if self._text_box:
            self._text_box.apply_layer((self.canvas_w, self.canvas_h))

    # -------------------------------------------- view
    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self._fit()

    def _fit(self) -> None:
        self.fitInView(0, 0, self.canvas_w, self.canvas_h, Qt.KeepAspectRatio)

    def auto_center_in_safe_zone(self) -> None:
        if not self._text_box:
            return
        layer = self._text_box.layer
        layer.x = 0.08
        layer.y = 0.36
        layer.width = 0.84
        layer.height = 0.28
        self._text_box.apply_layer((self.canvas_w, self.canvas_h))
        self.layer_changed.emit(layer)
