import sys
import os 
import pyvista as pv
from pyvistaqt import QtInteractor
import vtk 
import numpy as np  # Added for numerical operations
import json
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
    QSizePolicy,
    QPushButton,
    QButtonGroup,
    QAbstractButton,
    QFrame,
    QMessageBox,
    QListWidget,
    QListWidgetItem,
    QTabWidget,
    QGroupBox,
    QScrollArea,
    QDialog,
    QDialogButtonBox,
    QLineEdit,
    QComboBox
)
from PySide6.QtGui import QAction, QKeySequence, QIcon, QMouseEvent, QPixmap, QPainter
from PySide6.QtCore import Qt, QEvent, QObject, Slot, QByteArray, QSize
from PySide6.QtSvg import QSvgRenderer

# Configure PyVista to work with Qt
pv.set_plot_theme('document')
pv.global_theme.window_size = [1024, 768]
pv.global_theme.font.size = 12
pv.global_theme.font.label_size = 12


# --- SVG Icon Data ---
ICON_COLOR = "#e0e0e0" 

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

class ScanSectUnifiedInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self):
        super().__init__()
        self.current_left_click_mode = "rotate" 
    def set_left_click_mode(self, mode_str):
        self.current_left_click_mode = mode_str.lower()
    def OnLeftButtonDown(self): super().OnLeftButtonDown()
    def OnLeftButtonUp(self): super().OnLeftButtonUp()
    def OnMiddleButtonDown(self): super().OnMiddleButtonDown()
    def OnMiddleButtonUp(self): super().OnMiddleButtonUp()
    def OnRightButtonDown(self): super().OnRightButtonDown()
    def OnRightButtonUp(self): super().OnRightButtonUp()

