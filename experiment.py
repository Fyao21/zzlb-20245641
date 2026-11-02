"""Dataset, paired evaluation, parameter study, correctness and timing.
Run: python experiment.py (uses bundled clean PNGs if already prepared).
"""
from pathlib import Path
import argparse, csv, hashlib, json, math, platform, time, os
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter
import filters

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
RESULTS = ROOT / 'results'
SEED = 20245641
DENSITIES = [0, .05, .10, .20, .40, .60, .80]
REPEATS = 5
NATURAL = ['camera', 'coins', 'moon', 'astronaut', 'chelsea', 'coffee']
SYNTHETIC = ['thin_lines', 'binary_shapes']
METHODS = {
    'Noisy': lambda a: a.copy(),
    'Mean3': lambda a: filters.mean_filter(a, 3),
    'Median3': lambda a: filters.median_filter(a, 3),
    'Median5': lambda a: filters.median_filter(a, 5),
    'Median7': lambda a: filters.median_filter(a, 7),
    'AMF3': lambda a: filters.adaptive_median(a, 3),
    'AMF5': lambda a: filters.adaptive_median(a, 5),
    'AMF7': lambda a: filters.adaptive_median(a, 7),
    'AMF9': lambda a: filters.adaptive_median(a, 9),
}


def save_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                   allow_nan=False), encoding='utf-8')


def save_image(path, array):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.rint(np.clip(array, 0, 255)).astype(np.uint8)).save(path)


def read_image(path):
    return np.asarray(Image.open(path).convert('L'))


