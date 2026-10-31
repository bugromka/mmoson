# -*- coding: utf-8 -*-
"""ММОСО'Н — трёхмерная сцена станции и рендер внешнего вида.

Геометрия строится по числам документа. Балка соединяет ТОЛЬКО
подшипниковые узлы: её концы приварены к точкам axis_tip, которые
вычисляются из положения цапф, а не рисуются на глаз.

Растеризация: собственный z-буфер, модель освещения Блинна — Фонга,
источник — за камерой (Солнце светит на станцию спереди).
"""
import math, numpy as np
from PIL import Image, ImageDraw, ImageFilter

# ═══ ГЕОМЕТРИЯ ПО ДОКУМЕНТУ (метры) ═══
R      = 5000.
LCYL   = 40000.
CEND   = 4500.
GAPAX  = 21000.
AXLEN  = 9000.
AXR    = 260.
HUBR   = 1100.
HUBL   = 2200.

V=[]; F=[]; C=[]        # вершины, треугольники, цвет+материал

def add(verts, faces, col, spec=0.5, shin=48.):
    o=len(V); V.extend(verts)
    for f in faces: F.append((f[0]+o,f[1]+o,f[2]+o)); C.append((col,spec,shin))

def quad(a,b,c,d,col,**kw): add([a,b,c,d],[(0,1,2),(0,2,3)],col,**kw)

def tube(p0, p1, r0, r1, col, n=48, **kw):
    p0=np.array(p0,float); p1=np.array(p1,float)
    ax=p1-p0; L=np.linalg.norm(ax); ax=ax/L
    t=np.array([0,0,1.]) if abs(ax[2])<0.9 else np.array([1.,0,0])
    u=np.cross(ax,t); u/=np.linalg.norm(u); w=np.cross(ax,u)
    vs=[];fs=[]
    for i in range(n):
        a=2*math.pi*i/n
        d=math.cos(a)*u+math.sin(a)*w
        vs.append(tuple(p0+d*r0)); vs.append(tuple(p1+d*r1))
    for i in range(n):
        j=(i+1)%n
        fs.append((2*i,2*i+1,2*j+1)); fs.append((2*i,2*j+1,2*j))
    add(vs,fs,col,**kw)

def disc(c, ax, r, col, n=48, **kw):
    c=np.array(c,float); ax=np.array(ax,float); ax/=np.linalg.norm(ax)
    t=np.array([0,0,1.]) if abs(ax[2])<0.9 else np.array([1.,0,0])
    u=np.cross(ax,t); u/=np.linalg.norm(u); w=np.cross(ax,u)
    vs=[tuple(c)]; fs=[]
    for i in range(n):
        a=2*math.pi*i/n
        vs.append(tuple(c+(math.cos(a)*u+math.sin(a)*w)*r))
    for i in range(n): fs.append((0,1+i,1+(i+1)%n))
    add(vs,fs,col,**kw)

def dome(centre, axdir, a, c, col, nu=40, nv=14, **kw):
    """Полусфероид: полуось a поперёк, c вдоль оси."""
    centre=np.array(centre,float); ax=np.array(axdir,float)
    ax/=np.linalg.norm(ax)
    t=np.array([0,0,1.]) if abs(ax[2])<0.9 else np.array([1.,0,0])
    u=np.cross(ax,t); u/=np.linalg.norm(u); w=np.cross(ax,u)
    vs=[];fs=[]
    for j in range(nv+1):
        ph=math.pi/2*j/nv
        rr=a*math.cos(ph); hh=c*math.sin(ph)
        for i in range(nu):
            th=2*math.pi*i/nu
            vs.append(tuple(centre+(math.cos(th)*u+math.sin(th)*w)*rr+ax*hh))
    for j in range(nv):
        for i in range(nu):
            i2=(i+1)%nu
            A=j*nu+i; B=j*nu+i2; Cc=(j+1)*nu+i; D=(j+1)*nu+i2
            fs.append((A,B,D)); fs.append((A,D,Cc))
    add(vs,fs,col,**kw)

def box(centre, ex, ey, ez, col, **kw):
    cx,cy,cz=centre
    p=[(cx-ex,cy-ey,cz-ez),(cx+ex,cy-ey,cz-ez),(cx+ex,cy+ey,cz-ez),(cx-ex,cy+ey,cz-ez),
       (cx-ex,cy-ey,cz+ez),(cx+ex,cy-ey,cz+ez),(cx+ex,cy+ey,cz+ez),(cx-ex,cy+ey,cz+ez)]
    add(p,[(0,1,2),(0,2,3),(4,6,5),(4,7,6),(0,4,5),(0,5,1),
           (1,5,6),(1,6,2),(2,6,7),(2,7,3),(3,7,4),(3,4,0)],col,**kw)

