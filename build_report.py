"""Generate the Chinese course report from actual experiment artifacts.
Run using the bundled document Python runtime (python-docx required).
"""
from pathlib import Path
import json,csv
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parent;R=ROOT/'results';F=R/'figures'
S=json.loads((R/'summary.json').read_text(encoding='utf-8'))
A=json.loads((R/'analysis.json').read_text(encoding='utf-8'))
E=json.loads((R/'environment.json').read_text(encoding='utf-8'))
L=json.loads((R/'latency.json').read_text(encoding='utf-8'))
MAN=json.loads((ROOT/'data/manifest.json').read_text(encoding='utf-8'))
ROWS=list(csv.DictReader((R/'metrics.csv').open(encoding='utf-8-sig')))
MAIN=['Noisy','Mean3','Median3','Median5','Median7','AMF7']

def value(method,p,key='psnr_db',group='natural'):
    return next(x[key] for x in S if x['method']==method and x['density']==p and x['group']==group)
def time_value(method,p):return next(x['median_ms'] for x in L if x['method']==method and x['density']==p)
def image_value(image,method,p,key='psnr_db'):
    rs=[float(x[key]) for x in ROWS if x['image']==image and x['method']==method and float(x['density'])==p]
    return sum(rs)/len(rs)
def delta(p,base='Median7'):return value('AMF7',p)-value(base,p)

doc=Document();sec=doc.sections[0]
sec.page_width=Inches(8.5);sec.page_height=Inches(11)
sec.top_margin=Inches(.7);sec.bottom_margin=Inches(.65)
sec.left_margin=sec.right_margin=Inches(.8);sec.footer_distance=Inches(.28)
sec.different_first_page_header_footer=True
for name in ['Normal','Body Text','Title','Subtitle','Heading 1','Heading 2','Heading 3','Caption']:
    st=doc.styles[name];st.font.name='Times New Roman';st.font.color.rgb=RGBColor(0,0,0)
    st.element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'黑体' if name in ['Title','Heading 1','Heading 2','Heading 3'] else '宋体')
    st.font.size=Pt(11.5)
for st in doc.styles:
    for border in list(st.element.iter(qn('w:pBdr'))):border.getparent().remove(border)
st=doc.styles['Normal'];st.paragraph_format.line_spacing=1.22;st.paragraph_format.space_after=Pt(6)
for name,size in [('Title',23),('Subtitle',14),('Heading 1',16),('Heading 2',13),('Heading 3',12),('Caption',10)]:
    st=doc.styles[name];st.font.size=Pt(size);st.paragraph_format.space_before=Pt(8);st.paragraph_format.space_after=Pt(6)
    st.paragraph_format.keep_with_next=name not in ['Caption','Subtitle']
doc.styles['Title'].font.bold=True;doc.styles['Subtitle'].font.italic=False
doc.styles['Caption'].paragraph_format.space_before=Pt(4)
doc.styles['Caption'].paragraph_format.space_after=Pt(4)
footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE')
run=OxmlElement('w:r');pr=OxmlElement('w:rPr');sz=OxmlElement('w:sz');sz.set(qn('w:val'),'18');pr.append(sz);run.append(pr)
t=OxmlElement('w:t');t.text='2';run.append(t);field.append(run);footer._p.append(field)

def para(text='',bold=False):
    p=doc.add_paragraph();r=p.add_run(text);r.bold=bold;return p
def h(text,level=2):return doc.add_heading(text,level)
def page(title):
    p=h(title,1);p.paragraph_format.page_break_before=True
def caption(text):
    p=doc.add_paragraph(text,'Caption');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
def figure(name,width=6.65):
    p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.space_after=Pt(2)
    p.add_run().add_picture(str(F/name),width=Inches(width))
