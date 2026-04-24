
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

- **🌍 多言語対応:** 英語、韓国語、日本語、中国語（簡体字）に対応。ドロップダウンメニューから簡単に言語を切り替え可能です。
- **⚙️ 設定管理:** ダウンロードディレクトリ、順次モード、ダウンロード間の遅延、デフォルト品質、ミラードメインを Web UI から直接設定できます。
- **🔍 JAV コード変換:** JAV コード（例：ABP-123）を入力するだけで、アプリが自動的に正しい MissAV URL に変換します。
- **📦 バッチダウンロード:** 複数の URL または JAV コードを一度に追加して一括ダウンロードできます。
- **📁 ファイルマネージャー:** Web インターフェースからダウンロード済みファイルの閲覧、検索、プレビュー、削除が可能です。
- **📝 ダウンロードログ:** 各ダウンロードタスクごとに専用のログファイルが生成されます。
- **⚡ 順次 / 並列モード:** 一度に 1 本ずつ、または複数同時にダウンロードするモードを選択できます。
- **🎯 スマート解像度フォールバック:** 選択した品質（例：1080p）が利用できない場合、より高い解像度（1440p / 2160p）→低い解像度（720p / 480p）→最終的に利用可能な最適品質へと自動的に切り替えます。
- **📊 ダウンロードメタデータ:** ダウンロードされた動画の解像度、最終ファイルサイズ、正確な所要時間をタスクリストから確認できます。
- **⚡ 動的並列ダウンロード:** 設定から同時ダウンロードスレッド数をリアルタイムで調整可能。余分なスレッドはアプリ再起動なしで安全に終了されます。
- **🔧 カスタム FFmpeg パス:** Web UI 上で FFmpeg バイナリのディレクトリを指定可能。保存前に `ffmpeg`、`ffprobe`、`ffplay` の存在をバックエンドが自動検証します。
- **🗑️ 履歴クリーン:** UI のワンクリックボタンで、サーバー上のすべてのダウンロードファイルを完全に削除できます。
- **📄 ドキュメントビューア:** ローカライズされた README、SECURITY、LICENSE ファイルを Web UI 内から直接閲覧できます。

## 🛠️ Installation & Usage

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
````
### 2. Gluetun の `docker-compose.yml` にポートを追加

ダウンローダーは VPN コンテナに接続されるため、**Gluetun コンテナの設定に外部アクセス用ポートを追加する必要があります**：

```yaml
services:
  gluetun-vpn:
    # ...（既存の Gluetun 設定）...
    ports:
      - "58000:5000/tcp"  # ホストのポート 58000 をコンテナのポート 5000 にマッピング
````

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

| 言語                      | コード | 状態   |
| ----------------------- | --- | ---- |
| English                 | en  | ✅ 完全 |
| 한국어 (Korean)            | ko  | ✅ 完全 |
| 日本語 (Japanese)          | ja  | ✅ 完全 |
| 中文 (Chinese Simplified) | zh  | ✅ 完全 |

新しい言語を追加する方法：

1. `locales/` フォルダに新しい JSON ファイルを作成（例：`fr.json`）
2. `en.json` の構造をコピーして翻訳
3. `templates/index.html` のドロップダウンに言語コードを追加

## ⚙️ 設定

設定は `.settings.json` に保存され、Web UI から変更可能です：

| 設定項目              | 説明             | デフォルト                        |
| ----------------- | -------------- | ---------------------------- |
| ダウンロードディレクトリ      | 動画の保存場所        | `./downloads`                |
| FFmpeg バイナリディレクトリ | FFmpeg のカスタムパス | システム PATH                    |
| 最大同時ダウンロード数       | 並列ダウンロードスレッド数  | `1`                          |
| 順次モード             | 1つずつダウンロードするか  | `true`                       |
| ダウンロード間の遅延        | 次のダウンロードまでの秒数  | `3`                          |
| デフォルト品質           | 最大解像度          | `best`                       |
| ミラードメイン           | フォールバック用ドメイン   | `missav.ai`, `missav.net` など |

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

## 🔧 トラブルシューティング

| 問題                   | 解決方法                                                                 |
| ---------------------- | ------------------------------------------------------------------------ |
| Web UI にアクセスできない | Gluetun コンテナでポートが正しく公開されているか確認                     |
| ダウンロードが停止する   | VPN 接続およびネットワークモード設定を確認                               |
| ファイル名エラー        | ツールは自動的に短縮します — ダウンロードパスが書き込み可能か確認        |
| 設定が保存されない      | ルートディレクトリ内の `.settings.json` の書き込み権限を確認              |
| 言語が変更されない      | ブラウザキャッシュをクリア、または `locales/` が正しくマウントされているか確認 |
| JAV コードが動作しない  | フォーマットが正しいか確認（例：`ABP-123`, `SSIS-456`）                 |

## 🐳 Docker ビルド

Docker イメージをローカルでビルドする場合：

```bash
docker build -t missav-dlp-web .
docker run -p 5000:5000 -v $(pwd)/downloads:/downloads missav-dlp-web
````

## 📦 要件

* Docker & Docker Compose
* （任意）Gluetun または OpenVPN / WireGuard コンテナ
* Python 3.8+（ローカル開発用）
* FFmpeg（動画結合用）

### ローカル開発

```bash
# 依存関係をインストール
pip install -r requirements.txt

# アプリケーションを実行
python app.py

# http://localhost:5000 でアクセス
```

## 🔄 API エンドポイント

アプリケーションは REST API を提供します：

| エンドポイント                    | メソッド     | 説明                                           |
| -------------------------- | -------- | -------------------------------------------- |
| `/api/info`                | POST     | 動画情報を取得                                      |
| `/api/download`            | POST     | 単一ダウンロードを追加                                  |
| `/api/batch`               | POST     | 複数ダウンロードを追加                                  |
| `/api/tasks`               | GET      | 全タスク一覧を取得                                    |
| `/api/tasks/<id>`          | DELETE   | タスクをキャンセル                                    |
| `/api/queue/stats`         | GET      | キュー統計情報                                      |
| `/api/settings`            | GET/PUT  | 設定の取得 / 更新                                   |
| `/api/files`               | GET      | ダウンロード済みファイル一覧                               |
| `/api/language`            | GET/POST | 言語の取得 / 設定                                   |
| `/api/docs/<type>`         | GET      | ローカライズされたドキュメント取得（readme, security, license） |
| `/api/files/clean_history` | POST     | すべてのダウンロードファイルを削除                            |

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
