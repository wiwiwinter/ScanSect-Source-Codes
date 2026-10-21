"""ScanSect 3D Insect Model Viewer main window and application entry point."""

import sys
import os
import json
import csv
import uuid
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QFileDialog,
    QLabel,
    QStatusBar,
    QTextEdit,
    QPushButton,
    QButtonGroup,
    QAbstractButton,
    QFrame,
    QMessageBox,
    QListWidget,
    QListWidgetItem,
    QTabWidget,
    QDialog,
    QDialogButtonBox,
    QLineEdit,
    QComboBox,
    QSplitter,
    QSplashScreen,
    QSlider,
    QCheckBox,
)
from PySide6.QtGui import (
    QAction,
    QKeySequence,
    QIcon,
    QMouseEvent,
    QPixmap,
    QPainter,
    QFont,
    QColor,
    QShortcut,
    QDesktopServices,
)
from PySide6.QtCore import Qt, QEvent, Slot, QSize, QTimer, QUrl

from measurement_utils import (
    distance_raw,
    distance_mm,
    polyline_raw,
    polyline_mm,
    angle_degrees,
    unit_multiplier_from_mm,
    format_distance_from_mm,
    atomic_write_json_with_backup,
    load_json_with_backup,
)
from managers import (
    ensure_3d_libs,
    ModelLoaderWorker,
    MeshManager,
    ArchiveManager,
)
from widgets import (
    SVG_MEASURE_ICON,
    SVG_ROTATE_ICON,
    SVG_PAN_ICON_ALT,
    SVG_ZOOM_ICON,
    SVG_OPEN_FILE_ICON,
    SVG_TEXTURE_ICON,
    SVG_SAVE_ICON,
    SVG_ARCHIVE_ICON,
    SVG_CAMERA_ICON,
    get_icon_from_svg,
    MeasurementDisplayWidget,
    ScreenshotPreviewDialog,
    MeasurementDetailWidget,
    LoadingOverlay,
    ScanSectUnifiedInteractorStyle,
)