class ScanSectGUI(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ScanSect - 3D Insect Model Viewer")
        self.setGeometry(100, 100, 1400, 850) 

        # Initialize measurement-related attributes
        self.is_measuring = False
        self.line_widget = None
        self.measurement_text_actor = None
        
        # Initialize archive directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.archive_dir = os.path.join(script_dir, "ScanSect_Archive")
        if not os.path.exists(self.archive_dir):
            os.makedirs(self.archive_dir)
        self.archive_file = os.path.join(self.archive_dir, "archive_metadata.json")
        self.archive_data = self.load_archive_data()
        
        # Initialize recent models
        self.recent_models_file = os.path.join(script_dir, "recent_models.json")
        self.recent_models = self.load_recent_models()

        script_dir = os.path.dirname(os.path.abspath(__file__))
        app_icon_path = os.path.join(script_dir, "ScanSect ICON.png")
        if os.path.exists(app_icon_path):
            self.setWindowIcon(QIcon(app_icon_path))
        else:
            print(f"Warning: Application icon not found at {app_icon_path}")

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10) 
        self.main_layout.setSpacing(10)

        # Initialize plotter with proper settings
        self.plotter = QtInteractor(self.central_widget)
        self.plotter.setObjectName("Viewport3D")
        self.plotter.set_background('white')  # Set background color to white
        self.plotter.enable_trackball_style()  # Enable trackball interaction
        self.plotter.show_axes()  # Show orientation axes
        
        # Create toolbar section with grouped controls
        tool_button_container = QWidget()
        tool_button_container.setObjectName("ToolButtonContainer")
        tool_button_layout = QHBoxLayout(tool_button_container)
        tool_button_layout.setContentsMargins(0,5,0,5) 
        tool_button_layout.setSpacing(10)

        self.interaction_mode_group = QButtonGroup(self)
        self.interaction_mode_group.setExclusive(True) 

        icon_size = QSize(20,20) 

        tool_button_layout.addStretch()
        
        # --- Navigation Tools Group ---
        nav_label = QLabel("Navigation:")
        nav_label.setObjectName("ToolGroupLabel")
        tool_button_layout.addWidget(nav_label) 

        # --- Navigation Tools Group ---
        nav_label = QLabel("Navigation:")
        nav_label.setObjectName("ToolGroupLabel")
        tool_button_layout.addWidget(nav_label)

        self.rotate_button = QPushButton(" Rotate")
        self.rotate_button.setIcon(get_icon_from_svg(SVG_ROTATE_ICON, icon_size))
        self.rotate_button.setCheckable(True)
        self.rotate_button.setChecked(True) 
        tool_button_layout.addWidget(self.rotate_button)
        self.interaction_mode_group.addButton(self.rotate_button)

        self.pan_button = QPushButton(" Pan")
        self.pan_button.setIcon(get_icon_from_svg(SVG_PAN_ICON_ALT, icon_size))
        self.pan_button.setCheckable(True)
        tool_button_layout.addWidget(self.pan_button)
        self.interaction_mode_group.addButton(self.pan_button)

        self.zoom_button = QPushButton(" Zoom")
        self.zoom_button.setIcon(get_icon_from_svg(SVG_ZOOM_ICON, icon_size))
        self.zoom_button.setCheckable(True)
        tool_button_layout.addWidget(self.zoom_button)
        self.interaction_mode_group.addButton(self.zoom_button)
        
        # Add separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.VLine)
        separator1.setFrameShadow(QFrame.Sunken)
        separator1.setObjectName("ToolSeparator")
        tool_button_layout.addWidget(separator1)
        
        # --- Tools Group ---
        tools_label = QLabel("Tools:")
        tools_label.setObjectName("ToolGroupLabel")
        tool_button_layout.addWidget(tools_label)
        
        # Add measurement button
        self.measure_button = QPushButton(" Measure")
        self.measure_button.setIcon(get_icon_from_svg(SVG_MEASURE_ICON, icon_size))
        self.measure_button.setCheckable(True)
        self.measure_button.clicked.connect(self.toggle_measurement_mode)
        tool_button_layout.addWidget(self.measure_button)

        # Add texture button
        self.texture_button = QPushButton(" Load Texture")
        self.texture_button.setIcon(get_icon_from_svg(SVG_TEXTURE_ICON, icon_size))
        self.texture_button.clicked.connect(self.load_texture_dialog)
        self.texture_button.setEnabled(False)
        tool_button_layout.addWidget(self.texture_button)
        
        # Add separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setFrameShadow(QFrame.Sunken)
        separator2.setObjectName("ToolSeparator")
        tool_button_layout.addWidget(separator2)
        
        # --- Output Tools Group ---
        output_label = QLabel("Output:")
        output_label.setObjectName("ToolGroupLabel")
        tool_button_layout.addWidget(output_label)
        
        # Add screenshot button
        self.screenshot_button = QPushButton(" Capture")
        self.screenshot_button.setIcon(get_icon_from_svg(SVG_CAMERA_ICON, icon_size))
        self.screenshot_button.clicked.connect(self.capture_screenshot)
        tool_button_layout.addWidget(self.screenshot_button)
        
        # Add save measurement button
        self.save_measurement_button = QPushButton(" Save Data")
        self.save_measurement_button.setIcon(get_icon_from_svg(SVG_SAVE_ICON, icon_size))
        self.save_measurement_button.clicked.connect(self.save_measurement_data)
        self.save_measurement_button.setEnabled(False)
        tool_button_layout.addWidget(self.save_measurement_button)

        tool_button_layout.addStretch()
        
        left_panel_widget = QWidget()
        left_panel_layout = QVBoxLayout(left_panel_widget)
        left_panel_layout.setContentsMargins(0,0,0,0)
        left_panel_layout.setSpacing(5)
        left_panel_layout.addWidget(self.plotter, stretch=1) 
        left_panel_layout.addWidget(tool_button_container)

        self.main_layout.addWidget(left_panel_widget, stretch=3)

        # Create right panel with tabs for metadata and archive
        self.right_panel_tabs = QTabWidget()
        self.right_panel_tabs.setObjectName("RightPanelTabs")
        
        # Metadata tab
        self.metadata_panel = QTextEdit(self)
        self.metadata_panel.setReadOnly(True)
        self.metadata_panel.setPlaceholderText("Load a model to see its metadata here...")
        self.metadata_panel.setObjectName("MetadataPanel")
        self.right_panel_tabs.addTab(self.metadata_panel, "Model Info")
        
        # Archive tab
        archive_widget = QWidget()
        archive_layout = QVBoxLayout(archive_widget)
        archive_layout.setContentsMargins(5, 5, 5, 5)
        archive_layout.setSpacing(8)
        
        # Archive header with controls
        archive_header = QHBoxLayout()
        archive_title = QLabel("Saved Outputs")
        archive_title.setObjectName("ArchiveTitle")
        archive_header.addWidget(archive_title)
        archive_header.addStretch()
        
        # View Archive button
        self.view_archive_button = QPushButton("Open Archive Folder")
        self.view_archive_button.setIcon(get_icon_from_svg(SVG_ARCHIVE_ICON, QSize(16, 16)))
        self.view_archive_button.clicked.connect(self.open_archive_folder)
        archive_header.addWidget(self.view_archive_button)
        
        archive_layout.addLayout(archive_header)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        filter_label = QLabel("Filter:")
        filter_layout.addWidget(filter_label)
        
        self.archive_type_filter = QComboBox()
        self.archive_type_filter.addItems(["All Types", "Screenshots", "Measurements"])
        self.archive_type_filter.currentTextChanged.connect(self.apply_archive_filters)
        filter_layout.addWidget(self.archive_type_filter)
        
        self.archive_insect_filter = QComboBox()
        self.archive_insect_filter.addItem("All Insects")
        self.archive_insect_filter.currentTextChanged.connect(self.apply_archive_filters)
        filter_layout.addWidget(self.archive_insect_filter)
        
        archive_layout.addLayout(filter_layout)
        
        # Archive list with icon mode for thumbnails
        self.archive_list = QListWidget()
        self.archive_list.setObjectName("ArchiveList")
        self.archive_list.setIconSize(QSize(80, 80))  # Set icon size for thumbnails
        self.archive_list.setSpacing(4)  # Add spacing between items
        self.archive_list.itemDoubleClicked.connect(self.open_archive_item)
        archive_layout.addWidget(self.archive_list)
        
        # Archive buttons - Row 1
        archive_buttons_row1 = QHBoxLayout()
        
        self.load_measurement_button = QPushButton("Load Measurement")
        self.load_measurement_button.setIcon(get_icon_from_svg(SVG_MEASURE_ICON, QSize(16, 16)))
        self.load_measurement_button.clicked.connect(self.load_measurement_from_archive)
        self.load_measurement_button.setEnabled(False)
        archive_buttons_row1.addWidget(self.load_measurement_button)
        
        self.rename_archive_button = QPushButton("Rename")
        self.rename_archive_button.clicked.connect(self.rename_archive_item)
        self.rename_archive_button.setEnabled(False)
        archive_buttons_row1.addWidget(self.rename_archive_button)
        
        archive_layout.addLayout(archive_buttons_row1)
        
        # Archive buttons - Row 2
        archive_buttons_row2 = QHBoxLayout()
        
        self.refresh_archive_button = QPushButton("Refresh")
        self.refresh_archive_button.clicked.connect(self.refresh_archive_list)
        archive_buttons_row2.addWidget(self.refresh_archive_button)
        
        self.delete_archive_button = QPushButton("Delete Selected")
        self.delete_archive_button.clicked.connect(self.delete_archive_item)
        self.delete_archive_button.setEnabled(False)
        archive_buttons_row2.addWidget(self.delete_archive_button)
        
        archive_layout.addLayout(archive_buttons_row2)
        
        self.right_panel_tabs.addTab(archive_widget, "Archive")
        
        # Recent Models tab
        recent_widget = QWidget()
        recent_layout = QVBoxLayout(recent_widget)
        recent_layout.setContentsMargins(5, 5, 5, 5)
        recent_layout.setSpacing(8)
        
        # Recent models header
        recent_header = QHBoxLayout()
        recent_title = QLabel("Recent Models")
        recent_title.setObjectName("ArchiveTitle")
        recent_header.addWidget(recent_title)
        recent_header.addStretch()
        
        # Clear recent button
        self.clear_recent_button = QPushButton("Clear All")
        self.clear_recent_button.clicked.connect(self.clear_recent_models)
        recent_header.addWidget(self.clear_recent_button)
        
        recent_layout.addLayout(recent_header)
        
        # Recent models list
        self.recent_models_list = QListWidget()
        self.recent_models_list.setObjectName("ArchiveList")
        self.recent_models_list.itemDoubleClicked.connect(self.load_recent_model)
        recent_layout.addWidget(self.recent_models_list)
        
        # Recent models buttons
        recent_buttons = QHBoxLayout()
        self.load_recent_button = QPushButton("Load Selected")
        self.load_recent_button.clicked.connect(lambda: self.load_recent_model(self.recent_models_list.currentItem()))
        self.load_recent_button.setEnabled(False)
        recent_buttons.addWidget(self.load_recent_button)
        
        self.remove_recent_button = QPushButton("Remove Selected")
        self.remove_recent_button.clicked.connect(self.remove_recent_model)
        self.remove_recent_button.setEnabled(False)
        recent_buttons.addWidget(self.remove_recent_button)
        
        recent_layout.addLayout(recent_buttons)
        
        self.right_panel_tabs.addTab(recent_widget, "Recent Models")
        
        self.main_layout.addWidget(self.right_panel_tabs, stretch=1)
        
        # Connect archive list selection change
        self.archive_list.itemSelectionChanged.connect(self.on_archive_selection_changed)
        
        # Connect recent models list selection change
        self.recent_models_list.itemSelectionChanged.connect(self.on_recent_selection_changed)
        
        # Initial refresh
        self.refresh_archive_list()
        self.refresh_recent_models_list()

        self.plotter.add_axes()
        self.plotter.background_color = 'white' 

        self.custom_interactor_style = ScanSectUnifiedInteractorStyle()
        if hasattr(self.plotter, 'interactor') and self.plotter.interactor is not None:
            self.plotter.interactor.SetInteractorStyle(self.custom_interactor_style)
        
        self.plotter.installEventFilter(self)
        self._active_remapped_button = Qt.NoButton 

        self.custom_interactor_style.set_left_click_mode("rotate") 
        self.interaction_mode_group.buttonClicked.connect(self._on_interaction_mode_changed)

        self._create_menus()

        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. Left-Click: Rotate. Open a 3D model to begin.")

        self.current_model_path = None
        self.current_model_actor = None
        self.current_mesh_object = None 
        self.original_mesh_object = None 
        
        self._apply_stylesheet()

    def _apply_stylesheet(self):
        stylesheet = """
            QMainWindow { background-color: #1e1e1e; }
            QWidget { font-family: 'Segoe UI', Arial, sans-serif; font-size: 10pt; color: #e0e0e0; }
            QTextEdit#MetadataPanel { background-color: #2c2c2c; color: #d0d0d0; border: 1px solid #444444; border-radius: 4px; padding: 8px; font-size: 9pt; }
            QPushButton { background-color: #333333; color: #e0e0e0; border: 1px solid #555555; border-radius: 4px; padding: 6px 12px; min-height: 22px; icon-size: 16px; }
            QPushButton:hover { background-color: #444444; border-color: #666666; }
            QPushButton:pressed { background-color: #222222; }
            QPushButton:checked { background-color: #007acc; color: #ffffff; border: 1px solid #005c99; font-weight: bold; }
            QPushButton:disabled { background-color: #2a2a2a; color: #777777; border-color: #444444;}
            QStatusBar { font-size: 9pt; color: #c0c0c0; }
            QMenuBar { background-color: #2b2b2b; color: #e0e0e0; }
            QMenuBar::item { background-color: transparent; padding: 4px 8px; }
            QMenuBar::item:selected { background-color: #007acc; color: #ffffff; }
            QMenu { background-color: #333333; color: #e0e0e0; border: 1px solid #555555; }
            QMenu::item { padding: 4px 20px 4px 20px; }
            QMenu::item:selected { background-color: #007acc; color: #ffffff; }
            QMenu::separator { height: 1px; background: #555555; margin-left: 5px; margin-right: 5px; }
            QLabel#ToolGroupLabel { color: #888888; font-size: 9pt; font-weight: bold; margin: 0px 5px; }
            QFrame#ToolSeparator { color: #555555; }
            QTabWidget#RightPanelTabs { background-color: #1e1e1e; border: none; }
            QTabWidget::pane { border: 1px solid #444444; background-color: #2c2c2c; border-radius: 4px; }
            QTabBar::tab { background-color: #2c2c2c; color: #a0a0a0; border: 1px solid #444444; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; padding: 6px 12px; margin-right: 2px; }
            QTabBar::tab:selected { background-color: #007acc; color: #ffffff; font-weight: bold; }
            QTabBar::tab:hover:!selected { background-color: #3c3c3c; }
            QListWidget#ArchiveList { background-color: #252525; color: #d0d0d0; border: 1px solid #444444; border-radius: 4px; padding: 4px; font-size: 9pt; }
            QListWidget#ArchiveList::item { padding: 8px; border-bottom: 1px solid #333333; }
            QListWidget#ArchiveList::item:selected { background-color: #007acc; color: #ffffff; }
            QListWidget#ArchiveList::item:hover { background-color: #3c3c3c; }
            QLabel#ArchiveTitle { font-size: 11pt; font-weight: bold; color: #e0e0e0; }
        """
        self.setStyleSheet(stylesheet)

    def eventFilter(self, obj, event):
        if obj == self.plotter:
            if not isinstance(event, QMouseEvent):
                return super().eventFilter(obj, event)
            current_mode = self.custom_interactor_style.current_left_click_mode
            if event.type() == QEvent.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    target_button = Qt.NoButton
                    if current_mode == "pan": target_button = Qt.MiddleButton
                    elif current_mode == "zoom": target_button = Qt.RightButton
                    if target_button != Qt.NoButton:
                        self._active_remapped_button = target_button
                        # Use position() for local coordinates, globalPosition() for global
                        remapped_event = QMouseEvent(event.type(), event.position(), event.globalPosition(), 
                                                    target_button, event.buttons() | target_button, event.modifiers())
                        QApplication.postEvent(obj, remapped_event)
                        return True 
            elif event.type() == QEvent.MouseMove:
                if event.buttons() & Qt.LeftButton and self._active_remapped_button != Qt.NoButton:
                    remapped_buttons_state = (event.buttons() & ~Qt.LeftButton) | self._active_remapped_button
                    remapped_event = QMouseEvent(event.type(), event.position(), event.globalPosition(),
                                                self._active_remapped_button, remapped_buttons_state, event.modifiers())
                    QApplication.postEvent(obj, remapped_event)
                    return True 
            elif event.type() == QEvent.MouseButtonRelease:
                if event.button() == Qt.LeftButton and self._active_remapped_button != Qt.NoButton:
                    target_button_for_release = self._active_remapped_button
                    self._active_remapped_button = Qt.NoButton 
                    remapped_buttons_state = event.buttons() & ~Qt.LeftButton 
                    remapped_event = QMouseEvent(event.type(), event.position(), event.globalPosition(),
                                                target_button_for_release, remapped_buttons_state, event.modifiers())
                    QApplication.postEvent(obj, remapped_event)
                    return True 
                elif self._active_remapped_button != Qt.NoButton and event.button() == self._active_remapped_button: # Handle case where remapped button is released directly
                    self._active_remapped_button = Qt.NoButton
        return super().eventFilter(obj, event)

    def _create_menus(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        open_icon = get_icon_from_svg(SVG_OPEN_FILE_ICON, QSize(16,16))
        open_action = QAction(open_icon, "&Open Model/Texture...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_model_dialog)
        file_menu.addAction(open_action)
        file_menu.addSeparator()
        exit_action = QAction("&Exit", self) 
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    @Slot(QAbstractButton) 
    def _on_interaction_mode_changed(self, button_clicked):
        mode_string = "rotate" 
        if button_clicked == self.rotate_button: mode_string = "rotate"
        elif button_clicked == self.pan_button: mode_string = "pan"
        elif button_clicked == self.zoom_button: mode_string = "zoom"
            
        self.custom_interactor_style.set_left_click_mode(mode_string) 
        # Disable measurement mode when switching to other modes
        if hasattr(self, 'ruler_widget'):
            self.ruler_widget.SetEnabled(False)
        self.status_bar.showMessage(f"Left-Click Mode: {mode_string.capitalize()}")
        self.plotter.setFocus()

    @Slot()
    def open_model_dialog(self):
        file_filter = "3D Models (*.ply *.stl *.obj *.vtk *.vtp *.vtu);;Textures (*.png *.jpg *.jpeg *.bmp *.tiff);;All Files (*)"
        # Get the directory of the current model if one is loaded, otherwise use home directory
        start_dir = os.path.dirname(self.current_model_path) if self.current_model_path else os.path.expanduser("~")
        file_path, _ = QFileDialog.getOpenFileName(self, "Open 3D Model or Texture", start_dir, file_filter)
        if file_path:
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                self.apply_texture_to_current_model(file_path)
            else:
                self.load_model(file_path)
    
    def apply_texture_to_current_model(self, texture_path):
        if self.current_mesh_object is None:
            QMessageBox.warning(self, "No Model Loaded", "Please load a 3D model before applying a texture.")
            return

        self.status_bar.showMessage(f"Applying texture: {texture_path}...")
        QApplication.processEvents()
        try:
            # Load the texture
            texture = pv.read_texture(texture_path)
            print(f"Successfully loaded texture: {texture}")
            
            # Check for UV coordinates
            has_uvs = hasattr(self.current_mesh_object, 'active_texture_coordinates') and self.current_mesh_object.active_texture_coordinates is not None
            
            if not has_uvs:
                # Generate basic UV mapping if none exists
                reply = QMessageBox.question(
                    self, 
                    "No UV Coordinates", 
                    "This model lacks UV coordinates. Would you like to generate basic UV mapping?\n\n"
                    "Note: Results may vary depending on model geometry.",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    try:
                        # Generate texture coordinates using cylindrical mapping
                        self.current_mesh_object.texture_map_to_plane(inplace=True)
                        print("Generated UV coordinates using planar mapping")
                    except Exception as uv_error:
                        print(f"Could not generate UVs: {uv_error}")
                        QMessageBox.warning(
                            self, 
                            "UV Generation Failed", 
                            f"Could not generate UV coordinates:\n{uv_error}\n\n"
                            "The texture will be applied but may not display correctly."
                        )
                else:
                    QMessageBox.warning(
                        self, 
                        "Missing UV Coordinates", 
                        "Texture will be applied but may not display correctly without UV coordinates."
                    )
            
            # Remove existing actor if present
            if self.current_model_actor:
                self.plotter.remove_actor(self.current_model_actor)
            
            # Add mesh with texture - use the texture parameter correctly
            self.current_model_actor = self.plotter.add_mesh(
                self.current_mesh_object,
                texture=texture,
                smooth_shading=True,
                show_edges=False,
                lighting=True,
                color='white'  # Ensure white base color to show texture properly
            )
            
            # Store texture reference on the mesh for later use
            if not hasattr(self.current_mesh_object, 'textures'):
                self.current_mesh_object.textures = {}
            self.current_mesh_object.textures['diffuse'] = texture
            
            # Force a complete render update
            self.plotter.render()
            self.plotter.reset_camera()
            self.plotter.setFocus()
            
            self.status_bar.showMessage(f"Texture '{os.path.basename(texture_path)}' applied successfully!")
            self.display_metadata(self.current_mesh_object, self.current_model_path, texture_applied_manually=True)

        except Exception as e:
            self.status_bar.showMessage(f"Error applying texture: {e}")
            QMessageBox.critical(self, "Texture Error", f"Could not apply texture:\n{e}")
            print(f"Error applying texture: {e}")
    
    def create_thumbnail(self, image_path, thumbnail_size=(100, 100)):
        """
        Create a thumbnail from an image file.
        Returns the thumbnail QPixmap or None if failed.
        """
        try:
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                return None
            # Scale to thumbnail size maintaining aspect ratio
            thumbnail = pixmap.scaled(thumbnail_size[0], thumbnail_size[1], 
                                     Qt.KeepAspectRatio, Qt.SmoothTransformation)
            return thumbnail
        except Exception as e:
            print(f"Error creating thumbnail: {e}")
            return None
    
    def capture_model_thumbnail(self, save_path=None):
        """
        Capture current 3D view as a thumbnail.
        Returns the path to the saved thumbnail.
        """
        try:
            if save_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = os.path.join(self.archive_dir, f"thumb_{timestamp}.png")
            
            # Capture at higher resolution for better quality
            self.plotter.screenshot(save_path, transparent_background=False, 
                                   window_size=[400, 400])
            return save_path
        except Exception as e:
            print(f"Error capturing thumbnail: {e}")
            return None

    def get_organized_archive_path(self, archive_type):
        """
        Get the organized folder path for saving archive items.
        Creates folder structure: ScanSect_Archive/{Screenshots|Measurements}/{InsectName}/
        
        Args:
            archive_type: Either "Screenshots" or "Measurements"
        
        Returns:
            Full path to the organized folder
        """
        # Get insect name from current model
        if self.current_model_path:
            # Extract just the filename without path and extension
            model_filename = os.path.basename(self.current_model_path)
            insect_name = os.path.splitext(model_filename)[0]
            # Clean the name (remove invalid characters for folder names)
            insect_name = "".join(c for c in insect_name if c.isalnum() or c in (' ', '-', '_')).strip()
        else:
            insect_name = "Unknown"
        
        # Create organized path: ScanSect_Archive/Screenshots/InsectName or ScanSect_Archive/Measurements/InsectName
        organized_path = os.path.join(self.archive_dir, archive_type, insect_name)
        
        # Create the directory if it doesn't exist
        if not os.path.exists(organized_path):
            os.makedirs(organized_path)
        
        return organized_path

    def find_texture_file(self, obj_file_path, mtl_texture_path=None):
        """
        Intelligently search for texture files in multiple locations.
        Returns the path to the texture file if found, None otherwise.
        """
        obj_dir = os.path.dirname(obj_file_path)
        base_name = os.path.splitext(os.path.basename(obj_file_path))[0]
        
        # List of possible texture locations to check
        search_paths = []
        
        # 1. If MTL specifies a texture, try to use it
        if mtl_texture_path:
            # Try the exact path from MTL
            search_paths.append(mtl_texture_path)
            # Try just the filename from MTL in the OBJ directory
            mtl_filename = os.path.basename(mtl_texture_path)
            search_paths.append(os.path.join(obj_dir, mtl_filename))
        
        # 2. Try common naming patterns in the same directory as OBJ
        common_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']
        common_suffixes = ['', '_diffuse', '_u1_v1_diffuse', '_texture', '_color', '_basecolor']
        
        for suffix in common_suffixes:
            for ext in common_extensions:
                search_paths.append(os.path.join(obj_dir, f"{base_name}{suffix}{ext}"))
        
        # 3. Search in subdirectories (textures, maps, etc.)
        texture_folders = ['textures', 'Textures', 'maps', 'Maps', 'images', 'Images']
        for folder in texture_folders:
            folder_path = os.path.join(obj_dir, folder)
            if os.path.exists(folder_path):
                for suffix in common_suffixes:
                    for ext in common_extensions:
                        search_paths.append(os.path.join(folder_path, f"{base_name}{suffix}{ext}"))
        
        # 4. Search parent directory
        parent_dir = os.path.dirname(obj_dir)
        if parent_dir and parent_dir != obj_dir:
            for suffix in common_suffixes:
                for ext in common_extensions:
                    search_paths.append(os.path.join(parent_dir, f"{base_name}{suffix}{ext}"))
        
        # Check each path
        for path in search_paths:
            if os.path.exists(path):
                print(f"✓ Found texture: {path}")
                return path
        
        print(f"✗ No texture file found after checking {len(search_paths)} locations")
        return None

    def parse_mtl_file(self, obj_file_path):
        """
        Parse MTL file to extract texture path.
        Returns the texture path specified in map_Kd, or None.
        """
        mtl_path = obj_file_path.replace('.obj', '.mtl')
        if not os.path.exists(mtl_path):
            print(f"No MTL file found at: {mtl_path}")
            return None
        
        try:
            with open(mtl_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('map_Kd'):
                        # Extract texture path from "map_Kd <path>"
                        texture_path = line.split(None, 1)[1].strip()
                        print(f"MTL specifies texture: {texture_path}")
                        return texture_path
        except Exception as e:
            print(f"Error parsing MTL file: {e}")
        
        return None

    def load_model(self, file_path):
        self.status_bar.showMessage(f"Loading model: {file_path}...")
        QApplication.processEvents() 
        try:
            mesh = None
            print(f"\n{'='*60}")
            print(f"Attempting to read model: {file_path}")
            print(f"{'='*60}")
            
            # First load the mesh without any texture handling
            mesh = pv.read(file_path)
            
            if mesh is None or mesh.n_points == 0:
                QMessageBox.critical(self, "Model Load Error", f"Loaded mesh is empty or invalid from file:\n{file_path}")
                self.status_bar.showMessage(f"Loaded mesh from {os.path.basename(file_path)} is empty or invalid.")
                print(f"ScanSectGUI: Loaded mesh from '{file_path}' is empty or invalid.")
                self.texture_button.setEnabled(False)  # Disable texture button
                self.current_mesh_object = None
                self.original_mesh_object = None
                return
                
            # Enable texture button when model is loaded successfully
            self.texture_button.setEnabled(True)

            # Enhanced texture handling for OBJ files
            if file_path.lower().endswith('.obj'):
                print(f"\n--- Searching for Texture ---")
                try:
                    # Parse MTL file to get texture path
                    mtl_texture_path = self.parse_mtl_file(file_path)
                    
                    # Intelligently search for the texture file
                    texture_path = self.find_texture_file(file_path, mtl_texture_path)
                    
                    if texture_path:
                        try:
                            print(f"Loading texture: {texture_path}")
                            texture = pv.read_texture(texture_path)
                            if not hasattr(mesh, 'textures'):
                                mesh.textures = {}
                            mesh.textures['diffuse'] = texture
                            print(f"✓ Texture loaded successfully!")
                        except Exception as tex_error:
                            print(f"✗ Error loading texture file: {tex_error}")
                            QMessageBox.warning(
                                self, 
                                "Texture Load Error", 
                                f"Found texture file but couldn't load it:\n{texture_path}\n\nError: {tex_error}"
                            )
                    else:
                        print(f"✗ No texture file found")
                        QMessageBox.information(
                            self, 
                            "No Texture Found", 
                            f"Could not find a texture file for this model.\n\n"
                            f"Searched in:\n"
                            f"• Same folder as model\n"
                            f"• Parent folder\n"
                            f"• Common texture subfolders\n"
                            f"• Path from MTL file\n\n"
                            f"You can load a texture manually using:\n"
                            f"'Load Texture' button or File > Open Model/Texture"
                        )
                except Exception as tex_error:
                    print(f"✗ Error during texture search: {tex_error}")

            print(f"\n--- Post-Load Mesh Inspection ---")
            if hasattr(mesh, 'textures'):
                print(f"  mesh.textures exists. Type: {type(mesh.textures)}")
                if isinstance(mesh.textures, dict):
                    print(f"  mesh.textures is a dict. Keys: {list(mesh.textures.keys())}")
                    for key, tex_obj in mesh.textures.items():
                        print(f"    Texture key '{key}': {tex_obj} (Type: {type(tex_obj)})")
                else:
                    print(f"  mesh.textures is NOT a dict.")
            else:
                print(f"  mesh.textures attribute does NOT exist.")

            if hasattr(mesh, 'active_texture_coordinates'):
                print(f"  mesh.active_texture_coordinates exists. Value: {mesh.active_texture_coordinates}")
                if mesh.active_texture_coordinates is not None:
                    print(f"  Shape of active_texture_coordinates: {mesh.active_texture_coordinates.shape}")
            else:
                print(f"  mesh.active_texture_coordinates attribute does NOT exist.")
            print(f"--- End Post-Load Mesh Inspection ---")

            self.original_mesh_object = mesh.copy() 
            self.current_mesh_object = mesh   

            if self.current_model_actor:
                self.plotter.remove_actor(self.current_model_actor)
            
            texture_loaded_with_model = False
            has_uvs = hasattr(self.current_mesh_object, 'active_texture_coordinates') and self.current_mesh_object.active_texture_coordinates is not None
            
            # Check if textures were loaded with the model
            if hasattr(self.current_mesh_object, 'textures') and isinstance(self.current_mesh_object.textures, dict) and self.current_mesh_object.textures:
                if any(tex is not None for tex in self.current_mesh_object.textures.values()):
                    texture_loaded_with_model = True
                    print(f"CONFIRMED: Textures loaded with model.")

            # Add mesh with explicit texture settings
            if texture_loaded_with_model:
                # Get the first available texture
                texture_to_use = next(iter(self.current_mesh_object.textures.values()))
                self.current_model_actor = self.plotter.add_mesh(
                    self.current_mesh_object,
                    texture=texture_to_use,
                    smooth_shading=True,
                    show_edges=False,
                    lighting=True,
                    color='white'
                )
                print("Model rendered with texture")
            else:
                # Render without texture
                self.current_model_actor = self.plotter.add_mesh(
                    self.current_mesh_object,
                    smooth_shading=True,
                    show_edges=False,
                    color='white'
                )
                print("Model rendered without texture")
            
            # Force a render update
            self.plotter.render()
            self.plotter.reset_camera()
            self.plotter.setFocus() 
            self.current_model_path = file_path
            
            # Add to recent models
            self.add_to_recent_models(file_path)
            
            current_left_click_mode = self.custom_interactor_style.current_left_click_mode.capitalize()
            self.status_bar.showMessage(f"Loaded: {os.path.basename(file_path)}. Polys: {self.current_mesh_object.n_cells:,}. Mode: {current_left_click_mode}")
            self.display_metadata(self.current_mesh_object, self.current_model_path, texture_automatically_loaded=texture_loaded_with_model)

        except Exception as e:
            self.status_bar.showMessage(f"Error processing model: {e}")
            QMessageBox.critical(self, "Model Processing Error", f"Could not process model:\n{e}")
            print(f"ScanSectGUI: Error processing model '{file_path}': {e}")
            self.current_mesh_object = None
            self.original_mesh_object = None


    def display_metadata(self, mesh_to_display, file_path, texture_automatically_loaded=False, texture_applied_manually=False):
        if mesh_to_display is None:
            self.metadata_panel.setText("No model loaded.")
            return

        metadata_text = f"--- Model Information ---\n"
        metadata_text += f"File Path: {os.path.basename(file_path)}\n"
        metadata_text += f"Number of Points: {mesh_to_display.n_points:,}\n"
        metadata_text += f"Number of Polygons (Cells): {mesh_to_display.n_cells:,}\n" 
        
        bounds = mesh_to_display.bounds
        metadata_text += f"Bounds (X, Y, Z min/max):\n"
        metadata_text += f"  X: {bounds[0]:.2f} to {bounds[1]:.2f}\n"
        metadata_text += f"  Y: {bounds[2]:.2f} to {bounds[3]:.2f}\n"
        metadata_text += f"  Z: {bounds[4]:.2f} to {bounds[5]:.2f}\n"

        has_uvs = hasattr(mesh_to_display, 'active_texture_coordinates') and mesh_to_display.active_texture_coordinates is not None
        
        textures_present_in_mesh_dict = False
        if hasattr(mesh_to_display, 'textures') and isinstance(mesh_to_display.textures, dict) and mesh_to_display.textures:
            if any(tex is not None for tex in mesh_to_display.textures.values()):
                textures_present_in_mesh_dict = True

        if texture_applied_manually:
            metadata_text += f"Texture Status: Manually Applied\n"
        elif texture_automatically_loaded:
            metadata_text += f"Texture Status: Automatically Loaded (e.g., via MTL)\n"
        elif textures_present_in_mesh_dict:
            metadata_text += f"Texture Status: Present in mesh data (likely auto-loaded)\n"
        else:
            metadata_text += f"Texture Status: None detected or applied\n"

        if has_uvs:
            metadata_text += f"  Texture Coordinates (UVs): Present\n"
        else:
            metadata_text += f"  Texture Coordinates (UVs): MISSING (Textures cannot be displayed correctly)\n"
        
        if not hasattr(mesh_to_display, 'textures'):
            metadata_text += f"  (Internal: Mesh object missing 'textures' attribute entirely)\n"
        elif not isinstance(mesh_to_display.textures, dict):
            metadata_text += f"  (Internal: Mesh 'textures' attribute is not a dictionary)\n"


        metadata_text += f"\n--- ScanSect Specific Metadata (Placeholder) ---\n" 
        self.metadata_panel.setText(metadata_text)
        
    def toggle_measurement_mode(self):
        self.is_measuring = self.measure_button.isChecked()
        
        if self.is_measuring:
            if not hasattr(self.plotter, 'iren') or self.plotter.iren is None:
                QMessageBox.warning(self, "Error", "3D viewer not properly initialized. Please try again.")
                self.measure_button.setChecked(False)
                return
            
            try:
                # Create line widget for measurement
                self.line_widget = vtk.vtkLineWidget()
                # Set the interactor before any other operations
                vtk_interactor = self.plotter.iren.interactor
                self.line_widget.SetInteractor(vtk_interactor)
                
                # Place the widget in the scene using current mesh bounds
                if self.current_mesh_object is not None:
                    bounds = self.current_mesh_object.bounds
                else:
                    bounds = [-1, 1, -1, 1, -1, 1]  # Default bounds if no model loaded
                self.line_widget.PlaceWidget(bounds)
                
                # Add callback before enabling
                self.line_widget.AddObserver("InteractionEvent", self.update_measurement)
                
                # Create text actor for measurement display
                self.measurement_text_actor = vtk.vtkTextActor()
                self.measurement_text_actor.GetTextProperty().SetFontSize(14)
                self.measurement_text_actor.GetTextProperty().SetColor(1, 1, 1)  # White text
                self.measurement_text_actor.SetPosition(10, 10)
                self.plotter.renderer.AddActor(self.measurement_text_actor)
                
                # Enable the widget last
                self.line_widget.SetEnabled(1)
                
                # Initial measurement update
                self.update_measurement(None, None)
                
                # Enable save measurement button
                self.save_measurement_button.setEnabled(True)
                
                self.status_bar.showMessage("Click and drag the line endpoints to measure distance")
                
            except Exception as e:
                print(f"Error initializing measurement widget: {e}")
                self.measure_button.setChecked(False)
                self.is_measuring = False
                if hasattr(self, 'line_widget'):
                    self.line_widget.SetEnabled(0)
                    self.line_widget = None
                if hasattr(self, 'measurement_text_actor') and self.measurement_text_actor:
                    self.plotter.renderer.RemoveActor(self.measurement_text_actor)
                    self.measurement_text_actor = None
                QMessageBox.warning(self, "Error", f"Could not initialize measurement tool: {e}")
                return
                
        else:
            # Clean up measurement widgets
            if hasattr(self, 'line_widget') and self.line_widget:
                self.line_widget.SetEnabled(0)
                self.line_widget = None
            if hasattr(self, 'measurement_text_actor') and self.measurement_text_actor:
                self.plotter.renderer.RemoveActor(self.measurement_text_actor)
                self.measurement_text_actor = None
            # Disable save measurement button
            self.save_measurement_button.setEnabled(False)
            self.status_bar.clearMessage()
        
        self.plotter.render()

    def update_measurement(self, obj, event):
        if not self.is_measuring:
            return
            
        # Get line widget endpoints
        point1 = [0, 0, 0]
        point2 = [0, 0, 0]
        self.line_widget.GetPoint1(point1)
        self.line_widget.GetPoint2(point2)
        
        # Calculate distance in millimeters
        distance = np.sqrt(sum((p2 - p1) ** 2 for p1, p2 in zip(point1, point2)))
        
        # Store current measurement
        self.current_measurement = {
            'point1': point1,
            'point2': point2,
            'distance': distance
        }
        
        # Update measurement display
        measurement_text = f"Distance: {distance:.2f} mm"
        self.measurement_text_actor.SetInput(measurement_text)
        self.status_bar.showMessage(measurement_text)
        self.plotter.render()
    
    def load_archive_data(self):
        """Load archive metadata from JSON file"""
        if os.path.exists(self.archive_file):
            try:
                with open(self.archive_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading archive data: {e}")
                return []
        return []
    
    def save_archive_data(self):
        """Save archive metadata to JSON file"""
        try:
            with open(self.archive_file, 'w') as f:
                json.dump(self.archive_data, f, indent=2)
        except Exception as e:
            print(f"Error saving archive data: {e}")
            QMessageBox.warning(self, "Archive Error", f"Could not save archive data: {e}")
    
    def refresh_archive_list(self):
        """Refresh the archive list display with thumbnails and organized structure"""
        self.archive_list.clear()
        self.archive_data = self.load_archive_data()
        
        # Update insect filter dropdown
        current_insect_filter = self.archive_insect_filter.currentText()
        self.archive_insect_filter.clear()
        self.archive_insect_filter.addItem("All Insects")
        
        # Collect unique insect names
        insect_names = set()
        for item in self.archive_data:
            model_name = item.get('model_name', 'Unknown')
            if model_name != 'Unknown':
                insect_names.add(model_name)
        
        # Add insects to filter dropdown
        for insect in sorted(insect_names):
            self.archive_insect_filter.addItem(insect)
        
        # Restore previous filter if it still exists
        index = self.archive_insect_filter.findText(current_insect_filter)
        if index >= 0:
            self.archive_insect_filter.setCurrentIndex(index)
        
        # Apply filters and display
        self.apply_archive_filters()
    
    def apply_archive_filters(self):
        """Apply type and insect filters to the archive list"""
        self.archive_list.clear()
        
        type_filter = self.archive_type_filter.currentText()
        insect_filter = self.archive_insect_filter.currentText()
        
        for item in reversed(self.archive_data):  # Show newest first
            # Apply type filter
            item_type = item.get('type', 'Unknown')
            if type_filter != "All Types" and item_type != type_filter.rstrip('s'):  # Remove 's' from Screenshots/Measurements
                continue
            
            # Apply insect filter
            model_name = item.get('model_name', 'Unknown')
            if insect_filter != "All Insects" and model_name != insect_filter:
                continue
            
            # Item passed filters, add to list
            timestamp = item.get('timestamp', 'Unknown')
            description = item.get('description', 'No description')
            
            # Enhanced display with model name for better organization
            display_text = f"[{timestamp}] {model_name} - {item_type}: {description}"
            list_item = QListWidgetItem(display_text)
            list_item.setData(Qt.UserRole, item)
            
            # Add thumbnail if available
            thumbnail_path = item.get('thumbnail_path')
            if thumbnail_path and os.path.exists(thumbnail_path):
                thumbnail = self.create_thumbnail(thumbnail_path, thumbnail_size=(80, 80))
                if thumbnail:
                    list_item.setIcon(QIcon(thumbnail))
            else:
                # Try to create thumbnail from main file if it's an image
                file_path = item.get('file_path')
                if file_path and os.path.exists(file_path) and file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                    thumbnail = self.create_thumbnail(file_path, thumbnail_size=(80, 80))
                    if thumbnail:
                        list_item.setIcon(QIcon(thumbnail))
            
            self.archive_list.addItem(list_item)
    
    def on_archive_selection_changed(self):
        """Enable/disable buttons based on selection"""
        has_selection = len(self.archive_list.selectedItems()) > 0
        self.delete_archive_button.setEnabled(has_selection)
        self.rename_archive_button.setEnabled(has_selection)
        
        # Enable load measurement button only if a measurement is selected
        if has_selection:
            item = self.archive_list.selectedItems()[0]
            data = item.data(Qt.UserRole)
            is_measurement = data and data.get('type') == 'Measurement' and 'point1' in data and 'point2' in data
            self.load_measurement_button.setEnabled(is_measurement)
        else:
            self.load_measurement_button.setEnabled(False)
    
    def open_archive_item(self, item):
        """Open the selected archive item"""
        data = item.data(Qt.UserRole)
        if data and 'file_path' in data:
            file_path = data['file_path']
            if os.path.exists(file_path):
                os.startfile(file_path)
            else:
                QMessageBox.warning(self, "File Not Found", f"Archive file not found:\n{file_path}")
    
    def delete_archive_item(self):
        """Delete selected archive items"""
        selected_items = self.archive_list.selectedItems()
        if not selected_items:
            return
        
        reply = QMessageBox.question(self, "Confirm Delete", 
                                     f"Delete {len(selected_items)} selected item(s) from archive?",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            for item in selected_items:
                data = item.data(Qt.UserRole)
                # Remove file if it exists
                if data and 'file_path' in data:
                    file_path = data['file_path']
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            print(f"Error deleting file {file_path}: {e}")
                
                # Remove from archive data
                if data in self.archive_data:
                    self.archive_data.remove(data)
            
            self.save_archive_data()
            self.refresh_archive_list()
    
    def rename_archive_item(self):
        """Rename the description of a selected archive item"""
        selected_items = self.archive_list.selectedItems()
        if not selected_items:
            return
        
        # Get the current item data
        item = selected_items[0]
        data = item.data(Qt.UserRole)
        
        if not data:
            return
        
        current_description = data.get('description', '')
        item_type = data.get('type', 'Item')
        timestamp = data.get('timestamp', 'Unknown')
        
        # Create rename dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Rename {item_type}")
        dialog.setMinimumWidth(450)
        
        layout = QVBoxLayout(dialog)
        
        # Info label
        info_label = QLabel(f"Rename {item_type} from {timestamp}")
        info_label.setObjectName("ArchiveTitle")
        layout.addWidget(info_label)
        
        # Current description label
        current_label = QLabel(f"Current: {current_description}")
        layout.addWidget(current_label)
        
        # New description input
        new_desc_label = QLabel("New description:")
        layout.addWidget(new_desc_label)
        
        description_edit = QLineEdit()
        description_edit.setText(current_description)
        description_edit.setPlaceholderText("Enter new description...")
        description_edit.selectAll()  # Select all text for easy replacement
        layout.addWidget(description_edit)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        # Show dialog and process result
        if dialog.exec() == QDialog.Accepted:
            new_description = description_edit.text().strip()
            
            if not new_description:
                QMessageBox.warning(self, "Invalid Input", "Description cannot be empty.")
                return
            
            if new_description == current_description:
                return  # No change
            
            try:
                # Update the description in the archive data
                data['description'] = new_description
                
                # Save the updated archive data
                self.save_archive_data()
                
                # Refresh the list to show the new name
                self.refresh_archive_list()
                
                # Find and select the renamed item
                for i in range(self.archive_list.count()):
                    list_item = self.archive_list.item(i)
                    if list_item.data(Qt.UserRole) == data:
                        self.archive_list.setCurrentItem(list_item)
                        break
                
                self.status_bar.showMessage(f"Renamed: '{current_description}' → '{new_description}'")
                
            except Exception as e:
                QMessageBox.critical(self, "Rename Error", f"Could not rename item:\n{e}")
                print(f"Error renaming archive item: {e}")
    
    def open_archive_folder(self):
        """Open the archive folder in file explorer"""
        if os.path.exists(self.archive_dir):
            os.startfile(self.archive_dir)
        else:
            QMessageBox.warning(self, "Folder Not Found", "Archive folder does not exist.")
    
    def load_measurement_from_archive(self):
        """Load a saved measurement and display it at the exact position"""
        selected_items = self.archive_list.selectedItems()
        if not selected_items:
            return
        
        data = selected_items[0].data(Qt.UserRole)
        if not data or data.get('type') != 'Measurement':
            QMessageBox.warning(self, "Invalid Selection", "Please select a measurement to load.")
            return
        
        # Check if we have the required data
        if 'point1' not in data or 'point2' not in data:
            QMessageBox.warning(self, "Incomplete Data", 
                              "This measurement doesn't have position data.\n"
                              "Only measurements saved with the latest version can be reloaded.")
            return
        
        # Check if a model is loaded
        if self.current_mesh_object is None:
            # Try to load the associated model
            if 'model_path' in data and os.path.exists(data['model_path']):
                reply = QMessageBox.question(
                    self, 
                    "Load Model?", 
                    f"No model is currently loaded. Load the model this measurement was taken from?\n\n"
                    f"Model: {data.get('model_name', 'Unknown')}",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    self.load_model(data['model_path'])
                else:
                    return
            else:
                QMessageBox.warning(self, "No Model", 
                                  "Please load the 3D model this measurement was taken from.")
                return
        
        try:
            # Get the saved points
            point1 = data['point1']
            point2 = data['point2']
            
            # Ensure measurement mode is active
            if not self.is_measuring:
                self.measure_button.setChecked(True)
                self.toggle_measurement_mode()
            
            # Set the line widget to the saved positions
            if hasattr(self, 'line_widget') and self.line_widget:
                self.line_widget.SetPoint1(point1)
                self.line_widget.SetPoint2(point2)
                
                # Update the measurement display
                self.update_measurement(None, None)
                
                # Render the scene
                self.plotter.render()
                
                description = data.get('description', 'Loaded measurement')
                distance = data.get('distance', 'Unknown')
                self.status_bar.showMessage(f"Loaded measurement: {description} ({distance})")
                
                # Switch to Model Info tab to show user the measurement is loaded
                self.right_panel_tabs.setCurrentIndex(0)
                
                QMessageBox.information(
                    self, 
                    "Measurement Loaded", 
                    f"Measurement loaded successfully!\n\n"
                    f"Description: {description}\n"
                    f"Distance: {distance}\n\n"
                    f"You can now adjust the measurement points or save it again."
                )
            else:
                QMessageBox.warning(self, "Error", "Could not initialize measurement widget.")
                
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Could not load measurement:\n{e}")
            print(f"Error loading measurement: {e}")
    
    def capture_screenshot(self):
        """Capture the current 3D view and save to archive"""
        if self.current_mesh_object is None:
            QMessageBox.warning(self, "No Model", "Please load a 3D model first.")
            return
        
        # Get description from user
        description, ok = self.get_archive_description("Screenshot")
        if not ok:
            return
        
        # Get organized folder path
        organized_folder = self.get_organized_archive_path("Screenshots")
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        file_path = os.path.join(organized_folder, filename)
        
        # Generate thumbnail filename
        thumb_filename = f"thumb_screenshot_{timestamp}.png"
        thumb_path = os.path.join(organized_folder, thumb_filename)
        
        try:
            # Capture full screenshot
            self.plotter.screenshot(file_path)
            
            # Create thumbnail from the screenshot
            thumbnail = self.create_thumbnail(file_path)
            if thumbnail:
                thumbnail.save(thumb_path)
            
            # Add to archive
            archive_entry = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'type': 'Screenshot',
                'description': description,
                'file_path': file_path,
                'thumbnail_path': thumb_path if thumbnail else None,
                'model_name': os.path.basename(self.current_model_path) if self.current_model_path else "Unknown"
            }
            self.archive_data.append(archive_entry)
            self.save_archive_data()
            self.refresh_archive_list()
            
            self.status_bar.showMessage(f"Screenshot saved to archive: {filename}")
            QMessageBox.information(self, "Success", f"Screenshot saved successfully!\n{filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "Capture Error", f"Could not capture screenshot:\n{e}")
            print(f"Error capturing screenshot: {e}")
    
    def save_measurement_data(self):
        """Save current measurement data to archive"""
        if not self.is_measuring or not hasattr(self, 'current_measurement'):
            QMessageBox.warning(self, "No Measurement", "Please create a measurement first.")
            return
        
        # Get description from user
        description, ok = self.get_archive_description("Measurement")
        if not ok:
            return
        
        # Get organized folder path
        organized_folder = self.get_organized_archive_path("Measurements")
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"measurement_{timestamp}.txt"
        file_path = os.path.join(organized_folder, filename)
        
        # Generate thumbnail filename
        thumb_filename = f"thumb_measurement_{timestamp}.png"
        thumb_path = os.path.join(organized_folder, thumb_filename)
        
        try:
            # Capture thumbnail of current view with measurement
            thumb_saved = self.capture_model_thumbnail(thumb_path)
            
            # Save measurement data
            with open(file_path, 'w') as f:
                f.write(f"ScanSect Measurement Data\n")
                f.write(f"========================\n\n")
                f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Model: {os.path.basename(self.current_model_path) if self.current_model_path else 'Unknown'}\n")
                f.write(f"Description: {description}\n\n")
                f.write(f"Measurement:\n")
                f.write(f"  Point 1: ({self.current_measurement['point1'][0]:.4f}, {self.current_measurement['point1'][1]:.4f}, {self.current_measurement['point1'][2]:.4f})\n")
                f.write(f"  Point 2: ({self.current_measurement['point2'][0]:.4f}, {self.current_measurement['point2'][1]:.4f}, {self.current_measurement['point2'][2]:.4f})\n")
                f.write(f"  Distance: {self.current_measurement['distance']:.4f} mm\n")
            
            # Add to archive with measurement coordinates and thumbnail
            archive_entry = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'type': 'Measurement',
                'description': description,
                'file_path': file_path,
                'thumbnail_path': thumb_path if thumb_saved else None,
                'model_name': os.path.basename(self.current_model_path) if self.current_model_path else "Unknown",
                'model_path': self.current_model_path,
                'distance': f"{self.current_measurement['distance']:.2f} mm",
                'point1': self.current_measurement['point1'],
                'point2': self.current_measurement['point2']
            }
            self.archive_data.append(archive_entry)
            self.save_archive_data()
            self.refresh_archive_list()
            
            self.status_bar.showMessage(f"Measurement saved to archive: {filename}")
            QMessageBox.information(self, "Success", f"Measurement data saved successfully!\n{filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Could not save measurement data:\n{e}")
            print(f"Error saving measurement: {e}")
        filename = f"measurement_{timestamp}.txt"
        file_path = os.path.join(self.archive_dir, filename)
        
        try:
            # Save measurement data
            with open(file_path, 'w') as f:
                f.write(f"ScanSect Measurement Data\n")
                f.write(f"========================\n\n")
                f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Model: {os.path.basename(self.current_model_path) if self.current_model_path else 'Unknown'}\n")
                f.write(f"Description: {description}\n\n")
                f.write(f"Measurement:\n")
                f.write(f"  Point 1: ({self.current_measurement['point1'][0]:.4f}, {self.current_measurement['point1'][1]:.4f}, {self.current_measurement['point1'][2]:.4f})\n")
                f.write(f"  Point 2: ({self.current_measurement['point2'][0]:.4f}, {self.current_measurement['point2'][1]:.4f}, {self.current_measurement['point2'][2]:.4f})\n")
                f.write(f"  Distance: {self.current_measurement['distance']:.4f} mm\n")
            
            # Add to archive with measurement coordinates
            archive_entry = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'type': 'Measurement',
                'description': description,
                'file_path': file_path,
                'model_name': os.path.basename(self.current_model_path) if self.current_model_path else "Unknown",
                'model_path': self.current_model_path,
                'distance': f"{self.current_measurement['distance']:.2f} mm",
                'point1': self.current_measurement['point1'],
                'point2': self.current_measurement['point2']
            }
            self.archive_data.append(archive_entry)
            self.save_archive_data()
            self.refresh_archive_list()
            
            self.status_bar.showMessage(f"Measurement saved to archive: {filename}")
            QMessageBox.information(self, "Success", f"Measurement data saved successfully!\n{filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Could not save measurement data:\n{e}")
            print(f"Error saving measurement: {e}")
    
    def get_archive_description(self, item_type):
        """Get description from user for archive item"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Save {item_type}")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        label = QLabel(f"Enter a description for this {item_type.lower()}:")
        layout.addWidget(label)
        
        description_edit = QLineEdit()
        description_edit.setPlaceholderText(f"E.g., Wing span measurement, Top view, etc.")
        layout.addWidget(description_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.Accepted:
            return description_edit.text() or f"{item_type} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", True
        return None, False
    
    # ===== Recent Models Functions =====
    
    def load_recent_models(self):
        """Load recent models list from JSON file"""
        if os.path.exists(self.recent_models_file):
            try:
                with open(self.recent_models_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading recent models: {e}")
                return []
        return []
    
    def save_recent_models(self):
        """Save recent models list to JSON file"""
        try:
            with open(self.recent_models_file, 'w') as f:
                json.dump(self.recent_models, f, indent=2)
        except Exception as e:
            print(f"Error saving recent models: {e}")
    
    def add_to_recent_models(self, file_path):
        """Add a model to the recent models list"""
        if not os.path.exists(file_path):
            return
        
        # Create entry
        entry = {
            'path': file_path,
            'name': os.path.basename(file_path),
            'directory': os.path.dirname(file_path),
            'last_accessed': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'size': os.path.getsize(file_path)
        }
        
        # Remove if already exists (to update timestamp)
        self.recent_models = [m for m in self.recent_models if m.get('path') != file_path]
        
        # Add to beginning of list
        self.recent_models.insert(0, entry)
        
        # Keep only last 20 models
        self.recent_models = self.recent_models[:20]
        
        # Save and refresh
        self.save_recent_models()
        self.refresh_recent_models_list()
    
    def refresh_recent_models_list(self):
        """Refresh the recent models list display"""
        self.recent_models_list.clear()
        
        for model in self.recent_models:
            # Check if file still exists
            if not os.path.exists(model.get('path', '')):
                continue
            
            name = model.get('name', 'Unknown')
            last_accessed = model.get('last_accessed', 'Unknown')
            directory = model.get('directory', '')
            
            # Format size
            size = model.get('size', 0)
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            
            display_text = f"{name}\n  {size_str} • {last_accessed}\n  {directory}"
            list_item = QListWidgetItem(display_text)
            list_item.setData(Qt.UserRole, model)
            self.recent_models_list.addItem(list_item)
    
    def on_recent_selection_changed(self):
        """Enable/disable buttons based on recent models selection"""
        has_selection = len(self.recent_models_list.selectedItems()) > 0
        self.load_recent_button.setEnabled(has_selection)
        self.remove_recent_button.setEnabled(has_selection)
    
    def load_recent_model(self, item):
        """Load the selected recent model"""
        if item is None:
            return
        
        data = item.data(Qt.UserRole)
        if data and 'path' in data:
            file_path = data['path']
            if os.path.exists(file_path):
                self.load_model(file_path)
            else:
                QMessageBox.warning(self, "File Not Found", 
                                  f"Model file not found:\n{file_path}\n\n"
                                  "It may have been moved or deleted.")
                # Remove from recent list
                self.recent_models = [m for m in self.recent_models if m.get('path') != file_path]
                self.save_recent_models()
                self.refresh_recent_models_list()
    
    def remove_recent_model(self):
        """Remove selected model from recent list"""
        selected_items = self.recent_models_list.selectedItems()
        if not selected_items:
            return
        
        for item in selected_items:
            data = item.data(Qt.UserRole)
            if data in self.recent_models:
                self.recent_models.remove(data)
        
        self.save_recent_models()
        self.refresh_recent_models_list()
    
    def clear_recent_models(self):
        """Clear all recent models"""
        if not self.recent_models:
            return
        
        reply = QMessageBox.question(self, "Clear Recent Models", 
                                     "Clear all recent models from the list?",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.recent_models = []
            self.save_recent_models()
            self.refresh_recent_models_list()
    
    def closeEvent(self, event):
        if hasattr(self, 'plotter') and self.plotter is not None:
            self.plotter.close() 
        super().closeEvent(event)

    def load_texture_dialog(self):
        """Open a dialog to select and load a texture"""
        if self.current_mesh_object is None:
            QMessageBox.warning(self, "No Model", "Please load a 3D model first.")
            return
            
        file_filter = "Texture Files (*.jpg *.jpeg *.png *.bmp *.tiff);;All Files (*)"
        texture_path, _ = QFileDialog.getOpenFileName(
            self, "Open Texture", 
            os.path.dirname(self.current_model_path) if self.current_model_path else os.path.expanduser("~"),
            file_filter
        )
        if texture_path:
            self.apply_texture_to_current_model(texture_path)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show the main window
    window = ScanSectGUI()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec_())