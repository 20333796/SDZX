# 地质资源与地质工程学科大模型

双击 `index.html` 即可打开页面，无需安装依赖。页面可在电脑与手机上自适应显示。

## 已实现

- 高清地球横幅、学科名称及“工学”“地质资源与地质工程”标签。
- “大模型介绍”和“数据集介绍”标签页，支持鼠标及左右方向键切换。
- 大模型介绍使用《介绍(1).docx》的全部原文和框架图；数据集介绍使用《简介.docx》的全部原文及注意事项。
- 框架图按原文顺序展示，可点击打开高清原图。
- 右侧“在线体验”区域及“前往体验”链接。
- 尚未提供体验地址时，显示“体验页面即将上线”提示。

## 接入体验页面

编辑 `config.js` 中的 `experienceUrl`，填写完整网址或相对路径：

```js
window.GEO_MODEL_CONFIG = {
  experienceUrl: "./experience.html"
};
```

填好后点击“前往体验”，会在当前标签页直接打开目标页面。目标页面后续提供，本项目未预设其内容。

## 文件

- `index.html`：页面结构与两部分介绍文案。
- `styles.css`：样式与移动端布局。
- `script.js`：标签切换、体验跳转及待上线提示。
- `config.js`：体验页面地址。
- `assets/earth-nasa.webp`：NASA 地球影像，基于 8000 × 8000 原图制作为适合网页的 1600 × 1600 图像。
- `assets/model-framework.webp`：Word 框架图的网页预览。
- `assets/model-framework.png`：从 Word 原样提取的 4400 × 2486 高清框架图。

参考布局来源：https://ai-show.hep.com.cn/edu/models/e077ddab-7214-4f95-a8d9-6d7a0db36336 。页面未使用参考站点的登录功能、接口或机构标识。

介绍文字与框架图来自用户提供的两个 Word，保留原文内容与顺序。《简介.docx》原文件不含图片。

地球背景来源：NASA SVS — NPP Blue Marble，https://svs.gsfc.nasa.gov/30002/ 。

图像署名：NASA/NOAA/GSFC/Suomi NPP/VIIRS/Norman Kuring。原图：https://svs.gsfc.nasa.gov/vis/a030000/a030000/a030002/npp.jpg 。
