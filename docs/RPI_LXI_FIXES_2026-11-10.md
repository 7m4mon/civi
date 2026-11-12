# LXI監査4件のPi反映・実機確認 — 2026-11-10

**4件の修正をPiへ反映し、以下の範囲で実機確認した。LXI全体の適合・認証ではない。**

## 構成と反映

Pi 4、Linux 6.18.50+rpt-rpi-v8 aarch64、Python 3.13.5。
配置先は `/home/nom/civi-rpi-lxi`、有線 `192.168.73.2`、WLAN管理経路
`192.168.4.54`。Windowsコントローラーは有線 `192.168.73.1`、WLAN `192.168.4.93`。
ゲートウェイ0.1.0、Windowsにクリーン導入した独立クライアント0.13.1を使用した。
NI-VISA/PyVISA経由ではなく、Pythonドライバーのraw TCP通信である。

提供済みSSHホスト鍵を照合して接続。停止していた3プロセスの状態を確認後、変更121ファイルを
SFTPで反映した。各既存ファイルを事前バックアップし、転送ハッシュを検証して原子的に置換。
CRLFをLFへ正規化した。実設定・証明書・認証ファイルは転送対象外。

Pi上のバックアップ/マニフェスト:
`tmp/deploy-lxi-fixes-20261110-083023/manifest.json`。
利用者がデスクトップCIVIを開き、helper/CIVI/panelの3つを手動起動した。
自動起動、sudoポリシー、systemd登録は追加していない。

## 確認結果

| 対象 | 実機・実OSで確認したこと | 範囲の限界 |
|---|---|---|
| G01: VISA位置指定 | 導入済みWindowsクライアント0.13.1からboard番号付きINSTR、省略形、HiSLIP機器名/port付き位置指定で実Piへ接続。774000 Hz、AM、PTT OFF、エラーなしを読取 | 使用通信はraw TCP 5025。HiSLIPそのものの実装/試験ではない。無線機の設定変更なし |
| G02: 名前切り詰め | 利用者が本番Webで64文字ASCII名を保存。保存ファイルは先頭63byte（末尾A）、4サービスも同じ取得名へ再広告。元のDescriptionへ復元 | 日本語/絵文字の境界はPi上の模擬Web保存/再読込試験で確認。本番Webの非ASCII名まで実機確認済みとはしない |
| G03: 対象NIC | 本番HTTPS識別XMLのLXI Interfaceはeth0だけ。PCの有線インターフェースから4サービスを新規問い合わせして取得。WLAN側の新規問い合わせでは同サービスを取得しなかった。WLANのIP HTTPS管理は維持 | WLANの否定結果は今回のネットワーク/問い合わせ時間内の観察。全RFC/ネットワーク条件の適合証明ではない |
| G05: Fault優先 | 利用者が本番WebからIdentify開始。本体点滅と状態ACKを確認し、有線を抜いた。WLAN経由で3回、Fault/link=false/identify=false/本体ACKを取得。本体のLAN FAULT表示も利用者確認 | DHCPリース失効や重複IPによるFaultとの結合試験は今回行っていない |
| 復旧 | 有線を挿し直すだけで固定IP/Normalへ復帰。IdentifyはOFFのまま。利用者が再度Start→点滅→Stopを確認。最後も状態OFF/ACKを取得 | 全再起動・全リンク速度条件の試験ではない |

再接続・名前復元後、元の4サービスを新規に取得し、443/443/5025/443のポートと
`civi.local.` のSRV接続先を確認。LXI識別TXTはCIVI/IC-7300、ゲートウェイ0.1.0で一致した。
MACを含む生データはローカルの試験記録に留め、この公開記録には掲載しない。

## HTTPS証明書の検証範囲

保存済み公開証明書を鍵確認済みSSH経由で取得し、一時的な検証用信頼設定として使用した。
証明書とDNS名 `civi.local` の一致を検証し、実TCP接続先は有線/WLANのIPを指定した。
TLS検証を無効にはしていない。今回の証明書はDNS名civi.local/civi/localhostと
127.0.0.1に対応し、有線固定IP自体は含まない。そのため数値IP名での検証成功は主張しない。
証明書/秘密鍵は更新せず、OSやブラウザーの信頼ストアも変更していない。

## Pi上の模擬試験

Piの稼働用仮想環境にはpytestがなかったため、`tmp/lxi-test-libs`だけへ試験ライブラリを導入。
稼働用venvのパッケージを更新せず、試験プロセスだけPYTHONPATHで参照した。

```bash
PYTHONPATH=tmp/lxi-test-libs .venv/bin/python -m pytest \
  tests/test_lxi_fixes.py tests/test_lxi.py tests/test_lxi_defaults.py \
  tests/test_discovery_names.py tests/test_indicator.py tests/test_python_driver.py -q
```

**72成功、1スキップ（2.65秒）**。スキップはNode未導入によるWeb JavaScript実行試験で、
Windowsでは成功済み。WindowsでスキップしていたLinux Unix-socket試験はPiで成功した。
pytest-asyncioの将来のfixture loop scopeに関する警告は出たが、試験失敗ではない。
Piの全クライアント試験/全522ケースを実行したという記録ではない。

## 復元と最終状態

- Description: `CIVI CIVI-0001`、発見有効。
- 有線 `192.168.73.2`、LAN Normal、本体パネル接続/ACK、Identify OFF。
- IC-7300: 774000 Hz、AM、PTT OFF、`0,"No error"`。
- `config.toml`、保存Web認証、`.civi-network.json`のSHA-256が試験前と一致。
- helper/CIVI/panelは稼働したまま。無線機の周波数/モード/メモリー/送信設定は変更していない。

ローカル未追跡記録は `tmp/pi-lxi-*-20261110.json`。転送前後のハッシュ、実機読取、
サービス問い合わせ、Identify開始/切断/復旧/最終状態を保持する。公開リポジトリに秘密鍵、
パスワード、実MACの生記録は加えない。

残る全体要件は[残件表](LXI_REMAINING_2026-11-10.md)。今回の成功を、
DHCP期限切れ/競合/名前衝突/再起動の未試験条件やIVI登録の完了へ広げない。
