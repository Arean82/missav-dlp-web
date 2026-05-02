# 🎥 MissAV Downloader Web UI

TrueNAS 및 Docker 환경에서 완벽하게 작동하는 **MissAV 웹 기반 다운로더**입니다.
`curl_cffi`와 `yt-dlp`를 사용하여 ISP 차단(SNI) 및 Cloudflare의 강력한 봇 보호를 우회합니다.

## ✨ 기능

### 핵심 기능

- **웹 UI:** 브라우저에 URL을 입력하기만 하면 백그라운드에서 다운로드가 원활하게 실행됩니다.
- **실시간 진행률 표시:** 직관적인 녹색 게이지 바로 다운로드 진행률(%)을 확인할 수 있습니다 — 터미널을 확인할 필요가 없습니다.
- **스마트 우회 로직:**
  - `curl_cffi`를 사용하여 최신 Chrome 브라우저를 가장해 Cloudflare의 봇 감지 및 CAPTCHA를 우회합니다.
  - MissAV 미러 도메인을 자동으로 순환하여 접근 가능한 주소를 찾습니다.
- **완전한 VPN 호환성:** Gluetun과 같은 VPN 컨테이너 네트워크에 연결되어 있어도 정상적으로 작동하며 IP 제한을 우회합니다.
- **향상된 안정성:** 긴 일본어/한국어 제목으로 인해 발생하는 파일 시스템 오류(`Errno 36`)를 방지하기 위해 파일명을 자동으로 최적화합니다。
- **작업 취소 기능:** 목록에서 `Delete` 버튼을 클릭하면 백그라운드 다운로드 프로세스를 즉시 종료(취소)할 수 있습니다。

### 신규 기능

- **제로 설정 구성 (Zero-Configuration):** 더 이상 수동으로 프록시를 설정할 필요가 없습니다. 앱이 OS를 자동으로 감지하고 **SpoofDPI**를 자동으로 설치 및 구성합니다.
- **SQLite 데이터베이스:** 모든 다운로드 작업과 기록이 SQLite 데이터베이스에 저장됩니다. 앱이 재시작되거나 종료되어도 기록이 유실되지 않습니다.
- **실시간 이벤트 스트리밍 (SSE):** 서버에서 UI로 즉각적인 업데이트를 보냅니다. 더 이상 폴링이 필요 없으며, 진행률과 상태 변화가 실시간으로 반영됩니다.
- **딥 메타데이터 스크래핑:** 비디오 페이지를 직접 방문하여 배우 이름, 장르, 제작사, 레이블 및 고해상도 포스터를 자동으로 수집합니다.
- **MP4 메타데이터 태깅:** `mutagen`을 사용하여 수집된 메타데이터와 커버 아트를 MP4 파일에 직접 삽입하여 전문적인 미디어 라이브러리를 구축합니다.
- **비주얼 작업 목록:** 다운로드 큐에 모든 비디오의 고화질 썸네일 미리보기가 표시됩니다.
- **멀티 사이트 폴백:** MissAV에 메타데이터가 없는 경우 BestJavPorn 또는 JavGuru를 자동으로 검색합니다.
- **디스크 공간 보호:** 다운로드 시작 전 사용 가능한 공간을 자동으로 확인하여 시스템 충돌을 방지합니다 (Docker 호환).
- **안정적인 프로세스 관리:** 종료 시 SpoofDPI 및 기타 백그라운드 프로세스를 안정적으로 정리합니다.
- **📊 다운로드 메타데이터:** 해상도, 파일 크기, 소요 시간 표시。
- **⚡ 동적 병렬 다운로드:** 실행 중에도 동시 다운로드 수 변경 가능。
- **🔧 FFmpeg 경로 설정:** 웹 UI에서 FFmpeg 경로 지정 및 자동 검증。
- **🗑️ 기록 삭제:** 버튼 한 번으로 모든 다운로드 파일 삭제。
- **📄 문서 뷰어:** README, SECURITY, LICENSE를 UI에서 확인 가능。
- **🔗 사용자 정의 URL 크롤러:** 시리즈, 메이커 또는 검색 URL을 입력하고, 필터를 선택하고, 스크랩할 페이지 수를 선택한 후 결과에서 직접 비디오를 선택하여 다운로드할 수 있습니다.

## 🛠️ 설치 및 사용

### 📦 데스크탑 / 릴리스 (가장 쉬움)

