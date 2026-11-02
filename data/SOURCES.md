# 数据来源与处理

自然图使用scikit-image 0.25.2的公开样例数据，不来自某个去噪项目的训练/测试文件。

官方文档：https://scikit-image.org/docs/0.25.x/api/skimage.data.html

- camera：Lav Varshney摄影，CC0。scikit-image 0.18之后的新版camera，与早期经典摄影师图不同。
- astronaut：NASA宇航员Eileen Collins照片，公有领域。
- coins：Brooklyn Museum Collection的硬币照片，文档标记无已知版权限制。
- chelsea：Stefan van der Walt摄影，CC0。
- coffee：Rachel Michetti摄影，CC0，拍摄于Pikolo Espresso Bar。
- moon：scikit-image的月表灰度样例，来源说明见上述官方data.moon条目；本实验保留包内样例的来源归属，不主张对原始图像拥有版权。

文件在data/originals保留包内原始数组对应的PNG；data/clean为中心256×256裁剪，彩色图先用0.2125R+0.7154G+0.0721B转灰度并取整。manifest.json记录实际原尺寸、裁剪坐标和像素SHA-256。

thin_lines和binary_shapes由experiment.py确定性生成，用作细节与二值图的边界条件测试，无外部照片来源。
