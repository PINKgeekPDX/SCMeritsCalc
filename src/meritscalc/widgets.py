"""Custom animated widgets with holographic effects for Star Citizen UI."""

from __future__ import annotations

from PyQt6.QtCore import (
    QPropertyAnimation,
    QEasingCurve,
    Qt,
    QRect,
    QRectF,
    QPointF,
)
from PyQt6.QtCore import pyqtProperty, QTimer, QSize  # type: ignore
from PyQt6.QtGui import (
    QPainter,
    QColor,
    QPen,
    QBrush,
    QLinearGradient,
    QPainterPath,
)
from PyQt6.QtWidgets import (
    QPushButton,
    QProgressBar,
    QLabel,
    QLineEdit,
    QGroupBox,
    QWidget,
)

from meritscalc.theme import (
    COLOR_BG_SECONDARY,
    COLOR_ACCENT_PRIMARY,
    COLOR_ACCENT_SECONDARY,
    COLOR_TEXT_PRIMARY,
    COLOR_BG_PANEL,
    COLOR_BORDER_SECONDARY,
)


class SciFiPanel(QGroupBox):
    """A container with chamfered corners and holographic borders."""

    def __init__(self, title="", parent=None):
        super().__init__(title, parent)
        self._glow_intensity = 0.0
        # Animation for a subtle "pulse" or "breathing" effect
        self._pulse_anim = QPropertyAnimation(self, b"glowIntensity")
        self._pulse_anim.setDuration(4000)
        self._pulse_anim.setStartValue(0.0)
        self._pulse_anim.setEndValue(1.0)
        self._pulse_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._pulse_anim.setLoopCount(-1)
        self._pulse_anim.start()

    def getGlowIntensity(self):
        return self._glow_intensity

    def setGlowIntensity(self, value):
        self._glow_intensity = value
        self.update()

    glowIntensity = pyqtProperty(float, getGlowIntensity, setGlowIntensity)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        # Adjust for margins
        fm = self.fontMetrics()
        title_h = fm.height()
        top_margin = max(12.0, title_h + 4.0)
        content_rect = QRectF(rect).adjusted(1.0, top_margin, -1.0, -1.0)

        # Chamfer amount
        cut = 10.0

        path = QPainterPath()
        # Top Left
        path.moveTo(content_rect.left(), content_rect.top() + cut)
        path.lineTo(content_rect.left() + cut, content_rect.top())
        # Top Right
        path.lineTo(content_rect.right() - cut, content_rect.top())
        path.lineTo(content_rect.right(), content_rect.top() + cut)
        # Bottom Right
        path.lineTo(content_rect.right(), content_rect.bottom() - cut)
        path.lineTo(content_rect.right() - cut, content_rect.bottom())
        # Bottom Left
        path.lineTo(content_rect.left() + cut, content_rect.bottom())
        path.lineTo(content_rect.left(), content_rect.bottom() - cut)
        path.closeSubpath()

        # Fill
        bg_color = QColor(COLOR_BG_PANEL)
        bg_color.setAlpha(200)  # Slight transparency
        painter.fillPath(path, bg_color)

        # Border glow calculation
        border_color = QColor(COLOR_BORDER_SECONDARY)
        glow_alpha = int(100 + (155 * self._glow_intensity * 0.3))
        border_color.setAlpha(glow_alpha)

        pen = QPen(border_color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawPath(path)

        # Draw "Tech" decorative lines
        tech_pen = QPen(QColor(COLOR_ACCENT_PRIMARY))
        tech_pen.setWidth(2)
        painter.setPen(tech_pen)

        # Corner accents
        # Top Left Corner
        painter.drawLine(
            int(content_rect.left()),
            int(content_rect.top() + cut),
            int(content_rect.left()),
            int(content_rect.top() + cut + 8),
        )
        painter.drawLine(
            int(content_rect.left() + cut),
            int(content_rect.top()),
            int(content_rect.left() + cut + 8),
            int(content_rect.top()),
        )

        # Draw Title
        if self.title():
            font = self.font()
            font.setBold(True)
            font.setPointSize(8)
            painter.setFont(font)
            painter.setPen(QColor(COLOR_ACCENT_PRIMARY))
            title_rect = QRectF(
                content_rect.left() + cut + 15,
                rect.top(),
                content_rect.width() - (cut * 2) - 30,
                title_h,
            )
            painter.drawText(
                title_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                self.title().upper(),
            )


class QuantumButton(QPushButton):
    """A button with chamfered corners and slide animation."""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hover_progress = 0.0
        self._hover_anim = QPropertyAnimation(self, b"hoverProgress")
        self._hover_anim.setDuration(200)
        self._hover_anim.setEasingCurve(QEasingCurve.Type.OutQuad)

        # Initial size hint to ensure it's large enough

    def getHoverProgress(self):
        return self._hover_progress

    def setHoverProgress(self, value):
        self._hover_progress = value
        self.update()

    hoverProgress = pyqtProperty(float, getHoverProgress, setHoverProgress)

    def enterEvent(self, event):
        self._hover_anim.setStartValue(self._hover_progress)
        self._hover_anim.setEndValue(1.0)
        self._hover_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover_anim.setStartValue(self._hover_progress)
        self._hover_anim.setEndValue(0.0)
        self._hover_anim.start()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.rect())
        rect.adjust(1, 1, -1, -1)
        cut = 10.0

        # Create shape
        path = QPainterPath()
        path.moveTo(rect.left(), rect.top() + cut)
        path.lineTo(rect.left() + cut, rect.top())
        path.lineTo(
            rect.right(), rect.top()
        )  # No cut top-right for variation? Let's do all 4
        path.lineTo(rect.right(), rect.bottom() - cut)
        path.lineTo(rect.right() - cut, rect.bottom())
        path.lineTo(rect.left(), rect.bottom())
        path.closeSubpath()

        # Base Background
        base_color = QColor(COLOR_BG_SECONDARY)
        painter.fillPath(path, base_color)

        # Hover Background (Slide effect)
        if self._hover_progress > 0.01:
            painter.save()
            painter.setClipPath(path)

            # Slide from left
            slide_width = rect.width() * self._hover_progress
            slide_rect = QRectF(rect.left(), rect.top(), slide_width, rect.height())

            gradient = QLinearGradient(slide_rect.topLeft(), slide_rect.topRight())
            c1 = QColor(COLOR_ACCENT_SECONDARY)
            c2 = QColor(COLOR_ACCENT_PRIMARY)
            c1.setAlpha(150)
            c2.setAlpha(200)
            gradient.setColorAt(0, c1)
            gradient.setColorAt(1, c2)

            painter.fillRect(slide_rect, gradient)
            painter.restore()

        # Border
        border_color = QColor(COLOR_ACCENT_PRIMARY)
        if self.isDown():
            border_color = QColor(Qt.GlobalColor.white)
        elif self._hover_progress > 0:
            border_color = QColor(COLOR_ACCENT_PRIMARY)
        else:
            border_color = QColor(COLOR_BORDER_SECONDARY)

        pen = QPen(border_color)
        pen.setWidth(2 if self._hover_progress > 0 else 1)
        painter.setPen(pen)
        painter.drawPath(path)

        # Text
        painter.setPen(
            QColor(COLOR_TEXT_PRIMARY)
            if self._hover_progress < 0.5
            else QColor(Qt.GlobalColor.white)
        )
        font = self.font()
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text().upper())


