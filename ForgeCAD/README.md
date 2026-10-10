# Forge CAD v2.1

Lightweight parametric CAD software for Windows — Sketch, Model, Assemble, Document.

## Features
- 3D Primitives (Box, Sphere, Cylinder, Cone)
- Sketch tools (Line, Polyline, Circle, Rectangle)
- Extrude, Revolve, Loft, Sweep, Helix
- Boolean (Union, Cut, Intersect)
- Fillet, Chamfer, Hole, Shell
- Standard Parts (Bolts, Nuts, Washers, Bearings)
- Spur Gear generator
- Threading
- Assembly Mates + Exploded View
- 4-View Drawing with dimensions
- STL / STEP / DXF export
- WebGL HTML viewer
- Mass + Center of Mass analysis

## Install & Run

### Prerequisites
- Python 3.12
- Windows 10/11

### Setup
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install cadquery PySide6 pyvista pyvistaqt
python main.py