def plate(centre, u, w, hu, hw, col, **kw):
    c=np.array(centre,float); u=np.array(u,float); w=np.array(w,float)
    u/=np.linalg.norm(u); w/=np.linalg.norm(w)
    quad(tuple(c-u*hu-w*hw), tuple(c+u*hu-w*hw),
         tuple(c+u*hu+w*hw), tuple(c-u*hu+w*hw), col, **kw)

# ═══ ЦВЕТА ═══
STEEL=(0.80,0.82,0.85); DARK=(0.34,0.37,0.42); HUBC=(0.62,0.65,0.69)
SOLAR=(0.055,0.085,0.26); RAD=(0.93,0.94,0.95); WHITE=(0.90,0.91,0.93)
GOLD=(0.55,0.45,0.16); GREEN=(0.10,0.20,0.09); TRUSSC=(0.68,0.71,0.75)

HALF=LCYL/2
tips={}          # сюда кладём КОНЧИКИ цапф — к ним крепится балка

for s in (+1,-1):                      # два цилиндра, ось X — вдоль
    y=s*GAPAX/2
    # обечайка
    tube((-HALF,y,0),(HALF,y,0),R,R,STEEL,n=96,spec=0.62,shin=34)
    # купола
    dome((HALF,y,0),(1,0,0),R,CEND,STEEL,nu=64,nv=22,spec=0.62,shin=34)
    dome((-HALF,y,0),(-1,0,0),R,CEND,STEEL,nu=64,nv=22,spec=0.62,shin=34)
    for sx in (+1,-1):                 # нос sx=+1, корма sx=-1
        base=sx*(HALF+CEND)
        tip =sx*(HALF+CEND+AXLEN)
        # цапфа
        tube((base,y,0),(tip,y,0),AXR*1.5,AXR,DARK,n=28,spec=0.7,shin=70)
        # подшипниковый узел на КОНЦЕ цапфы
        hc=sx*(HALF+CEND+AXLEN+HUBL/2)
        tube((hc-sx*HUBL/2,y,0),(hc+sx*HUBL/2,y,0),HUBR,HUBR,HUBC,
             n=32,spec=0.6,shin=50)
        disc((hc+sx*HUBL/2,y,0),(sx,0,0),HUBR,(0.24,0.26,0.30),n=32,spec=0.4)
        tips[(s,sx)]=hc                # ← точка крепления балки
# (навесное оборудование перенесено на балку — см. ниже)

# ═══ БАЛКИ: ТОЛЬКО МЕЖДУ КОНЧИКАМИ ЦАПФ ═══
def equip_on_truss(x, sx):
    """Оборудование стоит только на внешней торцевой раме.

    Вдоль цилиндрических частей между оболочками нет никаких элементов;
    x находится за торцевой полусферой и за подшипниковым узлом.
    """
    assert abs(x) > HALF + CEND, 'оборудование не должно попадать на оболочку'
    a=HUBR*0.85
    # Электромагнитные подшипники и мотор-генераторы находятся в корпусах
    # торцевой рамы. Они обслуживают только осевые цапфы; на оболочке и в
    # продольном межцилиндровом зазоре оборудования нет.
    for yb in (-GAPAX/2, GAPAX/2):
        box((x+sx*260,yb,0),300,900,600,DARK,spec=0.65,shin=65)
        tube((x+sx*560,yb,0),(x+sx*920,yb,0),430,430,HUBC,n=24,spec=0.7,shin=70)
    # крылья батарей: по балке, плоскостью к Солнцу (+X)
    for k,yc in enumerate((-6200,-2100,2100,6200)):
        for kz in (+1,-1):
            tube((x,yc,kz*a),(x,yc,kz*(a+700)),240,240,HUBC,n=12,spec=0.5)
            for seg in range(4):
                z0=kz*(a+700+seg*1800); z1=kz*(a+700+(seg+1)*1800-130)
                plate((x+260,yc,(z0+z1)/2),(0,1,0),(0,0,1),1250,
                      abs(z1-z0)/2,SOLAR,spec=0.55,shin=60)
            tube((x,yc,kz*(a+700)),(x,yc,kz*(a+700+4*1800)),100,100,
                 HUBC,n=8,spec=0.5)
    # радиаторы: белые панели вдоль балки, ребром к Солнцу
    for yc in (-8000,-4200,4200,8000):
        for kz in (+1,-1):
            plate((x,yc,kz*(a+2400)),(1,0,0),(0,0,1),1000,2100,RAD,
                  spec=0.25,shin=20)
    if sx>0:
        # НОС: модули стыковки на балке
        for yc in (-3600,0,3600):
            box((x+a*1.5,yc,0),1300,1500,900,WHITE,spec=0.35,shin=30)
            disc((x+a*1.5+1300,yc,0),(1,0,0),620,DARK,n=20,spec=0.4)
        box((x+a*1.5,0,1900),900,2600,900,WHITE,spec=0.35,shin=30)
    else:
        # КОРМА: высоконаправленные антенны на задней раме, тарелками
        # в номинальном направлении связи с Землёй (-X). Их привод независим
        # от корпуса и позволяет работать при уходе из Солнечной системы.
        for yc,rr in ((-7000,2600),(-2400,3200),(2400,3200),(7000,2600)):
            tube((x,yc,a),(x-1200,yc,a+1700),220,220,HUBC,n=10,spec=0.5)
            dome((x-1200,yc,a+1700),(-1,0,0),rr,rr*0.40,WHITE,
                 nu=32,nv=9,spec=0.30,shin=25)
        # Собственные двигательные модули: только на задней неподвижной раме.
        # Сопла направлены назад; они не закреплены на вращающейся оболочке.
        for yc in (-5200, 5200):
            box((x-1500,yc,0),650,1150,900,DARK,spec=0.55,shin=45)
            tube((x-2150,yc,0),(x-4100,yc,0),650,950,DARK,n=24,spec=0.65,shin=55)
            disc((x-4100,yc,0),(-1,0,0),950,(0.10,0.12,0.15),n=32,spec=0.35)

