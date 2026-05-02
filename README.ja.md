# 🎥 MissAV Downloader Web UI

TrueNAS および Docker 環境で完全に動作する **MissAV Web ベースダウンローダー**。
`curl_cffi` と `yt-dlp` を使用して、ISP ブロック（SNI）や Cloudflare の強力なボット対策を回避します。

## ✨ Features

### Core Features

- **Web UI:** ブラウザで URL を入力するだけで、ダウンロードがバックグラウンドでスムーズに実行されます。
- **リアルタイム進捗表示:** 直感的な緑色のゲージバーでダウンロード進捗（%）を確認できます — ターミナルを確認する必要はありません。
- **スマートバイパスロジック:**
  - `curl_cffi` を使用して最新の Chrome ブラウザを偽装し、Cloudflare のボット検出や CAPTCHA を回避します。
  - MissAV のミラードメインを自動的にローテーションして、アクセス可能なアドレスを見つけます。
- **VPN 完全対応:** Gluetun のような VPN コンテナネットワークに接続している場合でもシームレスに動作し、IP 制限を正しく回避します。
- **安定性の向上:** 長い日本語/韓国語タイトルによって発生するファイルシステム保存エラー（`[Errno 36] File name too long`）を防ぐため、ファイル名を自動的に最適化します。
- **タスクキャンセル機能:** リスト内の `Delete` ボタンをクリックすると、バックグラウンドのダウンロードプロセスを即座に強制終了（キャンセル）できます。

### New Features

- **ゼロ設定セットアップ (Zero-Configuration):** プロキシの手動設定はもう不要です。アプリが OS を自動的に検出し、**SpoofDPI** を自動的にインストール・設定します。
- **SQLite データベース:** すべてのダウンロードタスクと履歴が永続的な SQLite データベースに保存されます。アプリがクラッシュしたり再起動したりしても、履歴が失われることはありません。
- **リアルタイムイベントストリーミング (SSE):** サーバーから UI に即座にアップデートを送信します。ポーリングは不要になり、進捗バーやステータスの変化がリアルタイムに反映されます。
- **ディープメタデータスクレイピング:** 動画ページを自動的に訪問し、出演者名、ジャンル、メーカー、レーベル、高画質ポスターを自動的に取得します。
- **MP4 メタデータタグ付け:** `mutagen` を使用して、取得したメタデータとカバーアートを MP4 ファイルに直接書き込み、プロフェッショナルなメディアライブラリ体験を提供します。
- **ビジュアルタスクリスト:** ダウンロードキューにすべての動画の高画質サムネイルプレビューが表示されます。
- **マルチサイトフォールバック:** MissAV にメタデータがない場合、BestJavPorn または JavGuru を自動的に検索します。
- **ディスク空き容量保護:** ダウンロード開始前に利用可能なディスク容量を自動的にチェックし、システムクラッシュを防止します（Docker 対応）。
- **プロセスのクリーン管理:** 終了時に SpoofDPI やその他のバックグラウンドプロセスを安全にクリーンアップします。
- **📊 ダウンロードメタデータ:** ダウンロードされた動画の解像度、最終ファイルサイズ、正確な所要時間をタスクリストから確認できます。
- **⚡ 動的並列ダウンロード:** 設定から同時ダウンロードスレッド数をリアルタイムで調整可能。余分なスレッドはアプリ再起動なしで安全に終了されます。
- **🔧 カスタム FFmpeg パス:** Web UI 上で FFmpeg バイナリのディレクトリを指定可能。保存前に `ffmpeg`、`ffprobe`、`ffplay` の存在をバックエンドが自動検証します。
- **🗑️ 履歴クリーン:** UI のワンクリックボタンで、サーバー上のすべてのダウンロードファイルを完全に削除できます。
- **📄 ドキュメントビューア:** ローカライズされた README、SECURITY、LICENSE ファイルを Web UI 内から直接閲覧できます。
- **🔗 カスタムURLクローラー:** シリーズ、メーカー、または検索URLを入力し、フィルターを選択し、スクレイプするページ数を選択すると、結果から直接動画を選択してダウンロードできます。

## 🛠️ Installation & Usage

### 📦 デスクトップ / リリース (最も簡単)

