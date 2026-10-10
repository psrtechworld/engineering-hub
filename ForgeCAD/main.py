import sys, os, json, csv, tempfile
import numpy as np
import cadquery as cq
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                                QHBoxLayout, QPushButton, QLabel, QLineEdit,
                                QComboBox, QGroupBox, QScrollArea, QFileDialog,
                                QListWidget, QListWidgetItem, QCheckBox, QSlider,
                                QColorDialog, QInputDialog, QDockWidget, QTabWidget,
                                QToolBar, QToolButton, QStatusBar, QStackedWidget,
                                QFormLayout, QFrame, QSizePolicy)
from PySide6.QtCore import Qt, QSettings, QTimer, QSize
from PySide6.QtGui import QColor, QShortcut, QKeySequence, QAction, QFont
from pyvistaqt import QtInteractor
import pyvista as pv


DEFAULT_COLORS = ['#4682b4', '#ff7f50', '#3cb371', '#ffd700', '#9370db',
                  '#ff6347', '#40e0d0', '#da70d6', '#fa8072', '#f0e68c']
FORGE_DIR = os.path.join(os.path.expanduser("~"), "ForgeCAD")
TEMPLATE_DIR = os.path.join(FORGE_DIR, "templates")
os.makedirs(FORGE_DIR, exist_ok=True); os.makedirs(TEMPLATE_DIR, exist_ok=True)

MATERIALS = {"Steel": 7.85, "Aluminum": 2.70, "Copper": 8.96, "Brass": 8.50,
             "Titanium": 4.51, "ABS Plastic": 1.04, "PLA Plastic": 1.24,
             "Nylon": 1.15, "Wood (Oak)": 0.75, "Glass": 2.50}
STL_QUALITY = {"Low": (0.5, 20), "Medium": (0.2, 12), "High": (0.05, 6)}

BOLT_METRIC = {"M3": (3, 5.5, 2.0, 0.5), "M4": (4, 7, 2.8, 0.7), "M5": (5, 8.5, 3.5, 0.8),
               "M6": (6, 10, 4.0, 1.0), "M8": (8, 13, 5.3, 1.25), "M10": (10, 16, 6.4, 1.5),
               "M12": (12, 18, 7.5, 1.75), "M16": (16, 24, 10.0, 2.0), "M20": (20, 30, 12.5, 2.5)}
NUT_METRIC = {"M3": (3, 5.5, 2.4), "M4": (4, 7, 3.2), "M5": (5, 8, 4.0), "M6": (6, 10, 5.0),
              "M8": (8, 13, 6.5), "M10": (10, 17, 8.0), "M12": (12, 19, 10.0),
              "M16": (16, 24, 13.0), "M20": (20, 30, 16.0)}
WASHER_METRIC = {"M3": (3.2, 7, 0.5), "M4": (4.3, 9, 0.8), "M5": (5.3, 10, 1.0),
                 "M6": (6.4, 12, 1.6), "M8": (8.4, 16, 1.6), "M10": (10.5, 20, 2.0),
                 "M12": (13, 24, 2.5), "M16": (17, 30, 3.0), "M20": (21, 37, 3.0)}
BEARING_METRIC = {"6000": (10, 26, 8), "6001": (12, 28, 8), "6002": (15, 32, 9),
                  "6003": (17, 35, 10), "6004": (20, 42, 12), "6005": (25, 47, 12),
                  "6006": (30, 55, 13), "6007": (35, 62, 14), "6008": (40, 68, 15)}


STYLE = """
QMainWindow { background: #0f1218; }
QMenuBar { background: #1a1f29; color: #d0d6e0; padding: 2px; }
QMenuBar::item { padding: 6px 12px; background: transparent; }
QMenuBar::item:selected { background: #2b3240; border-radius: 4px; }
QMenu { background: #1a1f29; color: #d0d6e0; border: 1px solid #2b3240; }
QMenu::item { padding: 6px 25px; }
QMenu::item:selected { background: #2b3240; }
QMenu::separator { height: 1px; background: #2b3240; margin: 4px 8px; }
QToolBar { background: #161b23; border: none; padding: 3px; spacing: 3px; }
QToolBar::separator { background: #2b3240; width: 1px; margin: 4px; }
QToolButton { background: #222a36; color: #d0d6e0; border: 1px solid #2b3240;
              border-radius: 5px; padding: 5px 8px; font-size: 11px; }
QToolButton:hover { background: #2d3745; border-color: #4a5568; }
QToolButton:pressed { background: #70a7ff; color: #0d1627; }
QToolButton:checked { background: #70a7ff; color: #0d1627; }
QTabWidget::pane { border: 1px solid #2b3240; background: #161b23; }
QTabBar::tab { background: #1a1f29; color: #9aa6ba; padding: 8px 16px;
               border: 1px solid #2b3240; border-bottom: none;
               border-top-left-radius: 5px; border-top-right-radius: 5px;
               margin-right: 2px; font-weight: 600; }
QTabBar::tab:selected { background: #2b3240; color: #70a7ff; }
QTabBar::tab:hover:!selected { background: #222a36; color: #d0d6e0; }
QDockWidget { color: #d0d6e0; }
QDockWidget::title { background: #1a1f29; padding: 6px; }
QListWidget { background: #161b23; color: #d0d6e0; border: 1px solid #2b3240;
              border-radius: 4px; padding: 4px; }
QListWidget::item { padding: 4px 6px; border-radius: 3px; }
QListWidget::item:selected { background: #70a7ff; color: #0d1627; }
QGroupBox { color: #70a7ff; border: 1px solid #2b3240; border-radius: 6px;
            margin-top: 10px; padding-top: 8px; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
QLineEdit, QComboBox { background: #222a36; color: #d0d6e0; border: 1px solid #2b3240;
                        border-radius: 4px; padding: 4px 6px; }
QLineEdit:focus, QComboBox:focus { border-color: #70a7ff; }
QPushButton { background: #222a36; color: #d0d6e0; border: 1px solid #2b3240;
              border-radius: 4px; padding: 5px 10px; font-weight: 500; }
QPushButton:hover { background: #2d3745; border-color: #4a5568; }
QPushButton:pressed { background: #70a7ff; color: #0d1627; }
QPushButton:checked { background: #70a7ff; color: #0d1627; }
QPushButton:disabled { color: #4a5568; background: #1a1f29; }
QStatusBar { background: #1a1f29; color: #9aa6ba; }
QLabel { color: #d0d6e0; }
QCheckBox { color: #d0d6e0; }
QSlider::groove:horizontal { height: 4px; background: #2b3240; border-radius: 2px; }
QSlider::handle:horizontal { background: #70a7ff; width: 12px; height: 12px;
                             margin: -5px 0; border-radius: 6px; }
QScrollArea { background: transparent; border: none; }
"""