def truss(x, y0, y1, bays=16):
    """Ферма между двумя узлами. Строится от tips до tips."""
    a=HUBR*0.85
    ln=abs(y1-y0); step=ln/bays
    rails=[(0,+a),(0,-a),(+a,0),(-a,0)]      # 4 пояса
    for dz,dy in rails:
        tube((x+dz,y0,dy),(x+dz,y1,dy),200,200,TRUSSC,n=10,spec=0.6,shin=60)
    for i in range(bays):                     # раскосы
        ya=min(y0,y1)+i*step; yb=ya+step
        for (dz1,dy1),(dz2,dy2) in [((0,a),(0,-a)),((a,0),(-a,0))]:
            tube((x+dz1,ya,dy1),(x+dz2,yb,dy2),95,95,TRUSSC,n=6,spec=0.6)
        for dz,dy in rails:                   # стойки
            tube((x+dz,yb,dy),(x-dz if dz else dz, yb, -dy if dy else dy),
                 85,85,TRUSSC,n=6,spec=0.6)

for sx in (+1,-1):
    x=tips[(+1,sx)]
    assert abs(tips[(+1,sx)]-tips[(-1,sx)])<1e-9, 'узлы не на одной линии'
    truss(x, +GAPAX/2, -GAPAX/2)
    equip_on_truss(x, sx)

print(f'вершин {len(V)}, треугольников {len(F)}')
print(f'кончики цапф по X: нос {tips[(1,1)]:.0f} м, корма {tips[(1,-1)]:.0f} м')
print(f'балка идёт по Y от {GAPAX/2:.0f} до {-GAPAX/2:.0f} при X={tips[(1,1)]:.0f}')
print(f'габарит корпуса по X: ±{HALF+CEND:.0f} м -> балка вынесена '
      f'на {AXLEN+HUBL/2:.0f} м за корпус')

# ═══ КАМЕРА ═══
W,H=1920,1080
eye=np.array([166000., 92000., 62000.])
tgt=np.array([2000., 0., 0.])
up =np.array([0.,0.,1.])
fw=tgt-eye; fw/=np.linalg.norm(fw)
rt=np.cross(fw,up); rt/=np.linalg.norm(rt)
uu=np.cross(rt,fw)
FOV=math.radians(30.)
f=(W/2)/math.tan(FOV/2)

P=np.array(V,float)
rel=P-eye
cam=np.stack([rel@rt, rel@uu, rel@fw],1)
z=cam[:,2].copy(); z[z<1e-6]=1e-6
sx_=W/2+cam[:,0]/z*f
sy_=H/2-cam[:,1]/z*f
scr=np.stack([sx_,sy_,cam[:,2]],1)

# Солнце ЗА КАМЕРОЙ: светит на станцию спереди
Ldir=fw.copy()
Vdir=-fw

img=np.zeros((H,W,3),np.float32)
zbuf=np.full((H,W),1e30,np.float32)

