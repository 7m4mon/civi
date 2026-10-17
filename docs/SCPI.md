# CIVI SCPI 0.1

TCP 5025、ASCII、LF終端。CRLFも受理します。最大1行4096バイト、入力待ち32行、共通キュー128件です。設定命令に通常応答はありません。問い合わせを含む1行に対してLF終端の1行を返し、複数の問い合わせ応答を`;`で連結します。

大文字小文字を区別せず、下表の大文字部分の短縮形または全形を各階層で独立に受理します。省略可能部分の途中までの形は受理しません。`;`後の1階層ヘッダーは直前の親を継承し、先頭`:`でルートに戻ります。複数階層を明記したヘッダーもルートとして受理します。共通コマンドは親を変えません。例: `SENS:FREQ 7.1MHz;FREQ?;:RAD:MODE USB;MODE?;*OPC?`。

| コマンド | 値 / 応答 | 備考 |
|---|---|---|
| `*IDN?` | `CIVI Project,CIVI/IC-7300,CIVI-0001,0.1.0` | CIVIの識別＋CI-V機種IDで確認した接続機種。末尾はCIVI版 |
| `*CLS` | 応答なし | このクライアントのエラーをクリア。機器接続の隔離は解除しない |
| `*OPC?` | `1` | キューに先行投入された通常操作が完了してから返す。設定はACKまで待つ |
| `SYSTem:ERRor?` | `0,"No error"`等 | クライアントごとのFIFO、32件。1件取得して除去 |
| `SENSe:FREQuency <値>` / `?` | 整数Hz / 整数Hz | Hz省略可、kHz、MHz、小数・指数記法可。換算後1Hz単位 |
| `RADio:MODE <値>` / `?` | LSB、USB、AM、CW、RTTY、FM、CW-R、RTTY-R | CIVI独自。06で既定フィルターを選択。DATA状態は表現しない |
| `READ:SMETer?` | 0–255の整数 | CIVI独自、単位raw、未校正。dBm変換なし |
| `RADio:PTT <ON\|OFF>` / `?` | ON / OFF | CIVI独自。ONは設定で明示的に許可する必要あり |
| `RADio:FIRMware?` | `Unknown`または手動登録値 | CIVI独自、問い合わせのみ。無線機のファームウェア版。CI-V自動取得ではない |

`*IDN?`は初回または識別キャッシュ無効化後、共有キュー内でCI-Vの`19 00`を問い合わせ、返った機種IDをプロファイルの`model_id`と照合します。IC-7300プロファイルでは94hをIC-7300に対応づけます。設定可能なCI-Vアドレスと機種IDは別の値として扱います。模擬バックエンドでは機種IDも模擬します。

未接続、タイムアウト、未知の機種IDでは、例えば`CIVI Project,CIVI/Unknown,CIVI-0001,0.1.0`を返します。通信エラーはエラーキューにも記録し、CIVI自身の識別応答は維持します。接続障害・接続設定変更・明示的復旧で識別キャッシュを無効にします。Webでは実際に識別したRadioと選択済みRadio profileを区別して表示します。

無線機のファームウェア版は自動取得しません。必要ならconfig.tomlのトップレベル（`[serial]`より前）に`radio_firmware = "1.42"`のように無線機で確認した値を登録して再起動します。空文字または未設定では`Unknown`です。Webでは手動登録値に`manually configured`を添えます。`*IDN?`の4番目のフィールドは常にCIVIの版で、無線機の版へ置き換えません。

`*RST`、`*OPC`（非問い合わせ）、状態レジスター・SRQ、バイナリブロックは提供しません。`*CLS`は未実装のレジスターを操作しません。

失敗した問い合わせはCIVI独自の`ERROR`を返し、詳細をエラーキューへ登録します。設定失敗は通常応答を返さず、`SYST:ERR?`で確認します。`*OPC? = 1`は処理が完了したことを表し、先行設定の成功を意味しません。設定後はエラーも確認してください。切断されたクライアントの未実行操作は破棄します。

| コード | 意味 |
|---|---|
| -102 / -104 | 構文 / データ形式エラー |
| -108 / -109 | 不要 / 不足パラメーター |
| -113 | 未知ヘッダー、非対応`*RST`など |
| -200 | NAK、PTT所有競合などの実行エラー |
| -203 | 送信開始禁止 |
| -222 / -224 | 範囲外 / 不正な選択値 |
| -241 | プロファイルで未対応の機能 |
| -310 | 不正なCI-V応答、内部エラー |
| -350 | キュー上限 |
| -365 | CI-Vタイムアウト、USB障害、隔離状態 |

USB障害は全クライアントから接続状態で確認でき、操作の失敗詳細は操作したクライアントのキューとWebログに残ります。アイドル時のポーリング失敗はWebログと接続状態に記録します。

## VISA接続例

PyVISAとpyvisa-pyを別途インストールし、RAW SOCKETリソースを使用します。VXI-11/HiSLIPの`INSTR`接続は提供しません。

```python
import pyvisa

rm = pyvisa.ResourceManager('@py')
with rm.open_resource('TCPIP0::127.0.0.1::5025::SOCKET') as radio:
    radio.read_termination = '\n'
    radio.write_termination = '\n'
    radio.timeout = 10000
    print(radio.query('*IDN?'))
    radio.write('SENS:FREQ 7.1 MHz')
    print(radio.query('*OPC?'))
    print(radio.query('SYST:ERR?'))
    print(radio.query('SENS:FREQ?'))
    print(radio.query('RAD:MODE?'))
    print(radio.query('READ:SMET?'))
```

LANでは127.0.0.1をCIVI PCのIPへ変更してください。設定命令に`query()`を使うと通常応答がないためタイムアウトします。
