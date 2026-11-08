"""Makes the link-preview picture (og.jpg, 1200x630, used when the site link is shared) and the
scan-to-play QR poster (icons/neon_arcade_qr.png). Needs Pillow and OpenCV. Run: python3 icons/share_images.py"""
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')+'/'  # repo root
PX=R+'games/fonts/PressStart2P-Regular.ttf'; VT=R+'games/fonts/VT323-Regular.ttf'
BG=(7,3,15); MAG=(255,43,214); CY=(25,243,255); YEL=(255,233,77); GRN=(57,255,122); OR=(255,158,44); RD=(232,86,106); MUT=(154,139,214)
def glow(base,draw_fn,col,rad=10,strength=2):
    lay=Image.new('RGBA',base.size,(0,0,0,0));draw_fn(ImageDraw.Draw(lay),col)
    g=lay.filter(ImageFilter.GaussianBlur(rad))
    for _ in range(strength):base.alpha_composite(g)
    base.alpha_composite(lay)
def scan(im):
    d=ImageDraw.Draw(im,'RGBA')
    for y in range(0,im.height,3):d.line([(0,y+2),(im.width,y+2)],fill=(0,0,0,40))
def bg(w,h):
    im=Image.new('RGBA',(w,h),BG+(255,));g=Image.new('RGBA',(w,h),(0,0,0,0));d=ImageDraw.Draw(g)
    d.ellipse([-w*.2,-h*.6,w*1.2,h*.5],fill=MAG+(50,));d.ellipse([-w*.2,h*.6,w*1.2,h*1.6],fill=CY+(36,))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(120)));return im
# ---- preview card 1200x630
W,H=1200,630;im=bg(W,H)
ic=Image.open(R+'icon.png').convert('RGBA').resize((590,590),Image.LANCZOS)
m=Image.new('L',(590,590),0);ImageDraw.Draw(m).rounded_rectangle([0,0,589,589],48,fill=255)
scan(im)
glow(im,lambda d,c:d.rounded_rectangle([18,18,612,612],52,outline=c,width=5),MAG,14,2)
im.paste(ic,(20,20),m)
x=665;fp=ImageFont.truetype(PX,30);fv=ImageFont.truetype(VT,52);fs=ImageFont.truetype(VT,36)
glow(im,lambda d,c:d.text((x,52),'5 GAMES',font=fp,fill=c),YEL,8,2)
for i,(t,c) in enumerate([('Knucklebones',GRN),('Othello',MAG),('Water Sort',CY),('Sudoku',OR),('Remi',RD)]):
    y=118+i*70
    glow(im,lambda d,cc,y=y:d.rounded_rectangle([x,y+12,x+22,y+34],4,fill=cc),c,6,1)
    glow(im,lambda d,cc,y=y,t=t:d.text((x+40,y-2),t,font=fv,fill=cc),c,7,1)
ImageDraw.Draw(im).text((x,486),'Solo, vs CPU or a friend',font=fs,fill=(234,246,255))
ImageDraw.Draw(im).text((x,530),'Free · plays offline',font=fs,fill=MUT)
im.convert('RGB').save(R+'og.jpg',quality=88,optimize=True,progressive=True)
# ---- QR poster 1080x1350
URL='https://need4ink.github.io/neon_arcade_90s/'
enc=cv2.QRCodeEncoder.create(cv2.QRCodeEncoder_Params());
try:
    p=cv2.QRCodeEncoder_Params();p.correction_level=cv2.QRCodeEncoder_CORRECT_LEVEL_H;enc=cv2.QRCodeEncoder.create(p)
except Exception as e:print('ecc default',e)
q=enc.encode(URL)  # 1 px per module incl quiet zone
n=q.shape[0];print('modules',n)
W,H=1080,1350;im=bg(W,H);scan(im)
ft=ImageFont.truetype(PX,72)
for i,(t,c) in enumerate([('NEON',MAG),('ARCADE',CY)]):
    w=ImageDraw.Draw(im).textlength(t,font=ft)
    glow(im,lambda d,cc,t=t,w=w,i=i:d.text(((W-w)/2,90+i*100),t,font=ft,fill=cc),c,14,3)
    ImageDraw.Draw(im).text(((W-w)/2,90+i*100),t,font=ft,fill=(255,255,255))
S=620;cell=S//n;S=cell*n;X=(W-S)//2;Y=330
glow(im,lambda d,c:d.rounded_rectangle([X-34,Y-34,X+S+34,Y+S+34],36,outline=c,width=8),CY,16,3)
ImageDraw.Draw(im).rounded_rectangle([X-26,Y-26,X+S+26,Y+S+26],30,fill=(255,255,255))
qi=Image.fromarray(q).convert('L').resize((S,S),Image.NEAREST)
dark=Image.new('RGBA',(S,S),BG+(255,));im.paste(dark,(X,Y),Image.eval(qi,lambda v:255-v))
fy=ImageFont.truetype(PX,40);t='SCAN TO PLAY';w=ImageDraw.Draw(im).textlength(t,font=fy)
glow(im,lambda d,c:d.text(((W-w)/2,Y+S+90),t,font=fy,fill=c),YEL,10,2)
fv=ImageFont.truetype(VT,44)
for i,(t,c) in enumerate([('Knucklebones · Othello · Water Sort',(234,246,255)),('Sudoku · Remi',(234,246,255)),('Add to Home Screen to play offline',MUT)]):
    w=ImageDraw.Draw(im).textlength(t,font=fv);ImageDraw.Draw(im).text(((W-w)/2,Y+S+170+i*52),t,font=fv,fill=c)
out=R+'icons/neon_arcade_qr.png';im.convert('RGB').save(out,optimize=True)
# verify the code scans
img=cv2.imread(out);val,_,_=cv2.QRCodeDetector().detectAndDecode(img);print('decoded:',val)
small=cv2.resize(img,(360,450));print('decoded small:',cv2.QRCodeDetector().detectAndDecode(small)[0])
# ---- QR as a small SVG for the cover's share pop-up (dark modules as one path; build.py embeds icons/qr.svg)
qm=(q<128);n=qm.shape[0];d=[]
for y in range(n):
    x=0
    while x<n:
        if qm[y,x]:
            s0=x
            while x<n and qm[y,x]:x+=1
            d.append('M%d %dh%dv1h-%dz'%(s0,y,x-s0,x-s0))
        else:x+=1
open(R+'icons/qr.svg','w').write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" shape-rendering="crispEdges" role="img" aria-label="QR code to %s"><rect width="%d" height="%d" fill="#fff"/><path fill="#07030f" d="%s"/></svg>'%(n,n,URL,n,n,''.join(d)))
print('qr.svg', len(''.join(d)))