class ForgeCAD(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Forge CAD v2.1")
        self.resize(1600, 960)
        self.setStyleSheet(STYLE)

        self.bodies = []; self.body_colors = []; self.body_props = []
        self.history = []; self.redo_stack = []
        self.active_index = 0
        self.sketch_mode = False; self.sketch_tool = None
        self.sketch_points = []; self.sketch_entities = []
        self.sketch_plane = 'XY'
        self._sketch_actors = []; self._sketch_plane_actor = None
        self._label_actors = []; self._measure_actors = []; self._bbox_actors = []
        self._dimension_actors = []; self._com_actor = None
        self.current_project_path = None
        self.wireframe = False; self.show_dimensions = True
        self.polyline_chain = []
        self.section_enabled = False; self.section_axis = 'X'; self.section_pos = 0.0
        self.grid_snap = 0.0; self.exploded = False; self.datum_planes = False
        self.measure_mode = False; self.measure_points = []
        self.show_bbox = False
        self.animation_on = False
        self.anim_timer = QTimer(); self.anim_timer.timeout.connect(self._anim_step)

        # v2.1 new state
        self.feature_history = []
        self.dimension_mode = False
        self.dimension_points = []
        self.projection_persp = False
        self._body_actors = {}   # actor -> body index map

        self.settings = QSettings("ForgeCAD", "ForgeCAD")
        self.recent_files = list(self.settings.value("recent_files", []) or [])

        self.plotter = QtInteractor(self)
        self.setCentralWidget(self.plotter.interactor)
        self._setup_viewport()

        self._build_menu()
        self._build_toolbar()
        self._build_left_dock()
        self._build_right_dock()
        self._build_ribbon()
        self._build_status_bar()
        self._setup_shortcuts()

        # Global shortcuts
        for sc in self.findChildren(QShortcut):
            sc.setContext(Qt.ApplicationShortcut)

        self._enable_body_picking()
        self._set_status("Ready — Forge CAD v2.1")

    # ================= VIEWPORT =================
    def _setup_viewport(self):
        self.plotter.show_grid(color='#333a45'); self.plotter.add_axes()
        self.plotter.set_background('#0f1218')

    # ================= MENU =================
    def _build_menu(self):
        mb = self.menuBar()

        f = mb.addMenu("&File")
        self._act(f, "New", "Ctrl+N", self.clear_scene)
        self._act(f, "Open...", "Ctrl+O", self.open_project)
        f.addSeparator()
        self._act(f, "Save", "Ctrl+S", self.save_project)
        self._act(f, "Save As...", "Ctrl+Shift+S", lambda: self.save_project(force=True))
        self._act(f, "Save as Template...", None, self.save_template)
        self._act(f, "Load Template...", None, self.load_template)
        f.addSeparator()
        imp = f.addMenu("Import")
        self._act(imp, "STEP...", "Ctrl+I", self.import_step)
        self._act(imp, "STL...", "Ctrl+Shift+I", self.import_stl)
        self._act(imp, "OBJ / PLY / VTK...", None, self.import_obj_ply)
        exp = f.addMenu("Export")
        self._act(exp, "STL", None, self.export_stl)
        self._act(exp, "STEP", None, self.export_step)
        self._act(exp, "4-View Drawing (PNG)", None, self.export_4view_drawing)
        self._act(exp, "Screenshot (PNG)", None, self.screenshot_viewport)
        self._act(exp, "Sketch DXF", None, self.export_sketch_dxf)
        self._act(exp, "WebGL Viewer (HTML)", None, self.export_webgl_viewer)
        self._act(exp, "BOM (CSV)", None, self.export_bom)
        self._act(exp, "Mass Report (CSV)", None, self.export_mass_report)
        self._act(exp, "Batch STL...", None, self.batch_stl_export)
        f.addSeparator()
        self._act(f, "Exit", "Ctrl+Q", self.close)

        e = mb.addMenu("&Edit")
        self._act(e, "Undo", "Ctrl+Z", self.undo)
        self._act(e, "Redo", "Ctrl+Y", self.redo)
        e.addSeparator()
        self._act(e, "Delete Active Body", "Delete", self.delete_active_body)
        self._act(e, "Copy Active Body", None, self.copy_body)
        self._act(e, "Change Body Color...", None, self.change_body_color)
        self._act(e, "Edit Properties...", None, self.edit_properties)
        self._act(e, "Rename Active...", None, lambda: self.rename_body(None))

        v = mb.addMenu("&View")
        self._act(v, "Front", "F", lambda: self.plotter.view_xz())
        self._act(v, "Top", "T", lambda: self.plotter.view_xy())
        self._act(v, "Right", "R", lambda: self.plotter.view_yz())
        self._act(v, "Isometric", "I", lambda: self.plotter.view_isometric())
        v.addSeparator()
        self._act(v, "Wireframe", None, self.toggle_wireframe, checkable=True)
        self._act(v, "Bounding Boxes", None, self._toggle_bbox, checkable=True)
        self._act(v, "Datum Planes", None, self._toggle_datum, checkable=True)
        self._act(v, "Section View", None, self._toggle_section, checkable=True)
        self._act(v, "Exploded View", None, self.toggle_explode, checkable=True)
        self._act(v, "Perspective Camera", None, self.toggle_perspective, checkable=True)
        v.addSeparator()
        self._act(v, "Reset Camera", None, lambda: self.plotter.reset_camera())

        ins = mb.addMenu("&Insert")
        self._act(ins, "Box", None, lambda: self._quick_prim("Box"))
        self._act(ins, "Sphere", None, lambda: self._quick_prim("Sphere"))
        self._act(ins, "Cylinder", None, lambda: self._quick_prim("Cylinder"))
        self._act(ins, "Cone", None, lambda: self._quick_prim("Cone"))
        ins.addSeparator()
        self._act(ins, "3D Text...", None, self.add_text)
        ins.addSeparator()
        std = ins.addMenu("Standard Parts")
        self._act(std, "Bolt", None, lambda: self._quick_std("Bolt"))
        self._act(std, "Nut", None, lambda: self._quick_std("Nut"))
        self._act(std, "Washer", None, lambda: self._quick_std("Washer"))
        self._act(std, "Bearing", None, lambda: self._quick_std("Bearing"))
        self._act(ins, "Spur Gear...", None, self.generate_gear)
        self._act(ins, "Helix / Spring...", None, self.create_helix)
        self._act(ins, "Cut Threads (active)...", None, self.cut_threads)

        sk = mb.addMenu("&Sketch")
        self._act(sk, "Start / Finish Sketch", None, self.toggle_sketch)
        sk.addSeparator()
        self._act(sk, "Line", None, lambda: self.set_tool('line'))
        self._act(sk, "Polyline", None, lambda: self.set_tool('poly'))
        self._act(sk, "Circle", None, lambda: self.set_tool('circle'))
        self._act(sk, "Rectangle", None, lambda: self.set_tool('rect'))
        self._act(sk, "Finish Polyline", None, self.finish_polyline)
        sk.addSeparator()
        self._act(sk, "Mirror Sketch X", None, lambda: self.mirror_sketch('X'))
        self._act(sk, "Mirror Sketch Y", None, lambda: self.mirror_sketch('Y'))
        self._act(sk, "Offset Sketch...", None, self.offset_sketch)
        self._act(sk, "Clear Sketch", None, self.clear_sketch)
        sk.addSeparator()
        self._act(sk, "Extrude...", None, self.extrude_sketch)
        self._act(sk, "Revolve...", None, self.revolve_sketch)
        self._act(sk, "Loft (2 sketches)", None, self.loft_sketches)
        self._act(sk, "Sweep (profile + path)", None, self.sweep_sketch)
        sk.addSeparator()
        self._act(sk, "Constrain: Horizontal", None, lambda: self.apply_constraint('horizontal'))
        self._act(sk, "Constrain: Vertical", None, lambda: self.apply_constraint('vertical'))
        self._act(sk, "Constrain: Perpendicular", None, lambda: self.apply_constraint('perpendicular'))
        self._act(sk, "Constrain: Parallel", None, lambda: self.apply_constraint('parallel'))
        self._act(sk, "Constrain: Coincident", None, lambda: self.apply_constraint('coincident'))
        self._act(sk, "Dimension Tool (D)", "D", self.toggle_dimension_mode)

        m = mb.addMenu("&Modify")
        self._act(m, "Move...", None, self.transform_move)
        self._act(m, "Rotate...", None, self.transform_rotate)
        self._act(m, "Scale...", None, self.transform_scale)
        self._act(m, "Non-uniform Scale...", None, self.transform_scale_xyz)
        m.addSeparator()
        self._act(m, "Boolean Union (last 2)", None, lambda: self.boolean_op('union'))
        self._act(m, "Boolean Cut (last 2)", None, lambda: self.boolean_op('cut'))
        self._act(m, "Boolean Intersect (last 2)", None, lambda: self.boolean_op('intersect'))
        m.addSeparator()
        self._act(m, "Fillet All Edges...", None, self.apply_fillet)
        self._act(m, "Chamfer All Edges...", None, self.apply_chamfer)
        self._act(m, "Shell (open top)...", None, self.shell_body)
        self._act(m, "Hole...", None, self.cut_hole)
        m.addSeparator()
        self._act(m, "Linear Pattern...", None, self.linear_pattern)
        self._act(m, "Circular Pattern...", None, self.circular_pattern)
        self._act(m, "Mirror Body...", None, self.mirror_body)

        t = mb.addMenu("&Tools")
        self._act(t, "Measure Active Body", None, self.measure_active)
        self._act(t, "Distance Measure", "M", self.toggle_distance_measure)
        self._act(t, "Calculate Mass", None, self.calculate_mass)
        self._act(t, "Show Center of Mass", None, self.show_center_of_mass)
        t.addSeparator()
        self._act(t, "Check Interference (all)", None, self.check_interference_all)
        self._act(t, "Check Clearance (2)", None, self.check_clearance_2)
        self._act(t, "All Bodies Info", None, self.show_all_info)
        t.addSeparator()
        self._act(t, "Turntable Animation", "Space", self.toggle_animation)
        t.addSeparator()
        self._act(t, "Bolt Wizard (M8 Assembly)", None, self.bolt_wizard)

        h = mb.addMenu("&Help")
        self._act(h, "About Forge CAD", None, self._show_about)

    def _act(self, menu, text, shortcut, slot, checkable=False):
        a = QAction(text, self)
        if shortcut: a.setShortcut(QKeySequence(shortcut))
        a.setCheckable(checkable)
        if checkable: a.toggled.connect(slot)
        else: a.triggered.connect(slot)
        menu.addAction(a)
        return a

    # ================= TOOLBAR =================
    def _build_toolbar(self):
        tb = QToolBar("Main"); tb.setIconSize(QSize(20, 20))
        tb.setMovable(False); self.addToolBar(tb)

        def btn(txt, tip, slot):
            b = QToolButton(); b.setText(txt); b.setToolTip(tip)
            b.clicked.connect(slot); tb.addWidget(b); return b

        btn("📄", "New", self.clear_scene)
        btn("📂", "Open", self.open_project)
        btn("💾", "Save", self.save_project)
        tb.addSeparator()
        btn("↶", "Undo", self.undo)
        btn("↷", "Redo", self.redo)
        tb.addSeparator()
        btn("⬛", "Box", lambda: self._quick_prim("Box"))
        btn("⚪", "Sphere", lambda: self._quick_prim("Sphere"))
        btn("◯", "Cylinder", lambda: self._quick_prim("Cylinder"))
        btn("△", "Cone", lambda: self._quick_prim("Cone"))
        tb.addSeparator()
        btn("✂", "Cut", lambda: self.boolean_op('cut'))
        btn("➕", "Union", lambda: self.boolean_op('union'))
        btn("∩", "Intersect", lambda: self.boolean_op('intersect'))
        tb.addSeparator()
        btn("⌐", "Fillet", self.apply_fillet)
        btn("▷", "Chamfer", self.apply_chamfer)
        btn("◎", "Hole", self.cut_hole)
        tb.addSeparator()
        btn("🔩", "Bolt Wizard", self.bolt_wizard)
        btn("📏", "Dimension (D)", self.toggle_dimension_mode)
        btn("⚖", "Center of Mass", self.show_center_of_mass)
        tb.addSeparator()
        for lbl, sl in [("Front", lambda: self.plotter.view_xz()),
                        ("Top", lambda: self.plotter.view_xy()),
                        ("Right", lambda: self.plotter.view_yz()),
                        ("Iso", lambda: self.plotter.view_isometric())]:
            btn(lbl, f"{lbl} view", sl)

    # ================= LEFT DOCK =================
    def _build_left_dock(self):
        dock = QDockWidget("Model Tree", self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        w = QWidget(); v = QVBoxLayout(w); v.setContentsMargins(6, 6, 6, 6)

        v.addWidget(QLabel("📦 Bodies"))
        self.body_list = QListWidget()
        self.body_list.currentRowChanged.connect(self.on_body_selected)
        self.body_list.itemDoubleClicked.connect(self.rename_body)
        v.addWidget(self.body_list, 1)

        row = QHBoxLayout()
        b1 = QPushButton("🎨 Color"); b1.clicked.connect(self.change_body_color)
        b2 = QPushButton("📝 Props"); b2.clicked.connect(self.edit_properties)
        b3 = QPushButton("🗑"); b3.setFixedWidth(30); b3.clicked.connect(self.delete_active_body)
        row.addWidget(b1); row.addWidget(b2); row.addWidget(b3)
        v.addLayout(row)

        self.bbox_cb = QCheckBox("Show bounding boxes")
        self.bbox_cb.stateChanged.connect(self.on_bbox_toggle)
        v.addWidget(self.bbox_cb)

        v.addWidget(QLabel("🌳 Feature Tree"))
        self.feature_list = QListWidget()
        self.feature_list.setFixedHeight(160)
        v.addWidget(self.feature_list)

        dock.setWidget(w); dock.setMinimumWidth(240)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

    # ================= RIGHT DOCK =================
    def _build_right_dock(self):
        dock = QDockWidget("Properties", self)
        dock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)

        self.prop_stack = QStackedWidget()
        self.prop_stack.addWidget(self._build_prop_home())
        self.prop_stack.addWidget(self._build_prop_sketch())
        self.prop_stack.addWidget(self._build_prop_model())
        self.prop_stack.addWidget(self._build_prop_assembly())
        self.prop_stack.addWidget(self._build_prop_drawing())
        self.prop_stack.addWidget(self._build_prop_tools())

        wrap = QWidget(); wv = QVBoxLayout(wrap); wv.setContentsMargins(0, 0, 0, 0)
        wv.addWidget(self.prop_stack)
        dock.setWidget(wrap)
        dock.setMinimumWidth(310)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

    def _scroll_wrap(self, widget):
        sc = QScrollArea(); sc.setWidgetResizable(True); sc.setWidget(widget); return sc

    def _build_prop_home(self):
        w = QWidget(); v = QVBoxLayout(w); v.setContentsMargins(6, 6, 6, 6)
        g = QGroupBox("Document"); f = QFormLayout(g)
        self.home_recent = QComboBox(); self.home_recent.addItem("— recent —")
        for p in self.recent_files: self.home_recent.addItem(os.path.basename(p), p)
        self.home_recent.currentIndexChanged.connect(self.open_recent)
        f.addRow("Recent:", self.home_recent)
        v.addWidget(g)
        g2 = QGroupBox("Scene"); f2 = QVBoxLayout(g2)
        self.home_info = QLabel("—")
        self.home_info.setStyleSheet("color:#a0e0a0;font-family:monospace;")
        f2.addWidget(self.home_info)
        b = QPushButton("Refresh"); b.clicked.connect(self._refresh_home_info); f2.addWidget(b)
        v.addWidget(g2)
        v.addStretch()
        return self._scroll_wrap(w)

    def _build_prop_sketch(self):
        w = QWidget(); v = QVBoxLayout(w); v.setContentsMargins(6, 6, 6, 6)
        g = QGroupBox("Sketch Plane"); f = QFormLayout(g)
        self.plane_combo = QComboBox(); self.plane_combo.addItems(["XY", "XZ", "YZ"])
        f.addRow("Plane:", self.plane_combo)
        self.sketch_toggle_btn = QPushButton("Start Sketch")
        self.sketch_toggle_btn.clicked.connect(self.toggle_sketch)
        f.addRow(self.sketch_toggle_btn)
        v.addWidget(g)

        g2 = QGroupBox("Tools"); f2 = QVBoxLayout(g2)
        row = QHBoxLayout()
        self.line_btn = QPushButton("Line"); self.line_btn.clicked.connect(lambda: self.set_tool('line'))
        self.poly_btn = QPushButton("Polyline"); self.poly_btn.clicked.connect(lambda: self.set_tool('poly'))
        row.addWidget(self.line_btn); row.addWidget(self.poly_btn); f2.addLayout(row)
        row2 = QHBoxLayout()
        self.circle_btn = QPushButton("Circle"); self.circle_btn.clicked.connect(lambda: self.set_tool('circle'))
        self.rect_btn = QPushButton("Rectangle"); self.rect_btn.clicked.connect(lambda: self.set_tool('rect'))
        row2.addWidget(self.circle_btn); row2.addWidget(self.rect_btn); f2.addLayout(row2)
        self.finish_poly_btn = QPushButton("✔ Finish Poly"); self.finish_poly_btn.clicked.connect(self.finish_polyline)
        f2.addWidget(self.finish_poly_btn)
        self.clear_sketch_btn = QPushButton("Clear Sketch"); self.clear_sketch_btn.clicked.connect(self.clear_sketch)
        f2.addWidget(self.clear_sketch_btn)
        for b in (self.line_btn, self.poly_btn, self.circle_btn, self.rect_btn,
                  self.finish_poly_btn, self.clear_sketch_btn):
            b.setEnabled(False)
        v.addWidget(g2)

        g3 = QGroupBox("Modify Sketch"); f3 = QVBoxLayout(g3)
        row = QHBoxLayout()
        b1 = QPushButton("Mirror X"); b1.clicked.connect(lambda: self.mirror_sketch('X'))
        b2 = QPushButton("Mirror Y"); b2.clicked.connect(lambda: self.mirror_sketch('Y'))
        row.addWidget(b1); row.addWidget(b2); f3.addLayout(row)
        row2 = QHBoxLayout()
        self.offset_sk_input = QLineEdit("5"); b3 = QPushButton("Offset")
        b3.clicked.connect(self.offset_sketch)
        row2.addWidget(QLabel("Dist:")); row2.addWidget(self.offset_sk_input); row2.addWidget(b3)
        f3.addLayout(row2)
        v.addWidget(g3)

        g4 = QGroupBox("Constraints"); f4 = QVBoxLayout(g4)
        row = QHBoxLayout()
        b1 = QPushButton("H"); b1.setToolTip("Horizontal")
        b2 = QPushButton("V"); b2.setToolTip("Vertical")
        b3 = QPushButton("⟂"); b3.setToolTip("Perpendicular")
        b4 = QPushButton("∥"); b4.setToolTip("Parallel")
        b1.clicked.connect(lambda: self.apply_constraint('horizontal'))
        b2.clicked.connect(lambda: self.apply_constraint('vertical'))
        b3.clicked.connect(lambda: self.apply_constraint('perpendicular'))
        b4.clicked.connect(lambda: self.apply_constraint('parallel'))
        for b in (b1, b2, b3, b4): row.addWidget(b)
        f4.addLayout(row)
        b5 = QPushButton("Coincident (nearest endpoints)")
        b5.clicked.connect(lambda: self.apply_constraint('coincident'))
        f4.addWidget(b5)
        self.constraint_status = QLabel("No constraints applied")
        self.constraint_status.setStyleSheet("color:#9aa6ba;font-size:11px;")
        f4.addWidget(self.constraint_status)
        v.addWidget(g4)

        g5 = QGroupBox("Dimension Tool"); f5 = QVBoxLayout(g5)
        self.dim_btn = QPushButton("📏 Dimension (D)")
        self.dim_btn.setCheckable(True)
        self.dim_btn.clicked.connect(self.toggle_dimension_mode)
        f5.addWidget(self.dim_btn)
        self.dim_label = QLabel("—")
        self.dim_label.setStyleSheet("color:#ffd166;font-family:monospace;padding:4px;background:#1a1a10;border-radius:4px;")
        f5.addWidget(self.dim_label)
        v.addWidget(g5)

        g6 = QGroupBox("Options"); f6 = QVBoxLayout(g6)
        self.hv_snap_cb = QCheckBox("Auto H/V Snap"); self.hv_snap_cb.setChecked(True)
        f6.addWidget(self.hv_snap_cb)
        self.show_dim_cb = QCheckBox("Show Dimensions"); self.show_dim_cb.setChecked(True)
        self.show_dim_cb.stateChanged.connect(self.on_dim_toggle); f6.addWidget(self.show_dim_cb)
        row = QHBoxLayout()
        self.grid_snap_input = QLineEdit("0")
        self.grid_snap_input.editingFinished.connect(self.update_grid_snap)
        row.addWidget(QLabel("Grid Snap:")); row.addWidget(self.grid_snap_input)
        f6.addLayout(row)
        v.addWidget(g6)

        g7 = QGroupBox("Create from Sketch"); f7 = QVBoxLayout(g7)
        row = QHBoxLayout()
        self.extrude_height = QLineEdit("20")
        row.addWidget(QLabel("Extrude H:")); row.addWidget(self.extrude_height)
        f7.addLayout(row)
        b = QPushButton("Extrude"); b.clicked.connect(self.extrude_sketch); f7.addWidget(b)
        row2 = QHBoxLayout()
        self.rev_axis = QComboBox(); self.rev_axis.addItems(["X", "Y", "Z"])
        self.rev_angle = QLineEdit("360")
        row2.addWidget(QLabel("Axis:")); row2.addWidget(self.rev_axis)
        row2.addWidget(QLabel("°:")); row2.addWidget(self.rev_angle)
        f7.addLayout(row2)
        b2 = QPushButton("Revolve"); b2.clicked.connect(self.revolve_sketch); f7.addWidget(b2)
        v.addWidget(g7)
        v.addStretch()
        return self._scroll_wrap(w)

    def _build_prop_model(self):
        w = QWidget(); v = QVBoxLayout(w); v.setContentsMargins(6, 6, 6, 6)
        g = QGroupBox("Add Primitive"); f = QFormLayout(g)
        self.prim_type = QComboBox(); self.prim_type.addItems(["Box", "Sphere", "Cone", "Cylinder"])
        f.addRow("Type:", self.prim_type)
        self.p1_input = QLineEdit("40"); f.addRow("L / Radius:", self.p1_input)
        self.p2_input = QLineEdit("40"); f.addRow("W / Height:", self.p2_input)
        self.p3_input = QLineEdit("40"); f.addRow("H / Top R:", self.p3_input)
        self.box_x = QLineEdit("0"); f.addRow("Pos X:", self.box_x)
        self.box_y = QLineEdit("0"); f.addRow("Pos Y:", self.box_y)
        self.box_z = QLineEdit("0"); f.addRow("Pos Z:", self.box_z)
        b = QPushButton("Add to Scene"); b.clicked.connect(self.add_primitive); f.addRow(b)
        v.addWidget(g)

        g2 = QGroupBox("Transform Active"); f2 = QVBoxLayout(g2)
        row = QHBoxLayout()
        self.move_x = QLineEdit("10"); self.move_y = QLineEdit("0"); self.move_z = QLineEdit("0")
        row.addWidget(QLabel("ΔX:")); row.addWidget(self.move_x)
        row.addWidget(QLabel("ΔY:")); row.addWidget(self.move_y)
        row.addWidget(QLabel("ΔZ:")); row.addWidget(self.move_z)
        f2.addLayout(row)
        b = QPushButton("Move"); b.clicked.connect(self.transform_move); f2.addWidget(b)
        row2 = QHBoxLayout()
        self.rot_axis = QComboBox(); self.rot_axis.addItems(["X", "Y", "Z"])
        self.rot_angle = QLineEdit("45")
        row2.addWidget(QLabel("Axis:")); row2.addWidget(self.rot_axis)
        row2.addWidget(QLabel("°:")); row2.addWidget(self.rot_angle)
        f2.addLayout(row2)
        b = QPushButton("Rotate"); b.clicked.connect(self.transform_rotate); f2.addWidget(b)
        row3 = QHBoxLayout()
        self.scale_factor = QLineEdit("1.5")
        row3.addWidget(QLabel("Scale:")); row3.addWidget(self.scale_factor)
        f2.addLayout(row3)
        b = QPushButton("Uniform Scale"); b.clicked.connect(self.transform_scale); f2.addWidget(b)
        v.addWidget(g2)

        g2b = QGroupBox("Non-uniform Scale"); f2b = QVBoxLayout(g2b)
        row = QHBoxLayout()
        self.scale_x = QLineEdit("1.0"); self.scale_y = QLineEdit("1.0"); self.scale_z = QLineEdit("1.0")
        row.addWidget(QLabel("X:")); row.addWidget(self.scale_x)
        row.addWidget(QLabel("Y:")); row.addWidget(self.scale_y)
        row.addWidget(QLabel("Z:")); row.addWidget(self.scale_z)
        f2b.addLayout(row)
        b = QPushButton("Apply Scale"); b.clicked.connect(self.transform_scale_xyz)
        f2b.addWidget(b)
        v.addWidget(g2b)

        g3 = QGroupBox("Boolean (last 2)"); f3 = QVBoxLayout(g3)
        row = QHBoxLayout()
        b1 = QPushButton("Union"); b1.clicked.connect(lambda: self.boolean_op('union'))
        b2 = QPushButton("Cut"); b2.clicked.connect(lambda: self.boolean_op('cut'))
        b3 = QPushButton("Intersect"); b3.clicked.connect(lambda: self.boolean_op('intersect'))
        row.addWidget(b1); row.addWidget(b2); row.addWidget(b3); f3.addLayout(row)
        v.addWidget(g3)

        g4 = QGroupBox("Detail"); f4 = QVBoxLayout(g4)
        row = QHBoxLayout()
        self.fillet_radius = QLineEdit("3")
        row.addWidget(QLabel("R / D:")); row.addWidget(self.fillet_radius)
        f4.addLayout(row)
        row2 = QHBoxLayout()
        b1 = QPushButton("Fillet"); b1.clicked.connect(self.apply_fillet)
        b2 = QPushButton("Chamfer"); b2.clicked.connect(self.apply_chamfer)
        row2.addWidget(b1); row2.addWidget(b2); f4.addLayout(row2)
        row3 = QHBoxLayout()
        self.hole_x = QLineEdit("0"); self.hole_y = QLineEdit("0")
        self.hole_d = QLineEdit("10"); self.hole_depth = QLineEdit("50")
        row3.addWidget(QLabel("X:")); row3.addWidget(self.hole_x)
        row3.addWidget(QLabel("Y:")); row3.addWidget(self.hole_y)
        f4.addLayout(row3)
        row4 = QHBoxLayout()
        row4.addWidget(QLabel("Ø:")); row4.addWidget(self.hole_d)
        row4.addWidget(QLabel("D:")); row4.addWidget(self.hole_depth)
        f4.addLayout(row4)
        b = QPushButton("Cut Hole"); b.clicked.connect(self.cut_hole); f4.addWidget(b)
        row5 = QHBoxLayout()
        self.shell_thick = QLineEdit("2")
        row5.addWidget(QLabel("Shell T:")); row5.addWidget(self.shell_thick)
        f4.addLayout(row5)
        b = QPushButton("Shell (open top)"); b.clicked.connect(self.shell_body); f4.addWidget(b)
        v.addWidget(g4)

        g5 = QGroupBox("Pattern"); f5 = QVBoxLayout(g5)
        row = QHBoxLayout()
        self.pattern_count = QLineEdit("4"); self.pattern_spacing = QLineEdit("50")
        row.addWidget(QLabel("N:")); row.addWidget(self.pattern_count)
        row.addWidget(QLabel("S:")); row.addWidget(self.pattern_spacing)
        f5.addLayout(row)
        b = QPushButton("Linear Pattern"); b.clicked.connect(self.linear_pattern); f5.addWidget(b)
        row2 = QHBoxLayout()
        self.circ_axis = QComboBox(); self.circ_axis.addItems(["X", "Y", "Z"])
        self.circ_count = QLineEdit("6"); self.circ_angle = QLineEdit("360")
        row2.addWidget(QLabel("Ax:")); row2.addWidget(self.circ_axis)
        row2.addWidget(QLabel("N:")); row2.addWidget(self.circ_count)
        row2.addWidget(QLabel("°:")); row2.addWidget(self.circ_angle)
        f5.addLayout(row2)
        b = QPushButton("Circular Pattern"); b.clicked.connect(self.circular_pattern); f5.addWidget(b)
        v.addWidget(g5)
        v.addStretch()
        return self._scroll_wrap(w)

    def _build_prop_assembly(self):
        w = QWidget(); v = QVBoxLayout(w); v.setContentsMargins(6, 6, 6, 6)

        g6 = QGroupBox("🔩 Bolt Wizard"); f6 = QVBoxLayout(g6)
        f6.addWidget(QLabel("Auto bolt + nut + washer + plate"))
        self.wiz_size = QComboBox(); self.wiz_size.addItems(list(BOLT_METRIC.keys()))
        self.wiz_size.setCurrentText("M8")
        f6.addWidget(QLabel("Size:")); f6.addWidget(self.wiz_size)
        row = QHBoxLayout()
        self.wiz_length = QLineEdit("30"); self.wiz_plate_thick = QLineEdit("10")
        row.addWidget(QLabel("Bolt L:")); row.addWidget(self.wiz_length)
        row.addWidget(QLabel("Plate T:")); row.addWidget(self.wiz_plate_thick)
        f6.addLayout(row)
        b = QPushButton("⚡ Create Bolt Assembly"); b.clicked.connect(self.bolt_wizard)
        f6.addWidget(b)
        v.addWidget(g6)

        g = QGroupBox("Mates (active ↔ previous)"); f = QVBoxLayout(g)
        row = QHBoxLayout()
        b1 = QPushButton("Coincident"); b1.clicked.connect(lambda: self.apply_mate('coincident'))
        b2 = QPushButton("Concentric"); b2.clicked.connect(lambda: self.apply_mate('concentric'))
        b3 = QPushButton("Distance"); b3.clicked.connect(lambda: self.apply_mate('distance'))
        row.addWidget(b1); row.addWidget(b2); row.addWidget(b3); f.addLayout(row)
        self.mate_distance_val = QLineEdit("10")
        row2 = QHBoxLayout(); row2.addWidget(QLabel("Distance:")); row2.addWidget(self.mate_distance_val)
        f.addLayout(row2)
        v.addWidget(g)

        g2 = QGroupBox("Align"); f2 = QVBoxLayout(g2)
        row = QHBoxLayout()
        for ax in ['X', 'Y', 'Z']:
            b = QPushButton(f"Align {ax}"); b.clicked.connect(lambda _, a=ax: self.align_bodies(a))
            row.addWidget(b)
        f2.addLayout(row)
        b = QPushButton("Align All Axes"); b.clicked.connect(lambda: self.align_bodies('ALL'))
        f2.addWidget(b)
        v.addWidget(g2)

        g5 = QGroupBox("Exploded View"); f5 = QVBoxLayout(g5)
        self.explode_dist = QLineEdit("40")
        row = QHBoxLayout(); row.addWidget(QLabel("Distance:")); row.addWidget(self.explode_dist)
        f5.addLayout(row)
        b = QPushButton("Toggle Exploded"); b.clicked.connect(self.toggle_explode); f5.addWidget(b)
        v.addWidget(g5)

        g3 = QGroupBox("Standard Parts"); f3 = QVBoxLayout(g3)
        self.std_type = QComboBox(); self.std_type.addItems(["Bolt", "Nut", "Washer", "Bearing"])
        self.std_size = QComboBox(); self.std_size.addItems(list(BOLT_METRIC.keys()))
        self.std_type.currentTextChanged.connect(self._on_std_type_change)
        self.std_length = QLineEdit("20")
        f3.addWidget(QLabel("Type:")); f3.addWidget(self.std_type)
        f3.addWidget(QLabel("Size:")); f3.addWidget(self.std_size)
        f3.addWidget(QLabel("Length (bolt):")); f3.addWidget(self.std_length)
        b = QPushButton("Add Part"); b.clicked.connect(self.add_standard_part); f3.addWidget(b)
        v.addWidget(g3)

        g4 = QGroupBox("Gear / Helix / Thread"); f4 = QVBoxLayout(g4)
        row = QHBoxLayout()
        self.gear_module = QLineEdit("2"); self.gear_teeth = QLineEdit("20")
        row.addWidget(QLabel("M:")); row.addWidget(self.gear_module)
        row.addWidget(QLabel("Z:")); row.addWidget(self.gear_teeth)
        f4.addLayout(row)
        row2 = QHBoxLayout()
        self.gear_width = QLineEdit("8"); self.gear_bore = QLineEdit("6")
        row2.addWidget(QLabel("W:")); row2.addWidget(self.gear_width)
        row2.addWidget(QLabel("Bore:")); row2.addWidget(self.gear_bore)
        f4.addLayout(row2)
        b = QPushButton("Generate Gear"); b.clicked.connect(self.generate_gear); f4.addWidget(b)
        row3 = QHBoxLayout()
        self.thread_size = QComboBox(); self.thread_size.addItems(list(BOLT_METRIC.keys()))
        self.thread_len = QLineEdit("20")
        row3.addWidget(QLabel("Thread:")); row3.addWidget(self.thread_size)
        row3.addWidget(QLabel("L:")); row3.addWidget(self.thread_len)
        f4.addLayout(row3)
        b = QPushButton("Cut Threads on Active"); b.clicked.connect(self.cut_threads); f4.addWidget(b)
        v.addWidget(g4)

        v.addStretch()
        return self._scroll_wrap(w)

    def _on_std_type_change(self, kind):
        self.std_size.clear()
        if kind == "Bolt": self.std_size.addItems(list(BOLT_METRIC.keys()))
        elif kind == "Nut": self.std_size.addItems(list(NUT_METRIC.keys()))
        elif kind == "Washer": self.std_size.addItems(list(WASHER_METRIC.keys()))
        else: self.std_size.addItems(list(BEARING_METRIC.keys()))

    def _build_prop_drawing(self):
        w = QWidget(); v = QVBoxLayout(w); v.setContentsMargins(6, 6, 6, 6)
        g = QGroupBox("Drawing Views"); f = QVBoxLayout(g)
        b = QPushButton("📐 4-View with Dimensions"); b.clicked.connect(self.export_4view_drawing); f.addWidget(b)
        b = QPushButton("📸 Screenshot Current View"); b.clicked.connect(self.screenshot_viewport); f.addWidget(b)
        b = QPushButton("📐 Sketch DXF"); b.clicked.connect(self.export_sketch_dxf); f.addWidget(b)
        v.addWidget(g)
        g2 = QGroupBox("Section View"); f2 = QVBoxLayout(g2)
        self.section_cb = QCheckBox("Enable Section")
        self.section_cb.stateChanged.connect(self.on_section_toggle); f2.addWidget(self.section_cb)
        row = QHBoxLayout()
        self.section_axis_cb = QComboBox(); self.section_axis_cb.addItems(["X", "Y", "Z"])
        self.section_axis_cb.currentTextChanged.connect(self.on_section_axis)
        row.addWidget(QLabel("Axis:")); row.addWidget(self.section_axis_cb)
        f2.addLayout(row)
        self.section_slider = QSlider(Qt.Horizontal); self.section_slider.setRange(-100, 100)
        self.section_slider.valueChanged.connect(self.on_section_slide)
        f2.addWidget(QLabel("Pos:")); f2.addWidget(self.section_slider)
        v.addWidget(g2)
        g3 = QGroupBox("Export Quality"); f3 = QVBoxLayout(g3)
        row = QHBoxLayout()
        row.addWidget(QLabel("STL Quality:"))
        self.stl_quality_cb = QComboBox(); self.stl_quality_cb.addItems(list(STL_QUALITY.keys()))
        self.stl_quality_cb.setCurrentText("Medium")
        row.addWidget(self.stl_quality_cb)
        f3.addLayout(row)
        v.addWidget(g3)
        g4 = QGroupBox("Web / Docs"); f4 = QVBoxLayout(g4)
        b = QPushButton("🌐 WebGL Viewer (HTML)"); b.clicked.connect(self.export_webgl_viewer); f4.addWidget(b)
        b = QPushButton("📊 Export BOM (CSV)"); b.clicked.connect(self.export_bom); f4.addWidget(b)
        b = QPushButton("⚖ Mass Report (CSV)"); b.clicked.connect(self.export_mass_report); f4.addWidget(b)
        b = QPushButton("📦 Batch STL Export"); b.clicked.connect(self.batch_stl_export); f4.addWidget(b)
        v.addWidget(g4)
        v.addStretch()
        return self._scroll_wrap(w)

    def _build_prop_tools(self):
        w = QWidget(); v = QVBoxLayout(w); v.setContentsMargins(6, 6, 6, 6)
        g = QGroupBox("Measure"); f = QVBoxLayout(g)
        b = QPushButton("📏 Measure Active Body"); b.clicked.connect(self.measure_active); f.addWidget(b)
        b = QPushButton("📏 Distance (2 points)"); b.clicked.connect(self.toggle_distance_measure); f.addWidget(b)
        self.measure_label = QLabel("—"); self.measure_label.setWordWrap(True)
        self.measure_label.setStyleSheet("color:#a0e0a0;padding:6px;background:#141a14;border-radius:6px;font-family:monospace;")
        f.addWidget(self.measure_label)
        v.addWidget(g)

        g2 = QGroupBox("Mass / Material"); f2 = QVBoxLayout(g2)
        self.material_cb = QComboBox(); self.material_cb.addItems(list(MATERIALS.keys()))
        f2.addWidget(QLabel("Material:")); f2.addWidget(self.material_cb)
        self.custom_density = QLineEdit("")
        f2.addWidget(QLabel("Custom density (g/cm³):")); f2.addWidget(self.custom_density)
        b = QPushButton("⚖ Calculate Mass"); b.clicked.connect(self.calculate_mass); f2.addWidget(b)
        self.mass_label = QLabel("—"); self.mass_label.setWordWrap(True)
        self.mass_label.setStyleSheet("color:#ffd166;padding:6px;background:#1a1a10;border-radius:6px;font-family:monospace;")
        f2.addWidget(self.mass_label)
        v.addWidget(g2)

        g6 = QGroupBox("Center of Mass"); f6 = QVBoxLayout(g6)
        b = QPushButton("Show COM + Moments"); b.clicked.connect(self.show_center_of_mass); f6.addWidget(b)
        b2 = QPushButton("Hide COM"); b2.clicked.connect(self.hide_center_of_mass); f6.addWidget(b2)
        self.com_label = QLabel("—"); self.com_label.setWordWrap(True)
        self.com_label.setStyleSheet("color:#c0a0ff;font-family:monospace;padding:6px;background:#15102a;border-radius:6px;")
        f6.addWidget(self.com_label)
        v.addWidget(g6)

        g3 = QGroupBox("QC Check"); f3 = QVBoxLayout(g3)
        b = QPushButton("⚠ Interference (all)"); b.clicked.connect(self.check_interference_all); f3.addWidget(b)
        b = QPushButton("📐 Min Clearance (2)"); b.clicked.connect(self.check_clearance_2); f3.addWidget(b)
        self.qc_label = QLabel("—"); self.qc_label.setWordWrap(True)
        self.qc_label.setStyleSheet("color:#ffcc88;padding:6px;background:#1a1208;border-radius:6px;font-family:monospace;")
        f3.addWidget(self.qc_label)
        v.addWidget(g3)

        g7 = QGroupBox("Camera"); f7 = QVBoxLayout(g7)
        self.persp_btn = QPushButton("Toggle Perspective / Ortho")
        self.persp_btn.setCheckable(True)
        self.persp_btn.clicked.connect(self.toggle_perspective)
        f7.addWidget(self.persp_btn)
        v.addWidget(g7)

        g5 = QGroupBox("Animation"); f5 = QVBoxLayout(g5)
        self.anim_speed = QLineEdit("30")
        row = QHBoxLayout(); row.addWidget(QLabel("Speed:")); row.addWidget(self.anim_speed)
        f5.addLayout(row)
        b = QPushButton("▶ Turntable Play/Stop"); b.clicked.connect(self.toggle_animation); f5.addWidget(b)
        v.addWidget(g5)
        v.addStretch()
        return self._scroll_wrap(w)

    # ================= RIBBON =================
    def _build_ribbon(self):
        dock = QDockWidget("Ribbon", self)
        dock.setAllowedAreas(Qt.TopDockWidgetArea)
        dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.ribbon_tabs = QTabWidget()
        self.ribbon_tabs.setDocumentMode(True)
        self.ribbon_tabs.setFixedHeight(110)
        self.ribbon_tabs.currentChanged.connect(self._on_ribbon_change)
        self.ribbon_tabs.addTab(self._ribbon_home(), "🏠 Home")
        self.ribbon_tabs.addTab(self._ribbon_sketch(), "✏ Sketch")
        self.ribbon_tabs.addTab(self._ribbon_model(), "🧊 3D Model")
        self.ribbon_tabs.addTab(self._ribbon_assembly(), "🔩 Assembly")
        self.ribbon_tabs.addTab(self._ribbon_drawing(), "📐 Drawing")
        self.ribbon_tabs.addTab(self._ribbon_tools(), "🔧 Tools")
        dock.setWidget(self.ribbon_tabs)
        self.addDockWidget(Qt.TopDockWidgetArea, dock)

    def _ribbon_btn(self, icon, label, tooltip, slot):
        b = QToolButton()
        b.setText(f"{icon}\n{label}")
        b.setToolTip(tooltip)
        b.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        b.setFixedSize(84, 84)
        b.setFont(QFont("Segoe UI", 9))
        b.setStyleSheet("""
            QToolButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #232b38, stop:1 #1a212c);
                color: #e0e6f0;
                border: 1px solid #2b3240;
                border-radius: 6px;
                padding: 4px;
                font-weight: 500;
            }
            QToolButton:hover {
                background: #2c3648;
                border-color: #70a7ff;
                color: #ffffff;
            }
            QToolButton:pressed {
                background: #70a7ff;
                color: #0d1627;
            }
        """)
        b.clicked.connect(slot)
        return b

    def _ribbon_group(self, title, buttons):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(10, 6, 10, 4)
        v.setSpacing(4)
        row = QHBoxLayout()
        row.setSpacing(4)
        for b in buttons:
            row.addWidget(b)
        v.addLayout(row)
        lbl = QLabel(title.upper())
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(
            "color: #7a8699; font-size: 9px; font-weight: 700; "
            "letter-spacing: 1px; padding-top: 2px;"
        )
        v.addWidget(lbl)
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("background: #2b3240; max-width: 1px; margin: 8px 0;")
        wrap = QWidget()
        h = QHBoxLayout(wrap)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)
        h.addWidget(w)
        h.addWidget(sep)
        return wrap

    def _ribbon_group(self, title, buttons):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(10, 6, 10, 4)
        v.setSpacing(4)
        row = QHBoxLayout()
        row.setSpacing(4)
        for b in buttons:
            row.addWidget(b)
        v.addLayout(row)
        lbl = QLabel(title.upper())
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(
            "color: #7a8699; font-size: 9px; font-weight: 700; "
            "letter-spacing: 1px; padding-top: 2px;"
        )
        v.addWidget(lbl)
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("background: #2b3240; max-width: 1px; margin: 8px 0;")
        wrap = QWidget()
        h = QHBoxLayout(wrap)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)
        h.addWidget(w)
        h.addWidget(sep)
        return wrap
    
    def _ribbon_home(self):
        w = QWidget(); h = QHBoxLayout(w); h.setContentsMargins(4, 4, 4, 4); h.setSpacing(0)
        h.addWidget(self._ribbon_group("File", [
            self._ribbon_btn("📄", "New", "New project (Ctrl+N)", self.clear_scene),
            self._ribbon_btn("📂", "Open", "Open project (Ctrl+O)", self.open_project),
            self._ribbon_btn("💾", "Save", "Save project (Ctrl+S)", self.save_project),
        ]))
        h.addWidget(self._ribbon_group("Edit", [
            self._ribbon_btn("↶", "Undo", "Undo (Ctrl+Z)", self.undo),
            self._ribbon_btn("↷", "Redo", "Redo (Ctrl+Y)", self.redo),
            self._ribbon_btn("🗑", "Delete", "Delete active (Del)", self.delete_active_body),
        ]))
        h.addWidget(self._ribbon_group("Primitives", [
            self._ribbon_btn("⬛", "Box", "Create Box", lambda: self._quick_prim("Box")),
            self._ribbon_btn("⚪", "Sphere", "Create Sphere", lambda: self._quick_prim("Sphere")),
            self._ribbon_btn("◯", "Cylinder", "Create Cylinder", lambda: self._quick_prim("Cylinder")),
            self._ribbon_btn("△", "Cone", "Create Cone", lambda: self._quick_prim("Cone")),
        ]))
        h.addWidget(self._ribbon_group("Views", [
            self._ribbon_btn("▣", "Front", "Front view (F)", lambda: self.plotter.view_xz()),
            self._ribbon_btn("⬓", "Top", "Top view (T)", lambda: self.plotter.view_xy()),
            self._ribbon_btn("◨", "Right", "Right view (R)", lambda: self.plotter.view_yz()),
            self._ribbon_btn("◇", "Iso", "Isometric view (I)", lambda: self.plotter.view_isometric()),
        ]))
        h.addWidget(self._ribbon_group("Display", [
            self._ribbon_btn("▦", "Wireframe", "Toggle wireframe", self.toggle_wireframe),
            self._ribbon_btn("▢", "BBox", "Show bounding boxes", self._toggle_bbox),
            self._ribbon_btn("✂", "Section", "Section view", self._toggle_section),
            self._ribbon_btn("◱", "Persp", "Perspective camera", self.toggle_perspective),
        ]))
        h.addStretch(); return w


    def _ribbon_sketch(self):
        w = QWidget(); h = QHBoxLayout(w); h.setContentsMargins(4, 4, 4, 4); h.setSpacing(0)
        h.addWidget(self._ribbon_group("Mode", [
            self._ribbon_btn("✏", "Sketch", "Start / Finish sketch", self.toggle_sketch),
            self._ribbon_btn("🗑", "Clear", "Clear all sketch", self.clear_sketch),
        ]))
        h.addWidget(self._ribbon_group("Draw", [
            self._ribbon_btn("╱", "Line", "Draw line", lambda: self.set_tool('line')),
            self._ribbon_btn("↝", "Polyline", "Draw polyline", lambda: self.set_tool('poly')),
            self._ribbon_btn("◯", "Circle", "Draw circle", lambda: self.set_tool('circle')),
            self._ribbon_btn("▭", "Rectangle", "Draw rectangle", lambda: self.set_tool('rect')),
            self._ribbon_btn("✔", "Finish", "Finish polyline", self.finish_polyline),
        ]))
        h.addWidget(self._ribbon_group("Constrain", [
            self._ribbon_btn("H", "Horizontal", "Make horizontal", lambda: self.apply_constraint('horizontal')),
            self._ribbon_btn("V", "Vertical", "Make vertical", lambda: self.apply_constraint('vertical')),
            self._ribbon_btn("⟂", "Perp", "Perpendicular", lambda: self.apply_constraint('perpendicular')),
            self._ribbon_btn("∥", "Parallel", "Parallel lines", lambda: self.apply_constraint('parallel')),
            self._ribbon_btn("⊙", "Coincident", "Coincident endpoints", lambda: self.apply_constraint('coincident')),
        ]))
        h.addWidget(self._ribbon_group("Measure", [
            self._ribbon_btn("📏", "Dimension", "Dimension tool (D)", self.toggle_dimension_mode),
        ]))
        h.addWidget(self._ribbon_group("Create 3D", [
            self._ribbon_btn("⬆", "Extrude", "Extrude sketch", self.extrude_sketch),
            self._ribbon_btn("⟳", "Revolve", "Revolve sketch", self.revolve_sketch),
            self._ribbon_btn("🔀", "Loft", "Loft 2 sketches", self.loft_sketches),
            self._ribbon_btn("🌀", "Sweep", "Sweep along path", self.sweep_sketch),
        ]))
        h.addStretch(); return w

    def _ribbon_model(self):
        w = QWidget(); h = QHBoxLayout(w); h.setContentsMargins(4, 4, 4, 4); h.setSpacing(0)
        h.addWidget(self._ribbon_group("Primitives", [
            self._ribbon_btn("⬛", "Box", "Add Box", lambda: self._quick_prim("Box")),
            self._ribbon_btn("⚪", "Sphere", "Add Sphere", lambda: self._quick_prim("Sphere")),
            self._ribbon_btn("◯", "Cylinder", "Add Cylinder", lambda: self._quick_prim("Cylinder")),
            self._ribbon_btn("△", "Cone", "Add Cone", lambda: self._quick_prim("Cone")),
        ]))
        h.addWidget(self._ribbon_group("Boolean", [
            self._ribbon_btn("➕", "Union", "Union last 2", lambda: self.boolean_op('union')),
            self._ribbon_btn("➖", "Cut", "Cut last 2", lambda: self.boolean_op('cut')),
            self._ribbon_btn("∩", "Intersect", "Intersect last 2", lambda: self.boolean_op('intersect')),
        ]))
        h.addWidget(self._ribbon_group("Detail", [
            self._ribbon_btn("⌐", "Fillet", "Fillet edges", self.apply_fillet),
            self._ribbon_btn("▷", "Chamfer", "Chamfer edges", self.apply_chamfer),
            self._ribbon_btn("◎", "Hole", "Cut hole", self.cut_hole),
            self._ribbon_btn("◫", "Shell", "Shell body", self.shell_body),
        ]))
        h.addWidget(self._ribbon_group("Pattern", [
            self._ribbon_btn("⋯", "Linear", "Linear pattern", self.linear_pattern),
            self._ribbon_btn("⟳", "Circular", "Circular pattern", self.circular_pattern),
            self._ribbon_btn("⇋", "Mirror", "Mirror body", self.mirror_body),
        ]))
        h.addWidget(self._ribbon_group("Transform", [
            self._ribbon_btn("↔", "Move", "Move body", self.transform_move),
            self._ribbon_btn("⟳", "Rotate", "Rotate body", self.transform_rotate),
            self._ribbon_btn("⤢", "Scale", "Uniform scale", self.transform_scale),
            self._ribbon_btn("⬚", "Scale XYZ", "Non-uniform scale", self.transform_scale_xyz),
        ]))
        h.addStretch(); return w

    def _ribbon_assembly(self):
        w = QWidget(); h = QHBoxLayout(w); h.setContentsMargins(4, 4, 4, 4); h.setSpacing(0)
        h.addWidget(self._ribbon_group("Wizard", [
            self._ribbon_btn("⚡", "Bolt Assembly", "Auto bolt+nut+washer+plate", self.bolt_wizard),
        ]))
        h.addWidget(self._ribbon_group("Standard Parts", [
            self._ribbon_btn("🔩", "Bolt", "Add Bolt", lambda: self._quick_std("Bolt")),
            self._ribbon_btn("🔘", "Nut", "Add Nut", lambda: self._quick_std("Nut")),
            self._ribbon_btn("⭕", "Washer", "Add Washer", lambda: self._quick_std("Washer")),
            self._ribbon_btn("◉", "Bearing", "Add Bearing", lambda: self._quick_std("Bearing")),
        ]))
        h.addWidget(self._ribbon_group("Feature Parts", [
            self._ribbon_btn("⚙", "Gear", "Generate gear", self.generate_gear),
            self._ribbon_btn("🌀", "Helix", "Create spring", self.create_helix),
            self._ribbon_btn("🔄", "Thread", "Cut threads", self.cut_threads),
            self._ribbon_btn("T", "3D Text", "Add text", self.add_text),
        ]))
        h.addWidget(self._ribbon_group("Mates", [
            self._ribbon_btn("≡", "Coincident", "Coincident mate", lambda: self.apply_mate('coincident')),
            self._ribbon_btn("◎", "Concentric", "Concentric mate", lambda: self.apply_mate('concentric')),
            self._ribbon_btn("↔", "Distance", "Distance mate", lambda: self.apply_mate('distance')),
        ]))
        h.addWidget(self._ribbon_group("Align", [
            self._ribbon_btn("↤", "Align X", "Align X", lambda: self.align_bodies('X')),
            self._ribbon_btn("↥", "Align Y", "Align Y", lambda: self.align_bodies('Y')),
            self._ribbon_btn("↦", "Align Z", "Align Z", lambda: self.align_bodies('Z')),
            self._ribbon_btn("✦", "Align All", "Align all axes", lambda: self.align_bodies('ALL')),
        ]))
        h.addWidget(self._ribbon_group("Explode", [
            self._ribbon_btn("💥", "Explode", "Toggle exploded view", self.toggle_explode),
        ]))
        h.addStretch(); return w

    def _ribbon_drawing(self):
        w = QWidget(); h = QHBoxLayout(w); h.setContentsMargins(4, 4, 4, 4); h.setSpacing(0)
        h.addWidget(self._ribbon_group("Views", [
            self._ribbon_btn("📐", "4-View", "4-view drawing PNG", self.export_4view_drawing),
            self._ribbon_btn("📸", "Screenshot", "Screenshot viewport", self.screenshot_viewport),
            self._ribbon_btn("📐", "DXF", "Sketch DXF export", self.export_sketch_dxf),
        ]))
        h.addWidget(self._ribbon_group("Export", [
            self._ribbon_btn("📦", "STL", "Export STL", self.export_stl),
            self._ribbon_btn("📄", "STEP", "Export STEP", self.export_step),
            self._ribbon_btn("📦", "Batch STL", "Batch export all bodies", self.batch_stl_export),
        ]))
        h.addWidget(self._ribbon_group("Document", [
            self._ribbon_btn("🌐", "WebGL", "HTML 3D viewer", self.export_webgl_viewer),
            self._ribbon_btn("📊", "BOM", "Bill of Materials CSV", self.export_bom),
            self._ribbon_btn("⚖", "Mass Report", "Full mass report CSV", self.export_mass_report),
        ]))
        h.addStretch(); return w

    def _ribbon_tools(self):
        w = QWidget(); h = QHBoxLayout(w); h.setContentsMargins(4, 4, 4, 4); h.setSpacing(0)
        h.addWidget(self._ribbon_group("Measure", [
            self._ribbon_btn("📏", "Body", "Measure active body", self.measure_active),
            self._ribbon_btn("📐", "Distance", "Distance 2 points (M)", self.toggle_distance_measure),
            self._ribbon_btn("⚖", "Mass", "Calculate mass", self.calculate_mass),
            self._ribbon_btn("⚫", "COM", "Center of mass", self.show_center_of_mass),
        ]))
        h.addWidget(self._ribbon_group("QC Check", [
            self._ribbon_btn("⚠", "Interference", "Check overlaps", self.check_interference_all),
            self._ribbon_btn("📏", "Clearance", "Min clearance", self.check_clearance_2),
            self._ribbon_btn("ℹ", "Info", "All bodies info", self.show_all_info),
        ]))
        h.addWidget(self._ribbon_group("Camera", [
            self._ribbon_btn("◱", "Perspective", "Toggle Persp/Ortho", self.toggle_perspective),
        ]))
        h.addWidget(self._ribbon_group("Animation", [
            self._ribbon_btn("▶", "Turntable", "Play/Stop animation", self.toggle_animation),
        ]))
        h.addStretch(); return w

    def _ribbon_tools(self):
        w = QWidget(); h = QHBoxLayout(w); h.setContentsMargins(4, 4, 4, 4); h.setSpacing(0)
        h.addWidget(self._ribbon_group("Measure", [
            self._ribbon_btn("📏", "Body", "Measure", self.measure_active),
            self._ribbon_btn("📐", "Dist", "Distance", self.toggle_distance_measure),
            self._ribbon_btn("⚖", "Mass", "Mass", self.calculate_mass),
            self._ribbon_btn("⚫", "COM", "Center of Mass", self.show_center_of_mass),
        ]))
        h.addWidget(self._ribbon_group("QC", [
            self._ribbon_btn("⚠", "Clash", "Interference", self.check_interference_all),
            self._ribbon_btn("📏", "Clear", "Clearance", self.check_clearance_2),
            self._ribbon_btn("ℹ", "Info", "All Info", self.show_all_info),
        ]))
        h.addWidget(self._ribbon_group("Camera", [
            self._ribbon_btn("◱", "Persp", "Perspective", self.toggle_perspective),
        ]))
        h.addWidget(self._ribbon_group("Animation", [
            self._ribbon_btn("▶", "Play", "Turntable", self.toggle_animation),
        ]))
        h.addStretch(); return w

    def _on_ribbon_change(self, idx):
        self.prop_stack.setCurrentIndex(idx)

    # ================= STATUS BAR =================
    def _build_status_bar(self):
        sb = QStatusBar(); self.setStatusBar(sb)
        self.status_label = QLabel("Ready")
        sb.addWidget(self.status_label, 1)
        self.mode_label = QLabel("Mode: Model")
        self.mode_label.setStyleSheet("color:#70a7ff;padding:0 10px;")
        sb.addPermanentWidget(self.mode_label)
        self.coords_label = QLabel("X: --  Y: --  Z: --")
        self.coords_label.setStyleSheet("color:#a0e0a0;font-family:monospace;padding:0 10px;")
        sb.addPermanentWidget(self.coords_label)
        self.bodies_label = QLabel("Bodies: 0")
        self.bodies_label.setStyleSheet("padding:0 10px;")
        sb.addPermanentWidget(self.bodies_label)

    def _set_status(self, msg):
        self.status_label.setText(msg)
        try: self.bodies_label.setText(f"Bodies: {len(self.bodies)}")
        except Exception: pass

    # ================= BODY PICKING =================
    def _enable_body_picking(self):
        if self.sketch_mode or self.measure_mode or self.dimension_mode:
            return
        try:
            self.plotter.disable_picking()
        except Exception:
            pass
        try:
            self.plotter.enable_mesh_picking(
                callback=self._on_mesh_picked,
                show_message=False, show=False,
                left_clicking=True, use_actor=True,
                pickable_window=False,
            )
        except Exception as e:
            print(f"Picking enable failed: {e}")

    def _on_mesh_picked(self, actor):
        try:
            if actor is None:
                return
            idx = self._body_actors.get(actor, None)
            if idx is None:
                # Try matching by name pattern as fallback
                name = ""
                if hasattr(actor, "GetObjectName"):
                    name = actor.GetObjectName() or ""
                if name.startswith("forge_body_"):
                    try: idx = int(name.replace("forge_body_", ""))
                    except Exception: idx = None
            if idx is None or not (0 <= idx < len(self.bodies)):
                return
            self.active_index = idx
            self.redraw_scene()
            p = self.body_props[idx]
            self._set_status(f"Selected: {p.get('name', f'Body {idx+1}')}")
        except Exception as e:
            print(f"Pick error: {e}")

    # ================= SHORTCUTS =================
    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self.clear_scene)
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.save_project)
        QShortcut(QKeySequence("Ctrl+O"), self, activated=self.open_project)
        QShortcut(QKeySequence("Ctrl+I"), self, activated=self.import_step)
        QShortcut(QKeySequence("Ctrl+Z"), self, activated=self.undo)
        QShortcut(QKeySequence("Ctrl+Y"), self, activated=self.redo)
        QShortcut(QKeySequence("Delete"), self, activated=self.delete_active_body)
        QShortcut(QKeySequence("F"), self, activated=lambda: self.plotter.view_xz())
        QShortcut(QKeySequence("T"), self, activated=lambda: self.plotter.view_xy())
        QShortcut(QKeySequence("R"), self, activated=lambda: self.plotter.view_yz())
        QShortcut(QKeySequence("I"), self, activated=lambda: self.plotter.view_isometric())
        QShortcut(QKeySequence("M"), self, activated=self.toggle_distance_measure)
        QShortcut(QKeySequence("D"), self, activated=self._toggle_dim_shortcut)
        QShortcut(QKeySequence("Space"), self, activated=self.toggle_animation)

    def _toggle_dim_shortcut(self):
        self.dim_btn.setChecked(not self.dim_btn.isChecked())
        self.toggle_dimension_mode()

    # ================= FEATURE TREE =================
    def log_feature(self, name, icon="✦"):
        self.feature_history.append({"name": name, "icon": icon})
        try:
            self.feature_list.addItem(QListWidgetItem(f"{icon}  {name}"))
            self.feature_list.scrollToBottom()
        except Exception:
            pass

    # ================= TOGGLES =================
    def _toggle_bbox(self):
        self.show_bbox = not self.show_bbox
        try: self.bbox_cb.blockSignals(True); self.bbox_cb.setChecked(self.show_bbox); self.bbox_cb.blockSignals(False)
        except Exception: pass
        self.redraw_scene()

    def _toggle_datum(self):
        self.datum_planes = not self.datum_planes
        self.redraw_scene()

    def _toggle_section(self):
        self.section_enabled = not self.section_enabled
        try: self.section_cb.blockSignals(True); self.section_cb.setChecked(self.section_enabled); self.section_cb.blockSignals(False)
        except Exception: pass
        self.redraw_scene()

    def _quick_prim(self, kind):
        idx = {"Box":0, "Sphere":1, "Cone":2, "Cylinder":3}[kind]
        self.prim_type.setCurrentIndex(idx)
        self.ribbon_tabs.setCurrentIndex(2)
        self.add_primitive()

    def _quick_std(self, kind):
        idx = {"Bolt":0, "Nut":1, "Washer":2, "Bearing":3}[kind]
        self.std_type.setCurrentIndex(idx)
        self.ribbon_tabs.setCurrentIndex(3)
        self.add_standard_part()

    def _show_about(self):
        QInputDialog.getText(self, "About Forge CAD",
            "Forge CAD v2.1\n\nParametric CAD + Sketch + Assembly + Drawing\nPython + CadQuery + PySide6")

    def _refresh_home_info(self):
        total_v = 0.0
        for b in self.bodies:
            try: total_v += b.val().Volume()
            except Exception: pass
        self.home_info.setText(
            f"Bodies: {len(self.bodies)}\n"
            f"Total Volume: {total_v/1000:.2f} cm³\n"
            f"Project: {os.path.basename(self.current_project_path) if self.current_project_path else 'Untitled'}")

    # ================= v2.1 FEATURES =================
    def apply_constraint(self, ctype):
        if not self.sketch_entities:
            self.constraint_status.setText("No sketch entities"); return
        changed = 0
        try:
            if ctype == 'horizontal':
                for ent in self.sketch_entities:
                    if ent['type'] == 'line':
                        p1, p2 = ent['p1'], ent['p2']
                        avg_y = (p1[1]+p2[1])/2
                        ent['p1'] = (p1[0], avg_y); ent['p2'] = (p2[0], avg_y)
                        changed += 1
            elif ctype == 'vertical':
                for ent in self.sketch_entities:
                    if ent['type'] == 'line':
                        p1, p2 = ent['p1'], ent['p2']
                        avg_x = (p1[0]+p2[0])/2
                        ent['p1'] = (avg_x, p1[1]); ent['p2'] = (avg_x, p2[1])
                        changed += 1
            elif ctype == 'perpendicular':
                lines = [e for e in self.sketch_entities if e['type'] == 'line']
                if len(lines) >= 2:
                    l1, l2 = lines[-2], lines[-1]
                    dx = l1['p2'][0]-l1['p1'][0]; dy = l1['p2'][1]-l1['p1'][1]
                    length = (dx*dx+dy*dy)**0.5
                    if length > 0:
                        nx, ny = -dy/length, dx/length
                        ox, oy = l2['p1']
                        old_len = ((l2['p2'][0]-ox)**2 + (l2['p2'][1]-oy)**2)**0.5
                        l2['p2'] = (ox+nx*old_len, oy+ny*old_len)
                        changed += 1
            elif ctype == 'parallel':
                lines = [e for e in self.sketch_entities if e['type'] == 'line']
                if len(lines) >= 2:
                    l1, l2 = lines[-2], lines[-1]
                    dx = l1['p2'][0]-l1['p1'][0]; dy = l1['p2'][1]-l1['p1'][1]
                    length = (dx*dx+dy*dy)**0.5
                    if length > 0:
                        ux, uy = dx/length, dy/length
                        ox, oy = l2['p1']
                        old_len = ((l2['p2'][0]-ox)**2 + (l2['p2'][1]-oy)**2)**0.5
                        l2['p2'] = (ox+ux*old_len, oy+uy*old_len)
                        changed += 1
            elif ctype == 'coincident':
                pts = []
                for e in self.sketch_entities:
                    if e['type'] == 'line':
                        pts.append(('p1', e, e['p1']))
                        pts.append(('p2', e, e['p2']))
                for i in range(len(pts)):
                    for j in range(i+1, len(pts)):
                        k1, e1, p1 = pts[i]; k2, e2, p2 = pts[j]
                        d = ((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)**0.5
                        if 0.01 < d < 3.0 and e1 is not e2:
                            mx = (p1[0]+p2[0])/2; my = (p1[1]+p2[1])/2
                            e1[k1] = (mx, my); e2[k2] = (mx, my)
                            changed += 1
            self.constraint_status.setText(f"{ctype}: {changed} change(s)")
            self.log_feature(f"Constraint: {ctype}", "🔒")
            self.redraw_sketch()
        except Exception as e:
            self.constraint_status.setText(f"Failed: {e}")

    def toggle_dimension_mode(self):
        self.dimension_mode = self.dim_btn.isChecked()
        self.dimension_points = []
        if self.dimension_mode:
            self.mode_label.setText("Mode: Dimension — click 2 points")
            try:
                self.plotter.disable_picking()
            except Exception:
                pass
            try:
                self.plotter.enable_surface_point_picking(
                    callback=self.on_dimension_click, show_message=False, show_point=False,
                    left_clicking=True, pickable_window=False)
            except Exception: pass
        else:
            self.mode_label.setText("Mode: Model")
            self._enable_body_picking()

    def on_dimension_click(self, point):
        if not self.dimension_mode: return
        self.dimension_points.append(point)
        if len(self.dimension_points) >= 2:
            p1 = np.array(self.dimension_points[-2]); p2 = np.array(self.dimension_points[-1])
            d = float(np.linalg.norm(p2-p1))
            self.dim_label.setText(f"Distance: {d:.2f}\nΔX: {abs(p2[0]-p1[0]):.2f}\n"
                                    f"ΔY: {abs(p2[1]-p1[1]):.2f}\nΔZ: {abs(p2[2]-p1[2]):.2f}")
            for a in self._dimension_actors:
                try: self.plotter.remove_actor(a)
                except Exception: pass
            self._dimension_actors = []
            line = pv.Line(p1, p2)
            self._dimension_actors.append(self.plotter.add_mesh(line, color='#ff66cc', line_width=4))
            mid = (p1+p2)/2
            label_actor = self.plotter.add_point_labels([mid], [f"{d:.2f}"], font_size=14,
                                                          text_color='#ff66cc', show_points=False,
                                                          shape=None, always_visible=True)
            self._dimension_actors.append(label_actor)
            self.plotter.render()
            self.log_feature(f"Dimension {d:.1f}", "📏")
            self.dimension_points = [self.dimension_points[-2], self.dimension_points[-1]]

    def transform_scale_xyz(self):
        if not self.bodies: return
        try:
            sx = float(self.scale_x.text()); sy = float(self.scale_y.text()); sz = float(self.scale_z.text())
        except ValueError: return
        if sx <= 0 or sy <= 0 or sz <= 0: return
        self._push_history()
        try:
            shape = self._get_active().val()
            from OCP.gp import gp_Trsf
            trsf = gp_Trsf()
            trsf.SetValues(sx, 0, 0, 0,
                           0, sy, 0, 0,
                           0, 0, sz, 0)
            transformed = shape.transformShape(trsf)
            self._set_active(cq.Workplane("XY").newObject([transformed]))
            self.log_feature(f"Scale ({sx},{sy},{sz})", "⤢")
            self.redraw_scene()
        except Exception as e:
            self.history.pop(); self._set_status(f"Scale failed: {e}")

    def show_center_of_mass(self):
        if not self.bodies: return
        try:
            shape = self._get_active().val()
            center = shape.Center()
            vol_cm3 = shape.Volume()/1000.0
            mat = self.body_props[self.active_index].get("material", "Steel")
            density = MATERIALS.get(mat, 7.85)
            mass_kg = vol_cm3 * density / 1000.0
            try:
                matrix = shape.MatrixOfInertia()
                Ixx = matrix.Value(1,1); Iyy = matrix.Value(2,2); Izz = matrix.Value(3,3)
                inertia_txt = f"Ixx: {Ixx:.1f}\nIyy: {Iyy:.1f}\nIzz: {Izz:.1f}"
            except Exception:
                inertia_txt = "(inertia unavailable)"
            self.com_label.setText(
                f"Center: ({center.x:.2f}, {center.y:.2f}, {center.z:.2f})\n"
                f"Volume: {vol_cm3:.2f} cm³\nMass: {mass_kg:.4f} kg\n{inertia_txt}")
            self.hide_center_of_mass()
            sphere = pv.Sphere(radius=2, center=(center.x, center.y, center.z))
            self._com_actor = self.plotter.add_mesh(sphere, color='#ff00ff')
            self.plotter.render()
            self.log_feature("Center of Mass", "⚫")
        except Exception as e:
            self.com_label.setText(f"Error: {e}")

    def hide_center_of_mass(self):
        if self._com_actor is not None:
            try: self.plotter.remove_actor(self._com_actor)
            except Exception: pass
            self._com_actor = None
            self.plotter.render()

    def toggle_perspective(self):
        try: self.projection_persp = self.persp_btn.isChecked()
        except Exception: self.projection_persp = not self.projection_persp
        try:
            if self.projection_persp:
                self.plotter.camera.enable_perspective_projection()
            else:
                self.plotter.camera.enable_parallel_projection()
            self.plotter.render()
            self._set_status(f"Camera: {'Perspective' if self.projection_persp else 'Orthographic'}")
        except Exception as e:
            self._set_status(f"Camera failed: {e}")

    def bolt_wizard(self):
        size = self.wiz_size.currentText()
        try:
            bolt_len = float(self.wiz_length.text())
            plate_t = float(self.wiz_plate_thick.text())
        except ValueError: return
        d, hd, hh, pitch = BOLT_METRIC[size]
        self._push_history()
        try:
            plate = cq.Workplane("XY").box(60, 60, plate_t)
            hole = cq.Workplane("XY").circle(d/2 + 0.2).extrude(plate_t)
            plate = plate.cut(hole).translate((0, 0, plate_t/2))

            head = cq.Workplane("XY").polygon(6, hd).extrude(hh)
            shaft = cq.Workplane("XY").workplane(offset=-bolt_len).circle(d/2).extrude(bolt_len)
            bolt = head.union(shaft).translate((0, 0, plate_t + hh/2))

            id_, od, t = WASHER_METRIC[size]
            washer = cq.Workplane("XY").circle(od/2).circle(id_/2).extrude(t).translate((0, 0, plate_t - t/2))

            nd, naf, nh = NUT_METRIC[size]
            nut = cq.Workplane("XY").polygon(6, naf).extrude(nh)
            nut = nut.cut(cq.Workplane("XY").circle(nd/2).extrude(nh)).translate((0, 0, -nh/2))

            for shape, name, pn, color in [
                (plate, f"Plate {plate_t}mm", "PLATE", '#4682b4'),
                (bolt, f"Bolt {size}×{bolt_len}", f"BOLT-{size}", '#ffd700'),
                (washer, f"Washer {size}", f"WSHR-{size}", '#c0c0c0'),
                (nut, f"Nut {size}", f"NUT-{size}", '#ff7f50'),
            ]:
                self.bodies.append(shape)
                self.body_colors.append(color)
                p = self._new_props(); p["name"] = name; p["part_number"] = pn
                p["material"] = "Steel"
                self.body_props.append(p)

            self.active_index = len(self.bodies)-1
            self.log_feature(f"Bolt Wizard {size}", "🔩")
            self.redraw_scene()
            self._set_status(f"Bolt assembly created ({size})")
        except Exception as e:
            self.history.pop(); self._set_status(f"Bolt Wizard failed: {e}")

    # ================= CAD CORE LOGIC =================
    def _push_history(self):
        self.history.append(([s for s in self.bodies], [c for c in self.body_colors],
                             [dict(p) for p in self.body_props], self.active_index))
        self.redo_stack.clear()

    def _add_recent(self, path):
        if path in self.recent_files: self.recent_files.remove(path)
        self.recent_files.insert(0, path); self.recent_files = self.recent_files[:5]
        self.settings.setValue("recent_files", self.recent_files)

    def open_recent(self, idx):
        if idx <= 0: return
        path = self.home_recent.itemData(idx)
        self.home_recent.setCurrentIndex(0)
        if path and os.path.exists(path): self._load_project(path)

    def check_interference_all(self):
        if len(self.bodies) < 2: self.qc_label.setText("Need ≥2 bodies"); return
        try:
            results = []
            for i in range(len(self.bodies)):
                for j in range(i+1, len(self.bodies)):
                    try:
                        inter = self.bodies[i].intersect(self.bodies[j])
                        vol = inter.val().Volume() if inter.val() else 0
                        if vol > 1e-3: results.append(f"B{i+1}↔B{j+1}: OVERLAP ({vol:.1f})")
                    except Exception: pass
            self.qc_label.setText("⚠ INTERFERENCE:\n" + "\n".join(results[:8]) if results else "✓ No interference")
        except Exception as e: self.qc_label.setText(f"Failed: {e}")

    def check_clearance_2(self):
        if len(self.bodies) < 2: self.qc_label.setText("Need 2 bodies"); return
        try:
            ba = self.bodies[-2].val().BoundingBox(); bb = self.bodies[-1].val().BoundingBox()
            dx = max(ba.xmin-bb.xmax, bb.xmin-ba.xmax, 0)
            dy = max(ba.ymin-bb.ymax, bb.ymin-ba.ymax, 0)
            dz = max(ba.zmin-bb.zmax, bb.zmin-ba.zmax, 0)
            dist = float(np.sqrt(dx*dx+dy*dy+dz*dz))
            overlap = (ba.xmin <= bb.xmax and ba.xmax >= bb.xmin and
                       ba.ymin <= bb.ymax and ba.ymax >= bb.ymin and
                       ba.zmin <= bb.zmax and ba.zmax >= bb.zmin)
            self.qc_label.setText("⚠ Overlap" if overlap else f"Clearance (bbox): {dist:.3f}")
        except Exception as e: self.qc_label.setText(f"Failed: {e}")

    def batch_stl_export(self):
        if not self.bodies: return
        folder = QFileDialog.getExistingDirectory(self, "Export folder", FORGE_DIR)
        if not folder: return
        try:
            tol, ang = STL_QUALITY[self.stl_quality_cb.currentText()]
            count = 0
            for i, b in enumerate(self.bodies):
                base = self.body_props[i].get("part_number", "").strip() or f"body_{i+1:02d}"
                safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in base)
                cq.exporters.export(b, os.path.join(folder, f"{safe}.stl"), tolerance=tol, angularTolerance=ang)
                count += 1
            self._set_status(f"Batch STL: {count} files")
        except Exception as e: self._set_status(f"Batch failed: {e}")

    def export_mass_report(self):
        if not self.bodies: return
        path, _ = QFileDialog.getSaveFileName(self, "Mass Report", os.path.join(FORGE_DIR, "mass_report.csv"), "CSV (*.csv)")
        if not path: return
        try:
            total = 0.0
            with open(path, "w", newline='', encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["Body","Name","Part No","Material","Density","Volume(cm³)","Mass(g)","Mass(kg)","Weight(N)"])
                for i, b in enumerate(self.bodies):
                    p = self.body_props[i]; mat = p.get("material", "Steel")
                    density = MATERIALS.get(mat, 7.85)
                    try: v = b.val(); vol_cm3 = v.Volume()/1000.0
                    except Exception: vol_cm3 = 0
                    m_g = vol_cm3*density; m_kg = m_g/1000.0; w_n = m_kg*9.81
                    total += m_kg
                    w.writerow([i+1, p.get("name", f"Body {i+1}"), p.get("part_number",""),
                                mat, f"{density:.2f}", f"{vol_cm3:.3f}", f"{m_g:.2f}",
                                f"{m_kg:.4f}", f"{w_n:.3f}"])
                w.writerow([]); w.writerow(["","TOTAL","","","","","","",f"{total:.4f}", f"{total*9.81:.3f}"])
            self._set_status(f"Mass report: {path}")
        except Exception as e: self._set_status(f"Failed: {e}")

    def rename_body(self, item):
        row = self.body_list.currentRow()
        if row < 0: return
        p = self.body_props[row]
        new, ok = QInputDialog.getText(self, "Rename", "New name:", text=p.get("name", f"Body {row+1}"))
        if ok and new.strip():
            self._push_history()
            p["name"] = new.strip()
            self._refresh_body_list()

    def import_obj_ply(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Mesh", FORGE_DIR, "Mesh (*.obj *.ply *.vtk *.vtp)")
        if not path: return
        try:
            mesh = pv.read(path)
            self.plotter.add_mesh(mesh, color='lightgray', opacity=0.85)
            self._set_status(f"Mesh: {os.path.basename(path)}")
        except Exception as e: self._set_status(f"Mesh failed: {e}")

    def toggle_animation(self):
        if self.animation_on:
            self.anim_timer.stop(); self.animation_on = False
        else:
            try: speed = max(5, int(self.anim_speed.text()))
            except ValueError: speed = 30
            self.anim_timer.start(1000 // speed); self.animation_on = True

    def _anim_step(self):
        try: self.plotter.camera.Azimuth(3)
        except Exception: pass
        self.plotter.render()

    def edit_properties(self):
        if not self.bodies: return
        p = self.body_props[self.active_index]
        name, ok = QInputDialog.getText(self, "Name", "Body name:", text=p.get("name", f"Body {self.active_index+1}"))
        if not ok: return
        pn, ok = QInputDialog.getText(self, "Part Number", "Part number:", text=p.get("part_number", ""))
        if not ok: return
        mat_list = list(MATERIALS.keys())
        cur = mat_list.index(p.get("material", "Steel")) if p.get("material","Steel") in MATERIALS else 0
        mat, ok = QInputDialog.getItem(self, "Material", "Material:", mat_list, cur, False)
        if not ok: return
        notes, ok = QInputDialog.getText(self, "Notes", "Notes:", text=p.get("notes", ""))
        if not ok: return
        self._push_history()
        self.body_props[self.active_index] = {"name": name, "part_number": pn, "material": mat, "notes": notes}
        self._refresh_body_list()

    def export_bom(self):
        if not self.bodies: return
        path, _ = QFileDialog.getSaveFileName(self, "BOM", os.path.join(FORGE_DIR, "bom.csv"), "CSV (*.csv)")
        if not path: return
        try:
            with open(path, "w", newline='', encoding="utf-8") as f:
                w = csv.writer(f); w.writerow(["Item","Name","Part Number","Material","Qty","Volume(cm³)","Mass(g)","Notes"])
                for i, b in enumerate(self.bodies):
                    p = self.body_props[i]
                    try: vol_cm3 = b.val().Volume()/1000.0
                    except Exception: vol_cm3 = 0
                    density = MATERIALS.get(p.get("material","Steel"), 7.85)
                    w.writerow([i+1, p.get("name",f"Body {i+1}"), p.get("part_number",""),
                                p.get("material",""), 1, f"{vol_cm3:.2f}", f"{vol_cm3*density:.2f}", p.get("notes","")])
            self._set_status("BOM saved")
        except Exception as e: self._set_status(f"Failed: {e}")

    def export_webgl_viewer(self):
        if not self.bodies: return
        path, _ = QFileDialog.getSaveFileName(self, "WebGL Viewer", os.path.join(FORGE_DIR, "viewer.html"), "HTML (*.html)")
        if not path: return
        try:
            import base64
            meshes = []
            for i, b in enumerate(self.bodies):
                meshes.append((self._mesh_from_shape(b), self.body_colors[i]))
            html = self._build_viewer_html(meshes)
            with open(path, "w", encoding="utf-8") as f: f.write(html)
            self._set_status(f"Viewer: {path}")
        except Exception as e: self._set_status(f"Viewer failed: {e}")

    def _build_viewer_html(self, meshes):
        import base64
        stl_data = []
        for m, color in meshes:
            tmp = tempfile.NamedTemporaryFile(suffix='.stl', delete=False)
            try:
                m.save(tmp.name)
                with open(tmp.name, 'rb') as f: b64 = base64.b64encode(f.read()).decode('ascii')
                stl_data.append((b64, color))
            finally:
                try: os.unlink(tmp.name)
                except OSError: pass
        items = ",\n".join(f'{{ "data": "{b64}", "color": "{color}" }}' for b64, color in stl_data)
        return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Forge CAD Viewer</title>
<style>body{{margin:0;background:#10131a;color:#eee;font-family:sans-serif}}
#info{{position:fixed;top:10px;left:10px;background:#191e28;padding:10px;border-radius:8px}}
</style></head><body>
<div id="info">Forge CAD Model — <span id="count"></span> bodies</div>
<script type="importmap">{{"imports":{{"three":"https://unpkg.com/three@0.160.0/build/three.module.js","three/addons/":"https://unpkg.com/three@0.160.0/examples/jsm/"}}}}</script>
<script type="module">
import * as THREE from 'three';
import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';
import {{ STLLoader }} from 'three/addons/loaders/STLLoader.js';
const scene = new THREE.Scene(); scene.background = new THREE.Color(0x10131a);
const camera = new THREE.PerspectiveCamera(45, innerWidth/innerHeight, 0.1, 10000);
camera.position.set(120, -120, 80);
const renderer = new THREE.WebGLRenderer({{antialias:true}});
renderer.setSize(innerWidth, innerHeight); document.body.appendChild(renderer.domElement);
const controls = new OrbitControls(camera, renderer.domElement);
scene.add(new THREE.AmbientLight(0xffffff, 0.6));
const d = new THREE.DirectionalLight(0xffffff, 1.0); d.position.set(200, -200, 300); scene.add(d);
scene.add(new THREE.GridHelper(400, 20, 0x334455, 0x223344));
const items = [{items}];
document.getElementById('count').textContent = items.length;
const loader = new STLLoader();
let loaded = 0; const boxes = [];
items.forEach(item => {{
  const bytes = Uint8Array.from(atob(item.data), c => c.charCodeAt(0)).buffer;
  const geo = loader.parse(bytes);
  const mesh = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({{ color: item.color, metalness: 0.3, roughness: 0.6 }}));
  scene.add(mesh); geo.computeBoundingBox(); boxes.push(geo.boundingBox);
  loaded++;
  if (loaded === items.length) {{
    const box = new THREE.Box3(); boxes.forEach(b => box.union(b));
    const c = box.getCenter(new THREE.Vector3()); const s = box.getSize(new THREE.Vector3()).length();
    controls.target.copy(c);
    camera.position.set(c.x + s, c.y - s, c.z + s * 0.7); controls.update();
  }}
}});
function animate(){{ requestAnimationFrame(animate); controls.update(); renderer.render(scene, camera); }}
animate();
</script></body></html>"""

    def apply_mate(self, kind):
        if len(self.bodies) < 2: return
        ia = self.active_index - 1 if self.active_index > 0 else 0
        ib = self.active_index if self.active_index > 0 else 1
        a, b = self.bodies[ia], self.bodies[ib]
        try:
            ca = self._shape_center(a); cb = self._shape_center(b)
            dx = ca[0]-cb[0]; dy = ca[1]-cb[1]
            bb_a = a.val().BoundingBox(); bb_b = b.val().BoundingBox()
            if kind == 'coincident': dz = bb_a.zmax - bb_b.zmin
            elif kind == 'concentric': dz = 0
            elif kind == 'distance':
                try: gap = float(self.mate_distance_val.text())
                except ValueError: gap = 10.0
                dz = bb_a.zmax - bb_b.zmin + gap
            else: return
            self._push_history()
            self.bodies[ib] = b.translate((dx, dy, dz))
            self.redraw_scene()
        except Exception as e: self._set_status(f"Mate failed: {e}")

    def _shape_center(self, shape):
        bb = shape.val().BoundingBox()
        return ((bb.xmin+bb.xmax)/2, (bb.ymin+bb.ymax)/2, (bb.zmin+bb.zmax)/2)

    def align_bodies(self, axis):
        if len(self.bodies) < 2: return
        ia = self.active_index - 1 if self.active_index > 0 else 0
        ib = self.active_index if self.active_index > 0 else 1
        a, b = self.bodies[ia], self.bodies[ib]
        try:
            ca = self._shape_center(a); cb = self._shape_center(b)
            dx = ca[0]-cb[0] if axis in ('X','ALL') else 0
            dy = ca[1]-cb[1] if axis in ('Y','ALL') else 0
            dz = ca[2]-cb[2] if axis in ('Z','ALL') else 0
            self._push_history()
            self.bodies[ib] = b.translate((dx, dy, dz)); self.redraw_scene()
        except Exception as e: self._set_status(f"Align failed: {e}")

    def _mesh_from_shape(self, shape):
        tmp = tempfile.NamedTemporaryFile(suffix='.stl', delete=False).name
        cq.exporters.export(shape, tmp)
        mesh = pv.read(tmp)
        try: os.unlink(tmp)
        except OSError: pass
        return mesh

    def redraw_scene(self):
        self.plotter.clear()
        self.plotter.show_grid(color='#333a45'); self.plotter.add_axes()
        self.plotter.set_background('#0f1218')
        self._sketch_actors = []; self._label_actors = []
        self._measure_actors = []; self._bbox_actors = []
        self._body_actors = {}   # reset actor map

        if self.datum_planes:
            for normal, color in [((0,0,1),'red'), ((0,1,0),'green'), ((1,0,0),'blue')]:
                plane = pv.Plane(center=(0,0,0), direction=normal, i_size=200, j_size=200)
                self.plotter.add_mesh(plane, color=color, opacity=0.12, show_edges=True, edge_color=color, line_width=1)

        n = len(self.bodies)
        for i, shape in enumerate(self.bodies):
            try:
                mesh = self._mesh_from_shape(shape)
                is_active = (i == self.active_index)
                color = '#ffd166' if is_active else self.body_colors[i]
                style = 'wireframe' if self.wireframe else 'surface'
                opacity = 1.0 if (self.wireframe or is_active) else 0.85
                if self.exploded and n > 1:
                    try: dist = float(self.explode_dist.text())
                    except ValueError: dist = 40.0
                    angle = 2*np.pi*i/n
                    offset = (dist*np.cos(angle), dist*np.sin(angle), dist*0.5)
                    mesh = mesh.translate(offset)
                actor = self.plotter.add_mesh(mesh, color=color, show_edges=True, opacity=opacity,
                                              style=style, line_width=2 if is_active else 1,
                                              name=f"forge_body_{i}")
                # Map actor -> body index
                self._body_actors[actor] = i
                if self.show_bbox:
                    box = pv.Box(bounds=mesh.bounds)
                    self._bbox_actors.append(self.plotter.add_mesh(box, style='wireframe',
                                                                    color='#88aadd', line_width=2))
            except Exception: pass

        if self.sketch_entities and self.sketch_mode: self.redraw_sketch()
        if self.measure_points: self._redraw_measure_points()
        self.plotter.reset_camera()
        self._update_title(); self._refresh_body_list()
        # Re-enable picking
        self._enable_body_picking()

    def _refresh_body_list(self):
        self.body_list.blockSignals(True); self.body_list.clear()
        for i in range(len(self.bodies)):
            marker = "► " if i == self.active_index else "   "
            p = self.body_props[i] if i < len(self.body_props) else {}
            name = p.get("name", f"Body {i+1}")
            pn = p.get("part_number", "")
            self.body_list.addItem(QListWidgetItem(f"{marker}{name}" + (f"  [{pn}]" if pn else "")))
        self.body_list.setCurrentRow(self.active_index if self.bodies else -1)
        self.body_list.blockSignals(False)
        try: self.bodies_label.setText(f"Bodies: {len(self.bodies)}")
        except Exception: pass

    def on_body_selected(self, row):
        if row < 0 or row >= len(self.bodies): return
        self.active_index = row; self.redraw_scene()

    def _update_title(self):
        name = os.path.basename(self.current_project_path) if self.current_project_path else "Untitled"
        self.setWindowTitle(f"Forge CAD v2.1 — {name} — {len(self.bodies)} bodies")

    def toggle_wireframe(self):
        self.wireframe = not self.wireframe; self.redraw_scene()

    def on_bbox_toggle(self, state):
        self.show_bbox = bool(state); self.redraw_scene()

    def on_dim_toggle(self, state):
        self.show_dimensions = bool(state)
        if self.sketch_mode: self.redraw_sketch()

    def update_grid_snap(self):
        try: self.grid_snap = max(0.0, float(self.grid_snap_input.text()))
        except ValueError: self.grid_snap = 0.0; self.grid_snap_input.setText("0")

    def on_section_toggle(self, state):
        self.section_enabled = bool(state); self.redraw_scene()

    def on_section_axis(self, axis):
        self.section_axis = axis
        if self.section_enabled: self.redraw_scene()

    def on_section_slide(self, val):
        self.section_pos = val/100.0
        if self.section_enabled: self.redraw_scene()

    def toggle_explode(self):
        self.exploded = not self.exploded; self.redraw_scene()

    def _get_active(self):
        if not self.bodies: return None
        if self.active_index >= len(self.bodies): self.active_index = len(self.bodies)-1
        return self.bodies[self.active_index]

    def _set_active(self, shape): self.bodies[self.active_index] = shape

    def _new_props(self):
        return {"name": f"Body {len(self.bodies)+1}", "part_number": "", "material": "Steel", "notes": ""}

    def multi_boolean(self, op):
        if len(self.bodies) < 2: return
        self._push_history()
        try:
            if op == 'union':
                r = self.bodies[0]
                for s in self.bodies[1:]: r = r.union(s)
            elif op == 'cut':
                r = self.bodies[0]
                for s in self.bodies[1:]: r = r.cut(s)
            else:
                r = self.bodies[0]
                for s in self.bodies[1:]: r = r.intersect(s)
            self.bodies = [r]; self.body_colors = [self.body_colors[0]]; self.body_props = [self.body_props[0]]
            self.active_index = 0; self.redraw_scene()
        except Exception as e: self.history.pop(); self._set_status(f"Failed: {e}")

    def add_standard_part(self):
        kind = self.std_type.currentText(); size = self.std_size.currentText()
        try:
            if kind == "Bolt":
                d, hd, hh, pitch = BOLT_METRIC[size]; length = float(self.std_length.text())
                head = cq.Workplane("XY").polygon(6, hd).extrude(hh)
                shaft = cq.Workplane("XY").workplane(offset=-length).circle(d/2).extrude(length)
                shape = head.union(shaft)
            elif kind == "Nut":
                d, af, h = NUT_METRIC[size]
                shape = cq.Workplane("XY").polygon(6, af).extrude(h)
                shape = shape.cut(cq.Workplane("XY").circle(d/2).extrude(h))
            elif kind == "Washer":
                id_, od, t = WASHER_METRIC[size]
                shape = cq.Workplane("XY").circle(od/2).circle(id_/2).extrude(t)
            else:
                id_, od, w = BEARING_METRIC[size]
                outer = cq.Workplane("XY").circle(od/2).circle(od/2-2).extrude(w)
                inner = cq.Workplane("XY").circle(id_/2+2).circle(id_/2).extrude(w)
                shape = outer.union(inner)
        except Exception as e: self._set_status(f"Failed: {e}"); return
        self._push_history()
        self.bodies.append(shape)
        self.body_colors.append(DEFAULT_COLORS[len(self.bodies) % len(DEFAULT_COLORS)])
        p = self._new_props(); p["name"] = f"{kind} {size}"; p["part_number"] = f"{kind}-{size}"
        self.body_props.append(p)
        self.active_index = len(self.bodies)-1
        self.log_feature(f"{kind} {size}", "🔩")
        self.redraw_scene()

    def generate_gear(self):
        try:
            module = float(self.gear_module.text()); teeth = int(self.gear_teeth.text())
            width = float(self.gear_width.text()); bore = float(self.gear_bore.text())
        except ValueError: return
        try:
            pitch_r = module*teeth/2.0; outer_r = pitch_r + module; root_r = pitch_r - 1.25*module
            pts = []
            for i in range(teeth):
                base = 2*np.pi*i/teeth; ta = 2*np.pi/teeth
                for k in range(4): pts.append((root_r*np.cos(base+(k/4)*ta*0.3), root_r*np.sin(base+(k/4)*ta*0.3)))
                pts.append((outer_r*np.cos(base+ta*0.3), outer_r*np.sin(base+ta*0.3)))
                pts.append((outer_r*np.cos(base+ta*0.5), outer_r*np.sin(base+ta*0.5)))
                pts.append((outer_r*np.cos(base+ta*0.7), outer_r*np.sin(base+ta*0.7)))
                for k in range(3, 7):
                    a = base+(k/4)*ta
                    if k <= 4: pts.append((root_r*np.cos(a), root_r*np.sin(a)))
            wp = cq.Workplane("XY").spline([cq.Vector(x, y) for x, y in pts]).close()
            gear = wp.extrude(width)
            if bore > 0: gear = gear.faces(">Z").workplane().hole(bore)
            self._push_history()
            self.bodies.append(gear)
            self.body_colors.append(DEFAULT_COLORS[len(self.bodies) % len(DEFAULT_COLORS)])
            p = self._new_props(); p["name"] = f"Gear M{module} Z{teeth}"
            self.body_props.append(p)
            self.active_index = len(self.bodies)-1
            self.log_feature(f"Gear M{module} Z{teeth}", "⚙")
            self.redraw_scene()
        except Exception as e: self._set_status(f"Gear failed: {e}")

    def cut_threads(self):
        if not self.bodies: return
        size = self.thread_size.currentText()
        try:
            d, hd, hh, pitch = BOLT_METRIC[size]; thread_len = float(self.thread_len.text())
        except ValueError: return
        self._push_history()
        try:
            coil = cq.Wire.makeHelix(pitch=pitch, height=thread_len, radius=d/2)
            profile = cq.Workplane("XZ").center(d/2, 0).polygon(3, pitch*0.6)
            path_wp = cq.Workplane("XY").newObject([coil])
            cutter = profile.sweep(path_wp, isFrenet=True)
            self._set_active(self._get_active().cut(cutter))
            self.log_feature(f"Thread {size}", "🔄")
            self.redraw_scene()
        except Exception: self.history.pop()

    def show_all_info(self):
        if not self.bodies: return
        lines = []; total = 0.0
        for i, b in enumerate(self.bodies):
            try: v = b.val().Volume(); total += v; lines.append(f"B{i+1}: {v:.0f}")
            except Exception: lines.append(f"B{i+1}: err")
        lines.append(f"TOTAL={total:.0f}")
        self.measure_label.setText("\n".join(lines))

    def mirror_sketch(self, axis):
        if not self.sketch_entities: return
        new = []
        for ent in self.sketch_entities:
            if ent['type'] == 'line':
                p1 = (-ent['p1'][0], ent['p1'][1]) if axis=='X' else (ent['p1'][0], -ent['p1'][1])
                p2 = (-ent['p2'][0], ent['p2'][1]) if axis=='X' else (ent['p2'][0], -ent['p2'][1])
                new.append({'type':'line','p1':p1,'p2':p2})
            elif ent['type'] == 'circle':
                c = ent['center']; nc = (-c[0], c[1]) if axis=='X' else (c[0], -c[1])
                new.append({'type':'circle','center':nc,'radius':ent['radius']})
            elif ent['type'] == 'rect':
                p1, p2 = ent['p1'], ent['p2']
                n1 = (-p1[0], p1[1]) if axis=='X' else (p1[0], -p1[1])
                n2 = (-p2[0], p2[1]) if axis=='X' else (p2[0], -p2[1])
                new.append({'type':'rect','p1':n1,'p2':n2})
        self.sketch_entities.extend(new); self.redraw_sketch()

    def offset_sketch(self):
        if not self.sketch_entities: return
        try: dist = float(self.offset_sk_input.text())
        except ValueError: return
        new = []
        for ent in self.sketch_entities:
            if ent['type'] == 'circle':
                nr = ent['radius']+dist
                if nr > 0: new.append({'type':'circle','center':ent['center'],'radius':nr})
            elif ent['type'] == 'rect':
                p1, p2 = ent['p1'], ent['p2']
                x1, y1 = min(p1[0],p2[0])-dist, min(p1[1],p2[1])-dist
                x2, y2 = max(p1[0],p2[0])+dist, max(p1[1],p2[1])+dist
                new.append({'type':'rect','p1':(x1,y1),'p2':(x2,y2)})
        self.sketch_entities.extend(new); self.redraw_sketch()

    def import_step(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import STEP", FORGE_DIR, "STEP (*.step *.stp)")
        if not path: return
        try:
            wp = cq.importers.importStep(path)
            self._push_history()
            self.bodies.append(wp)
            self.body_colors.append(DEFAULT_COLORS[len(self.bodies) % len(DEFAULT_COLORS)])
            p = self._new_props(); p["name"] = os.path.basename(path)
            self.body_props.append(p)
            self.active_index = len(self.bodies)-1
            self.log_feature(f"Import {os.path.basename(path)}", "📥")
            self.redraw_scene()
        except Exception as e: self._set_status(f"Import failed: {e}")

    def import_stl(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import STL", FORGE_DIR, "STL (*.stl)")
        if not path: return
        try:
            mesh = pv.read(path); self.plotter.add_mesh(mesh, color='lightgray', opacity=0.7)
        except Exception as e: self._set_status(f"STL failed: {e}")

    def save_template(self):
        if not self.bodies: return
        name, ok = QInputDialog.getText(self, "Save Template", "Name:")
        if not ok or not name: return
        path = os.path.join(TEMPLATE_DIR, f"{name}.forge")
        try:
            data = {"version": "2.1",
                    "bodies": [cq.exporters.toString(b, "STEP") for b in self.bodies],
                    "colors": self.body_colors, "props": self.body_props}
            with open(path, "w", encoding="utf-8") as f: json.dump(data, f)
        except Exception as e: self._set_status(f"Tmpl failed: {e}")

    def load_template(self):
        files = [f for f in os.listdir(TEMPLATE_DIR) if f.endswith('.forge')]
        if not files: return
        names = [os.path.splitext(f)[0] for f in files]
        name, ok = QInputDialog.getItem(self, "Load Template", "Choose:", names, 0, False)
        if not ok: return
        self._load_project(os.path.join(TEMPLATE_DIR, f"{name}.forge"))

    def loft_sketches(self):
        if not self.sketch_entities: return
        rects = [e for e in self.sketch_entities if e['type'] in ('rect','circle')]
        if len(rects) < 2: return
        try:
            self._push_history()
            wp = cq.Workplane("XY")
            for i, ent in enumerate(rects[:4]):
                z = i*30
                if ent['type'] == 'rect':
                    p1, p2 = ent['p1'], ent['p2']
                    cx, cy = (p1[0]+p2[0])/2, (p1[1]+p2[1])/2
                    w, hh = abs(p2[0]-p1[0]), abs(p2[1]-p1[1])
                    wp = wp.workplane(offset=z if i==0 else 30).moveTo(cx, cy).rect(w, hh)
                else:
                    c = ent['center']
                    wp = wp.workplane(offset=z if i==0 else 30).moveTo(c[0], c[1]).circle(ent['radius'])
            self.bodies.append(wp.loft())
            self.body_colors.append(DEFAULT_COLORS[len(self.bodies) % len(DEFAULT_COLORS)])
            self.body_props.append(self._new_props())
            self.active_index = len(self.bodies)-1
            self.log_feature("Loft", "🔀")
            self.redraw_scene()
        except Exception: self.history.pop()

    def sweep_sketch(self):
        if not self.sketch_entities: return
        circles = [e for e in self.sketch_entities if e['type'] == 'circle']
        polys = [e for e in self.sketch_entities if e['type'] == 'poly']
        if not circles or not polys: return
        try:
            self._push_history()
            circle = circles[0]; path_pts = polys[0]['points']
            profile_wp = cq.Workplane("XY").center(circle['center'][0], circle['center'][1]).circle(circle['radius'])
            path_wp = cq.Workplane("XZ").moveTo(path_pts[0][0], path_pts[0][1])
            for p in path_pts[1:]: path_wp = path_wp.lineTo(p[0], p[1])
            self.bodies.append(profile_wp.sweep(path_wp, isFrenet=True))
            self.body_colors.append(DEFAULT_COLORS[len(self.bodies) % len(DEFAULT_COLORS)])
            self.body_props.append(self._new_props())
            self.active_index = len(self.bodies)-1
            self.log_feature("Sweep", "🌀")
            self.redraw_scene()
        except Exception: self.history.pop()

    def create_helix(self):
        radius, ok = QInputDialog.getDouble(self, "Helix", "Radius:", 20.0, 0.1, 1000, 1)
        if not ok: return
        pitch, ok = QInputDialog.getDouble(self, "Helix", "Pitch:", 10.0, 0.1, 1000, 1)
        if not ok: return
        turns, ok = QInputDialog.getDouble(self, "Helix", "Turns:", 5.0, 0.5, 100, 1)
        if not ok: return
        wire_r, ok = QInputDialog.getDouble(self, "Helix", "Wire radius:", 3.0, 0.1, 100, 1)
        if not ok: return
        self._push_history()
        try:
            height = pitch*turns
            helix = cq.Wire.makeHelix(pitch=pitch, height=height, radius=radius)
            path_wp = cq.Workplane("XY").newObject([helix])
            profile = cq.Workplane("XZ").center(radius, 0).circle(wire_r)
            self.bodies.append(profile.sweep(path_wp, isFrenet=True))
            self.body_colors.append(DEFAULT_COLORS[len(self.bodies) % len(DEFAULT_COLORS)])
            self.body_props.append(self._new_props())
            self.active_index = len(self.bodies)-1
            self.log_feature(f"Helix r={radius}", "🌀")
            self.redraw_scene()
        except Exception: self.history.pop()

    def add_text(self):
        txt, ok = QInputDialog.getText(self, "3D Text", "Enter text:", text="FORGE")
        if not ok or not txt.strip(): return
        size, ok = QInputDialog.getDouble(self, "Size", "Text size:", 10.0, 0.1, 1000, 2)
        if not ok: return
        depth, ok = QInputDialog.getDouble(self, "Depth", "Depth:", 3.0, 0.1, 100, 2)
        if not ok: return
        self._push_history()
        try:
            shape = cq.Workplane("XY").text(txt, size, depth)
            self.bodies.append(shape)
            self.body_colors.append(DEFAULT_COLORS[len(self.bodies) % len(DEFAULT_COLORS)])
            p = self._new_props(); p["name"] = f"Text: {txt}"
            self.body_props.append(p)
            self.active_index = len(self.bodies)-1
            self.log_feature(f"Text '{txt}'", "T")
            self.redraw_scene()
        except Exception: self.history.pop()

    def calculate_mass(self):
        if not self.bodies: return
        try:
            shape = self._get_active().val()
            vol_cm3 = shape.Volume()/1000.0
            custom = self.custom_density.text().strip()
            if custom: density = float(custom); name = "Custom"
            else: name = self.material_cb.currentText(); density = MATERIALS[name]
            m_g = vol_cm3*density; m_kg = m_g/1000.0
            self.mass_label.setText(f"{name}: {density:.2f} g/cm³\nVol: {vol_cm3:.2f} cm³\n"
                                     f"Mass: {m_g:.2f} g ({m_kg:.4f} kg)\nW: {m_kg*9.81:.3f} N")
        except Exception as e: self.mass_label.setText(f"Error: {e}")

    def change_body_color(self):
        if not self.bodies: return
        color = QColorDialog.getColor(QColor(self.body_colors[self.active_index]), self, "Body Color")
        if color.isValid():
            self._push_history()
            self.body_colors[self.active_index] = color.name()
            self.redraw_scene()

    def clear_scene(self):
        self._push_history()
        self.bodies = []; self.body_colors = []; self.body_props = []; self.active_index = 0
        self.current_project_path = None
        self.feature_history = []
        try: self.feature_list.clear()
        except Exception: pass
        self.redraw_scene()

    def undo(self):
        if not self.history: return
        self.redo_stack.append(([s for s in self.bodies], [c for c in self.body_colors],
                                 [dict(p) for p in self.body_props], self.active_index))
        self.bodies, self.body_colors, self.body_props, self.active_index = self.history.pop()
        if self.active_index >= len(self.bodies): self.active_index = max(0, len(self.bodies)-1)
        self.redraw_scene()

    def redo(self):
        if not self.redo_stack: return
        self.history.append(([s for s in self.bodies], [c for c in self.body_colors],
                              [dict(p) for p in self.body_props], self.active_index))
        self.bodies, self.body_colors, self.body_props, self.active_index = self.redo_stack.pop()
        self.redraw_scene()

    def delete_active_body(self):
        if not self.bodies: return
        self._push_history()
        self.bodies.pop(self.active_index); self.body_colors.pop(self.active_index)
        self.body_props.pop(self.active_index)
        self.active_index = min(self.active_index, len(self.bodies)-1) if self.bodies else 0
        self.redraw_scene()

    def add_primitive(self):
        try:
            kind = self.prim_type.currentText()
            a = float(self.p1_input.text()); b = float(self.p2_input.text()); c = float(self.p3_input.text())
            px, py, pz = float(self.box_x.text()), float(self.box_y.text()), float(self.box_z.text())
            if kind == "Box": shape = cq.Workplane("XY").box(a, b, c)
            elif kind == "Sphere": shape = cq.Workplane("XY").sphere(a)
            elif kind == "Cylinder": shape = cq.Workplane("XY").circle(a).extrude(b)
            elif kind == "Cone": shape = cq.Workplane("XY").circle(a).workplane(offset=b).circle(c).loft()
            else: return
            shape = shape.translate((px, py, pz))
            self._push_history()
            self.bodies.append(shape)
            self.body_colors.append(DEFAULT_COLORS[len(self.bodies) % len(DEFAULT_COLORS)])
            self.body_props.append(self._new_props())
            self.active_index = len(self.bodies)-1
            self.log_feature(f"{kind} {a}×{b}×{c}", "⬛")
            self.redraw_scene()
        except Exception as e: self._set_status(f"Error: {e}")

    def transform_move(self):
        if not self.bodies: return
        try: dx, dy, dz = float(self.move_x.text()), float(self.move_y.text()), float(self.move_z.text())
        except ValueError: return
        self._push_history()
        self._set_active(self._get_active().translate((dx, dy, dz)))
        self.log_feature(f"Move ({dx},{dy},{dz})", "↔")
        self.redraw_scene()

    def transform_rotate(self):
        if not self.bodies: return
        try: angle = float(self.rot_angle.text())
        except ValueError: return
        axis = {'X':(1,0,0),'Y':(0,1,0),'Z':(0,0,1)}[self.rot_axis.currentText()]
        self._push_history()
        shape = self._get_active().val()
        self._set_active(cq.Workplane("XY").newObject([shape.rotate((0,0,0), axis, angle)]))
        self.log_feature(f"Rotate {angle}° {self.rot_axis.currentText()}", "⟳")
        self.redraw_scene()

    def transform_scale(self):
        if not self.bodies: return
        try: f = float(self.scale_factor.text())
        except ValueError: return
        self._push_history()
        shape = self._get_active().val()
        self._set_active(cq.Workplane("XY").newObject([shape.scale(f)]))
        self.log_feature(f"Scale ×{f}", "⤢")
        self.redraw_scene()

    def linear_pattern(self):
        if not self.bodies: return
        try: n = int(self.pattern_count.text()); sp = float(self.pattern_spacing.text())
        except ValueError: return
        self._push_history()
        base = self._get_active(); bc = self.body_colors[self.active_index]
        for i in range(1, n):
            self.bodies.append(base.translate((sp*i, 0, 0)))
            self.body_colors.append(bc); self.body_props.append(self._new_props())
        self.log_feature(f"Linear Pattern N={n}", "⋯")
        self.redraw_scene()

    def circular_pattern(self):
        if not self.bodies: return
        try: n = int(self.circ_count.text()); total = float(self.circ_angle.text())
        except ValueError: return
        axis = {'X':(1,0,0),'Y':(0,1,0),'Z':(0,0,1)}[self.circ_axis.currentText()]
        self._push_history()
        base_wp = self._get_active(); bc = self.body_colors[self.active_index]
        step = total/n if abs(total-360.0)<1e-6 else total/(n-1)
        for i in range(1, n):
            shape = base_wp.val().rotate((0,0,0), axis, step*i)
            self.bodies.append(cq.Workplane("XY").newObject([shape]))
            self.body_colors.append(bc); self.body_props.append(self._new_props())
        self.log_feature(f"Circular Pattern N={n}", "⟳")
        self.redraw_scene()

    def mirror_body(self):
        if not self.bodies: return
        plane, ok = QInputDialog.getItem(self, "Mirror", "Plane:", ["XY","XZ","YZ"], 0, False)
        if not ok: return
        self._push_history()
        m = self._get_active().mirror(mirrorPlane=plane, basePointVector=(0,0,0))
        self.bodies.append(m); self.body_colors.append(self.body_colors[self.active_index])
        self.body_props.append(self._new_props())
        self.active_index = len(self.bodies)-1
        self.log_feature(f"Mirror {plane}", "⇋")
        self.redraw_scene()

    def copy_body(self):
        if not self.bodies: return
        self._push_history()
        self.bodies.append(self._get_active().translate((0, 0, 0)))
        self.body_colors.append(self.body_colors[self.active_index])
        self.body_props.append(self._new_props())
        self.active_index = len(self.bodies)-1
        self.redraw_scene()

    def shell_body(self):
        if not self.bodies: return
        try: t = float(self.shell_thick.text())
        except ValueError: return
        self._push_history()
        try:
            self._set_active(self._get_active().faces(">Z").shell(t))
            self.log_feature(f"Shell t={t}", "◫")
            self.redraw_scene()
        except Exception: self.history.pop()

    def toggle_sketch(self):
        self.stop_sketch() if self.sketch_mode else self.start_sketch()

    def start_sketch(self):
        self.sketch_mode = True
        self.sketch_plane = self.plane_combo.currentText()
        self.sketch_toggle_btn.setText("Finish Sketch")
        self.mode_label.setText(f"Mode: Sketch ({self.sketch_plane})")
        for b in (self.line_btn, self.poly_btn, self.circle_btn, self.rect_btn,
                  self.finish_poly_btn, self.clear_sketch_btn):
            b.setEnabled(True)
        if self.sketch_plane == 'XY': self.plotter.view_xy(); normal = (0,0,1)
        elif self.sketch_plane == 'XZ': self.plotter.view_xz(); normal = (0,1,0)
        else: self.plotter.view_yz(); normal = (1,0,0)
        plane = pv.Plane(center=(0,0,0), direction=normal, i_size=200, j_size=200)
        self._sketch_plane_actor = self.plotter.add_mesh(
            plane, color='#3a4a66', opacity=0.3, show_edges=True, edge_color='#70a7ff')
        try: self.plotter.disable_picking()
        except Exception: pass
        self.plotter.enable_surface_point_picking(
            callback=self.on_point_picked, show_message=False, show_point=True,
            left_clicking=True, pickable_window=False)

    def stop_sketch(self):
        self.sketch_mode = False; self.sketch_tool = None
        self.sketch_points = []; self.polyline_chain = []
        self.sketch_toggle_btn.setText("Start Sketch")
        self.mode_label.setText("Mode: Model")
        for b in (self.line_btn, self.poly_btn, self.circle_btn, self.rect_btn,
                  self.finish_poly_btn, self.clear_sketch_btn):
            b.setEnabled(False)
        try: self.plotter.disable_picking()
        except Exception: pass
        if self._sketch_plane_actor is not None:
            self.plotter.remove_actor(self._sketch_plane_actor); self._sketch_plane_actor = None
        self.redraw_sketch()
        self._enable_body_picking()

    def set_tool(self, tool):
        self.sketch_tool = tool; self.sketch_points = []; self.polyline_chain = []
        self.mode_label.setText(f"Tool: {tool}")

    def _snap(self, val):
        if self.grid_snap <= 0: return val
        return round(val / self.grid_snap) * self.grid_snap

    def on_point_picked(self, point):
        if not self.sketch_mode or not self.sketch_tool: return
        x, y, z = point
        pt2d = (x, y) if self.sketch_plane=='XY' else ((x, z) if self.sketch_plane=='XZ' else (y, z))
        pt2d = (self._snap(pt2d[0]), self._snap(pt2d[1]))
        tool = self.sketch_tool
        if tool == 'poly':
            self.polyline_chain.append(pt2d); self.redraw_sketch(); return
        if tool == 'line' and len(self.sketch_points) == 1 and self.hv_snap_cb.isChecked():
            p0 = self.sketch_points[0]
            dx = abs(pt2d[0]-p0[0]); dy = abs(pt2d[1]-p0[1])
            if dx < 2 and dx < dy: pt2d = (p0[0], pt2d[1])
            elif dy < 2 and dy < dx: pt2d = (pt2d[0], p0[1])
        self.sketch_points.append(pt2d)
        if tool == 'line' and len(self.sketch_points) == 2:
            self.sketch_entities.append({'type':'line','p1':self.sketch_points[0],'p2':self.sketch_points[1]})
            self.sketch_points = []
        elif tool == 'circle' and len(self.sketch_points) == 2:
            c, e = self.sketch_points
            r = float(np.hypot(e[0]-c[0], e[1]-c[1]))
            self.sketch_entities.append({'type':'circle','center':c,'radius':r}); self.sketch_points = []
        elif tool == 'rect' and len(self.sketch_points) == 2:
            self.sketch_entities.append({'type':'rect','p1':self.sketch_points[0],'p2':self.sketch_points[1]})
            self.sketch_points = []
        self.redraw_sketch()

    def finish_polyline(self):
        if len(self.polyline_chain) < 2: return
        self.sketch_entities.append({'type':'poly','points':list(self.polyline_chain)})
        self.polyline_chain = []; self.redraw_sketch()

    def redraw_sketch(self):
        for a in self._sketch_actors: self.plotter.remove_actor(a)
        for a in self._label_actors: self.plotter.remove_actor(a)
        self._sketch_actors = []; self._label_actors = []
        for ent in self.sketch_entities:
            poly = self._entity_polydata(ent)
            if poly is not None:
                self._sketch_actors.append(self.plotter.add_mesh(poly, color='#ffd166', line_width=3))
            if self.show_dimensions: self._add_dimension_label(ent)
        if self.polyline_chain and len(self.polyline_chain) >= 2:
            poly = self._polyline_polydata(self.polyline_chain)
            if poly is not None:
                self._sketch_actors.append(self.plotter.add_mesh(poly, color='#88dd88', line_width=3))
        self.plotter.render()

    def _add_dimension_label(self, ent):
        def to3d(p, z=0.0):
            if self.sketch_plane == 'XY': return (p[0], p[1], z)
            if self.sketch_plane == 'XZ': return (p[0], z, p[1])
            return (z, p[0], p[1])
        try:
            if ent['type'] == 'line':
                p1, p2 = ent['p1'], ent['p2']
                mid = ((p1[0]+p2[0])/2, (p1[1]+p2[1])/2)
                length = np.hypot(p2[0]-p1[0], p2[1]-p1[1])
                self._label_actors.append(self.plotter.add_point_labels([to3d(mid, 2.0)], [f"{length:.1f}"],
                    font_size=11, text_color='#ffe066', show_points=False, shape=None, always_visible=True))
            elif ent['type'] == 'circle':
                c, r = ent['center'], ent['radius']
                self._label_actors.append(self.plotter.add_point_labels([to3d((c[0], c[1]+r), 2.0)], [f"R{r:.1f}"],
                    font_size=11, text_color='#ffe066', show_points=False, shape=None, always_visible=True))
            elif ent['type'] == 'rect':
                p1, p2 = ent['p1'], ent['p2']
                w = abs(p2[0]-p1[0]); h = abs(p2[1]-p1[1])
                mid = ((p1[0]+p2[0])/2, (p1[1]+p2[1])/2)
                self._label_actors.append(self.plotter.add_point_labels([to3d(mid, 2.0)], [f"{w:.1f}×{h:.1f}"],
                    font_size=11, text_color='#ffe066', show_points=False, shape=None, always_visible=True))
        except Exception: pass

    def _entity_polydata(self, ent):
        def to3d(p):
            if self.sketch_plane == 'XY': return (p[0], p[1], 0.0)
            if self.sketch_plane == 'XZ': return (p[0], 0.0, p[1])
            return (0.0, p[0], p[1])
        if ent['type'] == 'line': return pv.Line(to3d(ent['p1']), to3d(ent['p2']))
        if ent['type'] == 'poly': return self._polyline_polydata(ent['points'])
        if ent['type'] == 'circle':
            theta = np.linspace(0, 2*np.pi, 64); c, r = ent['center'], ent['radius']
            if self.sketch_plane == 'XY':
                pts = np.column_stack([c[0]+r*np.cos(theta), c[1]+r*np.sin(theta), np.zeros_like(theta)])
            elif self.sketch_plane == 'XZ':
                pts = np.column_stack([c[0]+r*np.cos(theta), np.zeros_like(theta), c[1]+r*np.sin(theta)])
            else:
                pts = np.column_stack([np.zeros_like(theta), c[0]+r*np.cos(theta), c[1]+r*np.sin(theta)])
            pts = np.vstack([pts, pts[0]])
            return pv.lines_from_points(pts)
        if ent['type'] == 'rect':
            p1, p2 = ent['p1'], ent['p2']
            corners = [(p1[0],p1[1]), (p2[0],p1[1]), (p2[0],p2[1]), (p1[0],p2[1]), (p1[0],p1[1])]
            return pv.lines_from_points(np.array([to3d(c) for c in corners]))
        return None

    def _polyline_polydata(self, points):
        def to3d(p):
            if self.sketch_plane == 'XY': return (p[0], p[1], 0.0)
            if self.sketch_plane == 'XZ': return (p[0], 0.0, p[1])
            return (0.0, p[0], p[1])
        pts = np.array([to3d(p) for p in points])
        if len(pts) < 2: return None
        return pv.lines_from_points(pts)

    def clear_sketch(self):
        self.sketch_entities = []; self.sketch_points = []; self.polyline_chain = []
        self.redraw_sketch()

    def _build_sketch_workplane(self):
        wp = cq.Workplane(self.sketch_plane)
        for ent in self.sketch_entities:
            if ent['type'] == 'rect':
                p1, p2 = ent['p1'], ent['p2']
                cx, cy = (p1[0]+p2[0])/2, (p1[1]+p2[1])/2
                w, hh = abs(p2[0]-p1[0]), abs(p2[1]-p1[1])
                wp = wp.moveTo(cx, cy).rect(w, hh).moveTo(0, 0)
            elif ent['type'] == 'circle':
                c = ent['center']
                wp = wp.moveTo(c[0], c[1]).circle(ent['radius']).moveTo(0, 0)
            elif ent['type'] == 'poly':
                pts = ent['points']
                wp = wp.moveTo(pts[0][0], pts[0][1])
                for pt in pts[1:]: wp = wp.lineTo(pt[0], pt[1])
                wp = wp.close().moveTo(0, 0)
        return wp

    def extrude_sketch(self):
        if not self.sketch_entities: return
        try: h = float(self.extrude_height.text())
        except ValueError: return
        self._push_history()
        try:
            solid = self._build_sketch_workplane().extrude(h)
            self.bodies.append(solid)
            self.body_colors.append(DEFAULT_COLORS[len(self.bodies) % len(DEFAULT_COLORS)])
            self.body_props.append(self._new_props())
            self.active_index = len(self.bodies)-1
            self.log_feature(f"Extrude {h}", "⬆")
            self.redraw_scene()
        except Exception: self.history.pop()

    def revolve_sketch(self):
        if not self.sketch_entities: return
        try: angle = float(self.rev_angle.text())
        except ValueError: return
        axis = {'X':(1,0,0),'Y':(0,1,0),'Z':(0,0,1)}[self.rev_axis.currentText()]
        self._push_history()
        try:
            solid = self._build_sketch_workplane().revolve(angle, axis)
            self.bodies.append(solid)
            self.body_colors.append(DEFAULT_COLORS[len(self.bodies) % len(DEFAULT_COLORS)])
            self.body_props.append(self._new_props())
            self.active_index = len(self.bodies)-1
            self.log_feature(f"Revolve {angle}°", "⟳")
            self.redraw_scene()
        except Exception: self.history.pop()

    def boolean_op(self, op):
        if len(self.bodies) < 2: return
        a, b = self.bodies[-2], self.bodies[-1]
        self._push_history()
        try:
            if op == 'union': result = a.union(b)
            elif op == 'cut': result = a.cut(b)
            else: result = a.intersect(b)
            self.bodies = self.bodies[:-2] + [result]
            self.body_colors = self.body_colors[:-2] + [self.body_colors[-2]]
            self.body_props = self.body_props[:-2] + [self.body_props[-2]]
            self.active_index = len(self.bodies)-1
            self.log_feature(f"Boolean {op}", "✂")
            self.redraw_scene()
        except Exception: self.history.pop()

    def apply_fillet(self):
        if not self.bodies: return
        try: r = float(self.fillet_radius.text())
        except ValueError: return
        self._push_history()
        try:
            self._set_active(self._get_active().edges().fillet(r))
            self.log_feature(f"Fillet r={r}", "⌐")
            self.redraw_scene()
        except Exception: self.history.pop()

    def apply_chamfer(self):
        if not self.bodies: return
        try: d = float(self.fillet_radius.text())
        except ValueError: return
        self._push_history()
        try:
            self._set_active(self._get_active().edges().chamfer(d))
            self.log_feature(f"Chamfer d={d}", "▷")
            self.redraw_scene()
        except Exception: self.history.pop()

    def cut_hole(self):
        if not self.bodies: return
        try:
            x, y = float(self.hole_x.text()), float(self.hole_y.text())
            d, depth = float(self.hole_d.text()), float(self.hole_depth.text())
        except ValueError: return
        self._push_history()
        try:
            hole = cq.Workplane("XY").center(x, y).circle(d/2).extrude(depth)
            self._set_active(self._get_active().cut(hole))
            self.log_feature(f"Hole Ø{d}", "◎")
            self.redraw_scene()
        except Exception: self.history.pop()

    def measure_active(self):
        if not self.bodies: return
        try:
            shape = self._get_active().val()
            bb = shape.BoundingBox()
            self.measure_label.setText(f"V: {shape.Volume():.2f}\nA: {shape.Area():.2f}\n"
                                        f"BB: {bb.xmax-bb.xmin:.1f}×{bb.ymax-bb.ymin:.1f}×{bb.zmax-bb.zmin:.1f}")
        except Exception as e: self.measure_label.setText(f"Error: {e}")

    def toggle_distance_measure(self):
        self.measure_mode = not self.measure_mode
        self.measure_points = []; self._redraw_measure_points()
        if self.measure_mode:
            self.mode_label.setText("Mode: Distance — click 2 points")
            try: self.plotter.disable_picking()
            except Exception: pass
            self.plotter.enable_surface_point_picking(
                callback=self.on_measure_click, show_message=False, show_point=False,
                left_clicking=True, pickable_window=False)
        else:
            self.mode_label.setText("Mode: Model")
            self._enable_body_picking()

    def on_measure_click(self, point):
        if not self.measure_mode: return
        self.measure_points.append(point)
        if len(self.measure_points) >= 2:
            p1 = np.array(self.measure_points[-2]); p2 = np.array(self.measure_points[-1])
            d = np.linalg.norm(p2-p1)
            self.measure_label.setText(f"Dist: {d:.3f}\nΔX: {p2[0]-p1[0]:.3f}\nΔY: {p2[1]-p1[1]:.3f}\nΔZ: {p2[2]-p1[2]:.3f}")
            self.measure_points = [self.measure_points[-2], self.measure_points[-1]]
        self._redraw_measure_points()

    def _redraw_measure_points(self):
        for a in self._measure_actors:
            try: self.plotter.remove_actor(a)
            except Exception: pass
        self._measure_actors = []
        for p in self.measure_points:
            sp = pv.Sphere(radius=2, center=p)
            self._measure_actors.append(self.plotter.add_mesh(sp, color='#ff3a3a'))
        if len(self.measure_points) >= 2:
            line = pv.Line(self.measure_points[0], self.measure_points[1])
            self._measure_actors.append(self.plotter.add_mesh(line, color='#ff3a3a', line_width=4))
        self.plotter.render()

    def screenshot_viewport(self):
        path, _ = QFileDialog.getSaveFileName(self, "Screenshot", os.path.join(FORGE_DIR, "forge_view.png"), "PNG (*.png)")
        if not path: return
        try: self.plotter.screenshot(path)
        except Exception as e: self._set_status(f"Failed: {e}")

    def export_4view_drawing(self):
        if not self.bodies: return
        path, _ = QFileDialog.getSaveFileName(self, "4-View", os.path.join(FORGE_DIR, "forge_drawing.png"), "PNG (*.png)")
        if not path: return
        try:
            mesh = self._mesh_from_shape(self._get_active())
            bounds = mesh.bounds
            cx = (bounds[0]+bounds[1])/2; cy = (bounds[2]+bounds[3])/2; cz = (bounds[4]+bounds[5])/2
            dx = bounds[1]-bounds[0]; dy = bounds[3]-bounds[2]; dz = bounds[5]-bounds[4]
            diag = max(dx, dy, dz)*3
            if diag <= 0: diag = 100
            SIZE = 500
            views = [("Front", (cx, cy-diag, cz), (0,0,1), f"W={dx:.1f}  H={dz:.1f}"),
                     ("Top", (cx, cy, cz+diag), (0,1,0), f"W={dx:.1f}  D={dy:.1f}"),
                     ("Right", (cx+diag, cy, cz), (0,0,1), f"D={dy:.1f}  H={dz:.1f}"),
                     ("Isometric", (cx+diag*0.8, cy-diag*0.8, cz+diag*0.6), (0,0,1), "")]
            images = {}
            for name, cam_pos, cam_up, dims in views:
                p = pv.Plotter(off_screen=True, window_size=(SIZE, SIZE))
                p.set_background("white")
                p.add_mesh(mesh, color="#b8d0ec", show_edges=True, edge_color="black", line_width=1)
                try: p.camera.enable_parallel_projection()
                except Exception: pass
                p.camera.position = cam_pos; p.camera.focal_point = (cx, cy, cz); p.camera.up = cam_up
                if dims: p.add_text(dims, position="lower_left", font_size=11, color="black")
                p.add_text(name, position="upper_left", font_size=14, color="black")
                images[name] = p.screenshot(return_img=True)
                try: p.close()
                except Exception: pass
            grid = np.ones((SIZE*2, SIZE*2, 3), dtype=np.uint8)*255
            grid[0:SIZE, 0:SIZE] = images["Front"][:, :, :3]
            grid[0:SIZE, SIZE:SIZE*2] = images["Top"][:, :, :3]
            grid[SIZE:SIZE*2, 0:SIZE] = images["Right"][:, :, :3]
            grid[SIZE:SIZE*2, SIZE:SIZE*2] = images["Isometric"][:, :, :3]
            grid = grid[::-1, :, :]
            try: pv.save_image(grid, path)
            except Exception:
                from PIL import Image
                Image.fromarray(grid).save(path)
        except Exception as e: self._set_status(f"Drawing failed: {e}")

    def export_sketch_dxf(self):
        if not self.sketch_entities: return
        path, _ = QFileDialog.getSaveFileName(self, "DXF", os.path.join(FORGE_DIR, "forge_sketch.dxf"), "DXF (*.dxf)")
        if not path: return
        try: cq.exporters.export(self._build_sketch_workplane(), path, exportType="DXF")
        except Exception as e: self._set_status(f"DXF failed: {e}")

    def _body_to_step_string(self, body): return cq.exporters.toString(body, "STEP")

    def _step_string_to_body(self, step_str):
        tmp = tempfile.NamedTemporaryFile(suffix=".step", delete=False, mode="w")
        try:
            tmp.write(step_str); tmp.close()
            wp = cq.importers.importStep(tmp.name)
            return cq.Workplane("XY").newObject([wp.val()])
        finally:
            try: os.unlink(tmp.name)
            except OSError: pass

    def save_project(self, force=False):
        if not self.bodies: return
        path = self.current_project_path
        if force or not path:
            path, _ = QFileDialog.getSaveFileName(self, "Save Project", os.path.join(FORGE_DIR, "untitled.forge"), "Forge Project (*.forge)")
            if not path: return
        try:
            data = {"version": "2.1",
                    "bodies": [self._body_to_step_string(b) for b in self.bodies],
                    "colors": self.body_colors, "props": self.body_props}
            with open(path, "w", encoding="utf-8") as f: json.dump(data, f)
            self.current_project_path = path; self._update_title(); self._add_recent(path)
        except Exception as e: self._set_status(f"Save failed: {e}")

    def _load_project(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f: data = json.load(f)
            bodies = [self._step_string_to_body(s) for s in data.get("bodies", [])]
            colors = data.get("colors", [])
            while len(colors) < len(bodies):
                colors.append(DEFAULT_COLORS[len(colors) % len(DEFAULT_COLORS)])
            props = data.get("props", [])
            while len(props) < len(bodies): props.append(self._new_props())
            self._push_history()
            self.bodies = bodies; self.body_colors = colors[:len(bodies)]
            self.body_props = props[:len(bodies)]
            self.active_index = 0; self.current_project_path = path
            self._add_recent(path); self.redraw_scene()
        except Exception as e: self._set_status(f"Open failed: {e}")

    def open_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Project", FORGE_DIR, "Forge Project (*.forge)")
        if path: self._load_project(path)

    def _merged_body(self):
        if not self.bodies: return None
        final = self.bodies[0]
        for s in self.bodies[1:]: final = final.union(s)
        return final

    def export_stl(self):
        if not self.bodies: return
        path, _ = QFileDialog.getSaveFileName(self, "Export STL", os.path.join(FORGE_DIR, "forge_export.stl"), "STL (*.stl)")
        if not path: return
        try:
            tol, ang = STL_QUALITY[self.stl_quality_cb.currentText()]
            cq.exporters.export(self._merged_body(), path, tolerance=tol, angularTolerance=ang)
        except Exception as e: self._set_status(f"STL failed: {e}")

    def export_step(self):
        if not self.bodies: return
        path, _ = QFileDialog.getSaveFileName(self, "Export STEP", os.path.join(FORGE_DIR, "forge_export.step"), "STEP (*.step *.stp)")
        if not path: return
        try: cq.exporters.export(self._merged_body(), path)
        except Exception as e: self._set_status(f"STEP failed: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = ForgeCAD()
    w.show()
    sys.exit(app.exec()) 
