"""Reusable UI widgets, dialogs, SVG icons, and VTK interactor style for ScanSect."""

import os
import html

from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QLabel,
    QPushButton,
    QFrame,
    QScrollArea,
    QDialog,
    QProgressBar,
)
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtCore import Qt, QByteArray, QSize
from PySide6.QtSvg import QSvgRenderer

from managers import ensure_3d_libs

ICON_COLOR = "#e2e8f0"

SVG_MEASURE_ICON = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{ICON_COLOR}" width="16px" height="16px"><path d="M21 6H3c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h18c.55 0 1-.45 1-1V7c0-.55-.45-1-1-1zm-1 10H4V8h16v8z"/><path d="M6 10h2v4H6zm4-1h2v6h-2zm4-2h2v8h-2zm4 1h2v6h-2z"/></svg>"""
SVG_ROTATE_ICON = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{ICON_COLOR}" width="16px" height="16px"><path d="M12 2c-5.52 0-10 4.48-10 10s4.48 10 10 10c2.76 0 5.26-1.12 7.07-2.93l-1.41-1.41C16.09 19.24 14.14 20 12 20c-4.41 0-8-3.59-8-8s3.59-8 8-8c2.08 0 3.96.79 5.41 2.09L13 10h7V3l-2.35 2.35C15.96 3.26 14.08 2 12 2z"/></svg>"""
SVG_PAN_ICON_ALT = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{ICON_COLOR}" width="16px" height="16px"><path d="M12 2l-4 4h3v2.04c-3.01.23-5.46 1.68-7.16 3.81l1.42 1.42C6.6 11.93 8.99 11 12 11s5.4 0.93 6.74 2.27l1.42-1.42C18.46 9.72 16.01 8.27 13 8.04V6h3l-4-4zm0 20l4-4h-3v-2.04c3.01-.23 5.46-1.68 7.16-3.81l-1.42-1.42C17.4 12.07 15.01 13 12 13s-5.4-0.93-6.74-2.27l-1.42 1.42c1.7 2.13 4.15 3.58 7.16 3.81V18h-3l4 4zM2 12l4-4v3h2.04c.23-3.01 1.68-5.46 3.81-7.16l1.42 1.42C11.93 6.6 11 8.99 11 12s0.93 5.4 2.27 6.74l-1.42 1.42c-2.13-1.7-3.58-4.15-3.81-7.16H7v3l-4-4z"/></svg>"""
SVG_ZOOM_ICON = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{ICON_COLOR}" width="16px" height="16px"><path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5A6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/><path d="M10.5 8H11v1.5H9.5V11h-1V9.5H7V8h1.5V6.5H10V8z" /></svg>"""
SVG_OPEN_FILE_ICON = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{ICON_COLOR}" width="16px" height="16px"><path d="M20 6h-8l-2-2H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm0 12H4V6h5.17l2 2H20v10z"/><path d="M0 0h24v24H0z" fill="none"/></svg>"""
SVG_TEXTURE_ICON = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{ICON_COLOR}" width="16px" height="16px"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14zm-5.04-6.71l-2.75 3.54-1.96-2.36L6.5 17h11l-3.54-4.71z"/></svg>"""
SVG_SAVE_ICON = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{ICON_COLOR}" width="16px" height="16px"><path d="M17 3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V7l-4-4zm-5 16c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3zm3-10H5V5h10v4z"/></svg>"""
SVG_ARCHIVE_ICON = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{ICON_COLOR}" width="16px" height="16px"><path d="M20.54 5.23l-1.39-1.68C18.88 3.21 18.47 3 18 3H6c-.47 0-.88.21-1.16.55L3.46 5.23C3.17 5.57 3 6.02 3 6.5V19c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V6.5c0-.48-.17-.93-.46-1.27zM12 17.5L6.5 12H10v-2h4v2h3.5L12 17.5zM5.12 5l.81-1h12l.94 1H5.12z"/></svg>"""
SVG_CAMERA_ICON = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{ICON_COLOR}" width="16px" height="16px"><path d="M9 2L7.17 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2h-3.17L15 2H9zm3 15c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5z"/></svg>"""