def table(headers,rows,widths,size=10):
    tb=doc.add_table(rows=1,cols=len(headers));tb.alignment=WD_TABLE_ALIGNMENT.CENTER;tb.autofit=False
    for col,w in zip(tb.columns,widths):col.width=Inches(w)
    for c,x in zip(tb.rows[0].cells,headers):c.text=str(x)
    for row in rows:
        for c,x in zip(tb.add_row().cells,row):c.text=str(x)
    borders=OxmlElement('w:tblBorders')
    for edge in ['top','bottom','left','right','insideH','insideV']:
        node=OxmlElement('w:'+edge);node.set(qn('w:val'),'single');node.set(qn('w:sz'),'4');node.set(qn('w:color'),'D9D9D9');borders.append(node)
    tb._tbl.tblPr.append(borders)
    for i,row in enumerate(tb.rows):
        cant=OxmlElement('w:cantSplit');row._tr.get_or_add_trPr().append(cant)
        for j,c in enumerate(row.cells):
            c.width=Inches(widths[j]);c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            pr=c._tc.get_or_add_tcPr();shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'DCE6F1' if i==0 else ('F5F7FA' if i%2==0 else 'FFFFFF'));pr.append(shade)
            margins=OxmlElement('w:tcMar')
            for edge in ['top','bottom','left','right']:
                node=OxmlElement('w:'+edge);node.set(qn('w:w'),'75');node.set(qn('w:type'),'dxa');margins.append(node)
            pr.append(margins)
            for p in c.paragraphs:
                p.paragraph_format.space_before=p.paragraph_format.space_after=Pt(2);p.paragraph_format.line_spacing=1.08
                p.alignment=WD_ALIGN_PARAGRAPH.CENTER if ((j>0 and len(c.text)<25) or c.text.isdigit()) else WD_ALIGN_PARAGRAPH.LEFT
                for run in p.runs:run.font.size=Pt(size);run.bold=i==0
    repeat=OxmlElement('w:tblHeader');tb.rows[0]._tr.get_or_add_trPr().append(repeat)
    p=doc.add_paragraph();p.paragraph_format.line_spacing=Pt(1);p.paragraph_format.space_after=Pt(4)
    p.add_run().font.size=Pt(1)
def code(text):
    p=doc.add_paragraph();p.paragraph_format.line_spacing=1.05;p.paragraph_format.space_after=Pt(6)
    r=p.add_run(text);r.font.name='Consolas';r.font.size=Pt(9.5)
def mr(s):
    r=OxmlElement('m:r');t=OxmlElement('m:t');t.text=s;r.append(t);return r
def fraction(a,b):
    f=OxmlElement('m:f');num=OxmlElement('m:num');num.append(mr(a));den=OxmlElement('m:den');den.append(mr(b));f.extend([num,den]);return f
def equation(parts):
    p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    mp=OxmlElement('m:oMathPara');m=OxmlElement('m:oMath')
    for part in parts:m.append(mr(part) if isinstance(part,str) else part)
    mp.append(m);p._p.append(mp)

# 1 Cover
para();para();para()
p=doc.add_paragraph('图像处理与分析期末大作业','Subtitle');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
p=doc.add_paragraph('中值滤波与自适应中值滤波\n去噪效果对比研究','Title');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
for _ in range(3):para()
for text in ['班级  人工智能2401班','姓名  文韬','学号  20245641','完成日期  2026年11月2日']:
    p=para(text);p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.space_after=Pt(15)

# 2
page('摘要与实验目的')
para('本实验围绕椒盐噪声下的灰度图像恢复问题，比较均值滤波、固定窗口中值滤波与自适应中值滤波。研究重点是窗口尺寸与局部判别规则怎样影响脉冲点去除、边缘细节和计算开销。实验不需要训练模型，便于把图像处理原理、程序实现和实际结果对应起来。')
para('我使用六张公开自然样例的256×256灰度中心区域进行主实验，另生成细线和二值图作为补充对照。椒盐替换概率设置为0%、5%、10%、20%、40%、60%、80%，每张图每个条件使用五个噪声种子；不同方法处理同一含噪图。主方案的最大自适应窗口预先固定为7×7，同时测试3、5、9作为参数敏感性分析。')
para(f'在自然图、40%椒盐替换条件下，自适应中值AMF7的平均PSNR为{value("AMF7",.4):.2f} dB，固定7×7中值为{value("Median7",.4):.2f} dB，相差{delta(.4):.2f} dB。替换概率升至80%后，AMF7降至{value("AMF7",.8):.2f} dB，图像仍存在明显破坏。随机灰度脉冲补充实验中，AMF7弱于固定5×5中值，说明结论依赖于退化假设。')
para('关键词  椒盐噪声  中值滤波  自适应窗口  图像恢复  配对实验',True)
para('记号说明：Mean3表示3×3均值，Median3/5/7表示对应的固定中值窗口；AMF3/5/7/9表示自适应中值的最大窗口边长，起始窗口均为3×3。Noisy为未经滤波的含噪输入。')
h('选题依据')
para('课程第3章图像增强部分介绍了邻域滤波和中值滤波，并指出大窗口去噪与纹理保持之间存在取舍。[1] 在已学固定窗口排序取中值的基础上，我进一步研究：能否让不同像素使用不同窗口，在降低噪声的同时减少不必要的平滑。')
h('要回答的问题')
para('第一，噪声比例升高时，固定3×3、5×5、7×7窗口的效果如何变化。第二，增加自适应窗口与中心像素判别后，质量和耗时是否改善。第三，无噪声细线、二值结构及不同类型的脉冲噪声会暴露哪些局限。')
para('自适应中值属于已有经典方法。[2] 本次工作的重点是自行编写和核验算法、设计统一实验、分析成功与失败条件，不将算法比较视为提出新的基础理论。')