1. **ダウンロード**: **Releases** ページから、お使いの OS (Windows、Linux、macOS) 用の最新リリースをダウンロードしてください。
2. **実行**:
   - **Windows**: `MissAV_Downloader.exe` をダブルクリックします。
   - **Linux/macOS**: ターミナルを開き、`./MissAV_Downloader` を実行します（実行権限が必要です: `chmod +x MissAV_Downloader`）。
3. **完了**: アプリが自動的に環境設定 (SpoofDPI) を行い、ブラウザで `http://localhost:5000` を開きます。

---

### 🐳 Docker インストール (サーバー/NAS 推奨)

> ⚠️ **推奨:** 安全のため、VPN（例：Gluetun）と一緒に実行してください。

### 1. `docker-compose.yml` を作成

ダウンローダーコンテナを VPN ネットワークに接続します。（GitHub Container Registry を使用）

```yaml
version: '3'
services:
  missav-dlp-web:
    image: ghcr.io/nerdnam/missav-dlp-web:latest
    network_mode: "container:gluetun-vpn" # 任意: VPN コンテナを使用する場合
    # ports:
    #   - "5000:5000" # VPN を使用しない場合のみ有効化
    volumes:
      - /path/to/your/downloads:/downloads
      - ./locales:/app/locales # 任意: カスタム翻訳用
    restart: unless-stopped
```

### 2. Gluetun の `docker-compose.yml` にポートを追加

ダウンローダーは VPN コンテナに接続されるため、**Gluetun コンテナの設定に外部アクセス用ポートを追加する必要があります**：

```yaml
services:
  gluetun-vpn:
    # ...（既存の Gluetun 設定）...
    ports:
      - "58000:5000/tcp"  # ホストのポート 58000 をコンテナのポート 5000 にマッピング
```

### 3. Web UI にアクセス

コンテナ起動後、ブラウザで以下にアクセスします：

```
http://[YOUR_NAS_OR_SERVER_IP]:58000
```

## 📁 プロジェクト構造

```
missav-dlp-web/
├── app.py                    # メイン Flask アプリケーション
├── .settings.json            # ユーザー設定（自動生成）
├── downloads/                # ダウンロードされた動画
├── logs/                     # ダウンロードタスクのログ
├── locales/                  # 言語ファイル
│   ├── en.json              # 英語
│   ├── ko.json              # 韓国語
│   ├── ja.json              # 日本語
│   └── zh.json              # 中国語（簡体字）
├── templates/                # Web インターフェース
│   ├── index.html           # メインページ
│   ├── script.js            # フロントエンドロジック
│   └── style.css            # スタイル
├── app_files/               # バックエンドモジュール
│   ├── config_manager.py    # 設定管理
│   ├── download_manager.py  # ダウンロードキューと yt-dlp
│   ├── extractor.py         # カスタム MissAV 抽出器
│   ├── language.py          # 多言語対応
│   ├── paths.py             # パス管理
│   └── utils.py             # ヘルパー関数
└── ffmpeg/                  # FFmpeg バイナリ（任意）
    └── bin/
        └── ffmpeg.exe
```

## 🌍 言語サポート

アプリケーションは複数の言語に対応しており、いつでも切り替え可能です：

| 言語                      | コード | 状態    |
| ------------------------- | ------ | ------- |
| English                   | en     | ✅ 完全 |
| 한국어 (Korean)           | ko     | ✅ 完全 |
| 日本語 (Japanese)         | ja     | ✅ 完全 |
| 中文 (Chinese Simplified) | zh     | ✅ 完全 |

新しい言語を追加する方法：

1. `locales/` フォルダに新しい JSON ファイルを作成（例：`fr.json`）
2. `en.json` の構造をコピーして翻訳
3. `templates/index.html` のドロップダウンに言語コードを追加

## ⚙️ 設定

設定は `.settings.json` に保存され、Web UI から変更可能です：

| 設定項目                    | 説明                       | デフォルト                         |
| --------------------------- | -------------------------- | ---------------------------------- |
| ダウンロードディレクトリ    | 動画の保存場所             | `./downloads`                    |
| FFmpeg バイナリディレクトリ | FFmpeg のカスタムパス      | システム PATH                      |
| 最大同時ダウンロード数      | 並列ダウンロードスレッド数 | `1`                              |
| 順次モード                  | 1つずつダウンロードするか  | `true`                           |
| ダウンロード間の遅延        | 次のダウンロードまでの秒数 | `3`                              |
| デフォルト品質              | 最大解像度                 | `best`                           |
| ミラードメイン              | フォールバック用ドメイン   | `missav.ai`, `missav.net` など |