1. **다운로드**: **Releases** 페이지에서 사용 중인 OS(Windows, Linux, macOS)용 최신 버전을 다운로드하세요.
2. **실행**:
   - **Windows**: `MissAV_Downloader.exe`를 더블 클릭하세요.
   - **Linux/macOS**: 터미널을 열고 `./MissAV_Downloader`를 실행하세요 (실행 권한 필요: `chmod +x MissAV_Downloader`).
3. **완료**: 앱이 자동으로 환경 설정(SpoofDPI)을 완료하고 브라우저에서 `http://localhost:5000`을 엽니다.

---

### 🐳 Docker 설치 (서버/NAS 권장)

> ⚠️ **권장:** 안전을 위해 VPN(예: Gluetun)과 함께 실행하세요.

### 1. `docker-compose.yml` 생성

다운로더 컨테이너를 VPN 네트워크에 연결합니다. (GitHub Container Registry 사용)

```yaml
version: '3'
services:
  missav-dlp-web:
    image: ghcr.io/nerdnam/missav-dlp-web:latest
    network_mode: "container:gluetun-vpn" # 선택 사항: VPN 컨테이너 사용 시
    # ports:
    #   - "5000:5000" # VPN을 사용하지 않을 때만 활성화
    volumes:
      - /path/to/your/downloads:/downloads
      - ./locales:/app/locales # 선택 사항: 사용자 정의 번역
    restart: unless-stopped
```

### 2. Gluetun `docker-compose.yml`에 포트 추가

다운로더가 VPN 컨테이너에 연결되므로, **Gluetun 컨테이너 설정에 외부 접근 포트를 반드시 추가해야 합니다**:

```yaml
services:
  gluetun-vpn:
    # ... (기존 Gluetun 설정) ...
    ports:
      - "58000:5000/tcp"  # 호스트 포트 58000을 컨테이너 포트 5000에 매핑
```

### 3. Web UI 접속

컨테이너 실행 후, 브라우저에서 다음 주소로 접속합니다:

```id=
http://[YOUR_NAS_OR_SERVER_IP]:58000
```

## 📁 프로젝트 구조

```id=
missav-dlp-web/
├── app.py                    # 메인 Flask 애플리케이션
├── .settings.json            # 사용자 설정 (자동 생성)
├── downloads/                # 다운로드된 영상
├── logs/                     # 다운로드 작업 로그
├── locales/                  # 언어 파일
│   ├── en.json              # 영어
│   ├── ko.json              # 한국어
│   ├── ja.json              # 일본어
│   └── zh.json              # 중국어(간체)
├── templates/                # 웹 인터페이스
│   ├── index.html           # 메인 페이지
│   ├── script.js            # 프론트엔드 로직
│   └── style.css            # 스타일
├── app_files/               # 백엔드 모듈
│   ├── config_manager.py    # 설정 관리
│   ├── download_manager.py  # 다운로드 큐 및 yt-dlp
│   ├── extractor.py         # 커스텀 MissAV 추출기
│   ├── language.py          # 다국어 지원
│   ├── paths.py             # 경로 관리
│   └── utils.py             # 유틸리티 함수
└── ffmpeg/                  # FFmpeg 바이너리 (선택 사항)
    └── bin/
        └── ffmpeg.exe
```

## 🌍 언어 지원

애플리케이션은 여러 언어를 지원하며 언제든지 전환할 수 있습니다:

| 언어                      | 코드 | 상태    |
| ------------------------- | ---- | ------- |
| English                   | en   | ✅ 전체 |
| 한국어 (Korean)           | ko   | ✅ 전체 |
| 日本語 (Japanese)         | ja   | ✅ 전체 |
| 中文 (Chinese Simplified) | zh   | ✅ 전체 |

새 언어 추가 방법:

1. `locales/` 폴더에 새 JSON 파일 생성 (예: `fr.json`)
2. `en.json` 구조를 복사하여 번역
3. `templates/index.html`의 드롭다운에 언어 코드 추가

## ⚙️ 설정

설정은 `.settings.json`에 저장되며 Web UI에서 수정할 수 있습니다:

| 설정 항목             | 설명                            | 기본값                           |
| --------------------- | ------------------------------- | -------------------------------- |
| 다운로드 디렉토리     | 영상 저장 위치                  | `./downloads`                  |
| FFmpeg 바이너리 경로  | FFmpeg 사용자 지정 경로         | 시스템 PATH                      |
| 최대 동시 다운로드 수 | 병렬 다운로드 스레드 수         | `1`                            |
| 순차 모드             | 한 번에 하나씩 다운로드         | `true`                         |
| 다운로드 간 지연      | 다음 다운로드까지 대기 시간(초) | `3`                            |
| 기본 화질             | 최대 다운로드 해상도            | `best`                         |
| 미러 도메인           | 대체용 MissAV 도메인            | `missav.ai`, `missav.net` 등 |

