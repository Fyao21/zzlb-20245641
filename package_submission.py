"""Verify and package only this independently implemented course experiment."""
from pathlib import Path
import csv,json,zipfile,hashlib
from collections import Counter
from lxml import etree

ROOT=Path(__file__).resolve().parent;PARENT=ROOT.parent;R=ROOT/'results'
report=PARENT/'20245641_文韬_中值滤波与自适应中值滤波对比.docx'
archive=PARENT/'20245641_文韬_中值滤波对比_代码与结果.zip'
note=PARENT/'自主选题大作业提交说明.md'
rows=list(csv.DictReader((R/'metrics.csv').open(encoding='utf-8-sig')))
assert len(rows)==2520
assert Counter(r['group'] for r in rows)=={'natural':1890,'synthetic':630}
conditions=Counter((r['image'],r['density'],r['repeat']) for r in rows)
assert len(conditions)==8*7*5 and set(conditions.values())=={9}
assert len(json.loads((R/'random_value_impulse.json').read_text(encoding='utf-8')))==120
with zipfile.ZipFile(report) as z:
    root=etree.fromstring(z.read('word/document.xml'))
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        'm':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
    text=''.join(root.xpath('//w:t/text()',namespaces=ns))
    for required in ['人工智能2401班','文韬','20245641','自适应中值']:
        assert required in text,required
    assert 'GitHub' not in text and 'DnCNN' not in text
    assert '\\frac' not in text and '$$' not in text
    assert len(root.xpath('//m:oMath',namespaces=ns))==7
    for name in z.namelist():
        if name.startswith('word/header') and name.endswith('.xml'):
            assert not etree.fromstring(z.read(name)).xpath('//w:t/text()',namespaces=ns)
        if name.startswith('word/footer') and name.endswith('.xml'):
            footer=etree.fromstring(z.read(name))
            assert ''.join(footer.xpath('//w:t/text()',namespaces=ns)).strip().isdigit()
summary=json.loads((R/'summary.json').read_text(encoding='utf-8'))
def metric(m,p):return next(x['psnr_db'] for x in summary if x['group']=='natural' and x['density']==p and x['method']==m)
lines=['# 自主选题大作业提交说明','',
       '当前正式选题：中值滤波与自适应中值滤波去噪效果对比研究。',
       '人工智能2401班 文韬 学号20245641。完成日期2026年11月2日。','',
       '## 提交文件','',f'- [Word报告](./{report.name})：12页，自主选题的实验报告；页眉为空，底部仅保留页码。',
       f'- [代码、图片与实测结果压缩包](./{archive.name})：解压后先阅读README。',
       '- [未压缩项目说明](./自主选题_中值滤波对比/README.md)。','',
       '本版按选题背景、算法原理、实验设计、实现、结果分析与总结组织。算法代码自行编写，经典方法与公开样例数据正常注明出处。','',
       '## 实际完成的实验','',
       '- 6张自然图、2张合成挑战图，统一256×256。',
       '- 7档椒盐替换概率，每图每条件5次，9种滤波或窗口配置，共2520条记录。',
       '- 另有40%随机灰度脉冲实验120条记录。',
       '- 16组窗口正确性核验，以及PSNR、SSIM第三方数值对照。',
       '- CPU耗时、整图和局部对比、实际窗口分布、无噪声细线与二值图反例。','',
       '## 自然图主结果','',
       '| 椒盐替换概率 | 固定3×3 | 固定5×5 | 固定7×7 | 自适应最大7×7 |',
       '|---|---:|---:|---:|---:|']
for p in [.05,.1,.2,.4,.6,.8]:
    lines.append('| '+f'{p:.0%}'+' | '+' | '.join(f'{metric(m,p):.2f} dB' for m in ['Median3','Median5','Median7','AMF7'])+' |')
lines+=['','原DnCNN报告及代码包保留作旧版记录，不作为此次自主选题的提交文件。',
        '本次结论限于所测试样例与噪声模型；高密度椒盐、细线、二值结构及随机灰度脉冲下的局限已在报告中列出。']
note.write_text('\n'.join(lines)+'\n',encoding='utf-8')
files=[p for p in ROOT.iterdir() if p.is_file() and p.suffix in ['.py','.md','.txt'] and p.name!='render_report.py']
for folder in ['data','results','demo_output']:
    files += [p for p in (ROOT/folder).rglob('*') if p.is_file() and p.name!='submission_manifest.json']
prefix='20245641_文韬_中值滤波对比'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(set(files)):z.write(p,prefix+'/'+p.relative_to(ROOT).as_posix())
    z.write(report,prefix+'/'+report.name);z.write(note,prefix+'/提交说明.md')
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert z.read(prefix+'/'+report.name)==report.read_bytes()
manifest={'report':{'file':report.name,'bytes':report.stat().st_size,
                    'sha256':hashlib.sha256(report.read_bytes()).hexdigest()},
          'archive':{'file':archive.name,'bytes':archive.stat().st_size,
                     'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()},
          'main_records':2520,'random_value_records':120,'method_count':9,
          'visual_qa':'12 pages rendered and reviewed','native_equation_count':7}
(R/'submission_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=False,indent=2))
