# 美术素材

三款炒鸡使用圆形锡纸盒，鸡块半浸在浓汁里，用少量粗线条和大色块提高小尺寸下的辨识度。

- 麻辣：红椒与红褐色酱汁。
- 蒜香：浅色蒜瓣与金黄色酱汁。
- 酱香：紫色洋葱与深棕色酱汁。

美术使用 AI 辅助创作，源码附带三款当前使用的透明源图。
构建器使用模组内的相对资源位置，不需要作者的本机目录配置。
物品栏、地面与锅内分别控制显示尺寸；食谱书使用高清素材。

纹理采用 KTEX 默认平台与 DXT5 压缩，包含完整 mipmap 和透明通道。
动画使用独立 BILD 符号，复用游戏现有的食物 idle 动画，不附带原版图像或动画文件。

公开格式参考：

- [BILD 格式说明](https://github.com/CN-DST-DEVELOPER/DstAnimTool/blob/main/build_compiler.py)
- [KTEX 字段定义](https://github.com/nsimplex/ktools/blob/master/src/common/ktex/specs.cpp)

## 工坊封面

`preview.jpg` 使用内置 imagegen，以本项目三款料理预览作参考生成，再导出为不含个人元数据的 1024×1024 JPEG。
生成提示词如下：

```text
Create a square Steam Workshop cover for a Don't Starve Together food mod. The attached reference is a sheet of the actual three game sprites. Use ONLY the three large foil tubs from the top row as food art references; ignore all small duplicate icons and English labels. Preserve the juicy chunky chicken in round silver foil takeaway tubs, thick rough black outlines and simple muted earthy color blocks. Three tubs arranged in a strong triangle: garlic golden gravy back-left, soy dark brown gravy with purple onion back-right, spicy reddish gravy with red peppers in the foreground center. Large readable Chinese title at the top, exact text: 他二哥炒鸡 . One smaller warm cream subtitle below title, exact text: 麻辣 · 蒜香 · 酱香 . Dark charcoal-brown hand-inked parchment background with a subtle warm ochre vignette; minimal decorative rough border. Cozy hearty survival-game mood. Food should occupy the lower two-thirds of the image and remain clear as a small thumbnail. NO characters, NO official logos, NO UI, NO inventory grid, NO other text, no watermarks, no tiny decorations, no photo-realistic details. Deliver a polished centered square promotional cover, opaque background.
```
