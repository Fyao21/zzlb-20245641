# 中值滤波与自适应中值滤波去噪对比

图像处理与分析期末大作业。人工智能2401班，文韬，学号20245641。

本题从课程中值滤波内容出发，自行编写均值、固定窗口中值及两阶段自适应中值滤波程序，设计配对实验。自适应中值是已有经典方法；本作业的工作是算法实现、向量化、参数比较与结果分析，不声称发明该算法。没有导入其他项目的算法代码。

## 文件

- `filters.py`：NumPy窗口、均值、固定中值、两阶段自适应中值；另有逐像素参考版本。
- `experiment.py`：数据准备、加噪、正确性核验、全量评测、窗口参数实验与CPU计时。
- `analyze_and_plot.py`：从已保存结果计算配对差值并生成图表。
- `demo.py`：单图演示，允许指定自己的图片。
- `data/clean/`：6张自然图中心裁剪、2张合成挑战图，均为256×256。
- `data/originals/`及`manifest.json`：自然原图、裁剪坐标、来源和像素哈希。
- `results/metrics.csv`：完整逐图逐噪声指标。
- `results/summary.json`、`analysis.json`、`window_stats.json`、`latency.json`：汇总、配对变化、窗口分布与计时。
- `results/correctness.json`：参考版本及第三方数值核验。
- `results/figures/`：报告图表；`results/visuals/`为固定样例的算法输出。

## 运行

推荐Python 3.10创建独立环境，在此目录运行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe experiment.py
.\.venv\Scripts\python.exe analyze_and_plot.py
.\.venv\Scripts\python.exe demo.py --density 0.4
```

数据已附带，普通复现无需重新下载图片。若删除data重新准备，程序通过scikit-image.data读取样例图，并按固定规则转换和裁剪。图片的权利与来源见data/SOURCES.md。

快速测试自己的图片：`python demo.py --image "你的图片.png" --density 0.6`。这个演示把输入当作参考图再叠加合成噪声；它不是对未知真实噪声图片进行客观质量评分的工具。

## 固定实验协议

主数据为camera、coins、moon、astronaut、chelsea、coffee六张自然样例；另外单列细线与二值棋盘两张合成图。自然图与合成图的指标不混合汇总。彩色图按0.2125R+0.7154G+0.0721B转为灰度并取整，所有自然图仅中心裁剪，不缩放。

替换概率为0%、5%、10%、20%、40%、60%、80%，每个条件5个噪声种子；种子基数20245641。同一图同一条件的所有方法共享相同噪声。椒盐各占替换概率的一半。替换到原本相同灰度不算实际改变，CSV分别保存选中比例和实际改变比例。零噪声的5次结果相同，仅作无噪声对照。

方法为含噪图、3×3均值、3/5/7固定中值及最大窗口3/5/7/9的自适应中值，共9种。主报告以AMF7作为预先设定方案，其他最大窗口只作敏感性分析，不根据测试图逐张选最优窗口。

所有滤波只读原始含噪输入，边界为NumPy symmetric（重复边缘像素的半采样对称）。自适应算法不使用真实污染掩码，算法和窗口分布详见代码。指标在0—1浮点域计算；均值结果不先量化，展示PNG取整。SSIM使用11×11高斯窗、sigma1.5、总体协方差并去除5像素边界，已与scikit-image核验；PSNR在MSE=0时为正无穷，在JSON中用null并单列infinite_psnr_count表示。

计时针对本机CPU、camera256×256，3次预热、15次重复，不包含磁盘读写与质量指标计算。耗时含窗口扩展、填充、局部统计及输出。不同硬件的时间不宜直接比较。

## 解释范围

这是小样本课程实验，样例图并非随机抽取的实际应用总体；5次噪声重复不能当作30张独立图像。主结论限于灰度图与理想黑白椒盐替换。另测40%随机灰度脉冲以观察假设变化；二值图和细线也用于暴露细节损伤。较大的最大窗口不保证在所有条件更好。

Word报告中的数值从实测JSON/CSV读取。公式采用可编辑Word原生公式，页眉为空，底部仅显示页码。

若需要重新生成报告，另安装`python-docx`后运行`python build_report.py`。`render_report.py`是本机用于版面检查的辅助脚本，依赖Codex文档技能路径和Microsoft Word，不是实验所需依赖，不放入提交压缩包。
