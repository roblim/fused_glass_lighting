"""Simplified 3D model of the JILN JL212R-35003B01 / Degson DG212R-THR-3.5-03P horizontal push-in
terminal block (3 poles, 3.5 mm), from the makers' drawings: body 11.2 x 12.3 x 8.5 mm, release
buttons 1.5 mm proud of the wire face, two 0.8 mm pins per pole 7.0 mm apart, pins 3.5 mm long.
Built in KiCad model coordinates (x right, y up = -footprint y, z up), origin = pin 1 front row."""
import sys
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
from OCP.gp import gp_Pnt, gp_Ax2, gp_Dir
from OCP.TopoDS import TopoDS_Compound
from OCP.BRep import BRep_Builder
from OCP.XCAFApp import XCAFApp_Application
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorType
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs
from OCP.TDataStd import TDataStd_Name
from OCP.TopLoc import TopLoc_Location

N, P = 3, 3.5
X0, X1 = -2.1, P * (N - 1) + 2.1
FRONT, REAR = -3.6, 8.7          # footprint y of the wire face and the rear face
TIP = -5.1                       # footprint y of the button fronts
H = 8.5


def box(x0, y0, z0, x1, y1, z1):
    # footprint y -> model y = -y
    ya, yb = sorted((-y0, -y1))
    return BRepPrimAPI_MakeBox(gp_Pnt(x0, ya, z0), gp_Pnt(x1, yb, z1)).Shape()


body = box(X0, FRONT, 0.0, X1, REAR, H)
for k in range(N):
    xc = k * P
    # wire entry: 2.0 mm hole into the front face, 9 mm deep
    cyl = BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(xc, -FRONT + 0.01, 2.7), gp_Dir(0, -1, 0)), 1.0, 9.0).Shape()
    body = BRepAlgoAPI_Cut(body, cyl).Shape()
    # slot above each button
    body = BRepAlgoAPI_Cut(body, box(xc - 1.3, FRONT - 0.01, 4.4, xc + 1.3, FRONT + 2.0, 8.0)).Shape()
    # separating grooves between poles on the front face
    if k:
        body = BRepAlgoAPI_Cut(body, box(xc - P / 2 - 0.15, FRONT - 0.01, 0.6, xc - P / 2 + 0.15, FRONT + 1.0, H - 0.6)).Shape()

buttons = None
for k in range(N):
    xc = k * P
    b = box(xc - 1.2, TIP, 4.6, xc + 1.2, FRONT + 1.9, 7.8)
    buttons = b if buttons is None else BRepAlgoAPI_Fuse(buttons, b).Shape()

pins = None
for k in range(N):
    for y in (0.0, 7.0):
        p = box(k * P - 0.4, y - 0.4, -3.5, k * P + 0.4, y + 0.4, 0.6)
        pins = p if pins is None else BRepAlgoAPI_Fuse(pins, p).Shape()

app = XCAFApp_Application.GetApplication_s()
doc = TDocStd_Document(TCollection_ExtendedString('MDTV-XCAF'))
app.InitDocument(doc)
st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
ct = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
asm = st.NewShape()
TDataStd_Name.Set_s(asm, TCollection_ExtendedString('JL212R-35003B01'))
for s, rgb, name in ((body, (0.08, 0.08, 0.08), 'housing'), (buttons, (0.93, 0.93, 0.90), 'buttons'), (pins, (0.80, 0.80, 0.78), 'pins')):
    lab = st.AddShape(s, False)
    TDataStd_Name.Set_s(lab, TCollection_ExtendedString(name))
    ct.SetColor(lab, Quantity_Color(*rgb, Quantity_TOC_RGB), XCAFDoc_ColorType.XCAFDoc_ColorSurf)
    st.AddComponent(asm, lab, TopLoc_Location())
st.UpdateAssemblies()
w = STEPCAFControl_Writer()
w.SetColorMode(True); w.SetNameMode(True)
w.Transfer(doc, STEPControl_AsIs)
w.Write(sys.argv[1])
print('wrote', sys.argv[1])