class HoloInput(QLineEdit):
    """An input field with holographic styling."""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(
            """
            QLineEdit {
                background: transparent;
                border: none;
                color: white;
                padding: 1px;
                font-family: 'Segoe UI';

                font-weight: bold;
            }
        """
        )
        self._focus_anim = 0.0
        self._anim = QPropertyAnimation(self, b"focusAnim")
        self._anim.setDuration(200)

    def getFocusAnim(self):
        return self._focus_anim

    def setFocusAnim(self, value):
        self._focus_anim = value
        self.update()

    focusAnim = pyqtProperty(float, getFocusAnim, setFocusAnim)

    def focusInEvent(self, event):
        self._anim.setStartValue(self._focus_anim)
        self._anim.setEndValue(1.0)
        self._anim.start()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self._anim.setStartValue(self._focus_anim)
        self._anim.setEndValue(0.0)
        self._anim.start()
        super().focusOutEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.rect())
        rect.adjust(1, 1, -1, -1)

        # Background
        bg = QColor(COLOR_BG_SECONDARY)
        bg.setAlpha(150)
        painter.fillRect(rect, bg)

        # Bottom Line
        pen = QPen(QColor(COLOR_BORDER_SECONDARY))
        pen.setWidth(1)
        painter.setPen(pen)

        # Draw bracket style
        h = rect.height()
        w = rect.width()

        # Left bracket
        path_l = QPainterPath()
        path_l.moveTo(rect.left(), rect.top() + h * 0.2)
        path_l.lineTo(rect.left(), rect.bottom())
        path_l.lineTo(rect.left() + 10, rect.bottom())
        painter.drawPath(path_l)

        # Right bracket
        path_r = QPainterPath()
        path_r.moveTo(rect.right(), rect.top() + h * 0.2)
        path_r.lineTo(rect.right(), rect.bottom())
        path_r.lineTo(rect.right() - 10, rect.bottom())
        painter.drawPath(path_r)

        # Glow Effect on Focus
        if self._focus_anim > 0.01:
            glow_pen = QPen(QColor(COLOR_ACCENT_PRIMARY))
            glow_pen.setWidth(2)
            glow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(glow_pen)

            # Draw highlight lines that grow from center
            center_x = rect.center().x()
            width = (w - 20) * self._focus_anim
            half_w = width / 2

            painter.drawLine(
                QPointF(center_x - half_w, rect.bottom()),
                QPointF(center_x + half_w, rect.bottom()),
            )

        super().paintEvent(event)


