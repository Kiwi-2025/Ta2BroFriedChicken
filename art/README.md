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

`preview.jpg` 使用内置 imagegen 编辑生成，无品牌标题，仅保留三种口味文字和料理画面。
口味文字靠近顶部，三款料理放大并上移，减少留白；导出为不含个人元数据的 1024×1024 JPEG。

本轮编辑提示词：

```text
Recompose the square cover to remove wasted top space. Center the existing flavor subtitle near the top at 7%-15% canvas height. Enlarge and move up the three foil tubs to occupy 19%-95% canvas height: garlic back-left, soy-onion back-right, spicy front-center, naturally overlapping. Keep balanced narrow margins, the same food designs, thick black outlines, warm earthy palette, parchment background and rough border. Keep all food fully in frame. Do not restore the brand name or add any text, logos or watermarks.
```