def get_icon_from_svg(svg_data_string, size=QSize(16, 16)):
    renderer = QSvgRenderer(QByteArray(svg_data_string.encode('utf-8')))
    pixmap = QPixmap(size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


class MeasurementDisplayWidget(QFrame):
    """Instrument readout bar for active 3D measurements."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MeasurementDisplay")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        self.hide()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        self._icon_label = QLabel()
        self._icon_label.setPixmap(get_icon_from_svg(SVG_MEASURE_ICON, QSize(16, 16)).pixmap(QSize(16, 16)))
        self._icon_label.setStyleSheet("background: transparent;")
        layout.addWidget(self._icon_label)

        self._title = QLabel("Measurement")
        self._title.setObjectName("MeasurementTitle")
        layout.addWidget(self._title)

        self._mode_badge = QLabel("/ Distance")
        self._mode_badge.setObjectName("MeasurementModeBadge")
        layout.addWidget(self._mode_badge)

        self._distance_label = QLabel("0.00 mm")
        self._distance_label.setObjectName("MeasurementValue")
        layout.addWidget(self._distance_label)

        self._coords_label = QLabel("")
        self._coords_label.setObjectName("MeasurementCoords")
        layout.addWidget(self._coords_label, stretch=1)

        self._step_label = QLabel("")
        self._step_label.setObjectName("MeasurementStep")
        layout.addWidget(self._step_label)

    def update_measurement(self, point1, point2, distance_text):
        self._distance_label.setText(distance_text)
        self._coords_label.setText(
            f"P1 ({point1[0]:.2f}, {point1[1]:.2f}, {point1[2]:.2f}) -> "
            f"P2 ({point2[0]:.2f}, {point2[1]:.2f}, {point2[2]:.2f})"
        )
        if not self.isVisible():
            self.show()

    def update_context(self, mode_text, step_text):
        self._mode_badge.setText(f"/ {(mode_text or 'Distance').capitalize()}")
        self._step_label.setText(step_text or "")
        if not self.isVisible():
            self.show()

    def clear_display(self):
        self._distance_label.setText("0.00 mm")
        self._coords_label.setText("")
        self._step_label.setText("")
        self.hide()


class ScreenshotPreviewDialog(QDialog):
    """Zoomable preview dialog for screenshots."""

    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Preview: {os.path.basename(image_path)}")
        self.setMinimumSize(640, 520)
        self._zoom_level = 1.0
        self._pixmap = QPixmap(image_path)

        layout = QVBoxLayout(self)

        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignCenter)
        self._image_label.setPixmap(self._pixmap)

        scroll = QScrollArea()
        scroll.setWidget(self._image_label)
        scroll.setWidgetResizable(False)
        scroll.setAlignment(Qt.AlignCenter)
        layout.addWidget(scroll, stretch=1)

        zoom_row = QHBoxLayout()
        zoom_in = QPushButton("Zoom In (+)")
        zoom_in.clicked.connect(self._zoom_in)
        zoom_row.addWidget(zoom_in)

        self._zoom_label = QLabel("100%")
        self._zoom_label.setAlignment(Qt.AlignCenter)
        self._zoom_label.setMinimumWidth(64)
        zoom_row.addWidget(self._zoom_label)

        zoom_out = QPushButton("Zoom Out (-)")
        zoom_out.clicked.connect(self._zoom_out)
        zoom_row.addWidget(zoom_out)

        fit_btn = QPushButton("Fit to Window")
        fit_btn.clicked.connect(self._fit_to_window)
        zoom_row.addWidget(fit_btn)

        layout.addLayout(zoom_row)

        info = QLabel(f"Resolution: {self._pixmap.width()} x {self._pixmap.height()} px   |   Path: {image_path}")
        info.setObjectName("PreviewDialogInfo")
        layout.addWidget(info)

        self._apply_zoom()

    def _zoom_in(self):
        self._zoom_level = min(self._zoom_level + 0.25, 5.0)
        self._apply_zoom()

    def _zoom_out(self):
        self._zoom_level = max(self._zoom_level - 0.25, 0.25)
        self._apply_zoom()

    def _fit_to_window(self):
        if self._pixmap.isNull():
            return
        available = self.size() - QSize(40, 120)
        scale_w = available.width() / self._pixmap.width()
        scale_h = available.height() / self._pixmap.height()
        self._zoom_level = min(scale_w, scale_h, 5.0)
        self._apply_zoom()

    def _apply_zoom(self):
        if self._pixmap.isNull():
            return
        new_size = self._pixmap.size() * self._zoom_level
        scaled = self._pixmap.scaled(new_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._image_label.setPixmap(scaled)
        self._image_label.resize(scaled.size())
        self._zoom_label.setText(f"{int(self._zoom_level * 100)}%")


class MeasurementDetailWidget(QFrame):
    """Detailed inspector panel for a selected measurement record."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MeasurementDetail")
        self.setMinimumHeight(130)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        header = QLabel("Measurement Inspector")
        header.setObjectName("MeasurementDetailHeader")
        layout.addWidget(header)

        self._detail_text = QLabel("Select a measurement to inspect coordinates and metadata.")
        self._detail_text.setObjectName("MeasurementDetailText")
        self._detail_text.setWordWrap(True)
        layout.addWidget(self._detail_text)

        self._linked_label = QLabel("")
        self._linked_label.setObjectName("MeasurementLinkedLabel")
        self._linked_label.setWordWrap(True)
        layout.addWidget(self._linked_label)
        layout.addStretch()

    def show_detail(self, data, linked_screenshots=None):
        if not data:
            self._detail_text.setText("Select a measurement to inspect coordinates and metadata.")
            self._linked_label.setText("")
            return

        dist = html.escape(str(data.get('distance', 'N/A')))
        m_type = html.escape(str(data.get('measurement_type', 'distance')).capitalize())
        desc = html.escape(str(data.get('description', 'No description')))
        ts = html.escape(str(data.get('timestamp', 'Unknown')))
        model = html.escape(str(data.get('model_name', 'Unknown')))
        sid = html.escape(str(data.get('session_id', 'N/A')))

        p1 = data.get('point1', [0, 0, 0])
        p2 = data.get('point2', [0, 0, 0])
        p3 = data.get('point3')

        self._detail_text.setText(
            f"<b>Value:</b> <span style='color: #38bdf8; font-size: 11pt; font-weight: bold;'>{dist}</span> "
            f"<span style='color: #94a3b8;'>({m_type})</span><br/>"
            f"<b>Note:</b> {desc}<br/>"
            f"<b>Model:</b> {model} &nbsp;|&nbsp; <b>Session:</b> <span style='color: #94a3b8;'>{sid}</span><br/>"
            f"<b>Recorded:</b> <span style='color: #94a3b8;'>{ts}</span><br/>"
            f"<b>P1:</b> ({p1[0]:.3f}, {p1[1]:.3f}, {p1[2]:.3f}) &nbsp;&nbsp;"
            f"<b>P2:</b> ({p2[0]:.3f}, {p2[1]:.3f}, {p2[2]:.3f})"
            + (f"<br/><b>P3:</b> ({p3[0]:.3f}, {p3[1]:.3f}, {p3[2]:.3f})" if p3 else "")
        )

        if linked_screenshots:
            names = ", ".join(os.path.basename(s.get('file_path', '?')) for s in linked_screenshots)
            self._linked_label.setText(f"Session screenshots: {names}")
        else:
            self._linked_label.setText("Session screenshots: None")


