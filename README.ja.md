# 🎥 MissAV Downloader Web UI

**MissAV向けウェブベースダウンローダー**。TrueNASやDocker環境で完璧に動作します。
`curl_cffi` と `yt-dlp` を使用して、ISPによるブロック（SNI）やCloudflareの強力なボット保護を回避します。

## ✨ 特徴

### コア機能

- **ウェブUI:** ブラウザにURLを入力するだけで、バックグラウンドでスムーズにダウンロードを実行。
- **リアルタイム進捗表示:** 直感的なゲージバーでダウンロード進捗率（%）を確認できます。
- **スマートバイパスロジック:**
  - `curl_cffi` を使用して最新Chromeブラウザを偽装し、Cloudflareのボット保護とCAPTCHAを回避。
  - MissAVのミラードメインを自動的にローテーションし、アクセス可能なアドレスを検索。
- **完全なVPN互換性:** GluetunなどのVPNコンテナネットワークに接続している場合でも正常に動作し、IP制限を適切にバイパス。
- **安定性の向上:** 長い日本語/韓国語のタイトルによるファイル名超過エラー `[Errno 36] File name too long` を防ぐため、自動的にファイル名を最適化。
- **タスクキャンセル機能:** リストの `Delete` ボタンをクリックすると、バックグラウンドのダウンロードプロセスを即座に強制終了（キャンセル）できます。

### 新機能

- **🌍 多言語サポート:** 英語、韓国語、日本語、中国語（簡体字）に対応。ドロップダウンメニューから簡単に言語を切り替え可能。
- **⚙️ 設定管理:** ウェブUIからダウンロードディレクトリ、順次モード、ダウンロード間隔、デフォルト品質、ミラードメインを設定可能。
- **🔍 JAVコード変換:** JAVコード（例：ABP-123）を入力するだけで、自動的に正しいMissAV URLに変換。
- **📦 バッチダウンロード:** 複数のURLやJAVコードを一度に追加して一括ダウンロード。
- **📁 ファイルマネージャー:** ダウンロードしたファイルをWebインターフェースから直接閲覧、検索、プレビュー、削除可能。
- **📝 ダウンロードログ:** 各ダウンロードタスクに個別のログファイルがあり、トラブルシューティングに役立ちます。
- **⚡ 順次/並列モード:** 一度に1つのビデオをダウンロードするか、複数を同時にダウンロードするかを選択可能。

## 🛠️ インストールと使用方法

> ⚠️ **推奨:** 安全性のため、VPN（例：Gluetun）と共に実行してください。

### 1. `docker-compose.yml` の作成

ダウンローダーコンテナをVPNネットワークに接続します（GitHub Container Registryを使用）。

```yaml
version: '3'
services:
  missav-dlp-web:
    image: ghcr.io/nerdnam/missav-dlp-web:latest
    network_mode: "container:gluetun-vpn" # オプション: VPNコンテナ使用時
    # ports:
    #   - "5000:5000" # VPNを使用しない場合のみ有効化
    volumes:
      - /path/to/your/downloads:/downloads
      - ./locales:/app/locales # オプション: カスタム翻訳用
    restart: unless-stopped
```

### 2. Gluetunの `docker-compose.yml` にポートを追加

ダウンローダーがVPNコンテナに接続するため、**Gluetunコンテナ設定**に外部アクセス用ポートを**追加する必要があります**：

```yaml
services:
  gluetun-vpn:
    # ... (既存のGluetun設定) ...
    ports:
      - "58000:5000/tcp"  # ホストポート58000をコンテナポート5000にマッピング
```

### 3. ウェブUIにアクセス

コンテナ起動後、ブラウザを開いて以下のURLにアクセスします：

```
http://[YOUR_NAS_OR_SERVER_IP]:58000
```

## 📁 プロジェクト構造

```
missav-dlp-web/
├── app.py                    # メインFlaskアプリケーション
├── .settings.json            # ユーザー設定（自動生成）
├── downloads/                # ダウンロードしたビデオ
├── logs/                     # ダウンロードタスクログ
├── locales/                  # 言語ファイル
│   ├── en.json              # 英語
│   ├── ko.json              # 韓国語
│   ├── ja.json              # 日本語
│   └── zh.json              # 中国語（簡体字）
├── templates/                # ウェブインターフェース
│   ├── index.html           # メインページ
│   ├── script.js            # フロントエンドロジック
│   └── style.css            # スタイル
├── app_files/               # バックエンドモジュール
│   ├── config_manager.py    # 設定管理
│   ├── download_manager.py  # ダウンロードキューとyt-dlp
│   ├── extractor.py         # カスタムMissAV抽出器
│   ├── language.py          # 多言語サポート
│   ├── paths.py             # パス管理
│   └── utils.py             # ヘルパー関数
└── ffmpeg/                  # FFmpegバイナリ（オプション）
    └── bin/
        └── ffmpeg.exe
```

## 🌍 言語サポート

このアプリケーションは複数の言語をサポートしており、いつでも切り替えられます：

| 言語                  | コード | ステータス |
| --------------------- | ------ | ---------- |
| English               | en     | ✅ 完全    |
| 한국어 (韓国語)       | ko     | ✅ 完全    |
| 日本語                | ja     | ✅ 完全    |
| 中文 (中国語・簡体字) | zh     | ✅ 完全    |

新しい言語を追加するには：

1. `locales/` フォルダに新しいJSONファイルを作成（例：`fr.json`）
2. `en.json` から構造をコピーし、値を翻訳
3. `templates/index.html` のドロップダウンに言語コードを追加

## ⚙️ 設定

設定は `.settings.json` に保存され、ウェブUIから変更できます：