### 고급 설정

`.settings.json`을 직접 편집할 수도 있습니다:

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

## 🚀 사용 예시

### 단일 다운로드

1. MissAV URL 또는 JAV 코드 입력 (예: `ABP-123`)
2. "Get Info" 클릭하여 영상 정보 가져오기
3. 화질 선택
4. "Download Now" 또는 "Add to Queue" 클릭

### 일괄 다운로드

1. "Batch Add" 클릭
2. 여러 URL 또는 JAV 코드 입력 (한 줄에 하나씩)
3. "Add All to Queue" 클릭

### 다운로드 관리

- 큐에서 실시간 진행률 확인
- ✕ 버튼으로 개별 다운로드 취소
- 완료된 작업 정리 또는 대기 큐 초기화
- Downloads 섹션에서 파일 탐색 및 관리

### 사용자 정의 URL 크롤러

1. MissAV 시리즈, 메이커 또는 검색 URL을 입력합니다
2. "Custom" 버튼을 클릭합니다
3. 목록에서 필터를 선택합니다 (또는 "All" 사용)
4. 스크랩할 페이지 수를 선택합니다
5. 결과 목록에서 비디오를 선택합니다
6. "Download Selected"를 클릭하여 큐에 추가합니다

## 🔧 문제 해결

| 문제                | 해결 방법                                                             |
| ------------------- | --------------------------------------------------------------------- |
| Web UI 접속 불가    | Gluetun 컨테이너에서 포트가 올바르게 노출되었는지 확인                |
| 다운로드 멈춤       | VPN 연결 및 네트워크 모드 설정 확인                                   |
| 파일 이름 오류      | 도구가 자동으로 이름을 줄입니다 — 다운로드 경로가 쓰기 가능한지 확인 |
| 설정 저장 안 됨     | 루트 디렉토리의 `.settings.json` 쓰기 권한 확인                     |
| 언어 변경 안 됨     | 브라우저 캐시 삭제 또는 `locales/` 마운트 확인                      |
| JAV 코드 작동 안 함 | 형식 확인 (예:`ABP-123`, `SSIS-456`)                              |

## 🐳 Docker 빌드

로컬에서 Docker 이미지를 빌드하려면:

```bash
docker build -t missav-dlp-web .
docker run -p 5000:5000 -v $(pwd)/downloads:/downloads missav-dlp-web
```

## 📦 요구 사항

- Docker & Docker Compose (컨테이너 배포용)
- Python 3.8+ (로컬 소스 실행용)
- **PyInstaller** (자체 .exe / 바이너리 빌드용)
- FFmpeg (영상 병합용)
- (선택 사항) Gluetun 또는 모든 OpenVPN/WireGuard 컨테이너

### 🛠️ 개발 및 빌드 (Development & Building)

소스 코드를 실행하거나 직접 실행 파일을 빌드하려는 경우:

#### 1. 환경 설정
```bash
# 가상 환경 생성
python -m venv venv

# 활성화
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
pip install pyinstaller
```

#### 2. 소스 코드 실행
```bash
python main.py
```

#### 3. 실행 파일 빌드
모든 플랫폼을 위한 자동화 스크립트를 제공합니다:
- **Windows**: `build.bat` 실행
- **Linux/macOS**: `bash build.sh` 실행

**수동 빌드:**
```bash
pyinstaller --clean MissAV_Downloader_onefile.spec
```

---

## 🔄 API 엔드포인트

애플리케이션은 REST API를 제공합니다:

| 엔드포인트                   | 메서드   | 설명                                       |
| ---------------------------- | -------- | ------------------------------------------ |
| `/api/info`                | POST     | 영상 정보 가져오기                         |
| `/api/download`            | POST     | 단일 다운로드 추가                         |
| `/api/batch`               | POST     | 여러 다운로드 추가                         |
| `/api/tasks`               | GET      | 모든 작업 목록 조회                        |
| `/api/tasks/<id>`          | DELETE   | 작업 취소                                  |
| `/api/queue/stats`         | GET      | 큐 통계 정보                               |
| `/api/settings`            | GET/PUT  | 설정 조회 / 수정                           |
| `/api/files`               | GET      | 다운로드 파일 목록 조회                    |
| `/api/language`            | GET/POST | 언어 조회 / 설정                           |
| `/api/docs/<type>`         | GET      | 로컬 문서 조회 (readme, security, license) |
| `/api/files/clean_history` | POST     | 모든 다운로드 파일 삭제                    |
| `/api/crawl`               | POST     | 필터/페이지네이션으로 URL에서 비디오 스크랩 |
| `/api/crawl/filters`       | POST     | URL에 사용 가능한 필터 가져오기 |