# 3
page('一 噪声模型与固定窗口滤波')
h('1 椒盐噪声的构造')
para('图像采用0—255灰度值。以概率p选中像素，将其中一半替换为0，另一半替换为255；未选中的像素保持原值。p表示替换概率，不一定等于实际发生数值变化的比例。例如原本为0的像素再次被替换为0，灰度值并未改变。')
equation(['P(替换为0) = p/2     P(替换为255) = p/2'])
para('程序分别记录选中比例和实际改变比例。算法只读取含噪灰度值，不读取加噪过程中保存的真实污染掩码，也不根据真实干净图决定替换哪个像素。')
h('2 均值与中值的区别')
equation(['均值输出 = ',fraction('窗口内全部灰度值之和','窗口像素数')])
equation(['中值输出 = median {窗口内的灰度值}'])
para('均值是线性平均，黑白极值会拉动输出；中值由排序位置决定，对少量孤立极端值较稳健。对于下面的3×3窗口，排序后第五个数为10，而平均值约为37.33。中心附近只出现一个255时，中值不会被这一极端值大幅拉高。')
table(['第一列','第二列','第三列'],[['8','10','11'],['9','255','10'],['10','11','12']],[1.8,1.8,1.8],11)
para('这里9个数的和为336，中值为10。该例只能解释孤立脉冲的情形，不能证明中值对任意密度噪声都有效。若窗口内相同极值占据多数，中值也可能仍是0或255。')
h('3 固定窗口的取舍')
para('3×3窗口更容易保留局部细节，但在密集脉冲区域可能残留黑白点。增大到5×5或7×7后，参与排序的样本更多，密集噪声下可能更稳定；同时细线、小目标和边缘也更容易被邻域多数值取代。因此本实验把三个窗口同时作为参照，不只选一个表现较弱的基线。')
para('所有方法只从本轮输入读取邻域，输出另存新数组。边界统一采用对称延拓，重复边缘像素；不能一边计算一边覆盖输入，否则结果还会依赖遍历方向。')

# 4
page('二 自适应中值滤波的实现原理')
para('本实验使用局部最小值zmin、中值zmed、最大值zmax和原始中心值zxy进行两阶段判别。窗口从3×3开始，每次边长增加2，最大边长Smax取预先设定值。以下规则完整定义了程序使用的算法。')
h('1 阶段A 判断当前中值')
equation(['zmin < zmed < zmax'])
para('若严格不等式成立，则进入阶段B；否则扩大窗口重新计算。达到最大窗口后仍不成立，直接输出该最大窗口的中值。平坦区域的最小值可能等于中值，因此扩大窗口并不一定说明该处噪声严重。')
h('2 阶段B 判断中心像素')
equation(['zmin < zxy < zmax'])
para('若成立，保留原始中心值；否则用当前窗口中值替换。它减少了一部分正常像素被全图中值平滑的机会，但合法局部极大值、极小值也可能被替换，不能把这个判别当成完美噪声检测器。')
code('for size in [3, 5, ..., Smax]:\n    zmin, zmed, zmax = local_statistics(input, size)\n    if zmin < zmed < zmax:\n        output = center if zmin < center < zmax else zmed\n        break\n    if size == Smax:\n        output = zmed')
h('3 扩大窗口的直观例子')
para('在灰度128的7×7背景上加入5个相邻255。中心3×3邻域是下列矩阵，中值仍为255；扩大到5×5时，中值恢复到128。正确性检查确认固定3×3输出255、最大窗口为5的自适应实现输出128。该例在最大窗口回退规则下得到恢复。')
table(['','中心邻域',''],[['255','255','128'],['255','255','128'],['128','128','255']],[1.8,1.8,1.8],11)
para('为减少重复运算，程序在扩大窗口时只收集尚未完成判别的像素。向量化版本与逐像素参考版本做逐点一致性核验；这项实现优化不改变上述判别规则。')

