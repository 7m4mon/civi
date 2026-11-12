# CIVI

[English](README.md) | **日本語** · 作者: **7M4MON**

**Icom IC-7300をLAN経由でSCPI/VISAから制御するゲートウェイ**です。WindowsまたはRaspberry Pi 4へUSB接続し、英語Web画面、型付きPythonドライバー、LabVIEWから操作できます。TCPとHTTPSは単一のCI-V制御キューを共有します。

## 機能

| インターフェース | 内容 |
|---|---|
| SCPI / VISA | TCP5025、LF終端、短縮形、単位、連続命令、エラー、完了確認、受信プロファイルreset |
| 無線機 | VFO・周波数・モード、ゲイン、フィルター、メーター、メモリー、バンドスタック、キーヤー保存、スキャン、475点スコープ、メニュー |
| Python | **CIVIの拡張339定義すべてに専用の型付きAPI**。基本命令も対応。公開・返却43型、索引352項目 |
| Web | HTTPS、コマンドexplorer、スコープ、接続復旧、認証情報の保存 |
| Pi | DHCP/AutoIP/固定IPv4、ホスト名/DNS、確定・復元、発見、LAN RESET、POWER ON/LAN状態・Identify |
| LabVIEW | VISAセッション、取得・設定例、CSV保存付き周波数スイープ |

## 検証結果

MAIN1.41/1.42で受信設定、全216メニュー読取、VFO、メモリー書込・読戻し・復元、バンドスタック、キーヤー、スコープ、スキャンを確認しました。PiではLAN設定・発見・再起動時の保存・復旧・本体表示を確認しています。

- [要求事項・実装・試験方法・最終結果](docs/IMPLEMENTATION_AND_TEST_RESULTS.md)
- [検証完了計画と登録手続き](docs/IVI_6_1_COMPLETION_2026-11-12.md)

記録したWindows自動試験は619成功、Linux専用1スキップです。実機の条件と版は各試験結果に記載しています。

![Pi本体のIdentify表示とIC-7300](civi-identify.jpg)

## Windowsで起動

Python3.11以上を用意し、PowerShellで実行します。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[test]'
Copy-Item config.example.toml config.toml
.\.venv\Scripts\python.exe -m civi --make-cert certs --host 192.168.1.20
.\start.cmd
```

`192.168.1.20`は接続に使うIP/名前へ置き換えます。`localhost`は自動で含まれます。生成した証明書をクライアントで信頼するか、CA発行の証明書を設定してください。

- Web: `https://localhost:8443`、SCPI: `localhost:5025`
- Webユーザー名は`admin`。初回にパスワードを入力し、以降は保存値を使用します。[変更・忘れた場合](docs/WEB_PASSWORD.md)。
- `config.toml`で`backend="civ"`、ポート（例`COM25`）、アドレス`0x94`、115200bpsを指定します。無線機のUSB CI-VはREMOTEとUnlink、ボーレートはAutoまたは一致する値にします。

無線機の電源がOFFでもWebは起動します。接続状態と復旧操作は **CI-V connection settings** に表示します。CI-V送受信は端末と認証済みWebログに出力します。送信開始は既定で禁止し、許可設定・最大時間に従って制御します。

## Raspberry Pi

[導入手順](docs/PORTING.md)と[HTTPS443設定](docs/RPI_HTTPS.md)の後、次を実行します。

```bash
bash desktop.sh --install
```

デスクトップの **CIVI** アイコンからgateway・helper・panelを手動起動します。端末を開いたまま、本体パネルを表示して使います。sudoパスワードはhelper端末へ入力します。USBは`/dev/serial/by-id/`のパスを使います。自動起動は設定しません。

## ドライバー・文書

- [Python導入・使用例](drivers/civi-ic7300/README.md) / [公開API](drivers/civi-ic7300/src/civi_ic7300/REFERENCE.md)
- [LabVIEWプロジェクト・使用例](labview/CIVI/README.md)
- [SCPI・VISA例](docs/SCPI.md) / [全コマンド](docs/COMMANDS.md)
- [LAN設定](docs/RPI_LAN_SETTINGS.md) / [Webパスワード](docs/WEB_PASSWORD.md)
- [構成](docs/ARCHITECTURE.md) / [LXI装置構成](docs/LXI_DEVICE_CONFIGURATION.md) / [条項対応表](docs/LXI_REQUIREMENTS_2026-11-10.md)
- [文書案内](docs/INDEX.md)

自動試験は`.\.venv\Scripts\python.exe -m pytest -q`で実行します。模擬無線機・偽シリアルを使います。

無線機の実装資料は[公式CI-V補足資料](https://www.icom.co.jp/support/manual/2557/)です。PDF本体は再配布しません。
