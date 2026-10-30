import sys, math, json
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, Rectangle
from geom import Board, rot
from place import PLACE, W, H

def corners(p, grow=0.0):
    w, h = p['w']/2+grow, p['h']/2+grow
    pts=[(-w,-h),(w,-h),(w,h),(-w,h)]
    return [(p['cx']+x, p['cy']+y) for x,y in (rot(a,b,p['ang']) for a,b in pts)]

def draw(b, out, routes=None, title=''):
    fig, ax = plt.subplots(figsize=(16, 16*H/W+0.5))
    ax.add_patch(Rectangle((0,0),W,H,fill=False,lw=1.5,ec='k'))
    cols = {}
    import itertools
    pal = itertools.cycle(plt.cm.tab20.colors)
    for ref in b.fps:
        x0,y0,x1,y1 = b.courtyard(ref)
        ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,fill=False,lw=0.5,ec='m',ls='--'))
        fx,fy,_ = b.fp_pos(ref)
        ax.text((x0+x1)/2, y0-0.2, ref, fontsize=7, ha='center', va='bottom', color='m')
    if routes:
        for t in routes.get('tracks',[]):
            c = 'tab:red' if t['layer']=='F.Cu' else 'tab:blue'
            ax.plot([t['x1'],t['x2']],[t['y1'],t['y2']],color=c,lw=t['w']*16*72/ (W*1.0)/1.0*0.9, solid_capstyle='round',alpha=0.6)
        for v in routes.get('vias',[]):
            ax.add_patch(Circle((v['x'],v['y']),v['size']/2,fc='gold',ec='k',lw=0.3))
    for p in b.pads():
        if p['net'] not in cols: cols[p['net']] = next(pal)
        if p['shape']=='circle' and p['w']==p['h']:
            ax.add_patch(Circle((p['cx'],p['cy']),p['w']/2,fc=cols[p['net']],ec='k',lw=0.3, alpha=0.8))
        else:
            ax.add_patch(Polygon(corners(p),fc=cols[p['net']],ec='k',lw=0.3,alpha=0.8))
        if p['drill']:
            ax.add_patch(Circle((p['cx'],p['cy']),min(p['drill'])/2,fc='w',ec='k',lw=0.3))
        lab = p['net'].replace('/','')
        if lab and not lab.startswith('unconnected'):
            ax.text(p['cx'],p['cy'],lab,fontsize=4,ha='center',va='center')
    ax.set_xlim(-2,W+2); ax.set_ylim(H+2,-3); ax.set_aspect('equal'); ax.grid(True,lw=0.2)
    ax.set_xticks(range(0,int(W)+1,2)); ax.set_yticks(range(0,int(H)+1,2)); ax.tick_params(labelsize=6)
    ax.set_title(title)
    fig.savefig(out, dpi=110, bbox_inches='tight'); plt.close(fig)

def crt_overlaps(b):
    refs=list(b.fps); bad=[]
    for i,a in enumerate(refs):
        A=b.courtyard(a)
        for c in refs[i+1:]:
            C=b.courtyard(c)
            if A[0]<C[2] and C[0]<A[2] and A[1]<C[3] and C[1]<A[3]:
                ox=min(A[2],C[2])-max(A[0],C[0]); oy=min(A[3],C[3])-max(A[1],C[1])
                bad.append((a,c,round(ox,2),round(oy,2)))
    return bad

if __name__=='__main__':
    b = Board('orig.kicad_pcb')
    for r,(x,y,a) in PLACE.items(): b.place(r,x,y,a)
    missing=[r for r in b.fps if r not in PLACE]; print('unplaced',missing)
    for o in crt_overlaps(b): print('overlap',o)
    draw(b,'place.png','','placement')