# 5
page('三 实验数据与统一设置')
para('自然图来自scikit-image公开样例数据。[3] 彩色图按0.2125R+0.7154G+0.0721B转换为灰度并取整，然后对所有图提取中心256×256区域，不缩放。下表的尺寸指裁剪前原图；实际裁剪坐标和像素SHA-256保存在数据清单中。')
table(['图像','原图宽×高','用于观察的内容'],[
    [m['image'],f'{m["source_shape"][1]}×{m["source_shape"][0]}',desc]
    for m,desc in zip(MAN[:6],['人物与器材边缘','硬币边界与纹理','平滑月面与局部结构','人像和服装细节','毛发与细纹理','杯口曲线和木纹'])],[1.25,1.25,4.1])
figure('dataset.png',5.75);caption('图1 主实验使用的六张自然图灰度中心区域')
para('参数在运行前固定：七档替换概率、每条件五个噪声种子、相同边界策略；同一条件的全部方法共享同一输入。主实验含6×7×5×9=1890条记录，另有两张合成图630条记录。无噪声时五次输入相同，仅作为对照。')
para('这里没有训练集和测试集划分，因为算法不学习参数。AMF7是预先固定的主方案；最大窗口3、5、9用于解释参数趋势，不把逐图最优结果拼成一个方法。六张样例数量有限，五次噪声重复不能当作三十张独立图像。')

# 6
page('四 自然图定量结果')
caption('表1 六张自然图平均PSNR 单位dB 越高越好')
table(['替换概率','Noisy','Mean3','Median3','Median5','Median7','AMF7'],[
    [f'{p:.0%}',*[f'{value(m,p):.2f}' for m in MAIN]] for p in [.05,.1,.2,.4,.6,.8]], [.8,.8,.85,.95,.95,.95,.9])
caption('表2 代表条件的平均SSIM 越高越好')
table(['替换概率','Median3','Median5','Median7','AMF7'],[
    [f'{p:.0%}',*[f'{value(m,p,"ssim"):.4f}' for m in ['Median3','Median5','Median7','AMF7']]] for p in [.1,.4,.8]], [1,1.4,1.4,1.4,1.4])
figure('quality.png',6.65);caption('图2 自然图在不同椒盐替换概率下的质量变化')
para(f'5%条件下，固定3×3中值的PSNR为{value("Median3",.05):.2f} dB，高于7×7的{value("Median7",.05):.2f} dB，说明大窗口并非始终合适。40%时7×7超过3×3，而AMF7又比7×7高{delta(.4):.2f} dB。先对每图五次结果平均、再对六张图等权平均，得到表中数值。')
para('AMF7在有噪声的六档条件下，相对固定7×7均在六张自然图上提高了图像级平均PSNR。但这个样本内结果不意味着对所有图像都占优；高污染条件下的视觉损伤仍需结合后续图像检查。')

# 7
page('五 最大窗口与无噪声对照')
caption('表3 不同最大自适应窗口的自然图平均PSNR 单位dB')
table(['替换概率','AMF3','AMF5','AMF7','AMF9'],[
    [f'{p:.0%}',*[f'{value(m,p):.2f}' for m in ['AMF3','AMF5','AMF7','AMF9']]] for p in [.1,.4,.6,.8]], [1,1.4,1.4,1.4,1.4])
figure('windows.png',6.65);caption('图3 最大窗口的质量影响与AMF7实际结束判别的窗口分布')
para(f'40%时，最大窗口由5增至7使PSNR从{value("AMF5",.4):.2f}增至{value("AMF7",.4):.2f} dB，增至9仅到{value("AMF9",.4):.2f} dB；80%时7增至9则从{value("AMF7",.8):.2f}增至{value("AMF9",.8):.2f} dB。可见窗口上限的影响随噪声条件变化，不能把本次AMF7称为所有条件下的最优方案。')
win40=next(r for r in A['window_proportions'] if r['density']==.4)
win80=next(r for r in A['window_proportions'] if r['density']==.8)
para(f'40%时约{win40["window_3_fraction"]:.1%}像素在3×3结束判别；80%时这一比例降为{win80["window_3_fraction"]:.1%}，约{win80["window_7_fraction"]:.1%}到达7×7。80%时仍有{win80["fallback_fraction"]:.1%}像素在最大窗口触发回退。图中窗口比例表示结束判别的位置，不等同于实际被替换的像素比例。')
h('无噪声时也会改变图像')
zero=next(r for r in A['window_proportions'] if r['density']==0)
para(f'无噪声自然图上，AMF7的平均PSNR为{value("AMF7",0):.2f} dB、SSIM为{value("AMF7",0,"ssim"):.4f}，平均改变{zero["changed_fraction"]:.1%}的像素。真正的恒等输出此时MSE应为0、PSNR为正无穷。AMF7虽比全图中值更少改变正常区域，仍不能保证无噪声细节完全保留。')