| 設定項目                 | 説明                                 | デフォルト                          |
| ------------------------ | ------------------------------------ | ----------------------------------- |
| ダウンロードディレクトリ | ビデオの保存先                       | `./downloads`                     |
| 順次モード               | 一度に1つのビデオをダウンロード      | `true`                            |
| ダウンロード間隔         | ダウンロード間の待機時間（秒）       | `3`                               |
| デフォルト品質           | ダウンロードする最大解像度           | `best`                            |
| ミラードメイン           | フォールバック用MissAVミラードメイン | `missav.ai`, `missav.net`, など |

### 詳細設定

`.settings.json` を直接編集することもできます：

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

## 🚀 使用例

### 単体ダウンロード

1. MissAVのURLまたはJAVコード（例：`ABP-123`）を入力
2. 「情報取得」をクリックしてビデオ詳細を取得
3. 品質を選択
4. 「今すぐダウンロード」または「キューに追加」をクリック

### バッチダウンロード

1. 「バッチ追加」をクリック
2. 複数のURLまたはJAVコードを1行ずつ入力
3. 「すべてキューに追加」をクリック

### ダウンロードの管理

- キューでリアルタイムの進捗を確認
- ✕ボタンで個別のダウンロードをキャンセル
- 完了したタスクをクリーンアップ、または待機中のキューをクリア
- 「ダウンロード」セクションでダウンロードしたファイルを閲覧・管理

## 🔧 トラブルシューティング

| 問題                     | 解決策                                                                                  |
| ------------------------ | --------------------------------------------------------------------------------------- |
| Web UIにアクセスできない | Gluetunコンテナでポートが正しく公開されているか確認                                     |
| ダウンロードが止まる     | VPN接続とネットワークモード設定を確認                                                   |
| ファイル名エラー         | ツールは自動的にファイル名を短縮します。ダウンロードパスが書き込み可能か確認            |
| 設定が保存されない       | ルートディレクトリの `.settings.json` の書き込み権限を確認                            |
| 言語が変わらない         | ブラウザキャッシュをクリアするか、`locales/` フォルダが正しくマウントされているか確認 |
| JAVコードが動作しない    | 形式が正しいか確認（例：`ABP-123`、`SSIS-456`）                                     |

## 🐳 Dockerビルド

Dockerイメージをローカルでビルドするには：

```bash
docker build -t missav-dlp-web .
docker run -p 5000:5000 -v $(pwd)/downloads:/downloads missav-dlp-web
```

## 📦 要件

- Docker & Docker Compose
- （オプション）Gluetun または任意のOpenVPN/WireGuardコンテナ
- Python 3.8+（ローカル開発用）
- FFmpeg（ビデオ結合用）

### ローカル開発

```bash
# 依存関係のインストール
pip install -r requirements.txt

# アプリケーションの実行
python app.py

# http://localhost:5000 にアクセス
```

## 🔄 APIエンドポイント

このアプリケーションはREST APIエンドポイントを提供します：

| エンドポイント       | メソッド | 説明                       |
| -------------------- | -------- | -------------------------- |
| `/api/info`        | POST     | ビデオ情報の取得           |
| `/api/download`    | POST     | 単体ダウンロードを追加     |
| `/api/batch`       | POST     | 複数ダウンロードを追加     |
| `/api/tasks`       | GET      | 全タスクの一覧             |
| `/api/tasks/<id>`  | DELETE   | タスクのキャンセル         |
| `/api/queue/stats` | GET      | キューの統計情報           |
| `/api/settings`    | GET/PUT  | 設定の取得/更新            |
| `/api/files`       | GET      | ダウンロードファイルの一覧 |
| `/api/language`    | GET/POST | 言語の取得/設定            |

## ⚠️ 免責事項

このツールは**個人利用のみ**を目的としています。著作権の遵守およびダウンロードしたコンテンツから生じる結果については、すべてユーザー自身が責任を負います。

## 📄 ライセンス

MITライセンス - [LICENSE](LICENSE) ファイルを参照

## 🙏 謝辞

このプロジェクトは **[nerdnam](https://github.com/nerdnam)** とオリジナルの **[missav-dlp-web](https://github.com/nerdnam/missav-dlp-web)** リポジトリの優れた成果に基づいています。

### オリジナルリポジトリ

- **作者:** nerdnam
- **リポジトリ:** [github.com/nerdnam/missav-dlp-web](https://github.com/nerdnam/missav-dlp-web)
- **ライセンス:** オリジナルリポジトリでライセンス条項を確認してください

### 使用/適応した主な機能

- Cloudflare回避のための `curl_cffi` + `yt-dlp` 統合
- ミラードメインローテーションロジック
- VPN互換性（Gluetun）
- リアルタイム進捗表示付きウェブベースダウンロードUI

### 追加された改善点

- 多言語サポート（4言語）
- 設定管理UI
- JAVコードコンバーター
- バッチダウンロード機能
- 検索・プレビュー付きファイルマネージャー
- タスク固有のロギング
- 順次/並列ダウンロードモード

### 謝辞

- オリジナルプロジェクトのすべての貢献者
- `yt-dlp` と `curl_cffi` のオープンソースコミュニティ
- ローカライゼーションに協力してくださった翻訳者の皆様

---

## 📝 変更履歴

### バージョン 3.0

- 多言語サポート（EN、KO、JA、ZH）を追加
- 設定管理UIを追加
- JAVコード変換を追加
- バッチダウンロード機能を追加
- 検索機能付きファイルマネージャーを追加
- タスク固有のロギングを追加
- コードを `app_files/` モジュールに再構成
- フォルダ構造を修正（downloads/logsをルートに配置）

### バージョン 2.0

- nerdnamの成果に基づく初回リリース
- 基本的なダウンロード機能
- リアルタイム進捗表示
- curl_cffiによるCloudflare回避