### 高度な設定

`.settings.json` を直接編集することも可能です：

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

## 🚀 使用例

### 単一ダウンロード

1. MissAV の URL または JAV コード（例：`ABP-123`）を入力
2. 「Get Info」をクリックして動画情報を取得
3. 希望する画質を選択
4. 「Download Now」または「Add to Queue」をクリック

### バッチダウンロード

1. 「Batch Add」をクリック
2. 複数の URL または JAV コードを入力（1行に1つ）
3. 「Add All to Queue」をクリック

### ダウンロード管理

- キュー内でリアルタイム進捗を確認
- ✕ ボタンで個別ダウンロードをキャンセル
- 完了済みタスクの整理や待機キューのクリア
- Downloads セクションでダウンロード済みファイルの閲覧・管理

### カスタムURLクローラー

1. MissAVのシリーズ、メーカー、または検索URLを入力します
2. 「Custom」ボタンをクリックします
3. リストからフィルターを選択します（または「All」を使用）
4. スクレイプするページ数を選択します
5. 結果リストから動画を選択します
6. 「Download Selected」をクリックしてキューに追加します

## 🔧 トラブルシューティング

| 問題                      | 解決方法                                                                         |
| ------------------------- | -------------------------------------------------------------------------------- |
| Web UI にアクセスできない | Gluetun コンテナでポートが正しく公開されているか確認                             |
| ダウンロードが停止する    | VPN 接続およびネットワークモード設定を確認                                       |
| ファイル名エラー          | ツールは自動的に短縮します — ダウンロードパスが書き込み可能か確認               |
| 設定が保存されない        | ルートディレクトリ内の `.settings.json` の書き込み権限を確認                   |
| 言語が変更されない        | ブラウザキャッシュをクリア、または `locales/` が正しくマウントされているか確認 |
| JAV コードが動作しない    | フォーマットが正しいか確認（例：`ABP-123`, `SSIS-456`）                      |

## 🐳 Docker ビルド

Docker イメージをローカルでビルドする場合：

```bash
docker build -t missav-dlp-web .
docker run -p 5000:5000 -v $(pwd)/downloads:/downloads missav-dlp-web
```

## 📦 要件

- Docker & Docker Compose (コンテナ展開用)
- Python 3.8+ (ローカルソース実行用)
- **PyInstaller** (独自の .exe / バイナリのビルド用)
- FFmpeg (動画結合用)
- (オプション) Gluetun または任意の OpenVPN/WireGuard コンテナ

### 🛠️ 開発とビルド (Development & Building)

ソースコードから実行するか、独自の実行ファイルをビルドする場合:

#### 1. 環境設定
```bash
# 仮想環境の作成
python -m venv venv

# 有効化
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt
pip install pyinstaller
```

#### 2. ソースから実行
```bash
python main.py
```

#### 3. 実行ファイルのビルド
すべてのプラットフォーム向けに自動化スクリプトを提供しています:
- **Windows**: `build.bat` を実行
- **Linux/macOS**: `bash build.sh` を実行

**手動ビルド:**
```bash
pyinstaller --clean MissAV_Downloader_onefile.spec
```

---

## 🔄 API エンドポイント

アプリケーションは REST API を提供します：

| エンドポイント               | メソッド | 説明                                                            |
| ---------------------------- | -------- | --------------------------------------------------------------- |
| `/api/info`                | POST     | 動画情報を取得                                                  |
| `/api/download`            | POST     | 単一ダウンロードを追加                                          |
| `/api/batch`               | POST     | 複数ダウンロードを追加                                          |
| `/api/tasks`               | GET      | 全タスク一覧を取得                                              |
| `/api/tasks/<id>`          | DELETE   | タスクをキャンセル                                              |
| `/api/queue/stats`         | GET      | キュー統計情報                                                  |
| `/api/settings`            | GET/PUT  | 設定の取得 / 更新                                               |
| `/api/files`               | GET      | ダウンロード済みファイル一覧                                    |
| `/api/language`            | GET/POST | 言語の取得 / 設定                                               |
| `/api/docs/<type>`         | GET      | ローカライズされたドキュメント取得（readme, security, license） |
| `/api/files/clean_history` | POST     | すべてのダウンロードファイルを削除                              |
| `/api/crawl`              | POST     | フィルター/ページネーションでURLから動画をスクレイプ |
| `/api/crawl/filters`      | POST     | URLで利用可能なフィルターを取得 |

