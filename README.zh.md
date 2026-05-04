# 🎥 MissAV Downloader Web UI

一个在 TrueNAS 和 Docker 环境中完美运行的 **MissAV Web 下载工具**。
基于 `curl_cffi` 和 `yt-dlp`，可绕过 ISP 封锁（SNI）以及 Cloudflare 的强力反爬虫保护。

## ✨ 功能

### 核心功能

- **Web UI：** 只需在浏览器中输入 URL，下载即可在后台顺利运行。
- **实时进度显示：** 使用直观的绿色进度条显示下载进度（%）——无需查看终端。
- **智能绕过逻辑：**
  - 使用 `curl_cffi` 模拟最新的 Chrome 浏览器，绕过 Cloudflare 机器人检测和 CAPTCHA。
  - 自动轮换 MissAV 镜像域名，寻找可访问地址。
- **完整 VPN 兼容性：** 即使连接到 Gluetun 等 VPN 容器网络也能正常工作，并正确绕过 IP 限制。
- **增强稳定性：** 自动优化文件名，防止由于过长的日文/韩文标题导致的文件系统错误（`[Errno 36] File name too long`）。
- **任务取消功能：** 在列表中点击 `Delete` 按钮可立即强制终止（取消）后台下载进程。

### 新功能

- **零配置设置 (Zero-Configuration)：** 不再需要手动设置代理。应用会自动检测您的操作系统并为您安装/配置 **SpoofDPI**。
- **SQLite 数据库：** 所有下载任务和历史记录现在都存储在持久的 SQLite 数据库中。即使应用崩溃或重启，历史记录也不会丢失。
- **实时事件流 (SSE)：** UI 现在可以接收来自服务器的即时更新。不再需要轮询——进度条和状态更改会在发生的瞬间显示。
- **深度元数据抓取：** 自动访问视频页面，抓取演员姓名、类型、厂商、发行商以及高清海报。
- **MP4 元数据打标：** 使用 `mutagen` 将抓取的元数据和封面图直接注入 MP4 文件，提供专业的媒体库体验。
- **可视化任务列表：** 下载队列现在可以显示每个视频的高清缩略图预览。
- **多站点回退：** 如果 MissAV 缺少元数据，会自动尝试 BestJavPorn 或 JavGuru 进行补充。
- **磁盘空间保护：** 在开始下载前自动检查可用磁盘空间，防止系统崩溃（兼容 Docker）。
- **优雅的进程管理：** 改进了退出时对 SpoofDPI 及其他后台进程的清理逻辑。
- **📊 下载元数据显示：** 可在任务列表中查看视频分辨率、最终文件大小以及耗时。
- **⚡ 动态并行下载：** 可在设置中动态调整并发下载线程数量，无需重启应用，多余线程会安全终止。
- **🔧 自定义 FFmpeg 路径：** 可在 Web UI 中指定 FFmpeg 二进制目录，保存前会自动验证 `ffmpeg`、`ffprobe` 和 `ffplay` 是否存在。
- **🗑️ 清理历史：** UI 中提供一键按钮，用于完全删除服务器上的所有下载文件。
- **📄 文档查看器：** 内置模态框，可直接在 Web 界面查看本地 README、SECURITY 和 LICENSE 文件。
- **🔗 自定义 URL 爬虫：** 输入系列、片商或搜索 URL，选择过滤器，选择要抓取的页数，然后直接从结果中批量选择视频进行下载。
- **📂 交互式文件夹浏览器：** 直接从 Web UI 安全地浏览和选择下载路径及 FFmpeg 目录（兼容 Docker 和便携版）。

## 🛠️ 安装与使用

### 📦 桌面端 / 发行版（最简单）

1. **下载**：从 **Releases** 页面下载适用于您的操作系统（Windows、Linux 或 macOS）的最新版本。
2. **运行**：
   - **Windows**：双击 `MissAV_Downloader.exe`。
   - **Linux/macOS**：打开终端并运行 `./MissAV_Downloader`（确保具有执行权限：`chmod +x MissAV_Downloader`）。