# 8
page('六 中等污染图像效果')
para('图4采用camera的40%椒盐替换输入及第一个噪声种子。六个结果使用同一参考图和相同灰度范围；局部图固定截取坐标x=80—175、y=80—175的96×96区域，使用最近邻放大。')
figure('camera_full.png',6.5);caption('图4 camera在40%椒盐替换条件下的整图对比')
figure('camera_crop.png',6.65);caption('图5 同一中心区域的细节对比')
para('均值结果仍有明显颗粒，固定3×3残留黑白脉冲点；7×7去除了更多脉冲，但人物、摄像机和支架边界变得平滑。AMF7在当前样例中减少了黑白点，并保留较清晰的部分器材轮廓；它仍有局部纹理损失，不能把看起来清晰等同于完全恢复。')

# 9
page('七 高密度噪声与窗口分布')
para('图6采用coins的80%椒盐替换输入及第一个噪声种子，用于检验大面积污染。展示这一预先固定的困难条件，有助于观察平均指标提高后仍未解决的问题。')
figure('coins_full.png',6.5);caption('图6 coins在80%椒盐替换条件下的整图对比')
figure('window_map.png',6.65);caption('图7 同一含噪图的AMF7结束窗口位置与输出')
para(f'主数据在80%时，AMF7虽比固定7×7高{delta(.8):.2f} dB，平均SSIM也仅为{value("AMF7",.8,"ssim"):.4f}。图中硬币细节大量丢失，且仍有黑白块残留。此时7×7邻域也可能被极值主导，窗口回退只能限制程序继续扩大，不能保证恢复真实内容。')

# 10
page('八 细线损伤与噪声假设变化')
para('为避免只展示自然图上的优势，我另外生成细线和二值棋盘，在完全无噪声时滤波。下图均取同一位置，灰度范围固定；原图有意包含较窄结构或只有0、255的合法区域。')
figure('thin_lines_control.png',6.65);caption('图8 无噪声细线区域的变化')
para('固定小窗口会删除部分窄线，大窗口损伤更明显；AMF7同样可能抹除细线。原因是线条在邻域内是少数值，严格极值判别无法知道它是合法结构。二值区域的中值总是等于最小值或最大值，阶段A也难以通过，容易持续扩大窗口并回退。')
figure('binary_shapes_control.png',6.65);caption('图9 无噪声二值棋盘交界处的变化')
caption('表4 40%随机灰度脉冲补充实验 自然图平均值')
table(['方法','PSNR dB','SSIM'],[[m,f'{A["random_value_impulse_means"][m]["psnr_db"]:.2f}',f'{A["random_value_impulse_means"][m]["ssim"]:.4f}'] for m in ['Noisy','Median3','Median5','AMF7']],[2.2,2.2,2.2])
para('补充实验将40%的像素替换为0—255均匀随机灰度，仍使用同图五次配对噪声。被污染的中心值可能落在局部最小、最大值之间，因而被AMF保留。此时AMF7弱于固定中值，说明它的优势不能直接推广到随机值脉冲、真实拍摄噪声或其他退化。')

# 11
page('九 程序核验与计算开销')
para(f'实验在CPU上完成，Python {E["python"]}、NumPy {E["numpy"]}、SciPy {E["scipy"]}、scikit-image {E["scikit_image"]}，无需GPU。滤波实现使用NumPy窗口、局部统计和分区选取中值；SciPy及scikit-image在这里用于指标计算或数值核验，不代替自编的滤波流程。')
caption('表5 camera 256×256滤波中位耗时 单位ms')
table(['替换概率','Mean3','Median3','Median5','Median7','AMF7'],[
    [f'{p:.0%}',*[f'{time_value(m,p):.2f}' for m in ['Mean3','Median3','Median5','Median7','AMF7']]] for p in [.1,.4,.8]], [.9,1.1,1.1,1.1,1.1,1.1])
