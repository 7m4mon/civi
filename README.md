# CIVI

Author: 7M4MON

Python製のSCPI → Icom CI-Vネットワークゲートウェイ。初期対象はIC-7300、開発環境はWindows、運用先はRaspberry Pi OS 64bitです。WebとSCPIは1つの制御サービスを共有します。現在の版は0.1.0、LXI未認証です。

## Windowsで起動

Python 3.11以上を用意し、PowerShellでこのフォルダーから実行します。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[test]'
Copy-Item config.example.toml config.toml
$env:CIVI_PASSWORD = 'replace-with-your-own-long-password'
.\.venv\Scripts\python.exe -m civi --make-cert certs --host 192.168.1.20
.\.venv\Scripts\python.exe -m civi --config config.toml
```

`--host`には実際のLAN IPやDNS名を指定できます。localhostは自動で含まれます。自己署名証明書を生成します。利用する端末で証明書を確認して信頼するか、信頼されたCAの証明書と鍵をconfig.tomlに指定してください。秘密鍵は共有しないでください。既存証明書は上書きしません。

Webは `https://localhost:8443`、SCPIは `localhost:5025`。初期設定は模擬無線機なので実機がなくても操作できます。Webログインユーザーは `admin`、パスワードは環境変数。12文字以上が必要です。パスワードをソースや設定ファイルには保存しません。

`*IDN?`は`CIVI Project,CIVI/IC-7300,CIVI-0001,0.1.0`のようにCIVIと識別済みの接続機種を返します。未接続・未知の機種IDでは機種部分が`Unknown`になります。末尾はCIVIのソフトウェア版です。無線機のファームウェア版はWebの`Radio firmware`と`RAD:FIRM?`に分けて表示します。自動取得は行わず、未設定では`Unknown`、config.tomlトップレベルの`radio_firmware`に手動登録できます。

Web画面は英語です。無線機が未接続でもCIVIのWebサーバーを起動でき、ログイン前から`Waiting for radio`を表示します。COMポートが不在の場合は約2秒ごとに再試行します。ポートが開いても無線機が無応答の場合は、遅延応答の誤認を防ぐため`Radio not ready — recovery required`を表示します。電源・USB・CI-V設定を確認し、無線機とUSBリンクをリセットしてから、ログイン後の`CI-V connection settings` → 確認チェック → `Recover connection`で復旧してください。無線機未準備でも設定画面とSCPIコンソールは利用できます。

`ERR_CONNECTION_REFUSED`はWebサーバーに接続できていない状態です。CIVI自体が終了していると待機画面も配信できません。起動したPowerShellを開いたままにし、`Web is ready`の表示と起動エラーの有無を確認してください。更新したコードの反映にはCIVIの再起動とブラウザの再読み込みが必要です。

`bind = "0.0.0.0"`でlocalhostとLANから利用可能です。Windowsファイアウォールで必要な端末からのTCP 5025/8443と、発見に必要なUDP 5353を許可してください。localhost限定の場合は`127.0.0.1`に変更します。SCPIは仕様どおり平文・認証なしのTCPです。Webの認証はSCPIポートを保護しないため、SCPIはアクセスを制限したLANで使用します。

## IC-7300接続

1. アイコムのUSBドライバーをインストールし、デバイスマネージャーでCOMポートを確認します。
2. 無線機をVFOモードにし、CI-Vアドレス、USB側ボーレートをconfig.tomlと合わせます。例は`94h`（十進148）、19200bpsです。他のCATソフトは終了してください。
3. USB SEND、USBキーイングの設定を確認し、USB SENDをOFFにしてください。CIVIはDTR/RTSをOFFにしてポートを開きますが、ドライバーの切替時の信号変化を実機で検証していません。
4. `backend = "civ"`、`[serial] port = "COM3"`など実際の値に変更して起動します。ポーリングで状態が表示されます。
5. 最初は周波数・モード取得、Sメーター、周波数設定を確認します。送信制御は既定で無効です。

直接CI-Vを採用し、Hamlibは使用していません。プロファイルでコマンド、モード、周波数範囲、機能を定義します。IC-7300の受信範囲は保守的に30kHz–60MHzを採用し、地域別70MHz拡張は対象外です。03/05は表示中の周波数を扱います。拡張コマンドではVFO選択、DATA/フィルター、各種ゲイン・メーター、RIT/XIT、メモリー、CW/音声メモリー再生、電源、メニュー、スコープを扱います。USB音声そのもののネットワーク伝送は別機能で、実装していません。

## 拡張コマンド

既存の基本コマンドに加え、339個の拡張コマンド定義（うちメニュー216項目）を追加しています。Webの`Radio command explorer`から全定義の例を確認し、共通キューを通して操作できます。詳細とCI-V番号の対応は[全コマンド対応表](docs/COMMANDS.md)を参照してください。新しい項目は模擬・偽シリアルで検証したソフトウェア実装で、実機動作は未確認です。

```text
RAD:AFGAIN 128;AFGAIN?
READ:SWR?
RAD:VFO:FREQ OTHER,14.074MHz;FREQ? OTHER
RAD:RIT:FREQ -1200;FREQ?
RAD:MENU:0094?
```

メニュー保存・メモリー書き込み/消去・電源・通信設定・校正の各操作は`config.toml`の`[permissions]`で対応する権限を有効にするまで拒否します。既存設定には自動で有効化しません。読み取りは可能です。送信につながるCW送出・ボイスメモリー・VOX・BK-IN・チューナー操作は既存の送信許可、所有クライアント、最大時間で制限します。

スコープ波形にはIC-7300のUSB CI-Vを115200bpsかつREMOTEから切り離した設定にする必要があります。`RAD:SCOPE:STREAM 0,ON`で開始し、`RAD:SCOPE:WAVE?`または認証済みWebで波形を取得します。Webにはスペクトラムとウォーターフォール履歴を表示します。周波数等の通常応答と分離して受信し、不完全な掃引と5秒以上古い波形は現在値として返しません。

公式資料: [IC-7300 CI-V補足説明書](https://www.icom.co.jp/support/manual/2557/)、[Icom AmericaのUSB SEND注意点](https://icomamericasupport.zendesk.com/hc/en-us/articles/35050809291668-IC7300-Instruction-Manuals-and-FAQs)。コマンド照合は前者の202312版、印刷ページ2–4、8–9を基準にしています。資料自体は配布物に含めません。

## 検証と文書

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

テストは模擬無線機・偽シリアルのみを使用し、実機へ送信しません。

- [SCPI仕様とVISA例](docs/SCPI.md)
- [全コマンド対応表・引数例](docs/COMMANDS.md)
- [構成・通信障害・送信制御](docs/ARCHITECTURE.md)
- [LXI対応表](docs/LXI.md)
- [検証結果・実機確認手順](docs/VALIDATION.md)
- [Raspberry Pi移植計画](docs/PORTING.md)

Raspberry Piへの導入手順とsystemd設定は、指定された移植段階の納品物として延期しています。Windows起動と模擬バックエンドによる確認に加え、2026-10-17にCOM25で実機の周波数・モード・Sメーター・送受信状態の読み取りを確認しました。実機設定変更、実機でのSCPI/Web通し操作、Linux運用、LXI認証は未確認です。詳細は検証記録を参照してください。
