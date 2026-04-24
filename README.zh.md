
# 🎥 MissAV Downloader Web UI

一个**基于网页的 MissAV 下载器**，在 TrueNAS 和 Docker 环境中完美运行。
使用 `curl_cffi` 和 `yt-dlp` 绕过 ISP 封锁（SNI）和 Cloudflare 强大的机器人防护。

## ✨ 功能特性

### 核心功能

- **网页界面：** 只需在浏览器中输入 URL，即可在后台流畅下载。
- **实时进度显示：** 通过直观的绿色进度条监控下载进度（%）。
- **智能绕过逻辑：**
  - 使用 `curl_cffi` 模拟最新版 Chrome 浏览器，绕过 Cloudflare 机器人防护和验证码。
  - 自动轮换 MissAV 的镜像域名，寻找可访问的地址。
- **完整 VPN 兼容：** 即使接入 Gluetun 等 VPN 容器网络也能正常工作，正确绕过 IP 限制。
- **增强稳定性：** 自动优化文件名，防止长日文/韩文标题导致的文件保存错误 `[Errno 36] File name too long`。
- **任务取消功能：** 点击列表中的 `Delete` 按钮，立即强制终止（取消）后台下载进程。

### 新功能

- **🌍 多语言支持：** 支持英语、韩语、日语、中文（简体）。可通过下拉菜单轻松切换语言。
- **⚙️ 设置管理：** 通过网页界面配置下载目录、顺序模式、下载延迟、默认质量和镜像域名。
- **🔍 JAV 代码转换：** 只需输入 JAV 代码（例如 ABP-123），应用会自动将其转换为正确的 MissAV URL。
- **📦 批量下载：** 一次添加多个 URL 或 JAV 代码进行批量下载。
- **📁 文件管理器：** 直接从网页界面浏览、搜索、预览和删除已下载的文件。
- **📝 下载日志：** 每个下载任务都有自己的日志文件，便于故障排查。
- **⚡ 顺序/并行模式：** 选择一次下载一个视频还是同时下载多个。

## 🛠️ 安装与使用

> ⚠️ **建议：** 为了安全，请配合 VPN（例如 Gluetun）运行。

### 1. 创建 `docker-compose.yml`

将下载器容器连接到 VPN 网络。（使用 GitHub Container Registry。）

```yaml
version: '3'
services:
  missav-dlp-web:
    image: ghcr.io/nerdnam/missav-dlp-web:latest
    network_mode: "container:gluetun-vpn" # 可选：使用 VPN 容器时
    # ports:
    #   - "5000:5000" # 仅当不使用 VPN 时启用
    volumes:
      - /path/to/your/downloads:/downloads
      - ./locales:/app/locales # 可选：用于自定义翻译
    restart: unless-stopped
```

### 2. 在 Gluetun 的 `docker-compose.yml` 中添加端口

由于下载器连接到 VPN 容器，你**必须**在 **Gluetun 容器配置**中添加外部访问端口：

```yaml
services:
  gluetun-vpn:
    # ... (现有的 Gluetun 配置) ...
    ports:
      - "58000:5000/tcp"  # 将主机端口 58000 映射到容器端口 5000
```

### 3. 访问网页界面

容器启动后，打开浏览器访问：

```
http://[你的NAS或服务器IP]:58000
```

## 📁 项目结构

```
missav-dlp-web/
├── app.py                    # 主 Flask 应用程序
├── .settings.json            # 用户设置（自动生成）
├── downloads/                # 下载的视频文件
├── logs/                     # 下载任务日志
├── locales/                  # 语言文件
│   ├── en.json              # 英语
│   ├── ko.json              # 韩语
│   ├── ja.json              # 日语
│   └── zh.json              # 中文（简体）
├── templates/                # 网页界面
│   ├── index.html           # 主页面
│   ├── script.js            # 前端逻辑
│   └── style.css            # 样式
├── app_files/               # 后端模块
│   ├── config_manager.py    # 设置管理
│   ├── download_manager.py  # 下载队列和 yt-dlp
│   ├── extractor.py         # 自定义 MissAV 提取器
│   ├── language.py          # 多语言支持
│   ├── paths.py             # 路径管理
│   └── utils.py             # 辅助函数
└── ffmpeg/                  # FFmpeg 二进制文件（可选）
    └── bin/
        └── ffmpeg.exe
```

## 🌍 语言支持

应用程序支持多种语言，可随时切换：

| 语言                      | 代码 | 状态      |
| ------------------------- | ---- | --------- |
| English                   | en   | ✅ 完全   |
| 한국어 (韩语)             | ko   | ✅ 完全   |
| 日本語 (日语)             | ja   | ✅ 完全   |
| 中文 (简体)               | zh   | ✅ 完全   |

添加新语言：

1. 在 `locales/` 文件夹中创建新的 JSON 文件（例如 `fr.json`）
2. 复制 `en.json` 的结构并翻译值
3. 将语言代码添加到 `templates/index.html` 的下拉菜单中

## ⚙️ 配置

设置存储在 `.settings.json` 中，可通过网页界面修改：