para('每种条件预热3次、计时15次。包含边界填充、窗口收集、统计和输出，不包含读写文件与指标计算。不同方法均使用本实验的NumPy实现，不能把这些时间理解为各算法在所有软件库中的最快性能。')
para(f'40%时AMF7中位耗时{time_value("AMF7",.4):.2f} ms，低于全图7×7中值的{time_value("Median7",.4):.2f} ms；80%时升到{time_value("AMF7",.8):.2f} ms，高于7×7的{time_value("Median7",.8):.2f} ms。较多像素需要大窗口时，额外判别与索引开销会增加，质量提升不总能同时带来速度优势。')
h('正确性核验')
para('对随机灰度、三值图、全黑和全白四类小矩阵，分别核验四种最大窗口，共16组。自适应向量化输出与逐像素参考输出完全相同；固定中值与SciPy输出逐点相同，均值误差在10⁻¹⁰以内。PSNR、SSIM另与scikit-image的同参数实现核对，通过后才执行正式实验。')
h('评价公式与复现入口')
equation(['MSE = ',fraction('∑ᵢ (输出ᵢ − 参考ᵢ)²','像素总数')])
equation(['PSNR = 10 log₁₀(',fraction('1','MSE'),')'])
para('上式使用0—1浮点灰度。SSIM采用11×11高斯窗、标准差1.5、总体协方差，C₁=0.01²、C₂=0.03²，去掉5像素边界再平均。均值结果在计分前不量化，图片展示时才取整。')
code('python experiment.py\npython analyze_and_plot.py\npython demo.py --density 0.4')
para('项目随附原图和裁剪图、算法文件、完整CSV、窗口分布与计时记录。随机灰度补充实验另有120条记录，未混入椒盐噪声的主结果。')

# 12
page('十 结论与参考资料')
h('实验结论')
para(f'第一，固定中值的合适窗口依赖噪声比例。低污染时大窗口会付出较明显的平滑代价；污染增加后，小窗口又容易残留极值。40%条件下，固定3×3、5×5、7×7的平均PSNR分别为{value("Median3",.4):.2f}、{value("Median5",.4):.2f}、{value("Median7",.4):.2f} dB。')
para(f'第二，在本次六张自然图及理想椒盐模型下，两阶段判别与窗口扩大取得了更好的质量。AMF7在40%时达到{value("AMF7",.4):.2f} dB、SSIM {value("AMF7",.4,"ssim"):.4f}。实现上只处理未完成判别的位置，减少了中低污染下对全图反复计算大窗口的工作量。')
para(f'第三，自适应方法存在明确边界。无噪声图像也会被改变，细线和二值交界可能受损；80%椒盐条件仍留下严重失真；40%随机灰度脉冲下，其PSNR为{A["random_value_impulse_means"]["AMF7"]["psnr_db"]:.2f} dB，低于固定5×5的{A["random_value_impulse_means"]["Median5"]["psnr_db"]:.2f} dB。选择算法前应先判断噪声和图像结构，而不能只看一种合成噪声的平均排名。')
h('不足与后续工作')
para('自然样例只有六张，且均取中心区域，不能代表全部应用。后续可以增加文本、医学或工业图像，设计更可靠的脉冲检测，结合边缘保护，并测试真实噪声。扩大实验时应保留相同输入、相同边界与独立参数选择流程；不能在每张测试图上挑最优参数后再声称获得统一算法。')
h('参考资料')
refs=[
    '[1] 课程课件 第3章-2深度学习图像增强 第20页 中值滤波。',
    '[2] Hwang H, Haddad R A. Adaptive Median Filters: New Algorithms and Results. IEEE Transactions on Image Processing, 1995, 4(4):499–502. DOI:10.1109/83.370679。该文提供可变窗口脉冲去噪的背景，本实验具体判别规则以第二节为准。',
    '[3] scikit-image 0.25.2 数据文档 skimage.data。https://scikit-image.org/docs/0.25.x/api/skimage.data.html。自然图来源与许可细节见项目data/SOURCES.md。',
    '[4] scikit-image 指标文档 skimage.metrics。https://scikit-image.org/docs/0.25.x/api/skimage.metrics.html。PSNR与SSIM的实现参数在第九节列明。',
]
for text in refs:
    p=para(text);p.paragraph_format.line_spacing=1.12
    for run in p.runs:run.font.size=Pt(10)

doc.core_properties.title='中值滤波与自适应中值滤波去噪效果对比研究'
doc.core_properties.author='文韬';doc.core_properties.subject='图像处理与分析自主选题期末大作业'
out=ROOT.parent/'20245641_文韬_中值滤波与自适应中值滤波对比.docx'
doc.save(out)
print(out)
