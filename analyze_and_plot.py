"""Create all report figures and paired summaries from saved measurements."""
from pathlib import Path
import csv,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from PIL import Image
from experiment import ROOT,DATA,RESULTS,NATURAL,METHODS,DENSITIES,save_json,read_image

F=RESULTS/'figures';F.mkdir(exist_ok=True)
summary=json.loads((RESULTS/'summary.json').read_text(encoding='utf-8'))
records=list(csv.DictReader((RESULTS/'metrics.csv').open(encoding='utf-8-sig')))
for r in records:
    r['density']=float(r['density']);r['ssim']=float(r['ssim']);r['mse']=float(r['mse'])
    r['psnr_db']=float(r['psnr_db']) if r['psnr_db'] else None
colors={'Noisy':'#909090','Mean3':'#9B7629','Median3':'#0072B2','Median5':'#E69F00',
        'Median7':'#009E73','AMF3':'#777777','AMF5':'#56B4E9','AMF7':'#CC3377','AMF9':'#664488'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,
                     'axes.spines.right':False,'savefig.facecolor':'white',
                     'figure.autolayout':False,'figure.constrained_layout.use':False,
                     'savefig.bbox':None})
main=['Noisy','Mean3','Median3','Median5','Median7','AMF7']
def stat(method,p,key='psnr_db',group='natural'):
    return next(s[key] for s in summary if s['group']==group and s['method']==method and s['density']==p)

fig,axs=plt.subplots(1,2,figsize=(10.2,3.5))
for m in main:
    ps=DENSITIES[1:]
    axs[0].plot(np.array(ps)*100,[stat(m,p) for p in ps],'o-',color=colors[m],label=m,ms=4)
    axs[1].plot(np.array(ps)*100,[stat(m,p,'ssim') for p in ps],'o-',color=colors[m],label=m,ms=4)
for ax,y in zip(axs,['Mean PSNR (dB)','Mean SSIM']):
    ax.set(xlabel='Salt-and-pepper replacement probability (%)',ylabel=y);ax.grid(alpha=.2)
fig.legend(*axs[0].get_legend_handles_labels(),loc='lower center',ncol=6,frameon=False,fontsize=10)
fig.tight_layout(rect=(0,.12,1,1));fig.savefig(F/'quality.png',dpi=220);plt.close(fig)

fig,axs=plt.subplots(1,2,figsize=(10.2,3.5))
for m in ['AMF3','AMF5','AMF7','AMF9']:
    axs[0].plot(np.array(DENSITIES[1:])*100,[stat(m,p) for p in DENSITIES[1:]],'o-',label=m,color=colors[m])
maps=json.loads((RESULTS/'window_stats.json').read_text(encoding='utf-8'))
props=[]
for p in DENSITIES:
    rs=[r for r in maps if r['group']=='natural' and r['density']==p]
    props.append({k:float(np.mean([r[k] for r in rs])) for k in
                  ['window_3_fraction','window_5_fraction','window_7_fraction','fallback_fraction','changed_fraction']})
base=np.zeros(len(DENSITIES))
for size,c in [(3,'#56B4E9'),(5,'#E69F00'),(7,'#CC3377')]:
    v=np.array([r[f'window_{size}_fraction'] for r in props])*100
    axs[1].bar(np.arange(len(DENSITIES)),v,bottom=base,label=f'{size} x {size}',color=c);base+=v
axs[0].set(xlabel='Replacement probability (%)',ylabel='Mean PSNR (dB)');axs[0].grid(alpha=.2)
axs[0].legend(frameon=False,ncol=2,fontsize=9)
axs[1].set(xticks=np.arange(len(DENSITIES)),xticklabels=[f'{p*100:g}' for p in DENSITIES],
           xlabel='Replacement probability (%)',ylabel='Selected window (%)',ylim=(0,100))
axs[1].legend(frameon=False,loc='upper center',bbox_to_anchor=(.5,1.2),ncol=3,fontsize=9)
fig.tight_layout();fig.savefig(F/'windows.png',dpi=220);plt.close(fig)

# Dataset overview uses fixed, equally sized images, no contrast adjustment.
fig,axs=plt.subplots(2,3,figsize=(9,5.7))
for ax,name in zip(axs.flat,NATURAL):
    ax.imshow(read_image(DATA/'clean'/f'{name}.png'),cmap='gray',vmin=0,vmax=255)
    ax.set_title(name);ax.axis('off')
fig.tight_layout(pad=.5);fig.savefig(F/'dataset.png',dpi=220);plt.close(fig)