class ScanSectGUI(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ScanSect - 3D Insect Model Viewer")
        self.setGeometry(100, 100, 1440, 880)

        self.is_measuring = False
        self.measurement_text_actor = None
        self.current_measurement = {}
        self._measurement_pick_points = []
        self._measurement_line_actors = []
        self._measurement_marker_actors = []
        self.measurement_mode = "Distance"
        self.session_measurements = []
        self._vertex_picker = None
        self._active_remapped_button = Qt.NoButton
        self._loader_worker = None
        self._pending_measurement_data = None
        self._current_session_id = str(uuid.uuid4())[:8]
        self.measurement_unit = "mm"
        self.scale_to_mm = 1.0
        self.render_preset = "Textured"
        self.clip_enabled = False
        self.clip_ratio = 0.5
        self.high_contrast_enabled = False
        self._thumbnail_cache = {}

        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.mesh_mgr = MeshManager()
        self.archive_mgr = ArchiveManager(os.path.join(script_dir, "ScanSect_Archive"))

        self.recent_models_file = os.path.join(script_dir, "recent_models.json")
        self.recent_models = self._load_recent_models()

        app_icon_path = os.path.join(script_dir, "ScanSect ICON.png")
        if os.path.exists(app_icon_path):
            self.setWindowIcon(QIcon(app_icon_path))

        self._init_3d_viewport()
        self._init_toolbar()
        self._init_side_panel()
        self._init_layout()
        self._init_menus()
        self._init_shortcuts()
        self._init_interactor()
        self._init_status_bar()
        self._apply_stylesheet()
        self._run_archive_integrity_check()

        self._refresh_screenshot_list()
        self._refresh_measurement_list()
        self._refresh_recent_models_list()

    def _init_3d_viewport(self):
        _, _, _, QtInteractor = ensure_3d_libs()
        self._viewport_container = QWidget()
        self._viewport_layout = QVBoxLayout(self._viewport_container)
        self._viewport_layout.setContentsMargins(0, 0, 0, 0)
        self._viewport_layout.setSpacing(0)

        self.plotter = QtInteractor(self._viewport_container)
        self.plotter.setObjectName("Viewport3D")
        self.plotter.set_background('white')
        self.plotter.enable_trackball_style()
        self.plotter.show_axes()
        self.plotter.add_axes()
        self.plotter.background_color = 'white'
        self._viewport_layout.addWidget(self.plotter, stretch=1)

        self.measurement_display = MeasurementDisplayWidget()
        self.loading_overlay = LoadingOverlay(self._viewport_container)

    def _init_toolbar(self):
        """Split controls into a top Display/File bar and a bottom Camera/Measure bar
        so buttons never crowd into a single horizontal strip.
        """
        icon_size = QSize(16, 16)

        # Top Viewport Header: Model file, Surface appearance, Z-Sectioning, and Capture
        self.top_viewport_bar = QFrame()
        self.top_viewport_bar.setObjectName("TopViewportBar")
        top_layout = QHBoxLayout(self.top_viewport_bar)
        top_layout.setContentsMargins(12, 8, 12, 8)
        top_layout.setSpacing(10)

        self.open_model_button = QPushButton("Open Model")
        self.open_model_button.setIcon(get_icon_from_svg(SVG_OPEN_FILE_ICON, icon_size))
        self.open_model_button.clicked.connect(self.open_model_dialog)
        self.open_model_button.setToolTip("Open 3D model or texture (Ctrl+O)")
        top_layout.addWidget(self.open_model_button)

        self.texture_button = QPushButton("Load Texture")
        self.texture_button.setIcon(get_icon_from_svg(SVG_TEXTURE_ICON, icon_size))
        self.texture_button.clicked.connect(self.load_texture_dialog)
        self.texture_button.setEnabled(False)
        self.texture_button.setToolTip("Apply image texture to current model")
        top_layout.addWidget(self.texture_button)

        top_layout.addWidget(self._make_separator())

        view_label = QLabel("Surface")
        view_label.setObjectName("ToolGroupLabel")
        top_layout.addWidget(view_label)

        self.render_preset_combo = QComboBox()
        self.render_preset_combo.addItems(["Textured", "Matte", "Wireframe", "X-Ray"])
        self.render_preset_combo.currentTextChanged.connect(self._on_render_preset_changed)
        self.render_preset_combo.setToolTip("Viewport render style")
        self.render_preset_combo.setMinimumWidth(105)
        top_layout.addWidget(self.render_preset_combo)

        top_layout.addWidget(self._make_separator())

        self.clip_toggle_button = QPushButton("Section Z")
        self.clip_toggle_button.setCheckable(True)
        self.clip_toggle_button.clicked.connect(self._toggle_clip_mode)
        self.clip_toggle_button.setEnabled(False)
        self.clip_toggle_button.setToolTip("Toggle Z-axis cross-section clipping")
        top_layout.addWidget(self.clip_toggle_button)

        self.clip_slider = QSlider(Qt.Horizontal)
        self.clip_slider.setRange(10, 90)
        self.clip_slider.setValue(50)
        self.clip_slider.setTracking(False)
        self.clip_slider.valueChanged.connect(self._on_clip_slider_changed)
        self.clip_slider.setEnabled(False)
        self.clip_slider.setFixedWidth(110)
        self.clip_slider.setToolTip("Release slider to update Z-section depth")
        top_layout.addWidget(self.clip_slider)

        top_layout.addStretch()

        self.screenshot_button = QPushButton("Capture View")
        self.screenshot_button.setIcon(get_icon_from_svg(SVG_CAMERA_ICON, icon_size))
        self.screenshot_button.clicked.connect(self.capture_screenshot)
        self.screenshot_button.setToolTip("Capture viewport screenshot (Ctrl+Shift+C)")
        top_layout.addWidget(self.screenshot_button)

        # Bottom Viewport Dock: Camera navigation and Morphometric measurement tools
        self.tool_button_container = QFrame()
        self.tool_button_container.setObjectName("ToolButtonContainer")
        bottom_layout = QHBoxLayout(self.tool_button_container)
        bottom_layout.setContentsMargins(12, 8, 12, 8)
        bottom_layout.setSpacing(10)

        self.interaction_mode_group = QButtonGroup(self)
        self.interaction_mode_group.setExclusive(True)

        nav_label = QLabel("Camera")
        nav_label.setObjectName("ToolGroupLabel")
        bottom_layout.addWidget(nav_label)

        self.rotate_button = QPushButton("Rotate")
        self.rotate_button.setIcon(get_icon_from_svg(SVG_ROTATE_ICON, icon_size))
        self.rotate_button.setCheckable(True)
        self.rotate_button.setChecked(True)
        bottom_layout.addWidget(self.rotate_button)
        self.interaction_mode_group.addButton(self.rotate_button)

        self.pan_button = QPushButton("Pan")
        self.pan_button.setIcon(get_icon_from_svg(SVG_PAN_ICON_ALT, icon_size))
        self.pan_button.setCheckable(True)
        bottom_layout.addWidget(self.pan_button)
        self.interaction_mode_group.addButton(self.pan_button)

        self.zoom_button = QPushButton("Zoom")
        self.zoom_button.setIcon(get_icon_from_svg(SVG_ZOOM_ICON, icon_size))
        self.zoom_button.setCheckable(True)
        bottom_layout.addWidget(self.zoom_button)
        self.interaction_mode_group.addButton(self.zoom_button)

        bottom_layout.addWidget(self._make_separator())

        tools_label = QLabel("Morphometrics")
        tools_label.setObjectName("ToolGroupLabel")
        bottom_layout.addWidget(tools_label)

        self.measure_button = QPushButton("Measure")
        self.measure_button.setIcon(get_icon_from_svg(SVG_MEASURE_ICON, icon_size))
        self.measure_button.setCheckable(True)
        self.measure_button.clicked.connect(self.toggle_measurement_mode)
        self.measure_button.setToolTip("Toggle vertex measurement mode (M)")
        bottom_layout.addWidget(self.measure_button)

        self.measure_mode_combo = QComboBox()
        self.measure_mode_combo.addItems(["Distance", "Angle", "Polyline"])
        self.measure_mode_combo.currentTextChanged.connect(self._on_measurement_mode_changed)
        self.measure_mode_combo.setToolTip("Measurement mode")
        self.measure_mode_combo.setMinimumWidth(105)
        bottom_layout.addWidget(self.measure_mode_combo)

        self.finish_measure_button = QPushButton("Finish Path")
        self.finish_measure_button.clicked.connect(self._finish_polyline_measurement)
        self.finish_measure_button.setEnabled(False)
        self.finish_measure_button.setVisible(False)
        self.finish_measure_button.setToolTip("Finish polyline measurement (Ctrl+Enter or Right-Click)")
        bottom_layout.addWidget(self.finish_measure_button)

        bottom_layout.addStretch()

        self.save_measurement_button = QPushButton("Save Measurement")
        self.save_measurement_button.setIcon(get_icon_from_svg(SVG_SAVE_ICON, icon_size))
        self.save_measurement_button.clicked.connect(self.save_measurement_data)
        self.save_measurement_button.setEnabled(False)
        self.save_measurement_button.setToolTip("Save current measurement to archive (Ctrl+Shift+S)")
        bottom_layout.addWidget(self.save_measurement_button)

    def _make_separator(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Plain)
        sep.setObjectName("ToolSeparator")
        return sep

    def _init_side_panel(self):
        self.right_panel_tabs = QTabWidget()
        self.right_panel_tabs.setObjectName("RightPanelTabs")
        self.right_panel_tabs.setMinimumWidth(370)

        self.metadata_panel = QTextEdit(self)
        self.metadata_panel.setReadOnly(True)
        self.metadata_panel.setPlaceholderText("Open a 3D model to inspect geometry, bounding box, and UV mapping.")
        self.metadata_panel.setObjectName("MetadataPanel")
        self.right_panel_tabs.addTab(self.metadata_panel, "Model Info")

        self._build_measurement_module_tab()
        self._build_screenshot_module_tab()
        self._build_recent_models_tab()

    def _build_measurement_module_tab(self):
        meas_widget = QWidget()
        meas_layout = QVBoxLayout(meas_widget)
        meas_layout.setContentsMargins(10, 10, 10, 10)
        meas_layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("Measurements")
        title.setObjectName("ArchiveTitle")
        header.addWidget(title)
        header.addStretch()

        self.meas_open_folder_btn = QPushButton("Open Folder")
        self.meas_open_folder_btn.setIcon(get_icon_from_svg(SVG_ARCHIVE_ICON, QSize(16, 16)))
        self.meas_open_folder_btn.clicked.connect(lambda: self._open_folder(self.archive_mgr.measurements_dir))
        header.addWidget(self.meas_open_folder_btn)
        meas_layout.addLayout(header)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(6)
        self.meas_insect_filter = QComboBox()
        self.meas_insect_filter.addItem("All Insects")
        self.meas_insect_filter.currentTextChanged.connect(self._apply_measurement_filters)
        filter_row.addWidget(self.meas_insect_filter, stretch=1)

        self.meas_sort_combo = QComboBox()
        self.meas_sort_combo.addItems([
            "Newest First",
            "Oldest First",
            "Distance \u2191",
            "Distance \u2193",
            "Angle \u2191",
            "Angle \u2193",
        ])
        self.meas_sort_combo.currentTextChanged.connect(self._apply_measurement_filters)
        filter_row.addWidget(self.meas_sort_combo)
        meas_layout.addLayout(filter_row)

        self.meas_search_edit = QLineEdit()
        self.meas_search_edit.setPlaceholderText("Search measurements by note, model, value, or session...")
        self.meas_search_edit.textChanged.connect(self._apply_measurement_filters)
        meas_layout.addWidget(self.meas_search_edit)

        scope_unit_row = QHBoxLayout()
        scope_unit_row.setSpacing(8)
        self.meas_current_model_only_chk = QCheckBox("Current Model")
        self.meas_current_model_only_chk.stateChanged.connect(self._apply_measurement_filters)
        scope_unit_row.addWidget(self.meas_current_model_only_chk)

        self.meas_current_session_only_chk = QCheckBox("Session Only")
        self.meas_current_session_only_chk.stateChanged.connect(self._apply_measurement_filters)
        scope_unit_row.addWidget(self.meas_current_session_only_chk)
        scope_unit_row.addStretch()

        scope_unit_row.addWidget(QLabel("Unit:"))
        self.meas_unit_combo = QComboBox()
        self.meas_unit_combo.addItems(["mm", "cm", "um", "m"])
        self.meas_unit_combo.setCurrentText("mm")
        self.meas_unit_combo.currentTextChanged.connect(self._on_measurement_display_settings_changed)
        scope_unit_row.addWidget(self.meas_unit_combo)

        scope_unit_row.addWidget(QLabel("Scale:"))
        self.meas_scale_edit = QLineEdit("1.0")
        self.meas_scale_edit.setPlaceholderText("1.0")
        self.meas_scale_edit.setToolTip("Millimeters per model unit")
        self.meas_scale_edit.editingFinished.connect(self._on_measurement_display_settings_changed)
        self.meas_scale_edit.setFixedWidth(58)
        scope_unit_row.addWidget(self.meas_scale_edit)
        meas_layout.addLayout(scope_unit_row)

        session_header = QHBoxLayout()
        self.session_measure_label = QLabel("Session Log (0)")
        self.session_measure_label.setObjectName("ArchiveSubTitle")
        session_header.addWidget(self.session_measure_label)
        session_header.addStretch()

        self.session_export_btn = QPushButton("Export CSV")
        self.session_export_btn.clicked.connect(self._export_session_measurements_csv)
        session_header.addWidget(self.session_export_btn)

        self.session_clear_btn = QPushButton("Clear")
        self.session_clear_btn.clicked.connect(self._clear_session_measurements)
        session_header.addWidget(self.session_clear_btn)
        meas_layout.addLayout(session_header)

        self.session_measure_list = QListWidget()
        self.session_measure_list.setObjectName("MeasurementListWidget")
        self.session_measure_list.setMaximumHeight(92)
        self.session_measure_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.session_measure_list.itemSelectionChanged.connect(self._load_session_measurement)
        self.session_measure_list.hide()
        meas_layout.addWidget(self.session_measure_list)

        saved_label = QLabel("Saved Archive")
        saved_label.setObjectName("ArchiveSubTitle")
        meas_layout.addWidget(saved_label)

        self.measurement_list = QListWidget()
        self.measurement_list.setObjectName("MeasurementListWidget")
        self.measurement_list.setIconSize(QSize(56, 56))
        self.measurement_list.setSpacing(4)
        self.measurement_list.setWordWrap(True)
        self.measurement_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.measurement_list.itemSelectionChanged.connect(self._on_measurement_selection_changed)
        self.measurement_list.itemDoubleClicked.connect(self._on_measurement_double_clicked)
        meas_layout.addWidget(self.measurement_list, stretch=1)

        self.measurement_empty_label = QLabel("No saved measurements match the active filters.")
        self.measurement_empty_label.setObjectName("EmptyStateLabel")
        self.measurement_empty_label.setAlignment(Qt.AlignCenter)
        self.measurement_empty_label.setWordWrap(True)
        self.measurement_empty_label.hide()
        meas_layout.addWidget(self.measurement_empty_label)

        self.measurement_detail = MeasurementDetailWidget()
        meas_layout.addWidget(self.measurement_detail)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        self.meas_load_btn = QPushButton("Load to Viewport")
        self.meas_load_btn.setIcon(get_icon_from_svg(SVG_MEASURE_ICON, QSize(16, 16)))
        self.meas_load_btn.clicked.connect(self._load_measurement_from_module)
        self.meas_load_btn.setEnabled(False)
        btn_row.addWidget(self.meas_load_btn)

        self.meas_rename_btn = QPushButton("Rename")
        self.meas_rename_btn.clicked.connect(self._rename_measurement)
        self.meas_rename_btn.setEnabled(False)
        btn_row.addWidget(self.meas_rename_btn)

        self.meas_delete_btn = QPushButton("Delete")
        self.meas_delete_btn.clicked.connect(self._delete_measurement)
        self.meas_delete_btn.setEnabled(False)
        btn_row.addWidget(self.meas_delete_btn)
        meas_layout.addLayout(btn_row)

        self.right_panel_tabs.addTab(
            meas_widget,
            get_icon_from_svg(SVG_MEASURE_ICON, QSize(14, 14)),
            "Measurements",
        )

    def _build_screenshot_module_tab(self):
        ss_widget = QWidget()
        ss_layout = QVBoxLayout(ss_widget)
        ss_layout.setContentsMargins(10, 10, 10, 10)
        ss_layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("Screenshots")
        title.setObjectName("ArchiveTitle")
        header.addWidget(title)
        header.addStretch()

        self.ss_open_folder_btn = QPushButton("Open Folder")
        self.ss_open_folder_btn.setIcon(get_icon_from_svg(SVG_ARCHIVE_ICON, QSize(16, 16)))
        self.ss_open_folder_btn.clicked.connect(lambda: self._open_folder(self.archive_mgr.screenshots_dir))
        header.addWidget(self.ss_open_folder_btn)
        ss_layout.addLayout(header)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(6)
        filter_row.addWidget(QLabel("Specimen:"))
        self.ss_insect_filter = QComboBox()
        self.ss_insect_filter.addItem("All Insects")
        self.ss_insect_filter.currentTextChanged.connect(self._apply_screenshot_filters)
        filter_row.addWidget(self.ss_insect_filter, stretch=1)
        ss_layout.addLayout(filter_row)

        self.ss_search_edit = QLineEdit()
        self.ss_search_edit.setPlaceholderText("Search screenshots by note, model, date, or filename...")
        self.ss_search_edit.textChanged.connect(self._apply_screenshot_filters)
        ss_layout.addWidget(self.ss_search_edit)

        ss_scope_row = QHBoxLayout()
        ss_scope_row.setSpacing(10)
        self.ss_current_model_only_chk = QCheckBox("Current Model")
        self.ss_current_model_only_chk.stateChanged.connect(self._apply_screenshot_filters)
        ss_scope_row.addWidget(self.ss_current_model_only_chk)

        self.ss_current_session_only_chk = QCheckBox("Current Session")
        self.ss_current_session_only_chk.stateChanged.connect(self._apply_screenshot_filters)
        ss_scope_row.addWidget(self.ss_current_session_only_chk)
        ss_scope_row.addStretch()
        ss_layout.addLayout(ss_scope_row)

        self.screenshot_list = QListWidget()
        self.screenshot_list.setObjectName("ScreenshotListWidget")
        self.screenshot_list.setIconSize(QSize(88, 88))
        self.screenshot_list.setSpacing(4)
        self.screenshot_list.setWordWrap(True)
        self.screenshot_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.screenshot_list.itemSelectionChanged.connect(self._on_screenshot_selection_changed)
        self.screenshot_list.itemDoubleClicked.connect(self._preview_screenshot)
        ss_layout.addWidget(self.screenshot_list, stretch=1)

        self.screenshot_empty_label = QLabel("No saved screenshots match the active filters.")
        self.screenshot_empty_label.setObjectName("EmptyStateLabel")
        self.screenshot_empty_label.setAlignment(Qt.AlignCenter)
        self.screenshot_empty_label.setWordWrap(True)
        self.screenshot_empty_label.hide()
        ss_layout.addWidget(self.screenshot_empty_label)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        self.ss_preview_btn = QPushButton("Preview")
        self.ss_preview_btn.clicked.connect(self._preview_selected_screenshot)
        self.ss_preview_btn.setEnabled(False)
        btn_row.addWidget(self.ss_preview_btn)

        self.ss_rename_btn = QPushButton("Rename")
        self.ss_rename_btn.clicked.connect(self._rename_screenshot)
        self.ss_rename_btn.setEnabled(False)
        btn_row.addWidget(self.ss_rename_btn)

        self.ss_delete_btn = QPushButton("Delete")
        self.ss_delete_btn.clicked.connect(self._delete_screenshot)
        self.ss_delete_btn.setEnabled(False)
        btn_row.addWidget(self.ss_delete_btn)
        ss_layout.addLayout(btn_row)

        self.right_panel_tabs.addTab(
            ss_widget,
            get_icon_from_svg(SVG_CAMERA_ICON, QSize(14, 14)),
            "Screenshots",
        )

    def _build_recent_models_tab(self):
        recent_widget = QWidget()
        recent_layout = QVBoxLayout(recent_widget)
        recent_layout.setContentsMargins(10, 10, 10, 10)
        recent_layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("Recent Models")
        title.setObjectName("ArchiveTitle")
        header.addWidget(title)
        header.addStretch()
        self.clear_recent_button = QPushButton("Clear All")
        self.clear_recent_button.clicked.connect(self._clear_recent_models)
        header.addWidget(self.clear_recent_button)
        recent_layout.addLayout(header)

        self.recent_models_list = QListWidget()
        self.recent_models_list.setObjectName("ArchiveList")
        self.recent_models_list.setSpacing(4)
        self.recent_models_list.setWordWrap(True)
        self.recent_models_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.recent_models_list.itemDoubleClicked.connect(self._load_recent_model)
        self.recent_models_list.itemSelectionChanged.connect(self._on_recent_selection_changed)
        recent_layout.addWidget(self.recent_models_list, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        self.load_recent_button = QPushButton("Load Selected")
        self.load_recent_button.clicked.connect(lambda: self._load_recent_model(self.recent_models_list.currentItem()))
        self.load_recent_button.setEnabled(False)
        btn_row.addWidget(self.load_recent_button)
        self.remove_recent_button = QPushButton("Remove Selected")
        self.remove_recent_button.clicked.connect(self._remove_recent_model)
        self.remove_recent_button.setEnabled(False)
        btn_row.addWidget(self.remove_recent_button)
        recent_layout.addLayout(btn_row)

        self.right_panel_tabs.addTab(recent_widget, "Recent")

    def _init_layout(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(0)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        left_layout.addWidget(self.top_viewport_bar)
        left_layout.addWidget(self._viewport_container, stretch=1)
        left_layout.addWidget(self.measurement_display)

        self.inline_alert_label = QLabel("")
        self.inline_alert_label.setObjectName("InlineAlert")
        self.inline_alert_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.inline_alert_label.hide()
        self._inline_alert_timer = QTimer(self)
        self._inline_alert_timer.setSingleShot(True)
        self._inline_alert_timer.timeout.connect(self.inline_alert_label.hide)
        left_layout.addWidget(self.inline_alert_label)

        left_layout.addWidget(self.tool_button_container)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(left_panel)
        self.splitter.addWidget(self.right_panel_tabs)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([1030, 400])
        self.splitter.setHandleWidth(8)
        self.splitter.setStyleSheet("""
            QSplitter::handle { background-color: #262b36; border-radius: 2px; margin: 0 2px; }
            QSplitter::handle:hover { background-color: #38bdf8; }
        """)
        self.main_layout.addWidget(self.splitter)

    def _show_inline_alert(self, message, level="info", timeout_ms=4000):
        level_styles = {
            "info": "background-color: #162a3d; border-color: #38bdf8; color: #e0f2fe;",
            "success": "background-color: #143326; border-color: #34d399; color: #d1fae5;",
            "warning": "background-color: #3b2a14; border-color: #fbbf24; color: #fef3c7;",
            "error": "background-color: #3f1d24; border-color: #f87171; color: #fee2e2;",
        }
        style = level_styles.get(level, level_styles["info"])
        self.inline_alert_label.setStyleSheet(
            f"border: 1px solid; border-radius: 4px; padding: 6px 10px; font-size: 9pt; {style}"
        )
        self.inline_alert_label.setText(message)
        self.inline_alert_label.show()
        self._inline_alert_timer.start(timeout_ms)

    def _on_toggle_high_contrast(self, enabled):
        self.high_contrast_enabled = bool(enabled)
        self._apply_stylesheet()
        mode = "enabled" if self.high_contrast_enabled else "disabled"
        self._show_inline_alert(f"High contrast mode {mode}.", level="info")

    def _init_menus(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        open_action = QAction(get_icon_from_svg(SVG_OPEN_FILE_ICON, QSize(16, 16)), "&Open Model or Texture...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_model_dialog)
        file_menu.addAction(open_action)
        file_menu.addSeparator()
        exit_action = QAction("&Exit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        settings_menu = menu_bar.addMenu("&Settings")
        self.high_contrast_action = QAction("High Contrast Mode", self)
        self.high_contrast_action.setCheckable(True)
        self.high_contrast_action.toggled.connect(self._on_toggle_high_contrast)
        settings_menu.addAction(self.high_contrast_action)

    def _init_shortcuts(self):
        self.shortcut_toggle_measure = QShortcut(QKeySequence("M"), self)
        self.shortcut_toggle_measure.activated.connect(self.measure_button.click)

        self.shortcut_capture = QShortcut(QKeySequence("Ctrl+Shift+C"), self)
        self.shortcut_capture.activated.connect(self.capture_screenshot)

        self.shortcut_save_measure = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        self.shortcut_save_measure.activated.connect(self.save_measurement_data)

        self.shortcut_finish_polyline = QShortcut(QKeySequence("Ctrl+Enter"), self)
        self.shortcut_finish_polyline.activated.connect(self._finish_polyline_measurement)

        self.shortcut_open_model = QShortcut(QKeySequence("Ctrl+Shift+O"), self)
        self.shortcut_open_model.activated.connect(self.open_model_dialog)

    def _init_interactor(self):
        self.custom_interactor_style = ScanSectUnifiedInteractorStyle.create()
        if hasattr(self.plotter, 'interactor') and self.plotter.interactor is not None:
            self.plotter.interactor.SetInteractorStyle(self.custom_interactor_style)
        self.plotter.installEventFilter(self)
        self.custom_interactor_style.set_left_click_mode("rotate")
        self.interaction_mode_group.buttonClicked.connect(self._on_interaction_mode_changed)

    def _init_status_bar(self):
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(
            "Ready. Left-click: Rotate | Shortcuts: Ctrl+O (Open), M (Measure), Ctrl+Shift+C (Capture), Ctrl+Shift+S (Save)"
        )

    def _format_distance_from_mm(self, value_mm, decimals=2):
        return format_distance_from_mm(value_mm, self.measurement_unit, decimals)

    def _measurement_display_text(self, entry):
        m_type = str(entry.get('measurement_type', 'distance')).lower()
        if m_type == 'angle':
            return f"{float(entry.get('angle_degrees', 0.0)):.2f} deg"
        return self._format_distance_from_mm(self._measurement_entry_mm(entry), decimals=2)

    def _measurement_entry_mm(self, entry):
        if not isinstance(entry, dict):
            return 0.0

        value_mm = entry.get('distance_value_mm')
        if value_mm is not None:
            try:
                return float(value_mm)
            except Exception:
                pass

        m_type = str(entry.get('measurement_type', 'distance')).lower()
        if m_type == 'angle':
            return 0.0

        dist_text = str(entry.get('distance', '0')).strip()
        parts = dist_text.split()
        try:
            value = float(parts[0])
        except Exception:
            return 0.0

        unit = parts[1].lower() if len(parts) > 1 else 'mm'
        multiplier = unit_multiplier_from_mm(unit)
        if multiplier <= 0:
            return value
        return value / multiplier

    def _on_measurement_display_settings_changed(self):
        self.measurement_unit = self.meas_unit_combo.currentText()

        try:
            scale_value = float(self.meas_scale_edit.text().strip())
            if scale_value <= 0:
                raise ValueError("Scale must be positive")
            self.scale_to_mm = scale_value
        except Exception:
            self.meas_scale_edit.setText(f"{self.scale_to_mm:.6g}")
            QMessageBox.warning(self, "Invalid Scale", "Scale to mm must be a positive number.")
            return

        if self.current_measurement:
            points = self.current_measurement.get('points')
            if points:
                self._finalize_measurement_from_points(record_history=False)

        self._refresh_measurement_list()

    def _measurement_required_points(self):
        mode = self.measurement_mode.lower()
        if mode == 'distance':
            return 2
        if mode == 'angle':
            return 3
        return 2

    def _measurement_mode_label(self):
        mode = self.measurement_mode.lower()
        if mode == 'distance':
            return "Shift+LeftClick two vertices to measure distance."
        if mode == 'angle':
            return "Shift+LeftClick three vertices (middle point is angle vertex)."
        return "Shift+LeftClick points to build polyline, then click Finish Path (Ctrl+Enter or Right-Click)."

    def _measurement_step_text(self):
        mode = self.measurement_mode.lower()
        count = len(self._measurement_pick_points)
        if mode == 'distance':
            return f"Step {min(count + 1, 2)}/2" if count < 2 else "Ready to save"
        if mode == 'angle':
            return f"Step {min(count + 1, 3)}/3" if count < 3 else "Ready to save"
        if count < 2:
            return "Step 1/2"
        return f"{count} pts (Right-Click to finish)"

    def _update_measure_ui_hints(self):
        is_polyline = self.measurement_mode.lower() == 'polyline'
        self.finish_measure_button.setVisible(is_polyline)
        self.finish_measure_button.setEnabled(self.is_measuring and is_polyline and len(self._measurement_pick_points) >= 2)
        if self.is_measuring:
            self.status_bar.showMessage(f"Measurement mode [{self.measurement_mode}]: {self._measurement_mode_label()}")
            self.measurement_display.update_context(self.measurement_mode, self._measurement_step_text())
            self.measurement_display._distance_label.setText("Select vertices...")
            self.measurement_display._coords_label.setText("Hold Shift + Left-Click on mesh surface")
            self._position_measurement_display()

    def _on_measurement_mode_changed(self, mode_text):
        self.measurement_mode = mode_text
        self._measurement_pick_points = []
        self.current_measurement = {}
        self._clear_measurement_visuals()
        self.finish_measure_button.setVisible(self.measurement_mode.lower() == 'polyline')
        if self.is_measuring:
            self._update_measure_ui_hints()
        else:
            self.measurement_display.clear_display()
        self.save_measurement_button.setEnabled(False)

    def _record_session_measurement(self, measurement_entry):
        entry = dict(measurement_entry)
        entry.setdefault('scale_to_mm', self.scale_to_mm)
        entry.setdefault('unit', self.measurement_unit)
        self.session_measurements.append(entry)
        self._refresh_session_measurement_list()

    def _refresh_session_measurement_list(self):
        self.session_measure_list.clear()
        count = len(self.session_measurements)
        self.session_measure_label.setText(f"Session Log ({count})")
        for idx, item in enumerate(self.session_measurements, start=1):
            label = self._measurement_display_text(item)
            m_type = str(item.get('measurement_type', 'distance')).capitalize()
            li = QListWidgetItem(f"#{idx} {m_type}: {label}")
            li.setData(Qt.UserRole, item)
            self.session_measure_list.addItem(li)
        self.session_measure_list.setVisible(count > 0)

    def _restore_measurement_scale_and_unit(self, data):
        saved_scale = data.get('scale_to_mm')
        if saved_scale is not None:
            try:
                scale_val = float(saved_scale)
                if scale_val > 0:
                    self.scale_to_mm = scale_val
                    self.meas_scale_edit.setText(f"{self.scale_to_mm:.6g}")
            except (TypeError, ValueError):
                pass
        saved_unit = data.get('unit')
        if saved_unit and self.meas_unit_combo.findText(str(saved_unit)) >= 0:
            self.measurement_unit = str(saved_unit)
            self.meas_unit_combo.blockSignals(True)
            self.meas_unit_combo.setCurrentText(self.measurement_unit)
            self.meas_unit_combo.blockSignals(False)

    def _load_session_measurement(self):
        selected = self.session_measure_list.selectedItems()
        if not selected:
            return
        self._apply_measurement_data_to_viewport(selected[0].data(Qt.UserRole), switch_tab=False)

    def _clear_session_measurements(self):
        self.session_measurements = []
        self._refresh_session_measurement_list()
        self.session_measure_list.clearSelection()

    def _export_session_measurements_csv(self):
        if not self.session_measurements:
            self._show_inline_alert("No session measurements to export yet.", level="warning")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"session_measurements_{timestamp}.csv"
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Session Measurements",
            os.path.join(os.path.expanduser("~"), default_name),
            "CSV Files (*.csv);;All Files (*)",
        )
        if not save_path:
            return

        try:
            with open(save_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "index",
                    "type",
                    "display_value",
                    "distance_mm",
                    "angle_degrees",
                    "point_count",
                    "points_json",
                ])

                for idx, item in enumerate(self.session_measurements, start=1):
                    points = item.get('points', [])
                    m_type = str(item.get('measurement_type', 'distance')).lower()
                    writer.writerow([
                        idx,
                        m_type,
                        self._measurement_display_text(item),
                        float(item.get('distance_value_mm', 0.0)) if m_type != 'angle' else "",
                        float(item.get('angle_degrees', 0.0)) if m_type == 'angle' else "",
                        len(points),
                        json.dumps(points),
                    ])

            self.status_bar.showMessage(f"Session measurements exported: {save_path}")
            self._show_inline_alert(f"Session measurements exported: {os.path.basename(save_path)}", level="success")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Could not export CSV:\n{e}")

    def _finish_polyline_measurement(self):
        if self.measurement_mode.lower() != 'polyline' or not self.is_measuring:
            return
        if len(self._measurement_pick_points) < 2:
            QMessageBox.warning(self, "Not Enough Points", "Pick at least two points for a polyline measurement.")
            return
        self._finalize_measurement_from_points(record_history=True)

    def _get_display_mesh(self):
        mesh = self.mesh_mgr.current_mesh
        if mesh is None:
            return None

        if not self.clip_enabled:
            return mesh

        try:
            bounds = mesh.bounds
            z_min, z_max = bounds[4], bounds[5]
            if z_max - z_min <= 1e-12:
                return mesh

            z_cut = z_min + (z_max - z_min) * self.clip_ratio
            x_mid = 0.5 * (bounds[0] + bounds[1])
            y_mid = 0.5 * (bounds[2] + bounds[3])
            clipped = mesh.clip(normal='z', origin=(x_mid, y_mid, z_cut), invert=False)
            if clipped is None or clipped.n_points == 0:
                return mesh
            return clipped
        except Exception:
            return mesh

    def _apply_render_to_current_mesh(self, reset_camera=False):
        if not self.mesh_mgr.has_model:
            return

        display_mesh = self._get_display_mesh()
        if display_mesh is None:
            return

        if self.mesh_mgr.current_actor:
            self.plotter.remove_actor(self.mesh_mgr.current_actor)

        texture = self.mesh_mgr.get_first_texture()
        use_texture = texture is not None and self.render_preset == "Textured"

        if self.render_preset == "Wireframe":
            self.mesh_mgr.current_actor = self.plotter.add_mesh(
                display_mesh,
                style='wireframe',
                color='#0284c7',
                line_width=1.2,
                lighting=False,
            )
        elif self.render_preset == "X-Ray":
            self.mesh_mgr.current_actor = self.plotter.add_mesh(
                display_mesh,
                smooth_shading=True,
                show_edges=True,
                opacity=0.35,
                color='#d9d9d9',
                lighting=True,
            )
        elif self.render_preset == "Matte":
            self.mesh_mgr.current_actor = self.plotter.add_mesh(
                display_mesh,
                smooth_shading=True,
                show_edges=False,
                color='#d9d9d9',
                lighting=True,
            )
        else:
            if use_texture:
                self.mesh_mgr.current_actor = self.plotter.add_mesh(
                    display_mesh,
                    texture=texture,
                    smooth_shading=True,
                    show_edges=False,
                    lighting=True,
                    color='white',
                )
            else:
                self.mesh_mgr.current_actor = self.plotter.add_mesh(
                    display_mesh,
                    smooth_shading=True,
                    show_edges=False,
                    lighting=True,
                    color='white',
                )

        self.plotter.render()
        if reset_camera:
            self.plotter.reset_camera()
        self.plotter.setFocus()

    def _on_render_preset_changed(self, preset_name):
        self.render_preset = preset_name
        if self.mesh_mgr.has_model:
            self._apply_render_to_current_mesh(reset_camera=False)

    def _toggle_clip_mode(self):
        if not self.mesh_mgr.has_model:
            self.clip_toggle_button.setChecked(False)
            QMessageBox.warning(self, "No Model", "Please load a 3D model before clipping.")
            return

        self.clip_enabled = self.clip_toggle_button.isChecked()
        self.clip_slider.setEnabled(self.clip_enabled)
        self._apply_render_to_current_mesh(reset_camera=False)

        if self.clip_enabled:
            self.status_bar.showMessage("Z-clipping enabled. Release the slider to update slice depth.")
        else:
            self.status_bar.showMessage("Z-clipping disabled.")

    def _on_clip_slider_changed(self, slider_value):
        self.clip_ratio = max(0.1, min(0.9, slider_value / 100.0))
        if self.clip_enabled and self.mesh_mgr.has_model:
            self._apply_render_to_current_mesh(reset_camera=False)

    def _run_archive_integrity_check(self):
        def _clean_entries(entries):
            valid, removed, fixed_thumbs = [], 0, 0
            for entry in entries:
                file_path = entry.get('file_path')
                if not file_path or not os.path.exists(file_path):
                    removed += 1
                    continue
                updated = dict(entry)
                thumb_path = updated.get('thumbnail_path')
                if thumb_path and not os.path.exists(thumb_path):
                    updated['thumbnail_path'] = None
                    fixed_thumbs += 1
                valid.append(updated)
            return valid, removed, fixed_thumbs

        valid_ss, rem_ss, fix_ss = _clean_entries(self.archive_mgr.screenshots)
        valid_meas, rem_meas, fix_meas = _clean_entries(self.archive_mgr.measurements)

        if rem_ss > 0 or fix_ss > 0:
            self.archive_mgr.screenshots = valid_ss
            self.archive_mgr.save_screenshots()
        if rem_meas > 0 or fix_meas > 0:
            self.archive_mgr.measurements = valid_meas
            self.archive_mgr.save_measurements()

        total_removed = rem_ss + rem_meas
        fixed_thumbnails = fix_ss + fix_meas
        if total_removed > 0 or fixed_thumbnails > 0:
            self.status_bar.showMessage(
                f"Archive check: removed {total_removed} missing entries, repaired {fixed_thumbnails} thumbnail links."
            )

    def _apply_stylesheet(self):
        """Precision lab instrument dark theme:
        - Base surface: #16181d, raised panel: #1e222a, control surface: #262b36
        - Primary text: #f1f5f9 (contrast ~16.2:1), secondary text: #94a3b8 (contrast ~6.2:1 >= 4.5:1)
        - Single active/focus accent: #0369a1 / #38bdf8
        """
        base_stylesheet = """
            QMainWindow { background-color: #16181d; }
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 9.5pt;
                color: #f1f5f9;
            }
            QTextEdit#MetadataPanel {
                background-color: #16181d;
                color: #e2e8f0;
                border: 1px solid #2e3440;
                border-radius: 4px;
                padding: 12px;
                font-family: 'Consolas', 'Cascadia Mono', 'Segoe UI', monospace;
                font-size: 9.5pt;
            }
            QFrame#TopViewportBar, QFrame#ToolButtonContainer {
                background-color: #1e222a;
                border: 1px solid #2e3440;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #262b36;
                color: #f1f5f9;
                border: 1px solid #384152;
                border-radius: 4px;
                padding: 6px 13px;
                min-height: 24px;
                icon-size: 16px;
            }
            QPushButton:hover {
                background-color: #303746;
                border-color: #38bdf8;
            }
            QPushButton:pressed {
                background-color: #1b2028;
            }
            QPushButton:checked {
                background-color: #0369a1;
                color: #ffffff;
                border: 1px solid #38bdf8;
                font-weight: 600;
            }
            QPushButton:disabled {
                background-color: #1b1f27;
                color: #64748b;
                border-color: #262b36;
            }
            QPushButton:focus {
                border: 1px solid #38bdf8;
            }
            QStatusBar {
                font-size: 9pt;
                color: #cbd5e1;
                background-color: #121418;
                border-top: 1px solid #262b36;
            }
            QMenuBar {
                background-color: #16181d;
                color: #e2e8f0;
                border-bottom: 1px solid #262b36;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 5px 10px;
            }
            QMenuBar::item:selected {
                background-color: #262b36;
                color: #ffffff;
                border-radius: 3px;
            }
            QMenu {
                background-color: #1e222a;
                color: #f1f5f9;
                border: 1px solid #384152;
                border-radius: 4px;
            }
            QMenu::item {
                padding: 5px 22px;
            }
            QMenu::item:selected {
                background-color: #0369a1;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background: #2e3440;
                margin: 4px 6px;
            }
            QLabel#ToolGroupLabel {
                color: #94a3b8;
                font-size: 9pt;
                font-weight: 600;
                margin: 0px 4px;
            }
            QFrame#ToolSeparator {
                color: #333b4a;
                background-color: #333b4a;
                max-width: 1px;
                margin: 3px 6px;
            }
            QTabWidget#RightPanelTabs {
                background-color: #16181d;
                border: none;
            }
            QTabWidget::pane {
                border: 1px solid #2e3440;
                background-color: #1e222a;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #16181d;
                color: #94a3b8;
                border: 1px solid #2e3440;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 7px 13px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #1e222a;
                color: #f8fafc;
                border-top: 2px solid #38bdf8;
                font-weight: 600;
            }
            QTabBar::tab:hover:!selected {
                background-color: #222731;
                color: #e2e8f0;
            }
            QLabel#ArchiveTitle {
                font-size: 10.5pt;
                font-weight: 600;
                color: #f8fafc;
            }
            QLabel#ArchiveSubTitle {
                font-size: 9pt;
                font-weight: 600;
                color: #94a3b8;
                margin-top: 2px;
            }
            QLabel#PreviewDialogInfo {
                color: #94a3b8;
                font-size: 8.5pt;
                padding-top: 2px;
            }
            QComboBox, QLineEdit {
                background-color: #262b36;
                color: #f1f5f9;
                border: 1px solid #384152;
                border-radius: 4px;
                padding: 5px 9px;
                min-height: 22px;
            }
            QComboBox:hover, QLineEdit:hover {
                border-color: #64748b;
            }
            QComboBox:focus, QLineEdit:focus, QListWidget:focus {
                border: 1px solid #38bdf8;
            }
            QComboBox QAbstractItemView {
                background-color: #1e222a;
                color: #f1f5f9;
                border: 1px solid #384152;
                selection-background-color: #0369a1;
            }
            QCheckBox {
                color: #cbd5e1;
                spacing: 6px;
            }
            QLabel#EmptyStateLabel {
                background-color: #16181d;
                border: 1px solid #2e3440;
                border-radius: 4px;
                color: #94a3b8;
                font-size: 9.5pt;
                padding: 16px;
            }
            QLabel#InlineAlert {
                border-radius: 4px;
                font-size: 9pt;
                padding: 6px 10px;
            }
            QListWidget#MeasurementListWidget,
            QListWidget#ScreenshotListWidget,
            QListWidget#ArchiveList {
                background-color: #16181d;
                color: #e2e8f0;
                border: 1px solid #2e3440;
                border-radius: 4px;
                padding: 6px;
                font-size: 9pt;
            }
            QListWidget#MeasurementListWidget::item,
            QListWidget#ScreenshotListWidget::item,
            QListWidget#ArchiveList::item {
                padding: 9px 10px;
                border-bottom: 1px solid #222731;
                border-left: 3px solid transparent;
                border-radius: 2px;
                margin-bottom: 2px;
            }
            QListWidget#MeasurementListWidget::item:selected,
            QListWidget#ScreenshotListWidget::item:selected,
            QListWidget#ArchiveList::item:selected {
                background-color: #172a3a;
                color: #ffffff;
                border-left: 3px solid #38bdf8;
            }
            QListWidget#MeasurementListWidget::item:hover:!selected,
            QListWidget#ScreenshotListWidget::item:hover:!selected,
            QListWidget#ArchiveList::item:hover:!selected {
                background-color: #1e2430;
            }
            QFrame#MeasurementDisplay {
                background-color: #16181d;
                border: 1px solid #38bdf8;
                border-radius: 4px;
            }
            QLabel#MeasurementTitle {
                color: #f8fafc;
                font-size: 9.5pt;
                font-weight: 600;
                background: transparent;
            }
            QLabel#MeasurementModeBadge {
                color: #38bdf8;
                background: transparent;
                font-size: 9.5pt;
                font-weight: 600;
            }
            QLabel#MeasurementValue {
                color: #ffffff;
                font-family: 'Consolas', 'Cascadia Mono', 'Segoe UI', monospace;
                font-size: 13pt;
                font-weight: bold;
                background: transparent;
                padding: 0px 4px;
            }
            QLabel#MeasurementCoords {
                color: #cbd5e1;
                font-family: 'Consolas', 'Cascadia Mono', 'Segoe UI', monospace;
                font-size: 9pt;
                background: transparent;
            }
            QLabel#MeasurementStep {
                color: #94a3b8;
                font-size: 9pt;
                background: transparent;
            }
            QFrame#MeasurementDetail {
                background-color: #16181d;
                border: 1px solid #2e3440;
                border-radius: 4px;
            }
            QLabel#MeasurementDetailHeader {
                color: #f8fafc;
                font-size: 9.5pt;
                font-weight: 600;
                background: transparent;
            }
            QLabel#MeasurementDetailText {
                color: #e2e8f0;
                font-size: 9pt;
                background: transparent;
            }
            QLabel#MeasurementLinkedLabel {
                color: #94a3b8;
                font-size: 8.5pt;
                background: transparent;
            }
        """

        high_contrast_stylesheet = """
            QMainWindow { background-color: #000000; }
            QWidget { color: #ffffff; }
            QMenuBar, QMenu, QStatusBar { background-color: #000000; color: #ffffff; }
            QTextEdit#MetadataPanel,
            QListWidget#MeasurementListWidget,
            QListWidget#ScreenshotListWidget,
            QListWidget#ArchiveList {
                background-color: #000000;
                color: #ffffff;
                border: 2px solid #ffffff;
            }
            QPushButton, QComboBox, QLineEdit {
                background-color: #000000;
                color: #ffffff;
                border: 2px solid #ffffff;
            }
            QPushButton:hover, QComboBox:hover, QLineEdit:focus, QListWidget:focus {
                border: 2px solid #ffd400;
            }
            QFrame#TopViewportBar, QFrame#ToolButtonContainer, QFrame#MeasurementDisplay, QFrame#MeasurementDetail {
                background-color: #000000;
                border: 2px solid #ffffff;
            }
            QLabel#MeasurementValue, QLabel#MeasurementTitle, QLabel#MeasurementModeBadge, QLabel#MeasurementStep,
            QLabel#MeasurementCoords, QLabel#ArchiveTitle, QLabel#ArchiveSubTitle, QLabel#ToolGroupLabel,
            QLabel#EmptyStateLabel, QLabel#PreviewDialogInfo, QLabel#MeasurementLinkedLabel {
                color: #ffffff;
            }
        """

        if self.high_contrast_enabled:
            self.setStyleSheet(base_stylesheet + high_contrast_stylesheet)
        else:
            self.setStyleSheet(base_stylesheet)

    def eventFilter(self, obj, event):
        if obj == self.plotter:
            if not isinstance(event, QMouseEvent):
                return super().eventFilter(obj, event)

            if (self.is_measuring
                    and self.measurement_mode.lower() == 'polyline'
                    and event.type() == QEvent.MouseButtonPress
                    and event.button() == Qt.RightButton):
                self._finish_polyline_measurement()
                return True

            if self.is_measuring and event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                # Hold Shift+LeftClick to pick vertices while keeping regular drag rotation active.
                if event.modifiers() & Qt.ShiftModifier:
                    self._handle_measurement_click(event)
                    return True

            current_mode = self.custom_interactor_style.current_left_click_mode

            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                target_button = Qt.NoButton
                if current_mode == "pan":
                    target_button = Qt.MiddleButton
                elif current_mode == "zoom":
                    target_button = Qt.RightButton
                if target_button != Qt.NoButton:
                    self._active_remapped_button = target_button
                    remapped = QMouseEvent(event.type(), event.position(), event.globalPosition(),
                                           target_button, event.buttons() | target_button, event.modifiers())
                    QApplication.postEvent(obj, remapped)
                    return True

            elif event.type() == QEvent.MouseMove:
                if event.buttons() & Qt.LeftButton and self._active_remapped_button != Qt.NoButton:
                    remapped_buttons = (event.buttons() & ~Qt.LeftButton) | self._active_remapped_button
                    remapped = QMouseEvent(event.type(), event.position(), event.globalPosition(),
                                           self._active_remapped_button, remapped_buttons, event.modifiers())
                    QApplication.postEvent(obj, remapped)
                    return True

            elif event.type() == QEvent.MouseButtonRelease:
                if event.button() == Qt.LeftButton and self._active_remapped_button != Qt.NoButton:
                    target = self._active_remapped_button
                    self._active_remapped_button = Qt.NoButton
                    remapped_buttons = event.buttons() & ~Qt.LeftButton
                    remapped = QMouseEvent(event.type(), event.position(), event.globalPosition(),
                                           target, remapped_buttons, event.modifiers())
                    QApplication.postEvent(obj, remapped)
                    return True
                elif self._active_remapped_button != Qt.NoButton and event.button() == self._active_remapped_button:
                    self._active_remapped_button = Qt.NoButton
        return super().eventFilter(obj, event)

    @Slot(QAbstractButton)
    def _on_interaction_mode_changed(self, button_clicked):
        mode_string = "rotate"
        if button_clicked == self.pan_button:
            mode_string = "pan"
        elif button_clicked == self.zoom_button:
            mode_string = "zoom"
        self.custom_interactor_style.set_left_click_mode(mode_string)
        self.status_bar.showMessage(f"Left-Click Mode: {mode_string.capitalize()}")
        self.plotter.setFocus()

    @Slot()
    def open_model_dialog(self):
        file_filter = "3D Models (*.ply *.stl *.obj *.vtk *.vtp *.vtu);;Textures (*.png *.jpg *.jpeg *.bmp *.tiff);;All Files (*)"
        start_dir = os.path.dirname(self.mesh_mgr.current_path) if self.mesh_mgr.current_path else os.path.expanduser("~")
        file_path, _ = QFileDialog.getOpenFileName(self, "Open 3D Model or Texture", start_dir, file_filter)
        if file_path:
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                self.apply_texture_to_current_model(file_path)
            else:
                self.load_model(file_path)

    def load_model(self, file_path):
        if self._loader_worker is not None and self._loader_worker.isRunning():
            QMessageBox.warning(self, "Busy", "A model is already being loaded.")
            return
        self.loading_overlay.show_message(f"Loading: {os.path.basename(file_path)}...")
        self.status_bar.showMessage(f"Loading model: {file_path}...")
        self._loader_worker = ModelLoaderWorker(file_path)
        self._loader_worker.progress.connect(self._on_load_progress)
        self._loader_worker.finished.connect(self._on_model_loaded)
        self._loader_worker.error.connect(self._on_model_load_error)
        self._loader_worker.start()

    @Slot(str)
    def _on_load_progress(self, message):
        self.loading_overlay.show_message(message)
        self.status_bar.showMessage(message)

    @Slot(object, str)
    def _on_model_loaded(self, mesh, file_path):
        self.loading_overlay.hide_overlay()
        try:
            self.mesh_mgr.set_mesh(mesh, file_path)
            self.texture_button.setEnabled(True)
            self.clip_toggle_button.setEnabled(True)
            self._current_session_id = str(uuid.uuid4())[:8]
            self._clear_session_measurements()

            self._apply_render_to_current_mesh(reset_camera=True)
            self._add_to_recent_models(file_path)

            mode = self.custom_interactor_style.current_left_click_mode.capitalize()
            if self.is_measuring:
                self._measurement_pick_points = []
                self.current_measurement = {}
                self._clear_measurement_visuals()
                self.measurement_display.clear_display()
                self.save_measurement_button.setEnabled(False)
                self._update_measure_ui_hints()
            else:
                self.status_bar.showMessage(f"Loaded: {self.mesh_mgr.model_basename} ({mesh.n_cells:,} cells) | Mode: {mode}")
            texture_loaded = self.mesh_mgr.has_textures()
            self.metadata_panel.setText(self.mesh_mgr.get_metadata_text(texture_auto=texture_loaded))
            self._apply_measurement_filters()
            self._apply_screenshot_filters()

            if self._pending_measurement_data is not None:
                pending = self._pending_measurement_data
                self._pending_measurement_data = None
                self._apply_measurement_data_to_viewport(pending, switch_tab=True)

            if file_path.lower().endswith('.obj') and not texture_loaded:
                QMessageBox.information(
                    self,
                    "No Texture Found",
                    "Could not find a texture file for this model.\n\n"
                    "You can apply one manually with the Load Texture button.",
                )
        except Exception as e:
            self.status_bar.showMessage(f"Error displaying model: {e}")
            QMessageBox.critical(self, "Model Display Error", f"Could not display model:\n{e}")

    @Slot(str, str)
    def _on_model_load_error(self, error_message, file_path):
        self._pending_measurement_data = None
        self.loading_overlay.hide_overlay()
        self.status_bar.showMessage(f"Error loading model: {error_message}")
        QMessageBox.critical(self, "Model Load Error", f"Could not load model:\n{error_message}")
        self.mesh_mgr.clear()
        self.texture_button.setEnabled(False)
        self.clip_toggle_button.setEnabled(False)
        self.clip_toggle_button.setChecked(False)
        self.clip_slider.setEnabled(False)

    def apply_texture_to_current_model(self, texture_path):
        if not self.mesh_mgr.has_model:
            QMessageBox.warning(self, "No Model Loaded", "Please load a 3D model before applying a texture.")
            return
        self.status_bar.showMessage(f"Applying texture: {texture_path}...")
        try:
            pv, _, _, _ = ensure_3d_libs()
            texture = pv.read_texture(texture_path)
            if not self.mesh_mgr.has_uvs():
                reply = QMessageBox.question(
                    self,
                    "No UV Coordinates",
                    "This model lacks UV coordinates. Generate planar UV mapping?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply == QMessageBox.Yes:
                    try:
                        self.mesh_mgr.current_mesh.texture_map_to_plane(inplace=True)
                    except Exception as uv_error:
                        QMessageBox.warning(self, "UV Generation Failed", f"Could not generate UV coordinates:\n{uv_error}")

            if self.mesh_mgr.current_actor:
                self.plotter.remove_actor(self.mesh_mgr.current_actor)
            self.mesh_mgr.current_texture = texture
            self._apply_render_to_current_mesh(reset_camera=True)
            self.status_bar.showMessage(f"Texture '{os.path.basename(texture_path)}' applied.")
            self.metadata_panel.setText(self.mesh_mgr.get_metadata_text(texture_manual=True))
        except Exception as e:
            self.status_bar.showMessage(f"Error applying texture: {e}")
            QMessageBox.critical(self, "Texture Error", f"Could not apply texture:\n{e}")

    def load_texture_dialog(self):
        if not self.mesh_mgr.has_model:
            QMessageBox.warning(self, "No Model", "Please load a 3D model first.")
            return
        file_filter = "Texture Files (*.jpg *.jpeg *.png *.bmp *.tiff);;All Files (*)"
        start_dir = os.path.dirname(self.mesh_mgr.current_path) if self.mesh_mgr.current_path else os.path.expanduser("~")
        texture_path, _ = QFileDialog.getOpenFileName(self, "Open Texture", start_dir, file_filter)
        if texture_path:
            self.apply_texture_to_current_model(texture_path)

    def toggle_measurement_mode(self):
        ensure_3d_libs()
        self.is_measuring = self.measure_button.isChecked()

        if self.is_measuring:
            if not self.mesh_mgr.has_model:
                QMessageBox.warning(self, "No Model", "Please load a 3D model before measuring.")
                self.measure_button.setChecked(False)
                self.is_measuring = False
                return
            if not hasattr(self.plotter, 'iren') or self.plotter.iren is None:
                QMessageBox.warning(self, "Error", "3D viewer not properly initialized.")
                self.measure_button.setChecked(False)
                return
            try:
                self._init_vertex_picker()

                self._measurement_pick_points = []
                self.current_measurement = {}
                self._clear_measurement_visuals()
                self.measurement_display.clear_display()
                self.save_measurement_button.setEnabled(False)
                self._update_measure_ui_hints()
            except Exception as e:
                self.measure_button.setChecked(False)
                self.is_measuring = False
                self._cleanup_measurement_widgets()
                QMessageBox.warning(self, "Error", f"Could not initialize measurement tool: {e}")
                return
        else:
            self._cleanup_measurement_widgets()
            self.measurement_display.clear_display()
            self.save_measurement_button.setEnabled(False)
            self.finish_measure_button.setEnabled(False)
            self.status_bar.clearMessage()

        self.plotter.render()

    def _cleanup_measurement_widgets(self):
        self._clear_measurement_visuals()
        self._measurement_pick_points = []
        self.current_measurement = {}
        self.finish_measure_button.setEnabled(False)
        if self.measurement_text_actor:
            self.plotter.renderer.RemoveActor(self.measurement_text_actor)
            self.measurement_text_actor = None

    def _init_vertex_picker(self):
        _, vtk, _, _ = ensure_3d_libs()
        if self._vertex_picker is None:
            self._vertex_picker = vtk.vtkPointPicker()
            self._vertex_picker.SetTolerance(0.01)
            self._vertex_picker.PickFromListOn()

    def _handle_measurement_click(self, event):
        if not self.is_measuring or not self.mesh_mgr.has_model:
            return
        vertex = self._pick_vertex_from_click(event.position())
        if vertex is None:
            self.status_bar.showMessage("No vertex selected. Click closer to a visible mesh vertex.")
            self._show_inline_alert("No vertex selected. Click closer to the model.", level="warning")
            return

        required_points = self._measurement_required_points()
        if self.measurement_mode.lower() != 'polyline' and len(self._measurement_pick_points) >= required_points:
            self._measurement_pick_points = []
            self.current_measurement = {}
            self.save_measurement_button.setEnabled(False)
            self.measurement_display.clear_display()

        self._measurement_pick_points.append(vertex)
        self._draw_measurement_visuals()

        mode = self.measurement_mode.lower()
        if mode == 'polyline':
            self.finish_measure_button.setEnabled(len(self._measurement_pick_points) >= 2)
            self.status_bar.showMessage(f"Polyline points: {len(self._measurement_pick_points)}. Click Finish Path when done.")
            self.measurement_display.update_context(self.measurement_mode, self._measurement_step_text())
            self._position_measurement_display()
            return

        if len(self._measurement_pick_points) < required_points:
            self.status_bar.showMessage(f"Point {len(self._measurement_pick_points)} locked. Need {required_points} points total.")
            self.measurement_display.update_context(self.measurement_mode, self._measurement_step_text())
            self._position_measurement_display()
            return

        self._finalize_measurement_from_points(record_history=True)

    def _pick_vertex_from_click(self, pos):
        if self._vertex_picker is None:
            self._init_vertex_picker()

        if self.mesh_mgr.current_actor is None or self.mesh_mgr.current_mesh is None:
            return None

        self._vertex_picker.InitializePickList()
        self._vertex_picker.AddPickList(self.mesh_mgr.current_actor)

        x = int(pos.x())
        y = int(self.plotter.height() - pos.y() - 1)
        did_pick = self._vertex_picker.Pick(x, y, 0, self.plotter.renderer)
        if not did_pick:
            return None

        point_id = self._vertex_picker.GetPointId()
        if point_id < 0:
            return None

        mapper = self.mesh_mgr.current_actor.GetMapper()
        dataset = mapper.GetInput() if mapper is not None else None
        if dataset is not None and point_id < dataset.GetNumberOfPoints():
            p = dataset.GetPoint(point_id)
            return [float(p[0]), float(p[1]), float(p[2])]

        points = self.mesh_mgr.current_mesh.points
        if point_id >= len(points):
            return None

        p = points[point_id]
        return [float(p[0]), float(p[1]), float(p[2])]

    def _draw_measurement_visuals(self):
        _, vtk, np, _ = ensure_3d_libs()
        self._clear_measurement_visuals()
        if not self._measurement_pick_points:
            self.plotter.render()
            return

        radius = 1.0
        if self.mesh_mgr.current_mesh is not None:
            bounds = self.mesh_mgr.current_mesh.bounds
            dx = bounds[1] - bounds[0]
            dy = bounds[3] - bounds[2]
            dz = bounds[5] - bounds[4]
            diag = max(np.sqrt(dx * dx + dy * dy + dz * dz), 1e-6)
            radius = max(diag * 0.005, 0.05)

        marker_colors = [(0.96, 0.62, 0.04), (0.01, 0.52, 0.78)]
        for idx, point in enumerate(self._measurement_pick_points):
            sphere = vtk.vtkSphereSource()
            sphere.SetCenter(point[0], point[1], point[2])
            sphere.SetRadius(radius)
            sphere.SetThetaResolution(18)
            sphere.SetPhiResolution(18)

            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(sphere.GetOutputPort())

            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            color = marker_colors[min(idx, len(marker_colors) - 1)]
            actor.GetProperty().SetColor(*color)
            actor.GetProperty().SetSpecular(0.3)
            actor.GetProperty().SetSpecularPower(20)

            self.plotter.renderer.AddActor(actor)
            self._measurement_marker_actors.append(actor)

        if len(self._measurement_pick_points) >= 2:
            for i in range(1, len(self._measurement_pick_points)):
                line = vtk.vtkLineSource()
                line.SetPoint1(self._measurement_pick_points[i - 1])
                line.SetPoint2(self._measurement_pick_points[i])

                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInputConnection(line.GetOutputPort())

                line_actor = vtk.vtkActor()
                line_actor.SetMapper(mapper)
                line_actor.GetProperty().SetColor(0.01, 0.52, 0.78)
                line_actor.GetProperty().SetLineWidth(3.0)

                self.plotter.renderer.AddActor(line_actor)
                self._measurement_line_actors.append(line_actor)

        self.plotter.render()

    def _clear_measurement_visuals(self):
        for actor in self._measurement_line_actors:
            self.plotter.renderer.RemoveActor(actor)
        self._measurement_line_actors = []
        for actor in self._measurement_marker_actors:
            self.plotter.renderer.RemoveActor(actor)
        self._measurement_marker_actors = []

    def _finalize_measurement_from_points(self, record_history=True):
        mode = self.measurement_mode.lower()
        points = [list(p) for p in self._measurement_pick_points]
        if mode == 'distance':
            if len(points) < 2:
                return
            self._update_measurement(points[0], points[1])
        elif mode == 'angle':
            if len(points) < 3:
                return
            angle_value = angle_degrees(points[0], points[1], points[2])
            self.current_measurement = {
                'measurement_type': 'angle',
                'points': points,
                'point1': points[0],
                'point2': points[1],
                'point3': points[2],
                'angle_degrees': angle_value,
                'distance_value_mm': 0.0,
            }
            value_text = f"{angle_value:.2f} deg"
            self.status_bar.showMessage(f"Angle: {value_text}")
            self.measurement_display.update_measurement(points[0], points[2], value_text)
            self._position_measurement_display()
            self.plotter.render()
        else:
            if len(points) < 2:
                return
            total_mm = polyline_mm(points, self.scale_to_mm)
            self.current_measurement = {
                'measurement_type': 'polyline',
                'points': points,
                'point1': points[0],
                'point2': points[-1],
                'distance': polyline_raw(points),
                'distance_value_mm': total_mm,
            }
            value_text = self._format_distance_from_mm(total_mm, decimals=2)
            self.status_bar.showMessage(f"Polyline ({len(points)} pts): {value_text}")
            self.measurement_display.update_measurement(points[0], points[-1], value_text)
            self._position_measurement_display()
            self.plotter.render()

        self.save_measurement_button.setEnabled(True)
        self.finish_measure_button.setEnabled(False)
        self.measurement_display.update_context(self.measurement_mode, "Ready to save")
        if record_history and self.current_measurement:
            self._record_session_measurement(self.current_measurement)

    def _update_measurement(self, point1, point2):
        if not self.is_measuring or point1 is None or point2 is None:
            return
        ensure_3d_libs()
        raw_len = distance_raw(point1, point2)
        value_mm = distance_mm(point1, point2, self.scale_to_mm)

        self.current_measurement = {
            'measurement_type': 'distance',
            'points': [point1, point2],
            'point1': point1,
            'point2': point2,
            'distance': raw_len,
            'distance_mm': value_mm,
            'distance_value_mm': value_mm,
        }

        measurement_text = f"Distance: {self._format_distance_from_mm(value_mm, decimals=2)}"
        self.status_bar.showMessage(measurement_text)

        self.measurement_display.update_measurement(point1, point2, self._format_distance_from_mm(value_mm, decimals=4))
        self._position_measurement_display()

        self.plotter.render()

    def _position_measurement_display(self):
        """MeasurementDisplayWidget is managed directly by left_layout outside the OpenGL surface."""
        self.measurement_display.update()

    def create_thumbnail(self, image_path, thumbnail_size=(100, 100)):
        try:
            if not image_path or not os.path.exists(image_path):
                return None

            cache_key = (image_path, int(thumbnail_size[0]), int(thumbnail_size[1]), os.path.getmtime(image_path))
            cached = self._thumbnail_cache.get(cache_key)
            if cached is not None:
                return cached

            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                return None
            thumb = pixmap.scaled(
                thumbnail_size[0],
                thumbnail_size[1],
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )

            if len(self._thumbnail_cache) > 500:
                self._thumbnail_cache.clear()
            self._thumbnail_cache[cache_key] = thumb
            return thumb
        except Exception:
            return None

    def _invalidate_thumbnail_cache_for_path(self, path):
        if not path:
            return
        keys_to_remove = [k for k in self._thumbnail_cache.keys() if k[0] == path]
        for key in keys_to_remove:
            self._thumbnail_cache.pop(key, None)

    def capture_model_thumbnail(self, save_path=None):
        try:
            if save_path is None:
                save_path = os.path.join(
                    self.archive_mgr.screenshots_dir,
                    f"thumb_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:19]}.png",
                )
            self.plotter.screenshot(save_path, transparent_background=False, window_size=[400, 400])
            return save_path
        except Exception as e:
            print(f"Error capturing thumbnail: {e}")
            return None

    def capture_screenshot(self):
        if not self.mesh_mgr.has_model:
            QMessageBox.warning(self, "No Model", "Please load a 3D model first.")
            return

        description, ok = self._get_archive_description("Screenshot")
        if not ok:
            return

        folder = self.archive_mgr.get_screenshot_path(self.mesh_mgr.insect_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]
        filename = f"screenshot_{timestamp}.png"
        file_path = os.path.join(folder, filename)
        thumb_path = os.path.join(folder, f"thumb_{timestamp}.png")

        try:
            self.plotter.screenshot(file_path)
            thumbnail = self.create_thumbnail(file_path)
            if thumbnail:
                thumbnail.save(thumb_path)

            entry = {
                'session_id': self._current_session_id,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'type': 'Screenshot',
                'description': description,
                'file_path': file_path,
                'thumbnail_path': thumb_path if thumbnail else None,
                'model_name': self.mesh_mgr.model_basename,
            }
            self.archive_mgr.add_screenshot(entry)
            self._refresh_screenshot_list()
            self.status_bar.showMessage(f"Screenshot saved: {filename}")
            self._show_inline_alert(f"Screenshot saved: {filename}", level="success")
        except Exception as e:
            QMessageBox.critical(self, "Capture Error", f"Could not capture screenshot:\n{e}")

    def save_measurement_data(self):
        if not self.is_measuring or not self.current_measurement:
            QMessageBox.warning(self, "No Measurement", "Please create a measurement first.")
            return

        description, ok = self._get_archive_description("Measurement")
        if not ok:
            return

        folder = self.archive_mgr.get_measurement_path(self.mesh_mgr.insect_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]
        filename = f"measurement_{timestamp}.txt"
        file_path = os.path.join(folder, filename)
        thumb_path = os.path.join(folder, f"thumb_{timestamp}.png")

        try:
            thumb_saved = self.capture_model_thumbnail(thumb_path)
            m = self.current_measurement
            m_type = str(m.get('measurement_type', 'distance')).lower()
            points = m.get('points', [])
            if not points and m.get('point1') and m.get('point2'):
                points = [m['point1'], m['point2']]

            distance_raw_value = float(m.get('distance', polyline_raw(points) if len(points) >= 2 else 0.0))
            distance_mm_value = float(m.get('distance_value_mm', m.get('distance_mm', distance_raw_value * self.scale_to_mm)))
            display_value = self._measurement_display_text(m)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("ScanSect Measurement Data\n")
                f.write("========================\n\n")
                f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Model: {self.mesh_mgr.model_basename}\n")
                f.write(f"Description: {description}\n\n")
                f.write("Measurement:\n")
                f.write(f"  Type: {m_type}\n")
                for idx, p in enumerate(points, start=1):
                    f.write(f"  Point {idx}: ({p[0]:.4f}, {p[1]:.4f}, {p[2]:.4f})\n")
                f.write(f"  Scale to mm: {self.scale_to_mm:.6g}\n")
                if m_type == 'angle':
                    f.write(f"  Angle (deg): {float(m.get('angle_degrees', 0.0)):.6f}\n")
                else:
                    f.write(f"  Length (raw model units): {distance_raw_value:.6f}\n")
                    f.write(f"  Length (mm): {distance_mm_value:.6f}\n")
                f.write(f"  Display Value: {display_value}\n")

            entry = {
                'session_id': self._current_session_id,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'type': 'Measurement',
                'measurement_type': m_type,
                'description': description,
                'file_path': file_path,
                'thumbnail_path': thumb_path if thumb_saved else None,
                'model_name': self.mesh_mgr.model_basename,
                'model_path': self.mesh_mgr.current_path,
                'distance': display_value,
                'distance_value_mm': distance_mm_value if m_type != 'angle' else 0.0,
                'distance_raw': distance_raw_value,
                'scale_to_mm': self.scale_to_mm,
                'unit': self.measurement_unit,
                'points': points,
                'point1': points[0] if points else None,
                'point2': points[1] if len(points) > 1 else None,
                'point3': points[2] if len(points) > 2 else None,
                'angle_degrees': float(m.get('angle_degrees', 0.0)) if m_type == 'angle' else None,
            }
            self.archive_mgr.add_measurement(entry)
            self._refresh_measurement_list()
            self.status_bar.showMessage(f"Measurement saved: {filename}")
            self._show_inline_alert(f"Measurement saved: {filename}", level="success")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Could not save measurement data:\n{e}")

    def _get_archive_description(self, item_type):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Save {item_type}")
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(f"Enter a note or label for this {item_type.lower()}:"))
        description_edit = QLineEdit()
        description_edit.setPlaceholderText("e.g., Wing span, dorsal thorax view")
        layout.addWidget(description_edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() == QDialog.Accepted:
            return description_edit.text() or f"{item_type} ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})", True
        return None, False

    def _refresh_measurement_list(self):
        current = self.meas_insect_filter.currentText()
        self.meas_insect_filter.blockSignals(True)
        self.meas_insect_filter.clear()
        self.meas_insect_filter.addItem("All Insects")
        names = set(
            m.get('model_name', 'Unknown')
            for m in self.archive_mgr.measurements
            if m.get('model_name') != 'Unknown'
        )
        for n in sorted(names):
            self.meas_insect_filter.addItem(n)
        idx = self.meas_insect_filter.findText(current)
        if idx >= 0:
            self.meas_insect_filter.setCurrentIndex(idx)
        self.meas_insect_filter.blockSignals(False)

        self._apply_measurement_filters()

    def _apply_measurement_filters(self):
        self.measurement_list.clear()
        insect = self.meas_insect_filter.currentText()
        sort_mode = self.meas_sort_combo.currentText()
        search_text = self.meas_search_edit.text().strip().lower()

        items = list(self.archive_mgr.measurements)

        if insect != "All Insects":
            items = [m for m in items if m.get('model_name') == insect]

        if self.meas_current_model_only_chk.isChecked():
            current_model = self.mesh_mgr.model_basename if self.mesh_mgr.has_model else None
            items = [m for m in items if current_model and m.get('model_name') == current_model]

        if self.meas_current_session_only_chk.isChecked():
            items = [m for m in items if m.get('session_id') == self._current_session_id]

        if sort_mode == "Newest First":
            items = list(reversed(items))
        elif sort_mode == "Oldest First":
            pass
        elif sort_mode.startswith("Distance"):
            reverse = "\u2193" in sort_mode
            items.sort(key=lambda m: self._measurement_entry_mm(m), reverse=reverse)
        elif sort_mode.startswith("Angle"):
            reverse = "\u2193" in sort_mode

            def _angle_sort_value(entry):
                m_type = str(entry.get('measurement_type', 'distance')).lower()
                if m_type != 'angle':
                    return float('-inf') if reverse else float('inf')
                try:
                    return float(entry.get('angle_degrees', 0.0))
                except Exception:
                    return 0.0

            items.sort(key=_angle_sort_value, reverse=reverse)

        if search_text:
            def _meas_matches(entry):
                haystack = " ".join([
                    str(entry.get('description', '')),
                    str(entry.get('model_name', '')),
                    str(entry.get('distance', '')),
                    str(entry.get('measurement_type', '')),
                    str(entry.get('angle_degrees', '')),
                    str(entry.get('timestamp', '')),
                    str(entry.get('session_id', '')),
                ]).lower()
                return search_text in haystack

            items = [m for m in items if _meas_matches(m)]

        for item in items:
            dist = self._measurement_display_text(item)
            desc = item.get('description', 'No description')
            ts = item.get('timestamp', '?')
            model = item.get('model_name', '?')
            sid = item.get('session_id', '')[:6]
            m_type = str(item.get('measurement_type', 'distance')).capitalize()
            display = f"{dist}  ({m_type})\n{desc}\n{model}  |  {ts}  [{sid}]"
            li = QListWidgetItem(display)
            li.setData(Qt.UserRole, item)

            thumb_path = item.get('thumbnail_path')
            if thumb_path and os.path.exists(thumb_path):
                thumb = self.create_thumbnail(thumb_path, (56, 56))
                if thumb:
                    li.setIcon(QIcon(thumb))

            self.measurement_list.addItem(li)

        has_items = self.measurement_list.count() > 0
        self.measurement_list.setVisible(has_items)
        self.measurement_empty_label.setVisible(not has_items)

    def _on_measurement_selection_changed(self):
        has_sel = len(self.measurement_list.selectedItems()) > 0
        self.meas_load_btn.setEnabled(has_sel)
        self.meas_rename_btn.setEnabled(has_sel)
        self.meas_delete_btn.setEnabled(has_sel)

        if has_sel:
            data = self.measurement_list.selectedItems()[0].data(Qt.UserRole)
            data_view = dict(data)
            data_view['distance'] = self._measurement_display_text(data)
            sid = data.get('session_id', '')
            linked = self.archive_mgr.find_linked_screenshots(sid) if sid else []
            self.measurement_detail.show_detail(data_view, linked)
        else:
            self.measurement_detail.show_detail(None)

    def _on_measurement_double_clicked(self, item):
        data = item.data(Qt.UserRole)
        if data and 'file_path' in data:
            fp = data['file_path']
            if os.path.exists(fp):
                QDesktopServices.openUrl(QUrl.fromLocalFile(fp))

    def _apply_measurement_data_to_viewport(self, data, switch_tab=True):
        if not data:
            return False
        points = data.get('points')
        if not points:
            p1 = data.get('point1')
            p2 = data.get('point2')
            p3 = data.get('point3')
            points = [p for p in [p1, p2, p3] if p is not None]
        if len(points) < 2:
            QMessageBox.warning(self, "Incomplete Data", "This measurement doesn't have enough position points.")
            return False
        try:
            if not self.is_measuring:
                self.measure_button.setChecked(True)
                self.toggle_measurement_mode()
            if not self.is_measuring:
                return False

            self._restore_measurement_scale_and_unit(data)
            m_type = str(data.get('measurement_type', 'distance')).capitalize()
            self.measurement_mode = m_type if m_type in ["Distance", "Angle", "Polyline"] else "Distance"
            self.measure_mode_combo.blockSignals(True)
            self.measure_mode_combo.setCurrentText(self.measurement_mode)
            self.measure_mode_combo.blockSignals(False)

            self._measurement_pick_points = [[float(v) for v in p] for p in points]
            self._draw_measurement_visuals()
            self._finalize_measurement_from_points(record_history=False)
            self.save_measurement_button.setEnabled(True)
            self._update_measure_ui_hints()
            desc = data.get('description', 'Loaded')
            dist = self._measurement_display_text(self.current_measurement or data)
            self.status_bar.showMessage(f"Loaded measurement: {desc} ({dist})")
            if switch_tab:
                self.right_panel_tabs.setCurrentIndex(0)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Could not load measurement:\n{e}")
            return False

    def _load_measurement_from_module(self):
        selected = self.measurement_list.selectedItems()
        if not selected:
            return
        data = selected[0].data(Qt.UserRole)
        if not data:
            QMessageBox.warning(self, "Incomplete Data", "This measurement doesn't have position data.")
            return

        points = data.get('points')
        if not points:
            p1 = data.get('point1')
            p2 = data.get('point2')
            p3 = data.get('point3')
            points = [p for p in [p1, p2, p3] if p is not None]

        if len(points) < 2:
            QMessageBox.warning(self, "Incomplete Data", "This measurement doesn't have enough position points.")
            return
        if not self.mesh_mgr.has_model:
            if 'model_path' in data and os.path.exists(data['model_path']):
                reply = QMessageBox.question(
                    self,
                    "Load Model?",
                    f"Load the associated model?\nModel: {data.get('model_name', 'Unknown')}",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply == QMessageBox.Yes:
                    self._pending_measurement_data = data
                    self.load_model(data['model_path'])
                return
            else:
                QMessageBox.warning(self, "No Model", "Please load the associated 3D model first.")
                return
        self._apply_measurement_data_to_viewport(data, switch_tab=True)

    def _rename_measurement(self):
        selected = self.measurement_list.selectedItems()
        if not selected:
            return
        data = selected[0].data(Qt.UserRole)
        new_desc = self._get_rename_input(data)
        if new_desc:
            data['description'] = new_desc
            self.archive_mgr.save_measurements()
            self._refresh_measurement_list()

    def _delete_entry_files(self, data):
        if not data:
            return
        for key in ('file_path', 'thumbnail_path'):
            fp = data.get(key)
            if fp and os.path.exists(fp):
                try:
                    os.remove(fp)
                except Exception:
                    pass
            self._invalidate_thumbnail_cache_for_path(fp)

    def _delete_measurement(self):
        selected = self.measurement_list.selectedItems()
        if not selected:
            return
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete {len(selected)} measurement(s)?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        for item in selected:
            data = item.data(Qt.UserRole)
            self._delete_entry_files(data)
            self.archive_mgr.remove_measurement(data)
        self._refresh_measurement_list()

    def _refresh_screenshot_list(self):
        current = self.ss_insect_filter.currentText()
        self.ss_insect_filter.blockSignals(True)
        self.ss_insect_filter.clear()
        self.ss_insect_filter.addItem("All Insects")
        names = set(
            s.get('model_name', 'Unknown')
            for s in self.archive_mgr.screenshots
            if s.get('model_name') != 'Unknown'
        )
        for n in sorted(names):
            self.ss_insect_filter.addItem(n)
        idx = self.ss_insect_filter.findText(current)
        if idx >= 0:
            self.ss_insect_filter.setCurrentIndex(idx)
        self.ss_insect_filter.blockSignals(False)

        self._apply_screenshot_filters()

    def _apply_screenshot_filters(self):
        self.screenshot_list.clear()
        insect = self.ss_insect_filter.currentText()
        search_text = self.ss_search_edit.text().strip().lower()

        items = list(reversed(self.archive_mgr.screenshots))
        if insect != "All Insects":
            items = [s for s in items if s.get('model_name') == insect]

        if self.ss_current_model_only_chk.isChecked():
            current_model = self.mesh_mgr.model_basename if self.mesh_mgr.has_model else None
            items = [s for s in items if current_model and s.get('model_name') == current_model]

        if self.ss_current_session_only_chk.isChecked():
            items = [s for s in items if s.get('session_id') == self._current_session_id]

        if search_text:
            def _ss_matches(entry):
                haystack = " ".join([
                    str(entry.get('description', '')),
                    str(entry.get('model_name', '')),
                    str(entry.get('timestamp', '')),
                    str(entry.get('session_id', '')),
                    os.path.basename(str(entry.get('file_path', ''))),
                ]).lower()
                return search_text in haystack

            items = [s for s in items if _ss_matches(s)]

        for item in items:
            desc = item.get('description', 'No description')
            ts = item.get('timestamp', '?')
            model = item.get('model_name', '?')
            sid = item.get('session_id', '')[:6]
            display = f"{desc}\n{model}  |  {ts}  [{sid}]"
            li = QListWidgetItem(display)
            li.setData(Qt.UserRole, item)

            thumb_path = item.get('thumbnail_path')
            if thumb_path and os.path.exists(thumb_path):
                thumb = self.create_thumbnail(thumb_path, (88, 88))
                if thumb:
                    li.setIcon(QIcon(thumb))
            else:
                fp = item.get('file_path')
                if fp and os.path.exists(fp) and fp.lower().endswith(('.png', '.jpg', '.jpeg')):
                    thumb = self.create_thumbnail(fp, (88, 88))
                    if thumb:
                        li.setIcon(QIcon(thumb))

            self.screenshot_list.addItem(li)

        has_items = self.screenshot_list.count() > 0
        self.screenshot_list.setVisible(has_items)
        self.screenshot_empty_label.setVisible(not has_items)

    def _on_screenshot_selection_changed(self):
        has_sel = len(self.screenshot_list.selectedItems()) > 0
        self.ss_preview_btn.setEnabled(has_sel)
        self.ss_rename_btn.setEnabled(has_sel)
        self.ss_delete_btn.setEnabled(has_sel)

    def _preview_screenshot(self, item):
        data = item.data(Qt.UserRole)
        if data and 'file_path' in data:
            fp = data['file_path']
            if os.path.exists(fp):
                dlg = ScreenshotPreviewDialog(fp, self)
                dlg.exec()
            else:
                QMessageBox.warning(self, "File Not Found", f"Screenshot not found:\n{fp}")

    def _preview_selected_screenshot(self):
        selected = self.screenshot_list.selectedItems()
        if selected:
            self._preview_screenshot(selected[0])

    def _rename_screenshot(self):
        selected = self.screenshot_list.selectedItems()
        if not selected:
            return
        data = selected[0].data(Qt.UserRole)
        new_desc = self._get_rename_input(data)
        if new_desc:
            data['description'] = new_desc
            self.archive_mgr.save_screenshots()
            self._refresh_screenshot_list()

    def _delete_screenshot(self):
        selected = self.screenshot_list.selectedItems()
        if not selected:
            return
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete {len(selected)} screenshot(s)?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        for item in selected:
            data = item.data(Qt.UserRole)
            self._delete_entry_files(data)
            self.archive_mgr.remove_screenshot(data)
        self._refresh_screenshot_list()

    def _get_rename_input(self, data):
        if not data:
            return None
        current = data.get('description', '')
        dialog = QDialog(self)
        dialog.setWindowTitle("Rename")
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(f"Current: {current}"))
        edit = QLineEdit()
        edit.setText(current)
        edit.selectAll()
        layout.addWidget(edit)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dialog.accept)
        btns.rejected.connect(dialog.reject)
        layout.addWidget(btns)
        if dialog.exec() == QDialog.Accepted:
            new = edit.text().strip()
            if new and new != current:
                return new
        return None

    def _open_folder(self, path):
        if os.path.exists(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        else:
            QMessageBox.warning(self, "Folder Not Found", f"Folder does not exist:\n{path}")

    def _load_recent_models(self):
        return load_json_with_backup(self.recent_models_file, [])

    def _save_recent_models(self):
        try:
            atomic_write_json_with_backup(self.recent_models_file, self.recent_models)
        except Exception as e:
            print(f"Error saving recent models: {e}")

    def _add_to_recent_models(self, file_path):
        if not os.path.exists(file_path):
            return
        entry = {
            'path': file_path,
            'name': os.path.basename(file_path),
            'directory': os.path.dirname(file_path),
            'last_accessed': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'size': os.path.getsize(file_path),
        }
        self.recent_models = [m for m in self.recent_models if m.get('path') != file_path]
        self.recent_models.insert(0, entry)
        self.recent_models = self.recent_models[:20]
        self._save_recent_models()
        self._refresh_recent_models_list()

    def _format_short_directory(self, directory):
        if not directory:
            return ""
        parts = os.path.normpath(directory).replace("\\", "/").split("/")
        if len(parts) <= 3:
            return "/".join(parts)
        return f"{parts[0]}/.../{'/'.join(parts[-2:])}"

    def _refresh_recent_models_list(self):
        self.recent_models_list.clear()
        for model in self.recent_models:
            full_path = model.get('path', '')
            if not os.path.exists(full_path):
                continue
            name = model.get('name', 'Unknown')
            last_accessed = model.get('last_accessed', 'Unknown')
            directory = model.get('directory', '')
            short_dir = self._format_short_directory(directory)
            size = model.get('size', 0)
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            display = f"{name}\n{size_str}  |  {last_accessed}\n{short_dir}"
            li = QListWidgetItem(display)
            li.setToolTip(full_path)
            li.setData(Qt.UserRole, model)
            self.recent_models_list.addItem(li)

    def _on_recent_selection_changed(self):
        has_sel = len(self.recent_models_list.selectedItems()) > 0
        self.load_recent_button.setEnabled(has_sel)
        self.remove_recent_button.setEnabled(has_sel)

    def _load_recent_model(self, item):
        if item is None:
            return
        data = item.data(Qt.UserRole)
        if data and 'path' in data:
            fp = data['path']
            if os.path.exists(fp):
                self.load_model(fp)
            else:
                QMessageBox.warning(self, "File Not Found", f"Model not found:\n{fp}")
                self.recent_models = [m for m in self.recent_models if m.get('path') != fp]
                self._save_recent_models()
                self._refresh_recent_models_list()

    def _remove_recent_model(self):
        for item in self.recent_models_list.selectedItems():
            data = item.data(Qt.UserRole)
            if data in self.recent_models:
                self.recent_models.remove(data)
        self._save_recent_models()
        self._refresh_recent_models_list()

    def _clear_recent_models(self):
        if not self.recent_models:
            return
        reply = QMessageBox.question(
            self,
            "Clear Recent Models",
            "Clear all recent models?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.recent_models = []
            self._save_recent_models()
            self._refresh_recent_models_list()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'loading_overlay') and self.loading_overlay.isVisible():
            self.loading_overlay.setGeometry(self._viewport_container.rect())
        if hasattr(self, 'measurement_display') and self.measurement_display.isVisible():
            self._position_measurement_display()

    def closeEvent(self, event):
        if self._loader_worker and self._loader_worker.isRunning():
            self._loader_worker.quit()
            self._loader_worker.wait(2000)
        self._cleanup_measurement_widgets()
        if hasattr(self, 'plotter') and self.plotter is not None:
            self.plotter.close()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    splash_pix = QPixmap(480, 260)
    splash_pix.fill(QColor("#16181d"))
    painter = QPainter(splash_pix)
    painter.setPen(QColor("#38bdf8"))
    font = QFont("Segoe UI", 26, QFont.Bold)
    painter.setFont(font)
    painter.drawText(splash_pix.rect().adjusted(0, -14, 0, -14), Qt.AlignCenter, "ScanSect")
    painter.setPen(QColor("#94a3b8"))
    font.setPointSize(10)
    font.setBold(False)
    painter.setFont(font)
    painter.drawText(splash_pix.rect().adjusted(0, 48, 0, 0), Qt.AlignCenter, "3D Entomology Specimen & Morphometrics Viewer")
    painter.end()

    splash = QSplashScreen(splash_pix)
    splash.show()
    app.processEvents()

    window = ScanSectGUI()
    window.show()
    splash.finish(window)

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