def prepare_data():
    """Use documented scikit-image sample photographs, not a GitHub project."""
    if (DATA / 'manifest.json').exists():
        return json.loads((DATA / 'manifest.json').read_text(encoding='utf-8'))
    from skimage import data, __version__
    manifest = []
    for name in NATURAL:
        original = getattr(data, name)()
        original_path = DATA / 'originals' / f'{name}.png'
        original_path.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(original).save(original_path)
        gray = original
        if original.ndim == 3:
            gray = np.rint(original @ np.array([.2125, .7154, .0721])).astype(np.uint8)
        y, x = (gray.shape[0]-256)//2, (gray.shape[1]-256)//2
        crop = gray[y:y+256, x:x+256].copy()
        save_image(DATA / 'clean' / f'{name}.png', crop)
        manifest.append({'image': name, 'group': 'natural',
                         'source': 'scikit-image.data', 'package_version': __version__,
                         'source_shape': list(original.shape), 'crop_xywh': [x,y,256,256],
                         'pixel_sha256': hashlib.sha256(crop.tobytes()).hexdigest()})
    # Thin lines are interior gray levels, to isolate loss of narrow structures.
    im = Image.new('L', (256,256), 180)
    d = ImageDraw.Draw(im)
    for width, x in [(1,35),(2,65),(3,100),(5,140)]:
        d.line((x,25,x,225), fill=35, width=width)
    for width, y in [(1,40),(2,75),(3,115),(5,165)]:
        d.line((20,y,230,y), fill=235, width=width)
    d.rectangle((170,185,230,230),fill=70)
    thin = np.asarray(im)
    yy,xx=np.indices((256,256))
    binary = np.where(((yy//32)+(xx//32))%2, 255, 0).astype(np.uint8)
    for name,a in [('thin_lines',thin),('binary_shapes',binary)]:
        save_image(DATA / 'clean' / f'{name}.png', a)
        manifest.append({'image': name, 'group': 'synthetic',
                         'source': 'experiment.py deterministic construction',
                         'source_shape':[256,256], 'crop_xywh':[0,0,256,256],
                         'pixel_sha256': hashlib.sha256(a.tobytes()).hexdigest()})
    save_json(DATA / 'manifest.json', manifest)
    return manifest


def add_noise(clean, density, rng):
    """Replacement probability, not fraction of pixels actually changed."""
    u = rng.random(clean.shape)
    noisy = clean.copy()
    noisy[u < density/2] = 0
    noisy[(u >= density/2) & (u < density)] = 255
    return noisy, u < density


def metrics(clean, output):
    x,y = clean.astype(np.float64)/255, np.asarray(output,dtype=np.float64)/255
    mse = float(np.mean((x-y)**2))
    psnr = None if mse == 0 else -10*math.log10(mse)
    kw = dict(sigma=1.5, mode='reflect', truncate=3.5)
    ux,uy=gaussian_filter(x,**kw),gaussian_filter(y,**kw)
    vx=gaussian_filter(x*x,**kw)-ux*ux
    vy=gaussian_filter(y*y,**kw)-uy*uy
    cov=gaussian_filter(x*y,**kw)-ux*uy
    ssim_map=((2*ux*uy+.01**2)*(2*cov+.03**2))/((ux*ux+uy*uy+.01**2)*(vx+vy+.03**2))
    ssim=float(ssim_map[5:-5,5:-5].mean())
    return {'mse':mse, 'psnr_db':psnr, 'ssim':ssim}


def check_implementations():
    from scipy.ndimage import median_filter, uniform_filter
    from skimage.metrics import structural_similarity, peak_signal_noise_ratio
    rng=np.random.default_rng(SEED)
    arrays=[rng.integers(0,256,(11,13),dtype=np.uint8),
            rng.choice(np.array([0,128,255],dtype=np.uint8),(13,15)),
            np.zeros((11,13),dtype=np.uint8),
            np.full((11,13),255,dtype=np.uint8)]
    tests=[]
    for i,a in enumerate(arrays):
        for size in [3,5,7,9]:
            v=filters.adaptive_median(a,size)
            ref=filters.adaptive_median_reference(a,size)
            assert np.array_equal(v,ref),(i,size)
            assert np.array_equal(filters.median_filter(a,size),median_filter(a,size,mode='reflect'))
            assert np.allclose(filters.mean_filter(a,size),uniform_filter(a.astype(float),size,mode='reflect'),atol=1e-10)
            tests.append({'case':i,'size':size,'adaptive_exact':True,'fixed_exact':True,'mean_atol':1e-10})
    a=rng.integers(0,256,(64,64),dtype=np.uint8)
    b,_=add_noise(a,.2,rng)
    m=metrics(a,b)
    official=structural_similarity(a/255,b/255,data_range=1.,gaussian_weights=True,
                                  sigma=1.5,use_sample_covariance=False)
    assert abs(m['ssim']-official)<1e-12
    assert abs(m['psnr_db']-peak_signal_noise_ratio(a,b,data_range=255))<1e-12
    # An actual 3x3 cluster with 5 salt pixels; a 5x5 neighborhood is clean enough.
    patch=np.full((7,7),128,dtype=np.uint8)
    for y,x in [(2,2),(2,3),(3,2),(3,3),(4,4)]:patch[y,x]=255
    assert filters.median_filter(patch,3)[3,3]==255
    assert filters.adaptive_median(patch,5)[3,3]==128
    # This experiment's AMF is *not* guaranteed to preserve all clean binary edges.
    return {'window_checks':tests, 'ssim_abs_error':abs(m['ssim']-official),
            'psnr_abs_error':abs(m['psnr_db']-peak_signal_noise_ratio(a,b,data_range=255)),
            'cluster_patch':patch.tolist(),'cluster_center_median3':255,'cluster_center_amf5':128}


def run():
    started=time.perf_counter()
    manifest=prepare_data()
    RESULTS.mkdir(exist_ok=True)
    checks=check_implementations();save_json(RESULTS/'correctness.json',checks)
    records=[]; maps=[]
    for image_index,item in enumerate(manifest):
        name=item['image'];clean=read_image(DATA/'clean'/f'{name}.png')
        assert hashlib.sha256(clean.tobytes()).hexdigest()==item['pixel_sha256']
        for density_index,p in enumerate(DENSITIES):
            for repeat in range(REPEATS):
                seed=SEED+image_index*10000+density_index*100+repeat
                noisy,mask=add_noise(clean,p,np.random.default_rng(seed))
                visual=(repeat==0 and ((name=='camera' and p==.4) or
                        (name=='coins' and p==.8) or
                        (name in SYNTHETIC and p in [0,.4])))
                folder=RESULTS/'visuals'/f'{name}_p{p:.2f}'
                if visual:save_image(folder/'Clean.png',clean)
                for method,fn in METHODS.items():
                    if method=='AMF7':
                        out,info=filters.adaptive_median(noisy,7,True)
                        maps.append({'image':name,'group':item['group'],'density':p,'repeat':repeat,
                                     'changed_fraction':float(info['changed'].mean()),
                                     'fallback_fraction':float(info['fallback'].mean()),
                                     **{f'window_{s}_fraction':float((info['window_size']==s).mean()) for s in [3,5,7]}})
                        if visual:
                            np.save(folder/'window_size.npy',info['window_size'])
                    else:out=fn(noisy)
                    records.append({'image':name,'group':item['group'],'density':p,'repeat':repeat,
                                    'seed':seed,'method':method,'selected_fraction':float(mask.mean()),
                                    'actual_changed_fraction':float((noisy!=clean).mean()),**metrics(clean,out)})
                    if visual:save_image(folder/f'{method}.png',out)
        print(f'Completed {name}: {len(records)} records',flush=True)
    with (RESULTS/'metrics.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    summary=[]
    for group in ['natural','synthetic']:
        for p in DENSITIES:
            for method in METHODS:
                rs=[r for r in records if r['group']==group and r['density']==p and r['method']==method]
                values=[r['psnr_db'] for r in rs if r['psnr_db'] is not None]
                summary.append({'group':group,'density':p,'method':method,'n':len(rs),
                                'psnr_db':float(np.mean(values)) if len(values)==len(rs) else None,
                                'infinite_psnr_count':len(rs)-len(values),
                                'ssim':float(np.mean([r['ssim'] for r in rs])),
                                'mse':float(np.mean([r['mse'] for r in rs]))})
    save_json(RESULTS/'summary.json',summary);save_json(RESULTS/'window_stats.json',maps)
    # Robustness outside the exact salt-and-pepper model. Same seeds across methods.
    robustness=[]
    for j,name in enumerate(NATURAL):
        clean=read_image(DATA/'clean'/f'{name}.png')
        for repeat in range(REPEATS):
            rng=np.random.default_rng(SEED+100000+j*100+repeat)
            u=rng.random(clean.shape);out=clean.copy();replace=u<.4
            values=rng.integers(0,256,clean.shape,dtype=np.uint8);out[replace]=values[replace]
            for method in ['Noisy','Median3','Median5','AMF7']:
                robustness.append({'image':name,'repeat':repeat,'method':method,**metrics(clean,METHODS[method](out))})
    save_json(RESULTS/'random_value_impulse.json',robustness)
    # Timing excludes I/O and metrics, includes padding and filtering on one CPU thread of Python;
    # NumPy/SciPy may use their own compiled kernels, environment recorded separately.
    timing=[];clean=read_image(DATA/'clean/camera.png')
    for pi,p in enumerate([.1,.4,.8]):
        noisy,_=add_noise(clean,p,np.random.default_rng(SEED+200000+pi))
        for method in ['Mean3','Median3','Median5','Median7','AMF7']:
            fn=METHODS[method]
            for _ in range(3):fn(noisy)
            durations=[]
            for _ in range(15):
                t=time.perf_counter();fn(noisy);durations.append((time.perf_counter()-t)*1000)
            timing.append({'method':method,'density':p,'shape':[256,256],
                           'median_ms':float(np.median(durations)), 'mean_ms':float(np.mean(durations)),
                           'p95_ms':float(np.percentile(durations,95)),'samples_ms':durations})
    save_json(RESULTS/'latency.json',timing)
    import scipy,skimage,matplotlib,PIL
    cpu=os.environ.get('PROCESSOR_IDENTIFIER',platform.processor())
    save_json(RESULTS/'environment.json',{'python':platform.python_version(),'platform':platform.platform(),
              'cpu':cpu,'numpy':np.__version__,'scipy':scipy.__version__,'scikit_image':skimage.__version__,
              'matplotlib':matplotlib.__version__,'Pillow':PIL.__version__,
              'seed':SEED,'densities':DENSITIES,'repeats':REPEATS,'methods':list(METHODS),
              'elapsed_seconds':time.perf_counter()-started,'metric_records':len(records),
              'natural_records':sum(r['group']=='natural' for r in records),
              'random_value_records':len(robustness),'training':False,
              'cpu_only':True,'source':'independent implementation; no imported project code'})
    print(f'Done: {len(records)} main/sensitivity records; elapsed {time.perf_counter()-started:.1f}s',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare-only',action='store_true')
    args=parser.parse_args()
    if args.prepare_only:prepare_data()
    else:run()