class AnimatedProgressBar(QProgressBar):
    """A progress bar with smooth animated fill."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._animated_value = 0
        self._value_animation = QPropertyAnimation(self, b"animatedValue")
        self._value_animation.setDuration(500)
        self._value_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def setValue(self, value: int):
        """Animate value change."""
        if value != self._animated_value:
            self._value_animation.stop()
            self._value_animation.setStartValue(self._animated_value)
            self._value_animation.setEndValue(value)
            self._value_animation.start()
        super().setValue(value)

    def getAnimatedValue(self):
        """Get current animated value."""
        return self._animated_value

    def setAnimatedValue(self, value):
        """Set animated value and update display."""
        self._animated_value = value
        self.update()

    animatedValue = pyqtProperty(int, getAnimatedValue, setAnimatedValue)

    def paintEvent(self, event):
        """Paint progress bar with animated fill."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()

        # Draw background
        bg_color = QColor(COLOR_BG_SECONDARY)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(rect, 6, 6)

        # Draw progress chunk with animation
        if self.maximum() > 0:
            progress_width = int(rect.width() * (self._animated_value / self.maximum()))
            if progress_width > 0:
                progress_rect = QRect(
                    rect.left(), rect.top(), progress_width, rect.height()
                )

                # Draw gradient fill
                gradient = QLinearGradient(
                    progress_rect.left(),
                    progress_rect.top(),
                    progress_rect.right(),
                    progress_rect.top(),
                )
                gradient.setColorAt(0, QColor(0, 162, 204))
                gradient.setColorAt(1, QColor(0, 217, 255))
                painter.setBrush(QBrush(gradient))
                painter.drawRoundedRect(progress_rect, 6, 6)

                # Draw glow effect
                glow_pen = QPen()
                glow_color = QColor(0, 240, 255)
                glow_color.setAlpha(150)
                glow_pen.setColor(glow_color)
                glow_pen.setWidth(2)
                painter.setPen(glow_pen)
                painter.drawRoundedRect(progress_rect.adjusted(1, 1, -1, -1), 5, 5)

        # Draw border
        border_pen = QPen()
        border_pen.setColor(QColor(0, 102, 128))
        border_pen.setWidth(2)
        painter.setPen(border_pen)
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 6, 6)

        # Draw text
        if self.text():
            painter.setPen(QColor(230, 233, 239))  # COLOR_TEXT_PRIMARY
            font = self.font()
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text())