3. **完成**：应用将自动处理环境设置 (SpoofDPI) 并在浏览器中打开 `http://localhost:5000`。

---

### 🐳 Docker 安装（推荐用于服务器/NAS）

> ⚠️ **建议：** 为了安全起见，请在 VPN（例如 Gluetun）环境中运行。

### 1. 创建 `docker-compose.yml`

将下载器容器连接到 VPN 网络。（使用 GitHub Container Registry）

```yaml
version: '3'
services:
  missav-dlp-web:
    image: ghcr.io/nerdnam/missav-dlp-web:latest
    network_mode: "container:gluetun-vpn" # 可选：当使用 VPN 容器时
    # ports:
    #   - "5000:5000" # 仅在不使用 VPN 时启用
    volumes:
      - /path/to/your/downloads:/downloads
      - ./locales:/app/locales # 可选：用于自定义翻译
    restart: unless-stopped
```

### 2. 在 Gluetun 的 `docker-compose.yml` 中添加端口

由于下载器连接到 VPN 容器，你**必须**在 **Gluetun 容器配置中**添加外部访问端口：

```yaml
services:
  gluetun-vpn:
    # ...（现有的 Gluetun 配置）...
    ports:
      - "58000:5000/tcp"  # 将主机端口 58000 映射到容器端口 5000
```

### 3. 访问 Web UI

容器启动后，在浏览器中打开：

```
http://[YOUR_NAS_OR_SERVER_IP]:58000
```

## 📁 项目结构

```
missav-dlp-web/
├── app.py                    # 主 Flask 应用程序
├── .settings.json            # 用户设置（自动生成）
├── downloads/                # 已下载的视频
├── logs/                     # 下载任务日志
├── locales/                  # 语言文件
│   ├── en.json              # 英语
│   ├── ko.json              # 韩语
│   ├── ja.json              # 日语
│   └── zh.json              # 简体中文
├── templates/                # Web 界面
│   ├── index.html           # 主页面
│   ├── script.js            # 前端逻辑
│   └── style.css            # 样式
├── app_files/               # 后端模块
│   ├── config_manager.py    # 设置管理
│   ├── download_manager.py  # 下载队列与 yt-dlp
│   ├── extractor.py         # 自定义 MissAV 提取器
│   ├── language.py          # 多语言支持
│   ├── paths.py             # 路径管理
│   └── utils.py             # 工具函数
└── ffmpeg/                  # FFmpeg 二进制（可选）
    └── bin/
        └── ffmpeg.exe
```

## 🌍 语言支持

该应用支持多种语言，并可随时切换：

| 语言                      | 代码 | 状态   |
| ----------------------- | -- | ---- |
| English                 | en | ✅ 完整 |
| 한국어 (Korean)            | ko | ✅ 完整 |
| 日本語 (Japanese)          | ja | ✅ 完整 |
| 中文 (Chinese Simplified) | zh | ✅ 完整 |

添加新语言：

1. 在 `locales/` 文件夹中创建新的 JSON 文件（例如：`fr.json`）
2. 复制 `en.json` 的结构并翻译内容
3. 在 `templates/index.html` 的下拉菜单中添加语言代码

## ⚙️ 配置

设置存储在 `.settings.json` 中，可通过 Web UI 修改：

| 设置项          | 描述               | 默认值                         |
| ------------ | ---------------- | --------------------------- |
| 下载目录         | 视频保存位置           | `./downloads`               |
| FFmpeg 二进制目录 | FFmpeg 自定义路径     | 系统 PATH                     |
| 最大并发下载数      | 并行下载线程数          | `1`                         |
| 顺序模式         | 是否逐个下载           | `true`                      |
| 下载间隔         | 两次下载之间的等待秒数      | `3`                         |
| 默认清晰度        | 最大下载分辨率          | `best`                      |
| 镜像域名         | 用于回退的 MissAV 镜像域 | `missav.ai`, `missav.net` 等 |

### 高级配置

也可以直接编辑 `.settings.json`：

