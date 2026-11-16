# Derive the HC-PM254-5.0H-1x5PZ model from the manufacturer-series 1x7 model (same body
# section and pins): keep pins 1-5, cut the body to 5 positions (5*2.54+0.4 = 13.1 mm).
# Kept in the 1x7's frame (pins at x = -7.62 ... 2.54); KiCad offset handles placement.
import sys
from OCP.STEPCAFControl import STEPCAFControl_Reader, STEPCAFControl_Writer
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorSurf, XCAFDoc_ColorGen
from OCP.TDF import TDF_ChildIterator
from OCP.Quantity import Quantity_Color
from OCP.TopAbs import TopAbs_FACE, TopAbs_SOLID
from OCP.TopExp import TopExp_Explorer
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.gp import gp_Pnt
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.TopoDS import TopoDS_Compound
from OCP.BRep import BRep_Builder
from OCP.STEPControl import STEPControl_AsIs
src,dst=sys.argv[1],sys.argv[2]
XCUT=-9.09+0.2+5*2.54+0.2
doc=TDocStd_Document(TCollection_ExtendedString("a"))
r=STEPCAFControl_Reader(); r.SetColorMode(True); r.ReadFile(src); r.Transfer(doc)
st=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main()); ct=XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
top=st.GetShape_s(TDF_ChildIterator(st.Label(),False).Value())
def col(s):
    c=Quantity_Color()
    return c if (ct.GetColor(s,XCAFDoc_ColorSurf,c) or ct.GetColor(s,XCAFDoc_ColorGen,c)) else None
def faces(s):
    e=TopExp_Explorer(s,TopAbs_FACE); out=[]
    while e.More(): out.append(e.Current()); e.Next()
    return out
box=BRepPrimAPI_MakeBox(gp_Pnt(XCUT,-50,-50),gp_Pnt(XCUT+100,50,50)).Shape()
comp=TopoDS_Compound(); B=BRep_Builder(); B.MakeCompound(comp)
fcols=[]  # (face, color)
e=TopExp_Explorer(top,TopAbs_SOLID)
while e.More():
    s=e.Current(); e.Next()
    b=Bnd_Box(); BRepBndLib.Add_s(s,b); x0=b.CornerMin().X(); x1=b.CornerMax().X()
    if x0>=XCUT-1e-6: continue
    fc=[(f,col(f) or col(s)) for f in faces(s)]
    if x1>XCUT+1e-6:
        cut=BRepAlgoAPI_Cut(s,box); ns=cut.Shape()
        newf=[]
        for f,c in fc:
            mods=list(cut.Modified(f)) if cut.HasModified() else []
            if mods: newf+=[(m,c) for m in mods]
            elif not cut.IsDeleted(f): newf.append((f,c))
        # new cut faces: colour like the body
        body=[c for f,c in fc if c is not None]
        known=set(id(x) for x,_ in newf)
        s=ns; fc2=[]
        for f in faces(ns):
            c=None
            for g,cc in newf:
                if g.IsSame(f): c=cc; break
            fc2.append((f,c if c is not None else (body[0] if body else None)))
        fc=fc2
    B.Add(comp,s); fcols+=fc
doc2=TDocStd_Document(TCollection_ExtendedString("b"))
st2=XCAFDoc_DocumentTool.ShapeTool_s(doc2.Main()); ct2=XCAFDoc_DocumentTool.ColorTool_s(doc2.Main())
L=st2.AddShape(comp,False)
n=0
for f,c in fcols:
    if c is None: continue
    sl=st2.AddSubShape(L,f)
    if not sl.IsNull(): ct2.SetColor(sl,c,XCAFDoc_ColorSurf); n+=1
print('faces coloured',n,'of',len(fcols))
w=STEPCAFControl_Writer(); w.SetColorMode(True); w.Transfer(doc2,STEPControl_AsIs); w.Write(dst)