## ⚠️ 免責事項

このツールは**個人利用のみ**を目的としています。
ダウンロードされたコンテンツに関する著作権遵守およびその結果については、すべてユーザー自身の責任となります。

## 📄 ライセンス

MIT License - 詳細は [LICENSE](LICENSE) ファイルを参照してください。

## 🙏 謝辞

本プロジェクトは **[nerdnam](https://github.com/nerdnam)** および元の **[missav-dlp-web](https://github.com/nerdnam/missav-dlp-web)** リポジトリの優れた成果を基にしています。

### 元リポジトリ

* **作者:** nerdnam
* **リポジトリ:** [https://github.com/nerdnam/missav-dlp-web](https://github.com/nerdnam/missav-dlp-web)
* **ライセンス:** 詳細は元リポジトリを参照

### 使用 / 改良された主な機能

* Cloudflare 回避のための `curl_cffi` + `yt-dlp` 統合
* ミラードメインローテーションロジック
* VPN（Gluetun）対応
* リアルタイム進捗付き Web ダウンロード UI

### 追加改善点

* 多言語対応（4言語）
* 設定管理 UI
* JAV コード変換
* バッチダウンロード機能
* 検索・プレビュー付きファイルマネージャー
* タスク単位のログ管理
* 順次 / 並列ダウンロードモード

### Thanks To

* 元プロジェクトのすべての貢献者
* `yt-dlp` および `curl_cffi` のオープンソースコミュニティ
* ローカライズに貢献した翻訳者

---

## 📝 変更履歴

### Version 4.0 (Industrial Grade)

- **ゼロ設定**: Linux および macOS での SpoofDPI **自動インストール**に対応、Windows でのバイナリ自動検出。
- **原子的永続性**: メモリ保存を **SQLite** に置き換え、クラッシュに強い履歴保存を実現。
- **反応型 UI**: **SSE (Server-Sent Events)** を導入し、即時かつ低負荷なアップデートを実装。
- **メタデータ・プロ**: **ディープスクレイピング + Mutagen** の統合により、自動 MP4 タグ付けとカバーアートに対応。
- **ビジュアルキュー**: タスクリストに **120px サムネイル** を追加。
- **安全装置**: Docker マウントポイント検出機能付きの **ディスク空き容量保護** を追加。
- **インテリジェンス**: 欠落したタグを補完する **マルチサイトフォールバック** (BestJavPorn/JavGuru) を追加。
- **安定性**: SpoofDPI インスタンスのクリーンアップのためのプロセスライフサイクルを改善。

### Version 3.1

* スマート解像度フォールバックロジックを追加（正確 → 高 → 低 → デフォルト）
* 動的並列ダウンロードスケーリングと安全なスレッド終了を追加
* ダウンロードメタデータ表示（解像度、サイズ、所要時間）を追加
* カスタム FFmpeg パス設定とバックエンド検証を追加
* ダウンロードファイルを一括削除する「履歴クリーン」ボタンを追加
* ローカライズされたドキュメントビューアを追加（README、SECURITY、LICENSE）
* yt-dlp 抽出器の競合による「Get Info」クラッシュを修正
* マージ後にファイル名 / サイズが正しく表示されない問題を修正
* 低解像度モニターでの設定モーダルのオーバーフローを修正

### Version 3.0

* 多言語対応（EN、KO、JA、ZH）を追加
* 設定管理 UI を追加
* JAV コード変換を追加
* バッチダウンロード機能を追加
* 検索付きファイルマネージャーを追加
* タスク単位ログを追加
* コードを `app_files/` モジュールへ再編成
* フォルダ構成修正（downloads / logs をルートに配置）

### Version 2.0

* nerdnam の成果を基にした初期リリース
* 基本ダウンロード機能
* リアルタイム進捗表示
* curl_cffi による Cloudflare 回避
