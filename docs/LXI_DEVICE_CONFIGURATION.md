# CIVI Piの装置構成

| 項目 | 構成 |
|---|---|
| 本体 | Raspberry Pi4 Model B Rev1.4、標準bcmgenet/BCM54213PE Ethernet |
| LXI対象NIC | eth0。WLANは管理用 |
| 本体操作 | 付属画面・ローカルキーボード/マウス等の入力。LANなしでLAN RESETへ到達可能 |
| 起動 | CIVI/helper/panelをデスクトップから手動起動。画面を表示したまま使用 |
| 表示 | POWER ON、LAN NORMAL/FAULT、Identify。RJ45のlink/activity LEDは物理リンク表示 |
| 無線機 | 安定したUSBシリアルパスのIC-7300。送信開始は既定で禁止 |
| 確認環境 | Debian13.7/aarch64、kernel6.18.50+rpt-rpi-v8、NetworkManager1.52.1、Python3.13.5 |

## ネットワーク

NetworkManagerがDHCP/AutoIP/固定IPv4とリースを管理します。helperは使用中IPの重複監視、AutoIP返信経路、設定の一時適用・確定・復元を担当します。CIVIのmDNSスイッチはAvahiの名前応答とサービス広告を制御します。RFC2136 DDNS更新はCIVIの提供範囲に含めません。

装置はDevice規則から参照される識別GETを提供します。独立したLXI Extended Functionは宣言しません。

## HTTP応答

gateway自体の識別情報は無線機の接続状態に関係なく200を返します。既知の利用不能な子機器は503、不明な子機器は404、gateway停止時は503です。同期GETであり202を使いません。無線機の状態は別項目に表示します。

## Auto-MDIX applicability decision

標準Pi4のBCM54213PEは[メーカー製品情報](https://www.mouser.com/pdfDocs/BroadcomBCM54213PERGMIIGigabitEthernetTransceiver.pdf)のMDIクロス配線補正機能を根拠にAuto-MDIX対応とします。Device7.5の非対応機向け物理ラベルはこの構成には適用しません。別NIC/改造基板では判定を見直します。

実際の100/1000Mbpsリンク、表示、復旧の結果は[試験結果](IMPLEMENTATION_AND_TEST_RESULTS.md)にまとめています。