## ⚠️ 면책 조항

이 도구는 **개인 용도**로만 사용됩니다.
다운로드된 콘텐츠와 관련된 저작권 준수 및 결과에 대한 책임은 전적으로 사용자에게 있습니다。

## 📄 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일을 참고하세요。

## 🙏 감사의 말

이 프로젝트는 **[nerdnam](https://github.com/nerdnam)** 의 훌륭한 작업과 원본 저장소 **[missav-dlp-web](https://github.com/nerdnam/missav-dlp-web)** 를 기반으로 합니다。

### 원본 저장소

* **작성자:** nerdnam
* **저장소:** [https://github.com/nerdnam/missav-dlp-web](https://github.com/nerdnam/missav-dlp-web)
* **라이선스:** 원본 저장소에서 확인

### 사용 / 적용된 주요 기능

* Cloudflare 우회를 위한 `curl_cffi` + `yt-dlp` 통합
* 미러 도메인 순환 로직
* VPN 호환 (Gluetun)
* 실시간 진행률 표시가 있는 웹 기반 다운로드 UI

### 추가 개선 사항

* 다국어 지원 (4개 언어)
* 설정 관리 UI
* JAV 코드 변환
* 일괄 다운로드 기능
* 검색 및 미리보기가 가능한 파일 관리자
* 작업별 로그 시스템
* 순차 / 병렬 다운로드 모드

### Thanks To

* 원본 프로젝트의 모든 기여자
* `yt-dlp` 및 `curl_cffi` 오픈소스 커뮤니티
* 로컬라이제이션에 기여한 번역자들

---

## 📝 변경 기록

### Version 4.0 (Industrial Grade)

- **제로 설정**: Linux 및 macOS에서 SpoofDPI **자동 설치** 지원, Windows에서 바이너리 자동 감지.
- **원자적 지속성**: 메모리 저장 방식을 **SQLite**로 교체하여 영구적인 기록 보관 가능.
- **반응형 UI**: **SSE (Server-Sent Events)**를 도입하여 실시간, 저부하 업데이트 구현.
- **메타데이터 프로**: **딥 스크래핑 + Mutagen** 통합으로 자동 MP4 태깅 및 커버 아트 지원.
- **비주얼 큐**: 작업 목록에 **120px 썸네일** 추가.
- **안전 장치**: Docker 마운트 지점 감지가 포함된 **디스크 공간 보호** 기능 추가.
- **지능형 기능**: 누락된 태그를 보완하는 **멀티 사이트 폴백** (BestJavPorn/JavGuru) 추가.
- **안정성**: SpoofDPI 인스턴스 정리를 위한 프로세스 생명주기 개선.

### Version 3.1

* 스마트 해상도 fallback 로직 추가 (정확 → 더 높음 → 더 낮음 → 기본값)
* 동적 병렬 다운로드 조정 및 안전한 스레드 종료 기능 추가
* 다운로드 메타데이터 표시 (해상도, 파일 크기, 소요 시간)
* FFmpeg 경로 설정 및 백엔드 검증 추가
* 전체 다운로드 파일 삭제 기능 (“Clean History”) 추가
* 로컬 문서 뷰어 추가 (README, SECURITY, LICENSE)
* yt-dlp 추출기 충돌로 인한 "Get Info" 크래시 수정
* 병합 후 파일명/크기 표시 오류 수정
* 저해상도 화면에서 설정 창 overflow 문제 수정

### Version 3.0

* 다국어 지원 (EN, KO, JA, ZH) 추가
* 설정 관리 UI 추가
* JAV 코드 변환 추가
* 일괄 다운로드 기능 추가
* 검색 기능 포함 파일 관리자 추가
* 작업별 로그 추가
* 코드 구조를 `app_files/` 모듈로 재구성
* 폴더 구조 수정 (downloads/logs를 루트로 이동)

### Version 2.0

* nerdnam 프로젝트 기반 초기 릴리스
* 기본 다운로드 기능
* 실시간 진행률 표시
* curl_cffi를 통한 Cloudflare 우회