display=['Clean','Noisy','Mean3','Median3','Median7','AMF7']
for name,p in [('camera',.4),('coins',.8)]:
    folder=RESULTS/'visuals'/f'{name}_p{p:.2f}'
    fig,axs=plt.subplots(2,3,figsize=(9,6.5))
    for ax,m in zip(axs.flat,display):
        ax.imshow(read_image(folder/f'{m}.png'),cmap='gray',vmin=0,vmax=255);ax.set_title(m);ax.axis('off')
    fig.subplots_adjust(left=.01,right=.99,bottom=.01,top=.94,wspace=.04,hspace=.15)
    fig.savefig(F/f'{name}_full.png',dpi=220);plt.close(fig)
    fig,axs=plt.subplots(1,4,figsize=(10,3.0))
    for ax,m in zip(axs,['Clean','Median3','Median7','AMF7']):
        image=read_image(folder/f'{m}.png')[80:176,80:176]
        ax.imshow(image,cmap='gray',vmin=0,vmax=255,interpolation='nearest');ax.set_title(m);ax.axis('off')
    fig.subplots_adjust(left=.01,right=.99,bottom=.02,top=.88,wspace=.04)
    fig.savefig(F/f'{name}_crop.png',dpi=220);plt.close(fig)

# Failure visualizations are predetermined controls, not selected by score.
for name in ['thin_lines','binary_shapes']:
    folder=RESULTS/'visuals'/f'{name}_p0.00'
    fig,axs=plt.subplots(1,4,figsize=(10,3.0))
    region=(slice(20,116),slice(10,106)) if name=='thin_lines' else (slice(0,96),slice(0,96))
    for ax,m in zip(axs,['Clean','Median3','Median7','AMF7']):
        ax.imshow(read_image(folder/f'{m}.png')[region],cmap='gray',vmin=0,vmax=255,interpolation='nearest')
        ax.set_title(m);ax.axis('off')
    fig.subplots_adjust(left=.01,right=.99,bottom=.02,top=.88,wspace=.04)
    fig.savefig(F/f'{name}_control.png',dpi=220);plt.close(fig)

folder=RESULTS/'visuals/coins_p0.80'
size_map=np.load(folder/'window_size.npy')
fig,axs=plt.subplots(1,3,figsize=(10,3.3))
axs[0].imshow(read_image(folder/'Noisy.png'),cmap='gray',vmin=0,vmax=255);axs[0].set_title('Noisy (80%)')
cmap=ListedColormap(['#56B4E9','#E69F00','#CC3377'])
im=axs[1].imshow(size_map,cmap=cmap,norm=BoundaryNorm([2,4,6,8],3));axs[1].set_title('AMF7 selected window')
cb=fig.colorbar(im,ax=axs[1],ticks=[3,5,7],fraction=.046,pad=.03);cb.ax.tick_params(labelsize=9)
axs[2].imshow(read_image(folder/'AMF7.png'),cmap='gray',vmin=0,vmax=255);axs[2].set_title('AMF7 output')
for ax in axs:ax.axis('off')
fig.subplots_adjust(left=.01,right=.99,bottom=.02,top=.86,wspace=.18)
fig.savefig(F/'window_map.png',dpi=220);plt.close(fig)

paired=[]
for p in DENSITIES[1:]:
    record={'density':p}
    for b in ['Median3','Median5','Median7']:
        differences=[]
        for image in NATURAL:
            a=np.mean([r['psnr_db'] for r in records if r['image']==image and r['method']=='AMF7' and r['density']==p])
            v=np.mean([r['psnr_db'] for r in records if r['image']==image and r['method']==b and r['density']==p])
            differences.append(float(a-v))
        record[b]={'mean_delta_db':float(np.mean(differences)),
                   'min_image_delta_db':min(differences),'max_image_delta_db':max(differences),
                   'images_improved':sum(d>0 for d in differences),'total_images':len(differences),
                   'image_deltas':dict(zip(NATURAL,differences))}
    paired.append(record)

rv=json.loads((RESULTS/'random_value_impulse.json').read_text(encoding='utf-8'))
robust={m:{k:float(np.mean([r[k] for r in rv if r['method']==m])) for k in ['psnr_db','ssim']}
        for m in ['Noisy','Median3','Median5','AMF7']}
analysis={'paired':paired,'window_proportions':[{'density':p,**r} for p,r in zip(DENSITIES,props)],
          'random_value_impulse_means':robust}
save_json(RESULTS/'analysis.json',analysis)
print(json.dumps({'natural_p40':{m:stat(m,.4) for m in main},
                  'natural_p80':{m:stat(m,.8) for m in main},
                  'paired':paired,'robustness':robust},ensure_ascii=False,indent=2))
