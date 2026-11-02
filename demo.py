"""Single-image demo. Examples: python demo.py --density 0.4
python demo.py --image path/to/image.png --density 0.6
"""
import argparse
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from experiment import ROOT,DATA,read_image,add_noise,metrics,METHODS,save_json,save_image

p=argparse.ArgumentParser()
p.add_argument('--image',type=Path,default=DATA/'clean/camera.png')
p.add_argument('--density',type=float,default=.4)
a=p.parse_args()
if not 0<=a.density<=1:p.error('--density must be between 0 and 1')
clean=read_image(a.image)
noisy,_=add_noise(clean,a.density,np.random.default_rng(20245641))
out=ROOT/'demo_output';out.mkdir(exist_ok=True)
methods=['Noisy','Mean3','Median3','Median5','Median7','AMF7']
canvas=Image.new('RGB',(3*256,2*288),'white');draw=ImageDraw.Draw(canvas)
scores={}
for i,m in enumerate(methods):
    result=METHODS[m](noisy);save_image(out/f'{m}.png',result)
    scores[m]=metrics(clean,result)
    thumbnail=Image.fromarray(np.rint(np.clip(result,0,255)).astype(np.uint8))
    thumbnail.thumbnail((256,256))
    x,y=i%3*256,i//3*288
    canvas.paste(thumbnail,(x,y+32));value=scores[m]['psnr_db']
    draw.text((x+6,y+8),f'{m}  PSNR '+(f'{value:.2f}' if value is not None else 'infinity'),fill='black')
canvas.save(out/'comparison.png');save_json(out/'metrics.json',scores)
print('Saved demo_output/comparison.png and metrics.json')