```json
{
  "max_concurrent": 1,
  "ffmpeg_path": "",
  "filename_template": "[%(id)s] %(title).60s.%(ext)s",
  "filename_template": "[%(id)s] %(title).60s.%(ext)s",
  "spoofdpi_enabled": true,
  "video_quality": "best",
  "mirrors": ["missav.ai", "missav.net", "missav123.com", "missav.com", "missav.ws"],
  "download_dir": "./downloads",
  "delay_between_downloads": 3,
  "max_retries": 3,
  "sequential_mode": true
}
```

## 🚀 使用示例

### 单个下载

1. 输入 MissAV URL 或 JAV 代码（例如：`ABP-123`）
2. 点击 “Get Info” 获取视频信息
3. 选择清晰度
4. 点击 “Download Now” 或 “Add to Queue”

### 批量下载

1. 点击 “Batch Add”
2. 输入多个 URL 或 JAV 代码（每行一个）
3. 点击 “Add All to Queue”

### 下载管理

- 在队列中查看实时进度
- 使用 ✕ 按钮取消单个下载
- 清理已完成任务或清空等待队列
- 在 Downloads 区域浏览和管理已下载文件

### 自定义URL爬虫

1. 输入MissAV系列、厂商或搜索URL
2. 点击“Custom”按钮
3. 从列表中选择筛选器（或使用“All”）
4. 选择要抓取的页数
5. 从结果列表中选择视频
6. 点击“Download Selected”添加到队列

## 🔧 故障排除

| 问题                   | 解决方案                                                                 |
| ---------------------- | ------------------------------------------------------------------------ |
| 无法访问 Web UI        | 检查 Gluetun 容器中端口是否正确暴露                                      |
| 下载卡住               | 确认 VPN 连接和网络模式配置                                              |
| 文件名错误             | 工具会自动缩短文件名 — 确保下载路径可写                                  |
| 设置无法保存           | 检查根目录中 `.settings.json` 的写入权限                                |
| 语言无法切换           | 清除浏览器缓存或检查 `locales/` 是否正确挂载                           |
| JAV 代码无法使用       | 确保格式正确（例如：`ABP-123`, `SSIS-456`）                            |

## 🐳 Docker 构建

本地构建 Docker 镜像：

```bash
docker build -t missav-dlp-web .
docker run -p 5000:5000 -v $(pwd)/downloads:/downloads missav-dlp-web
```

## 📦 依赖要求

* Docker & Docker Compose
* （可选）Gluetun 或任何 OpenVPN / WireGuard 容器
* Python 3.8+（用于本地开发）
* **PyInstaller**（用于构建可执行文件）
* FFmpeg（用于视频合并）

### 🛠️ 开发与构建 (Development & Building)

如果您想从源代码运行或构建自己的可执行文件：

#### 1. 设置环境
```bash
# 创建虚拟环境
python -m venv venv

# 激活环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install pyinstaller
```

#### 2. 从源码运行
```bash
python main.py
```

#### 3. 构建可执行文件
我们为所有平台提供了自动化脚本：
- **Windows**: 运行 `build.bat`
- **Linux/macOS**: 运行 `bash build.sh`

**手动构建:**
```bash
pyinstaller --clean MissAV_Downloader_onefile.spec
```

---

## 🔄 API 接口

该应用提供 REST API 接口：

| 接口路径                       | 方法       | 说明                                 |
| -------------------------- | -------- | ---------------------------------- |
| `/api/info`                | POST     | 获取视频信息                             |
| `/api/download`            | POST     | 添加单个下载任务                           |
| `/api/batch`               | POST     | 添加多个下载任务                           |
| `/api/tasks`               | GET      | 获取所有任务列表                           |
| `/api/tasks/<id>`          | DELETE   | 取消任务                               |
| `/api/queue/stats`         | GET      | 队列统计信息                             |
| `/api/settings`            | GET/PUT  | 获取/更新设置                            |
| `/api/files`               | GET      | 获取已下载文件列表                          |
| `/api/language`            | GET/POST | 获取/设置语言                            |
| `/api/docs/<type>`         | GET      | 获取本地化文档（readme, security, license） |
| `/api/files/clean_history` | POST     | 删除所有下载文件                           |
| `/api/crawl`              | POST     | 使用筛选器/分页从URL抓取视频 |
| `/api/crawl/filters`       | POST     | 获取 URL 的可用过滤器 |
| `/api/utils/ls`            | POST     | 安全地浏览和列出服务器端目录 |

