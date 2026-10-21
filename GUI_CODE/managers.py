"""Model loading, mesh state, and archive persistence for ScanSect."""

import os
import json
import uuid

from PySide6.QtCore import QThread, Signal
from measurement_utils import atomic_write_json_with_backup, load_json_with_backup

pv = None
vtk = None
np = None
QtInteractor = None


def ensure_3d_libs():
    """Lazy-load pyvista, vtk, numpy, and pyvistaqt on first use."""
    global pv, vtk, np, QtInteractor
    if pv is None:
        import pyvista as _pv
        import vtk as _vtk
        import numpy as _np
        from pyvistaqt import QtInteractor as _QtInteractor

        pv = _pv
        vtk = _vtk
        np = _np
        QtInteractor = _QtInteractor

        pv.set_plot_theme('document')
        pv.global_theme.window_size = [1024, 768]
        pv.global_theme.font.size = 12
        pv.global_theme.font.label_size = 12
    return pv, vtk, np, QtInteractor


class ModelLoaderWorker(QThread):
    finished = Signal(object, str)
    error = Signal(str, str)
    progress = Signal(str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        try:
            ensure_3d_libs()
            self.progress.emit(f"Reading file: {os.path.basename(self.file_path)}...")
            mesh = pv.read(self.file_path)

            if mesh is None or mesh.n_points == 0:
                self.error.emit(f"Loaded mesh is empty or invalid from file:\n{self.file_path}", self.file_path)
                return

            if self.file_path.lower().endswith('.obj'):
                self.progress.emit("Searching for texture...")
                self._load_obj_texture(mesh)

            self.finished.emit(mesh, self.file_path)
        except Exception as e:
            self.error.emit(str(e), self.file_path)

    def _load_obj_texture(self, mesh):
        try:
            mtl_texture_path = self._parse_mtl_file(self.file_path)
            texture_path = self._find_texture_file(self.file_path, mtl_texture_path)
            if texture_path:
                try:
                    texture = pv.read_texture(texture_path)
                    mesh._scansect_texture = texture
                except Exception as tex_error:
                    print(f"Error loading texture file: {tex_error}")
        except Exception as tex_error:
            print(f"Error during texture search: {tex_error}")

    def _parse_mtl_file(self, obj_file_path):
        mtl_path = obj_file_path.replace('.obj', '.mtl')
        if not os.path.exists(mtl_path):
            return None
        try:
            with open(mtl_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('map_Kd'):
                        return line.split(None, 1)[1].strip()
        except Exception:
            pass
        return None

    def _find_texture_file(self, obj_file_path, mtl_texture_path=None):
        obj_dir = os.path.dirname(obj_file_path)
        base_name = os.path.splitext(os.path.basename(obj_file_path))[0]
        search_paths = []

        if mtl_texture_path:
            search_paths.append(mtl_texture_path)
            search_paths.append(os.path.join(obj_dir, os.path.basename(mtl_texture_path)))

        common_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']
        common_suffixes = ['', '_diffuse', '_u1_v1_diffuse', '_texture', '_color', '_basecolor']

        for suffix in common_suffixes:
            for ext in common_extensions:
                search_paths.append(os.path.join(obj_dir, f"{base_name}{suffix}{ext}"))

        for folder in ['textures', 'Textures', 'maps', 'Maps', 'images', 'Images']:
            folder_path = os.path.join(obj_dir, folder)
            if os.path.exists(folder_path):
                for suffix in common_suffixes:
                    for ext in common_extensions:
                        search_paths.append(os.path.join(folder_path, f"{base_name}{suffix}{ext}"))

        parent_dir = os.path.dirname(obj_dir)
        if parent_dir and parent_dir != obj_dir:
            for suffix in common_suffixes:
                for ext in common_extensions:
                    search_paths.append(os.path.join(parent_dir, f"{base_name}{suffix}{ext}"))

        for path in search_paths:
            if os.path.exists(path):
                return path
        return None


class MeshManager:
    def __init__(self):
        self.current_mesh = None
        self.current_path = None
        self.current_actor = None
        self.current_texture = None

    @property
    def has_model(self):
        return self.current_mesh is not None

    @property
    def model_basename(self):
        return os.path.basename(self.current_path) if self.current_path else "Unknown"

    @property
    def insect_name(self):
        if self.current_path:
            name = os.path.splitext(os.path.basename(self.current_path))[0]
            return "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        return "Unknown"

    def set_mesh(self, mesh, file_path):
        self.current_mesh = mesh
        self.current_path = file_path

    def clear(self):
        self.current_mesh = None
        self.current_path = None
        self.current_actor = None
        self.current_texture = None

    def has_textures(self):
        if getattr(self.current_mesh, '_scansect_texture', None) is not None:
            return True
        if self.current_texture is not None:
            return True
        if self.current_mesh is None:
            return False
        if hasattr(self.current_mesh, 'textures') and isinstance(self.current_mesh.textures, dict):
            return any(tex is not None for tex in self.current_mesh.textures.values())
        return False

    def has_uvs(self):
        if self.current_mesh is None:
            return False
        return (hasattr(self.current_mesh, 'active_texture_coordinates')
                and self.current_mesh.active_texture_coordinates is not None)

    def get_first_texture(self):
        if getattr(self.current_mesh, '_scansect_texture', None) is not None:
            return self.current_mesh._scansect_texture
        if self.current_texture is not None:
            return self.current_texture
        if self.has_textures():
            return next(iter(self.current_mesh.textures.values()))
        return None

    def get_metadata_text(self, texture_auto=False, texture_manual=False):
        mesh = self.current_mesh
        if mesh is None:
            return "No model loaded."
        lines = [
            "Model Geometry",
            f"  File:     {self.model_basename}",
            f"  Vertices: {mesh.n_points:,}",
            f"  Cells:    {mesh.n_cells:,}",
            "",
            "Bounding Box (model units)",
        ]
        bounds = mesh.bounds
        lines.append(f"  X: {bounds[0]:.3f} to {bounds[1]:.3f}  (span {bounds[1] - bounds[0]:.3f})")
        lines.append(f"  Y: {bounds[2]:.3f} to {bounds[3]:.3f}  (span {bounds[3] - bounds[2]:.3f})")
        lines.append(f"  Z: {bounds[4]:.3f} to {bounds[5]:.3f}  (span {bounds[5] - bounds[4]:.3f})")
        lines.append("")
        lines.append("Surface & UV Mapping")

        if texture_manual:
            lines.append("  Texture: Manually applied")
        elif texture_auto:
            lines.append("  Texture: Loaded from material (.mtl)")
        elif self.has_textures():
            lines.append("  Texture: Present in mesh data")
        else:
            lines.append("  Texture: None applied")

        if self.has_uvs():
            lines.append("  UV Map:  Present")
        else:
            lines.append("  UV Map:  Missing")

        return "\n".join(lines)


class ArchiveManager:
    """Manages archive data with separate storage for screenshots and measurements."""

    def __init__(self, archive_dir):
        self.archive_dir = archive_dir
        self.screenshots_dir = os.path.join(archive_dir, "Screenshots")
        self.measurements_dir = os.path.join(archive_dir, "Measurements")

        for d in [self.archive_dir, self.screenshots_dir, self.measurements_dir]:
            if not os.path.exists(d):
                os.makedirs(d)

        self.screenshots_index = os.path.join(self.screenshots_dir, "screenshots_index.json")
        self.measurements_index = os.path.join(self.measurements_dir, "measurements_index.json")

        old_archive = os.path.join(archive_dir, "archive_metadata.json")
        if os.path.exists(old_archive):
            self._migrate_old_archive(old_archive)

        self.screenshots = self._load_index(self.screenshots_index)
        self.measurements = self._load_index(self.measurements_index)

    def _migrate_old_archive(self, old_path):
        if os.path.exists(self.screenshots_index) or os.path.exists(self.measurements_index):
            return
        try:
            with open(old_path, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
            screenshots = []
            measurements = []
            for item in old_data:
                if 'session_id' not in item:
                    item['session_id'] = str(uuid.uuid4())[:8]
                if item.get('type') == 'Screenshot':
                    screenshots.append(item)
                elif item.get('type') == 'Measurement':
                    measurements.append(item)
            self._save_index(self.screenshots_index, screenshots)
            self._save_index(self.measurements_index, measurements)
        except Exception as e:
            print(f"Error migrating old archive: {e}")

    def _load_index(self, index_path):
        return load_json_with_backup(index_path, [])

    def _save_index(self, index_path, data):
        try:
            atomic_write_json_with_backup(index_path, data)
        except Exception as e:
            print(f"Error saving index {index_path}: {e}")
            raise

    def save_screenshots(self):
        self._save_index(self.screenshots_index, self.screenshots)

    def save_measurements(self):
        self._save_index(self.measurements_index, self.measurements)

    def add_screenshot(self, entry):
        if 'session_id' not in entry:
            entry['session_id'] = str(uuid.uuid4())[:8]
        self.screenshots.append(entry)
        self.save_screenshots()

    def add_measurement(self, entry):
        if 'session_id' not in entry:
            entry['session_id'] = str(uuid.uuid4())[:8]
        self.measurements.append(entry)
        self.save_measurements()

    def remove_screenshot(self, entry):
        if entry in self.screenshots:
            self.screenshots.remove(entry)
            self.save_screenshots()

    def remove_measurement(self, entry):
        if entry in self.measurements:
            self.measurements.remove(entry)
            self.save_measurements()

    def get_screenshot_path(self, insect_name="Unknown"):
        p = os.path.join(self.screenshots_dir, insect_name)
        if not os.path.exists(p):
            os.makedirs(p)
        return p

    def get_measurement_path(self, insect_name="Unknown"):
        p = os.path.join(self.measurements_dir, insect_name)
        if not os.path.exists(p):
            os.makedirs(p)
        return p

    def find_linked_screenshots(self, session_id):
        return [s for s in self.screenshots if s.get('session_id') == session_id]

