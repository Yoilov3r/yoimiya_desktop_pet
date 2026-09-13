# 宵宫 Q 版桌宠

一个面向 Windows 的互动桌面小宠物，支持透明窗口、状态成长、上下文对话、系统感知和自动日常。

当前版本：`2.1.0`

## 下载

Windows 绿色版可在仓库的 `release` 目录下载：

```text
release\yoimiya-desktop-pet-windows.zip
```

解压后保留整个文件夹，双击 `启动桌宠.bat` 或 `YoimiyaDesktopPet\YoimiyaDesktopPet.exe`。

## 启动

双击 `启动桌宠.bat`，或直接运行：

```text
dist\YoimiyaDesktopPet\YoimiyaDesktopPet.exe
```

首次运行如果 Windows 提示“已保护你的电脑”，选择“更多信息”再选择“仍要运行”。程序不需要联网。

## 互动

- 单击头部：摸头反应
- 单击身体：普通对话
- 单击手部：击掌与互动粒子
- 双击：随机切换日常行动
- 拖动：移动位置
- 右键：控制中心、烟花小游戏和全部行动
- 鼠标滚轮：调整大小

## 新增系统

- 精力、心情、饱腹、专注度会影响行动概率和台词。
- 自动避开最近说过的台词。
- 支持喝水提醒、低电量提示和全屏应用隐藏。
- 支持自定义 JSON 台词包。
- 支持多显示器切换、桌面散步和窗口上沿停留。
- 支持开机启动、安静模式和始终置顶。
- 支持季节装饰、小游戏和粒子特效。

## 控制中心

右键角色后选择“打开控制中心”，可以调整：

- 自动日常、安静模式、始终置顶
- 开机启动、全屏隐藏、省电自动降帧
- 喝水提醒、桌面散步、窗口上沿停留
- 桌宠大小、动画速度、喝水提醒间隔

## 自定义台词

在控制中心选择“编辑台词”，程序会创建：

```text
data\custom_dialogues.json
```

保存后回到控制中心，或者右键选择“重新载入台词”即可生效。

## 从源码运行

需要 Python 3.11 或更高版本，并安装 Pillow：

```powershell
python -m pip install -r requirements.txt
python app.py
```

## 重新打包

```powershell
.\build.ps1
```

打包结果生成在 `dist\YoimiyaDesktopPet\YoimiyaDesktopPet.exe`，发布时请保留整个 `YoimiyaDesktopPet` 文件夹。