class GlowLabel(QLabel):
    """A label with optional glow effect for output values."""

    def __init__(self, text="", parent=None, glow_enabled=True):
        super().__init__(text, parent)
        self._glow_enabled = glow_enabled
        self._glow_intensity = 0.5

    def setGlowEnabled(self, enabled: bool):
        """Enable or disable glow effect."""
        self._glow_enabled = enabled
        self.update()

    def paintEvent(self, event):
        """Paint label with glow effect."""
        if not self._glow_enabled:
            super().paintEvent(event)
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw text with glow
        font = self.font()
        painter.setFont(font)

        # Draw glow shadow (multiple layers for effect)
        glow_color = QColor(0, 217, 255)
        for i in range(3, 0, -1):
            glow_color.setAlpha(int(50 * self._glow_intensity / i))
            pen = QPen(glow_color)
            pen.setWidth(i * 2)
            painter.setPen(pen)
            painter.drawText(self.rect(), self.alignment(), self.text())

        # Draw main text
        painter.setPen(QColor(self.palette().color(self.foregroundRole())))
        painter.drawText(self.rect(), self.alignment(), self.text())


class ToastOverlay(QWidget):
    """A pop-up notification toast with a futuristic look."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.SubWindow)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._message = ""
        self._opacity = 0.0
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(300)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Timer to auto-hide
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide_toast)

        self.hide()

    def show_toast(self, message, duration=2500):
        self._message = message
        self.adjustSize()
        self.raise_()
        self.show()

        # Position bottom-right of parent
        if self.parent():
            p_rect = self.parent().rect()
            my_rect = self.rect()
            # 20px padding from bottom-right
            x = p_rect.width() - my_rect.width() - 20
            y = p_rect.height() - my_rect.height() - 20
            self.move(x, y)

        self._anim.stop()
        self._anim.setStartValue(self._opacity)
        self._anim.setEndValue(1.0)
        self._anim.start()

        self._timer.start(duration)

    def hide_toast(self):
        self._anim.stop()
        self._anim.setStartValue(self._opacity)
        self._anim.setEndValue(0.0)

        def _on_finish():
            if self._opacity == 0.0:
                self.hide()

        # self._anim.finished.connect(_on_finish) # Avoid multiple connects
        try:
            self._anim.finished.disconnect()
        except TypeError:
            pass
        self._anim.finished.connect(_on_finish)

        self._anim.start()

    def getWindowOpacity(self):
        return self._opacity

    def setWindowOpacity(self, value):
        self._opacity = value
        self.update()

    windowOpacity = pyqtProperty(float, getWindowOpacity, setWindowOpacity)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()

        # Background
        bg_color = QColor(COLOR_BG_SECONDARY)
        bg_color.setAlpha(220)
        painter.setBrush(QBrush(bg_color))

        # Border
        pen = QPen(QColor(COLOR_ACCENT_PRIMARY))
        pen.setWidth(1)
        painter.setPen(pen)

        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 6, 6)

        # Text
        painter.setPen(QColor(COLOR_TEXT_PRIMARY))
        font = self.font()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)

        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._message)

    def sizeHint(self):
        fm = self.fontMetrics()
        w = fm.horizontalAdvance(self._message) + 40
        h = fm.height() + 20
        return QSize(w, h)