class LoadingOverlay(QWidget):
    """Opaque overlay shown during model loading.
    Parented to the regular QWidget container rather than the VTK/OpenGL widget.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        self.setStyleSheet("background-color: #16181d;")
        self.hide()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self._label = QLabel("Loading model...")
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setStyleSheet("color: #f1f5f9; font-size: 13pt; font-weight: 600; background: transparent;")
        layout.addWidget(self._label)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setFixedWidth(280)
        self._progress.setStyleSheet("""
            QProgressBar { border: 1px solid #334155; border-radius: 4px; background: #1e222a; height: 14px; }
            QProgressBar::chunk { background-color: #0284c7; border-radius: 3px; }
        """)
        layout.addWidget(self._progress, alignment=Qt.AlignCenter)

    def show_message(self, text):
        self._label.setText(text)
        if self.parent():
            self.setGeometry(self.parent().rect())
        self.show()
        self.raise_()

    def hide_overlay(self):
        self.hide()


class ScanSectUnifiedInteractorStyle:
    @classmethod
    def create(cls):
        _, vtk, _, _ = ensure_3d_libs()

        class _Style(vtk.vtkInteractorStyleTrackballCamera):
            def __init__(self):
                super().__init__()
                self.current_left_click_mode = "rotate"

            def set_left_click_mode(self, mode_str):
                self.current_left_click_mode = mode_str.lower()

        return _Style()