## ⚠️ 免责声明

本工具仅供**个人使用**。
用户需自行承担与下载内容相关的版权责任及一切后果。

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

本项目基于 **[nerdnam](https://github.com/nerdnam)** 的优秀工作以及原始仓库 **[missav-dlp-web](https://github.com/nerdnam/missav-dlp-web)**。

### 原始仓库

* **作者：** nerdnam
* **仓库：** [https://github.com/nerdnam/missav-dlp-web](https://github.com/nerdnam/missav-dlp-web)
* **许可证：** 请查看原仓库获取详细信息

### 使用 / 改进的关键功能

* 使用 `curl_cffi` + `yt-dlp` 实现 Cloudflare 绕过
* 镜像域名轮换机制
* VPN 兼容（Gluetun）
* 带实时进度的 Web 下载界面

### 额外改进

* 多语言支持（4 种语言）
* 设置管理界面
* JAV 代码转换
* 批量下载功能
* 带搜索和预览的文件管理器
* 任务级日志记录
* 顺序 / 并行下载模式

### 致谢

* 原项目的所有贡献者
* `yt-dlp` 和 `curl_cffi` 开源社区
* 参与本地化翻译的贡献者

---

## 📝 更新日志

### Version 4.0 (Industrial Grade)

- **零配置**：新增 Linux 和 macOS 上的 SpoofDPI **自动安装**支持；Windows 上的二进制文件自动检测。
- **原子化持久性**: 将内存存储替换为 **SQLite**，实现防崩溃的历史记录保存。
- **响应式 UI**: 引入 **SSE (Server-Sent Events)**，实现即时、低开销的状态更新。
- **元数据增强**: 集成 **深度抓取 + Mutagen**，支持自动 MP4 打标和封面注入。
- **可视化队列**: 任务列表新增 **120px 缩略图**。
- **安全保障**: 新增具备 Docker 挂载点检测功能的 **磁盘空间保护**。
- **智能回退**: 新增 **多站点回退** (BestJavPorn/JavGuru) 以补全缺失标签。
- **模块化代理**：添加全局开关，可将 SpoofDPI 绕过应用于元数据抓取和爬虫。
- **工业级启动器**：全新的 CustomTkinter UI，支持浅色/深色主题并集成 Windows 任务栏。
- **路径选择**：实现了 **交互式文件夹浏览器**，用于安全、可视化的路径选择（兼容 Docker）。
- **稳定性**: 优化进程生命周期，防止产生孤儿 SpoofDPI 实例。

### Version 3.1

* 新增智能分辨率回退逻辑（精确 → 更高 → 更低 → 默认）
* 新增动态并发下载调节与安全线程终止
* 新增下载元数据显示（分辨率、大小、耗时）
* 新增自定义 FFmpeg 路径及后端校验
* 新增“一键清理历史”功能
* 新增本地化文档查看器（README、SECURITY、LICENSE）
* 修复由于 yt-dlp 提取器冲突导致的 “Get Info” 崩溃问题
* 修复合并后文件名/大小显示异常问题
* 修复低分辨率屏幕下设置窗口溢出问题

### Version 3.0

* 新增多语言支持（EN、KO、JA、ZH）
* 新增设置管理界面
* 新增 JAV 代码转换
* 新增批量下载功能
* 新增带搜索的文件管理器
* 新增任务日志
* 重构代码到 `app_files/` 模块
* 修复目录结构（downloads/logs 移至根目录）

### Version 2.0

* 基于 nerdnam 项目的初始版本
* 基本下载功能
* 实时进度显示
* 使用 curl_cffi 绕过 Cloudflare
