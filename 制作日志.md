# 菲比啾比桌宠 — 制作日志

## 1. 素材准备

### 1.1 图片收集与提示词生成

- 网络搜集菲比啾比的角色图片作为参考素材
- 将图片输入豆包 AI，生成文生视频的提示词

### 1.2 视频生成

- 使用豆包 AI 根据提示词生成菲比啾比多种动作的视频片段

---

## 2. 视频转序列帧

### 2.1 安装 FFmpeg

- 官网下载：<https://ffmpeg.org/download.html>
- GitHub 镜像：<https://github.com/GyanD/codexffmpeg>

### 2.2 导出 PNG 序列帧

使用 FFmpeg 将每段视频按 **每秒 10 帧** 导出为 PNG 序列：

```bash
ffmpeg -i input.mp4 -vf fps=10 frames/%04d.png
```

---

## 3. 图片处理

### 3.1 安装 GIMP

- 官网下载：<https://www.gimp.org/downloads/>
- 下载速度较慢时可使用 [Motrix](https://motrix.app/) 加速

### 3.2 序列帧处理

- 使用 GIMP 对导出的 PNG 序列帧进行裁剪、去背景等处理
- 将处理后的序列帧合成为 GIF 动图

---

## 4. 桌宠程序开发

### 4.1 技术栈

- Python + PyQt5（GUI 框架）
- PyInstaller（打包为 exe）

### 4.2 功能实现

- 无边框透明窗口，GIF 动画循环播放
- 鼠标左键拖拽移动，右键弹出菜单（对话 / 吃瓜 / 退出）
- 窗口位置记忆：拖拽松手和退出时保存位置到 `pet_config.json`，下次启动自动恢复
- 背景透明化处理：泛洪填充去除 GIF 浅色背景 + 清除角落水印残留

### 4.3 项目结构

```
FeibijiubPet/
├── assets/                  # 资源文件
│   └── eat_watermelon.gif
├── pet.py                   # 主程序
├── FeibijiubPet.spec        # PyInstaller 打包配置
├── requirements.txt         # 依赖：PyQt5
└── .gitignore
```

---

## 5. 待办

- [ ] 更多动作动画（走路、睡觉、互动等）
- [ ] 语音播放功能（菲比啾比.mp3 VAD 分段）
- [ ] 系统托盘支持
- [ ] 自动漫游（桌宠在屏幕底部自动走动）