| 配置项              | 描述                   | 默认值                                  |
| ------------------- | ---------------------- | --------------------------------------- |
| 下载目录            | 视频保存位置           | `./downloads`                           |
| 顺序模式            | 一次下载一个视频       | `true`                                  |
| 下载延迟            | 下载之间的等待时间（秒） | `3`                                     |
| 默认质量            | 下载的最大分辨率       | `best`                                  |
| 镜像域名            | 用于回退的 MissAV 镜像域名 | `missav.ai`, `missav.net`, 等         |

### 高级配置

你也可以直接编辑 `.settings.json`：

```json
{
  "max_concurrent": 1,
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

1. 输入 MissAV URL 或 JAV 代码（例如 `ABP-123`）
2. 点击“获取信息”获取视频详情
3. 选择质量偏好
4. 点击“立即下载”或“添加到队列”

### 批量下载

1. 点击“批量添加”
2. 每行输入一个 URL 或 JAV 代码
3. 点击“全部添加到队列”

### 管理下载

- 在队列中查看实时进度
- 使用 ✕ 按钮取消单个下载
- 清理已完成任务或清除等待队列
- 在“下载文件”部分浏览和管理已下载文件

## 🔧 故障排除

| 问题                 | 解决方案                                                             |
| -------------------- | -------------------------------------------------------------------- |
| 无法访问网页界面     | 检查 Gluetun 容器中端口是否正确暴露                                    |
| 下载卡住             | 验证 VPN 连接和网络模式配置                                            |
| 文件名错误           | 工具会自动缩短文件名 — 确保下载路径可写                               |
| 设置未保存           | 检查根目录中 `.settings.json` 的写入权限                              |
| 语言未更改           | 清除浏览器缓存或检查 `locales/` 文件夹是否正确挂载                    |
| JAV 代码不起作用     | 确保格式正确（例如 `ABP-123`、`SSIS-456`）                          |

## 🐳 Docker 构建

在本地构建 Docker 镜像：

```bash
docker build -t missav-dlp-web .
docker run -p 5000:5000 -v $(pwd)/downloads:/downloads missav-dlp-web
```

## 📦 要求

- Docker & Docker Compose
- （可选）Gluetun 或任何 OpenVPN/WireGuard 容器
- Python 3.8+（用于本地开发）
- FFmpeg（用于视频合并）

### 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 运行应用程序
python app.py

# 访问 http://localhost:5000
```

## 🔄 API 端点

应用程序提供 REST API 端点：

| 端点                    | 方法      | 描述             |
| ----------------------- | --------- | ---------------- |
| `/api/info`             | POST      | 获取视频信息     |
| `/api/download`         | POST      | 添加单个下载     |
| `/api/batch`            | POST      | 添加多个下载     |
| `/api/tasks`            | GET       | 列出所有任务     |
| `/api/tasks/<id>`       | DELETE    | 取消任务         |
| `/api/queue/stats`      | GET       | 队列统计信息     |
| `/api/settings`         | GET/PUT   | 获取/更新设置    |
| `/api/files`            | GET       | 列出已下载文件   |
| `/api/language`         | GET/POST  | 获取/设置语言    |

## ⚠️ 免责声明

此工具**仅供个人使用**。用户对版权合规性以及下载内容引起的任何后果承担全部责任。

## 📄 许可证

MIT 许可证 - 参见 [LICENSE](LICENSE) 文件

## 🙏 鸣谢

本项目基于 **[nerdnam](https://github.com/nerdnam)** 和原始 **[missav-dlp-web](https://github.com/nerdnam/missav-dlp-web)** 仓库的优秀工作。

### 原始仓库

- **作者:** nerdnam
- **仓库:** [github.com/nerdnam/missav-dlp-web](https://github.com/nerdnam/missav-dlp-web)
- **许可证:** 请查看原始仓库的许可条款

### 使用/改编的主要功能

- 集成 `curl_cffi` + `yt-dlp` 以绕过 Cloudflare
- 镜像域名轮换逻辑
- VPN 兼容性（Gluetun）
- 带有实时进度显示的网页下载界面

### 额外改进

- 多语言支持（4 种语言）
- 设置管理界面
- JAV 代码转换器
- 批量下载功能
- 带搜索和预览的文件管理器
- 任务特定日志记录
- 顺序/并行下载模式

### 感谢

- 原始项目的所有贡献者
- `yt-dlp` 和 `curl_cffi` 的开源社区
- 协助本地化的翻译人员

---

## 📝 更新日志

### 版本 3.0

- 添加多语言支持（EN、KO、JA、ZH）
- 添加设置管理界面
- 添加 JAV 代码转换
- 添加批量下载功能
- 添加带搜索功能的文件管理器
- 添加任务特定日志记录
- 将代码重组到 `app_files/` 模块
- 修复文件夹结构（downloads/logs 放在根目录）

### 版本 2.0

- 基于 nerdnam 的工作初始发布
- 基本下载功能
- 实时进度显示
- 使用 curl_cffi 绕过 Cloudflare