tri=np.array(F)
p0=scr[tri[:,0]]; p1=scr[tri[:,1]]; p2=scr[tri[:,2]]
w0=P[tri[:,0]]; w1=P[tri[:,1]]; w2=P[tri[:,2]]
nrm=np.cross(w1-w0,w2-w0)
nl=np.linalg.norm(nrm,axis=1); nl[nl==0]=1
nrm=nrm/nl[:,None]
zc=(p0[:,2]+p1[:,2]+p2[:,2])/3
order=np.argsort(-zc)

def shade(n, col, spec, shin):
    if n@Vdir < 0: n=-n
    dif=max(0.,n@(-Ldir))
    hv=(-Ldir+Vdir); hv/=np.linalg.norm(hv)
    sp=max(0.,n@hv)**shin*spec
    rim=(1-max(0.,n@Vdir))**3*0.16
    a=np.array(col,float)*(0.10+0.92*dif)+sp+rim
    return np.clip(a,0,1)

drawn=0
for k in order:
    if p0[k,2]<=1 or p1[k,2]<=1 or p2[k,2]<=1: continue
    xs=[p0[k,0],p1[k,0],p2[k,0]]; ys=[p0[k,1],p1[k,1],p2[k,1]]
    x0=int(max(0,math.floor(min(xs)))); x1=int(min(W-1,math.ceil(max(xs))))
    y0=int(max(0,math.floor(min(ys)))); y1=int(min(H-1,math.ceil(max(ys))))
    if x1<x0 or y1<y0: continue
    ax_,ay_=p0[k,0],p0[k,1]; bx,by=p1[k,0],p1[k,1]; cx_,cy_=p2[k,0],p2[k,1]
    den=(by-cy_)*(ax_-cx_)+(cx_-bx)*(ay_-cy_)
    if abs(den)<1e-9: continue
    yy,xx=np.mgrid[y0:y1+1, x0:x1+1]
    xx=xx+0.5; yy=yy+0.5
    l1=((by-cy_)*(xx-cx_)+(cx_-bx)*(yy-cy_))/den
    l2=((cy_-ay_)*(xx-cx_)+(ax_-cx_)*(yy-cy_))/den
    l3=1-l1-l2
    m=(l1>=0)&(l2>=0)&(l3>=0)
    if not m.any(): continue
    zz=l1*p0[k,2]+l2*p1[k,2]+l3*p2[k,2]
    sub=zbuf[y0:y1+1, x0:x1+1]
    m&= zz<sub
    if not m.any(): continue
    col,spec,shin=C[k]
    rgb=shade(nrm[k],col,spec,shin)
    sub[m]=zz[m]
    img[y0:y1+1, x0:x1+1][m]=rgb
    drawn+=1

print(f'отрисовано треугольников: {drawn}')

# ═══ ЗВЁЗДЫ, ЗЕМЛЯ, СВЕДЕНИЕ ═══
rng=np.random.default_rng(7)
bg=np.zeros((H,W,3),np.float32)
for _ in range(2600):
    x=rng.integers(0,W); y=rng.integers(0,H); b=rng.random()**3
    bg[y,x]=b*1.1
bg=np.array(Image.fromarray((np.clip(bg,0,1)*255).astype(np.uint8))
            .filter(ImageFilter.GaussianBlur(0.55)),np.float32)/255*1.7

mask=(zbuf<1e29)
out=np.where(mask[...,None], img, bg)
im=Image.fromarray((np.clip(out,0,1)**(1/1.9)*255).astype(np.uint8))

# Земля — вдали за кормой станции
d=ImageDraw.Draw(im)
_earth=np.array([-500000., -160000., -100000.])
_r=_earth-eye
_cam=np.array([_r@rt,_r@uu,_r@fw])
ex_=int(W/2+_cam[0]/_cam[2]*f); ey_=int(H/2-_cam[1]/_cam[2]*f); er=24
print(f'Земля за кормой: экран ({ex_},{ey_})')
d.ellipse([ex_-er,ey_-er,ex_+er,ey_+er], fill=(92,132,190))
d.ellipse([ex_-er+5,ey_-er+3,ex_+er-9,ey_+er-11], fill=(120,158,205))
d.ellipse([ex_-er+3,ey_-er+9,ex_-er+13,ey_-er+19], fill=(96,140,110))
im=im.filter(ImageFilter.SMOOTH)
# Стационарный постерный вывод удалён из комплекта проекта.
# Изображение остаётся в памяти для интерактивного запуска, но файл не сохраняется.
print('отрисовка внешнего вида завершена; постерный файл намеренно не сохраняется', im.size)
