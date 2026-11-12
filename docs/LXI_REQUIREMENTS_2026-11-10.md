# LXI 1.6.2 条項対応表

対象：Pi4/eth0、付属画面とローカル入力、手動起動のCIVI/helper/panel。
gateway0.1.0、Python driver0.13.1。WLANは管理用。

Deviceの現行RULE101件を含む175行を照合。親子条項があるため達成率には換算しません。

[実装・試験結果](IMPLEMENTATION_AND_TEST_RESULTS.md) · [検証・手続きの完了条件](IVI_6_1_COMPLETION_2026-11-12.md)

実装確認は記載された範囲の証拠、適用外は宣言構成による判定です。
最終照合・手続きが必要な行の説明は完了計画へ集約しています。

## 規格の出典

- [Device](https://public.lxistandard.org/specifications/LXI_1.6_Specifications/LXI_Device_Specification_1.6.2_2026-04-02.pdf) — SHA-256 `97e65b8baf38a8aa9f57eec1c8cf7b0b35b74d33ee63dd046d01e1253775474b`
- [API](https://public.lxistandard.org/specifications/LXI_1.6_Specifications/LXI_API_Extended_Function_1.1_2025-03-10.pdf) — SHA-256 `7e9ca8fb33e9af13827ebe25986b79d1e1ea11185da2e4b4054e296c8cd2d8d0`
- [Interpretations](https://public.lxistandard.org/specifications/LXI_1.6_Specifications/LXI_Interpretations_and_Clarifications_for_LXI_Standard_1.6.1_2025-02-16.pdf) — SHA-256 `ee68abe3a10500e5ec576603459824259b7c76fa60278ee21d5f5b0c93f3ce19`

`python tools/lxi_audit_check.py --check` で条項の在庫・参照先・入力hashを確認できます。

## Device

| 条項 / PDF頁 | 適用条件 | 判定・結果 | 根拠 |
|---|---|---|---|
| 1.4.1 / p.10 | 必須 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G12 | [LXI.md](../docs/LXI.md) |
| 1.4.4.2 / p.14 | 必須 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G12 | [LXI.md](../docs/LXI.md) |
| 1.4.4.2.1 / p.14 | 必須 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G10, G12 | [AUDIT.md](../drivers/civi-ic7300/src/civi_ic7300/AUDIT.md) |
| 1.4.5 / p.14 | 必須 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G11 | [identification.py](../civi/identification.py)<br>[LXI.md](../docs/LXI.md) |
| 1.4.6 / p.14 | 必須 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G11 | [identification.py](../civi/identification.py) |
| 1.4.7 / p.15 | 必須 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G11 | [identification.py](../civi/identification.py)<br>[LXI.md](../docs/LXI.md) |
| 2.4.5.1 / p.16 | 必須 | 実装確認：ローカルLAN RESETの機構と初期化・実機復旧を確認。条項が規定する機構は実装済み。 | [lci.py](../civi/pi/lci.py)<br>[RPI_LCI_BOOT_2026-11-08.md](../docs/RPI_LCI_BOOT_2026-11-08.md)<br>[IVI_6_1_COMPLETION_2026-11-12.md](../docs/IVI_6_1_COMPLETION_2026-11-12.md) |
| 2.4.5.2 / p.16 | 必須 | 実装確認：付属画面とローカル入力を恒久的な装置構成に固定。LAN非依存のLCI実機証拠あり。この構成以外へ適合判断を広げない。 | [RPI_LAN_RESET.md](../docs/RPI_LAN_RESET.md)<br>[RPI_DESKTOP.md](../docs/RPI_DESKTOP.md)<br>[IVI_6_1_COMPLETION_2026-11-12.md](../docs/IVI_6_1_COMPLETION_2026-11-12.md) |
| 2.4.5.3 / p.17 | 必須 | 実装確認：LAN RESET文字列による本体確認を要求する。 | [lci.py](../civi/pi/lci.py)<br>[RPI_LAN_RESET.md](../docs/RPI_LAN_RESET.md) |
| 2.4.9.1 / p.17 | 必須 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G09 | [RPI_ETHERNET_2026-11-08.md](../docs/RPI_ETHERNET_2026-11-08.md) |
| 2.5.1.1 / p.19 | 必須 | 実装確認：付属本体画面を装置前面表示として固定し、POWER ONを追加。2026-11-11にユーザーが緑色POWER ONとLAN状態の表示を目視受入。 | [panel.py](../civi/pi/panel.py)<br>[RPI_PANEL.md](../docs/RPI_PANEL.md)<br>[LXI_DEVICE_CONFIGURATION.md](../docs/LXI_DEVICE_CONFIGURATION.md)<br>[IVI_6_1_COMPLETION_2026-11-12.md](../docs/IVI_6_1_COMPLETION_2026-11-12.md) |
| 2.5.2.1 / p.20 | 必須 | 実装確認：本体パネルを必須構成に固定。Normal/Fault/Identifyを実機確認。RJ45のリンクLEDとは区別。 | [indicator.py](../civi/indicator.py)<br>[RPI_PANEL_2026-11-07.md](../docs/RPI_PANEL_2026-11-07.md)<br>[IVI_6_1_COMPLETION_2026-11-12.md](../docs/IVI_6_1_COMPLETION_2026-11-12.md) |
| 2.6.1.1 / p.22 | 必須 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G11 | [panel.py](../civi/pi/panel.py) |
| 3.5.1 / p.24 | イベント/同期機能を実装した場合 | 適用外：LXIイベントによる実行機構なし。通常のSCPI設定はLXI Eventではない。 | [LXI.md](../docs/LXI.md) |
| 3.5.1.3 / p.25 | イベント/同期機能を実装した場合 | 適用外：LXIイベントで起動する測定機能なし。イベント応答時間仕様は対象外。 | [LXI.md](../docs/LXI.md) |
| 3.5.2.1 / p.27 | イベント/同期機能を実装した場合 | 適用外：LXIイベント送出/トリガー出力を実装しない。 | [LXI.md](../docs/LXI.md) |
| 3.7 / p.27 | イベント/同期機能を実装した場合 | 適用外：LXIイベントの生成/処理なし。通常の通信ログとは区別。 | [LXI.md](../docs/LXI.md) |
| 6.1 / p.31 | 必須 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G01, G10 | [AUDIT.md](../drivers/civi-ic7300/src/civi_ic7300/AUDIT.md)<br>[COMPLIANCE.md](../drivers/civi-ic7300/src/civi_ic7300/COMPLIANCE.md)<br>[IVI_RECEIVE_ACCEPTANCE_2026-11-11.md](../docs/IVI_RECEIVE_ACCEPTANCE_2026-11-11.md)<br>[IVI_VERIFICATION_WORKLIST_2026-11-11.csv](../docs/IVI_VERIFICATION_WORKLIST_2026-11-11.csv)<br>[IVI_TX_INHIBIT_2026-11-11.md](../docs/IVI_TX_INHIBIT_2026-11-11.md)<br>[IVI_6_1_COMPLETION_2026-11-12.md](../docs/IVI_6_1_COMPLETION_2026-11-12.md)<br>[IVI_VERIFICATION_RECONCILED_2026-11-12.json](../docs/IVI_VERIFICATION_RECONCILED_2026-11-12.json)<br>[IVI_MENU_VERIFICATION_2026-11-12.csv](../docs/IVI_MENU_VERIFICATION_2026-11-12.csv) |
| 6.1.1 / p.31 | イベント/同期機能を実装した場合 | 適用外：IviLxiSyncを要する同期/イベント拡張なし。 | [LXI.md](../docs/LXI.md) |
| 6.2 / p.32 | 必須 | 実装確認：0.13.1で位置指定を修正。導入済みWindowsドライバーからINSTR/省略形/HiSLIP位置指定で実Pi・IC-7300を読取。通信はraw TCP。 | [driver.py](../drivers/civi-ic7300/src/civi_ic7300/driver.py)<br>[test_python_driver.py](../tests/test_python_driver.py)<br>[test_lxi_fixes.py](../tests/test_lxi_fixes.py)<br>[IMPLEMENTATION_AND_TEST_RESULTS.md](../docs/IMPLEMENTATION_AND_TEST_RESULTS.md)<br>[RPI_LXI_FIXES_2026-11-10.md](../docs/RPI_LXI_FIXES_2026-11-10.md) |
| 6.3 / p.34 | イベント/同期機能を実装した場合 | 適用外：LXIイベント/有線トリガー入力のSource APIなし。 | [LXI.md](../docs/LXI.md) |
| 6.4 / p.34 | イベント/同期機能を実装した場合 | 適用外：LXIイベント用Arm/Trigger機構なし。無線機のスキャンとは区別。 | [LXI.md](../docs/LXI.md) |
| 6.4.2 / p.34 | イベント/同期機能を実装した場合 | 適用外：LXIイベント/有線トリガーへのルーティングなし。 | [LXI.md](../docs/LXI.md) |
| 6.4.3 / p.34 | イベント/同期機能を実装した場合 | 適用外：LXIイベントパケットを送出しない。 | [LXI.md](../docs/LXI.md) |
| 6.4.4 / p.35 | イベント/同期機能を実装した場合 | 適用外：LXIイベント信号名を実装しない。 | [LXI.md](../docs/LXI.md) |
| 6.4.4.1 / p.38 | イベント/同期機能を実装した場合 | 適用外：Arm/Trigger信号を公開しない。 | [LXI.md](../docs/LXI.md) |
| 6.4.4.2 / p.38 | イベント/同期機能を実装した場合 | 適用外：対応イベント信号なしと本表に明記。 | [LXI.md](../docs/LXI.md) |
| 6.4.5 / p.38 | イベント/同期機能を実装した場合 | 適用外：LXI予約イベント名をベンダー信号に使用しない。 | [LXI.md](../docs/LXI.md) |
| 6.4.6 / p.38 | イベント/同期機能を実装した場合 | 適用外：LXIイベント宛先パスを使用しない。 | [LXI.md](../docs/LXI.md) |
| 6.5 / p.39 | イベント/同期機能を実装した場合 | 適用外：IEEE 1588時刻/タイムスタンプ/アラームをAPI公開しない。無線機の時計設定とは別。 | [LXI.md](../docs/LXI.md) |
| 6.5.1 / p.39 | Deprecated | 廃止：現行必須の不足には数えない。後継条項を本表で追跡。 | [LXI.md](../docs/LXI.md) |
| 6.5.2 / p.39 | Deprecated | 廃止：現行必須の不足には数えない。後継条項を本表で追跡。 | [LXI.md](../docs/LXI.md) |
| 6.6 / p.39 | イベント/同期機能を実装した場合 | 適用外：LXIイベントのドメイン機能なし。 | [LXI.md](../docs/LXI.md) |
| 7.1 / p.41 | 必須 | 実装確認：実Piで100/1000 Mb/s通信を確認。 | [RPI_ETHERNET_2026-11-08.md](../docs/RPI_ETHERNET_2026-11-08.md) |
| 7.1.2 / p.41 | 必須 | 実装確認：物理100Mbps Full/HalfでSCPI/証明書検証HTTPSを確認し、1000Mbps Full自動交渉へ復元。10Mbps全条件の実測は主張しない。 | [RPI_ETHERNET_2026-11-08.md](../docs/RPI_ETHERNET_2026-11-08.md)<br>[IVI_6_1_COMPLETION_2026-11-12.md](../docs/IVI_6_1_COMPLETION_2026-11-12.md) |
| 7.2 / p.41 | 必須 | 実装確認：対象有線MACを本体/Webに表示。公開写真のマスクは実機表示と別。 | [identification.py](../civi/identification.py)<br>[RPI_PANEL_2026-11-07.md](../docs/RPI_PANEL_2026-11-07.md) |
| 7.3 / p.42 | 必須 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G05 | [indicator.py](../civi/indicator.py)<br>[RPI_UNPLUGGED_BOOT_2026-11-08.md](../docs/RPI_UNPLUGGED_BOOT_2026-11-08.md) |
| 7.5 / p.42 | Auto-MDIX非対応の場合 | 適用外：標準Pi 4/BCM54213PEの製品情報にあるMDIクロス配線の検出・補正をAuto-MDIX対応の根拠とする。非対応機向けの物理ラベルは当該構成では不要。新たなケーブル実測を主張せず、別NIC採用時は再評価。 | [RPI_ETHERNET_2026-11-08.md](../docs/RPI_ETHERNET_2026-11-08.md)<br>[LXI_DEVICE_CONFIGURATION.md](../docs/LXI_DEVICE_CONFIGURATION.md) |
| 7.6 / p.43 | 必須 | 実装確認：見出しRULEだが本文should。保存値と再起動後の自動交渉onを実機確認。 | [RPI_ETHERNET_2026-11-08.md](../docs/RPI_ETHERNET_2026-11-08.md) |
| 7.7 / p.43 | 必須 | 実装確認：Piへ反映。実識別XMLはeth0だけ。4サービスを有線で新規取得しWLANでは未取得、WLANのIP管理HTTPSは維持。 | [identification.py](../civi/identification.py)<br>[network.py](../civi/network.py)<br>[config.pi.example.toml](../config.pi.example.toml)<br>[test_lxi_fixes.py](../tests/test_lxi_fixes.py)<br>[IMPLEMENTATION_AND_TEST_RESULTS.md](../docs/IMPLEMENTATION_AND_TEST_RESULTS.md)<br>[RPI_LXI_FIXES_2026-11-10.md](../docs/RPI_LXI_FIXES_2026-11-10.md) |
| 8.1 / p.45 | 必須 | 実装確認：Linux TCP/UDP/IPv4を利用。実機HTTPS/SCPI/mDNS通信証拠あり。 | [__main__.py](../civi/__main__.py)<br>[RPI_AUTOIP_TCP_2026-11-08.md](../docs/RPI_AUTOIP_TCP_2026-11-08.md) |
| 8.2 / p.45 | 必須 | 実装確認：有線/WLANのPing応答を確認。 | [ping.py](../civi/pi/ping.py)<br>[RPI_PING.md](../docs/RPI_PING.md)<br>[test_ping_control.py](../tests/test_ping_control.py) |
| 8.3 / p.45 | 必須 | 実装確認：既定有効とLCI再有効化を実装・確認。 | [ping.py](../civi/pi/ping.py)<br>[RPI_PING.md](../docs/RPI_PING.md)<br>[test_ping_control.py](../tests/test_ping_control.py) |
| 8.4 / p.45 | 必須 | 実装確認：Web無効化/保存/再起動保持/復帰を実機確認。 | [ping.py](../civi/pi/ping.py)<br>[RPI_PING.md](../docs/RPI_PING.md)<br>[test_ping_control.py](../tests/test_ping_control.py) |
| 8.6 / p.46 | 必須 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G05 | [network.py](../civi/pi/network.py)<br>[DHCP_2026-11-08.md](../docs/DHCP_2026-11-08.md)<br>[RPI_DHCP_ETHERNET_2026-11-10.md](../docs/RPI_DHCP_ETHERNET_2026-11-10.md)<br>[test_applied_ipv4.py](../tests/test_applied_ipv4.py)<br>[RPI_DHCP_BOOT_2026-11-11.md](../docs/RPI_DHCP_BOOT_2026-11-11.md) |
| 8.6.1 / p.47 | 必須 | 実装確認：Automatic(DHCP+AutoIP)とManualを提供。物理/隔離Piの取得・保存・再起動・LCI記録あり。全組合せを合格と主張しない。 | [network.py](../civi/pi/network.py)<br>[DHCP_2026-11-08.md](../docs/DHCP_2026-11-08.md)<br>[RPI_DHCP_ETHERNET_2026-11-10.md](../docs/RPI_DHCP_ETHERNET_2026-11-10.md)<br>[test_applied_ipv4.py](../tests/test_applied_ipv4.py)<br>[RPI_DHCP_BOOT_2026-11-11.md](../docs/RPI_DHCP_BOOT_2026-11-11.md)<br>[IVI_6_1_COMPLETION_2026-11-12.md](../docs/IVI_6_1_COMPLETION_2026-11-12.md) |
| 8.6.3 / p.47 | 必須 | 実装確認：使用するIP設定パラメーター1/3/6を実eth0の要求リストで確認。OSの全任意オプションの網羅試験を追加必須にはしない。 | [DHCP_2026-11-08.md](../docs/DHCP_2026-11-08.md)<br>[RPI_DHCP_ETHERNET_2026-11-10.md](../docs/RPI_DHCP_ETHERNET_2026-11-10.md)<br>[test_applied_ipv4.py](../tests/test_applied_ipv4.py)<br>[IVI_6_1_COMPLETION_2026-11-12.md](../docs/IVI_6_1_COMPLETION_2026-11-12.md) |
| 8.6.5 / p.47 | 必須 | 実装確認：gateway/DNS省略の実ACKでも取得・Normal、異なるhostname optionでシステム名維持を確認。追加オプションに動作を依存させない。 | [DHCP_2026-11-08.md](../docs/DHCP_2026-11-08.md)<br>[RPI_DHCP_ETHERNET_2026-11-10.md](../docs/RPI_DHCP_ETHERNET_2026-11-10.md)<br>[test_applied_ipv4.py](../tests/test_applied_ipv4.py)<br>[IVI_6_1_COMPLETION_2026-11-12.md](../docs/IVI_6_1_COMPLETION_2026-11-12.md) |
| 8.6.6 / p.48 | 必須 | 実装確認：実eth0でリース失効時のアドレス/gateway/DNS破棄、AutoIP移行とFault保持を確認。本体表示の共通ロジックは試験済み。 | [DHCP_2026-11-08.md](../docs/DHCP_2026-11-08.md)<br>[indicator.py](../civi/indicator.py)<br>[test_indicator.py](../tests/test_indicator.py)<br>[RPI_DHCP_ETHERNET_2026-11-10.md](../docs/RPI_DHCP_ETHERNET_2026-11-10.md)<br>[test_applied_ipv4.py](../tests/test_applied_ipv4.py)<br>[IVI_6_1_COMPLETION_2026-11-12.md](../docs/IVI_6_1_COMPLETION_2026-11-12.md) |
| 8.6.7 / p.48 | 必須 | 実装確認：実eth0の自然更新ACKでgateway/DNS変更と実効OS設定への反映を確認。保存/再起動は別の既存記録で確認。 | [DHCP_2026-11-08.md](../docs/DHCP_2026-11-08.md)<br>[RPI_DHCP_ETHERNET_2026-11-10.md](../docs/RPI_DHCP_ETHERNET_2026-11-10.md)<br>[test_applied_ipv4.py](../tests/test_applied_ipv4.py)<br>[IVI_6_1_COMPLETION_2026-11-12.md](../docs/IVI_6_1_COMPLETION_2026-11-12.md) |
| 8.6.10 / p.49 | 必須 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G05 | [linklocal.py](../civi/pi/linklocal.py)<br>[RPI_AUTOIP_TCP_2026-11-08.md](../docs/RPI_AUTOIP_TCP_2026-11-08.md) |
| 8.7 / p.50 | 必須 | 実装確認：隔離Piの実NetworkManager/ARP/DHCPで開始前重複拒否、使用中切断とFaultを確認。物理NICの全経路組合せは追加信頼性試験として区別。 | [conflict.py](../civi/pi/conflict.py)<br>[RPI_CONFLICT.md](../docs/RPI_CONFLICT.md)<br>[IVI_6_1_COMPLETION_2026-11-12.md](../docs/IVI_6_1_COMPLETION_2026-11-12.md) |
| 8.9/legal-name / p.51 | 本文の必須文 | 実装確認：推奨節内のshallも追跡。共通既定名はDNSラベルとして検証。 | [network.py](../civi/pi/network.py)<br>[defaults.py](../civi/defaults.py) |
| 8.10 / p.51 | 必須 | 実装確認：DHCP失効後のFault保持と新リースのNormal復帰を実eth0で確認。本体状態遷移とFault優先は共通ロジック・既存実機記録で確認。 | [indicator.py](../civi/indicator.py)<br>[test_indicator.py](../tests/test_indicator.py)<br>[DHCP_2026-11-08.md](../docs/DHCP_2026-11-08.md)<br>[RPI_DHCP_ETHERNET_2026-11-10.md](../docs/RPI_DHCP_ETHERNET_2026-11-10.md)<br>[test_applied_ipv4.py](../tests/test_applied_ipv4.py)<br>[IVI_6_1_COMPLETION_2026-11-12.md](../docs/IVI_6_1_COMPLETION_2026-11-12.md) |
| 8.10/initial-autoip / p.51 | 親条項の内訳 | 実装確認：初回DHCP不在からAutoIP取得時はNormalを単体/実機で確認。 | [indicator.py](../civi/indicator.py)<br>[test_indicator.py](../tests/test_indicator.py)<br>[RPI_LCI_BOOT_2026-11-08.md](../docs/RPI_LCI_BOOT_2026-11-08.md) |
| 8.10/expired-autoip / p.52 | 親条項の内訳 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G05 | [indicator.py](../civi/indicator.py)<br>[test_indicator.py](../tests/test_indicator.py)<br>[DHCP_2026-11-08.md](../docs/DHCP_2026-11-08.md)<br>[RPI_DHCP_ETHERNET_2026-11-10.md](../docs/RPI_DHCP_ETHERNET_2026-11-10.md)<br>[test_applied_ipv4.py](../tests/test_applied_ipv4.py) |
| 8.10/identify-fault / p.52 | 親条項の状態遷移図 | 実装確認：実PiでIdentify中に有線を抜きFault優先・Identify解除・本体ACKを確認。再接続でNormal/Identify OFF、利用者の再開始/停止も確認。DHCP失効等は別行。 | [panel.py](../civi/pi/panel.py)<br>[indicator.py](../civi/indicator.py)<br>[indicator.js](../civi/static/indicator.js)<br>[test_indicator.py](../tests/test_indicator.py)<br>[test_lxi_fixes.py](../tests/test_lxi_fixes.py)<br>[IMPLEMENTATION_AND_TEST_RESULTS.md](../docs/IMPLEMENTATION_AND_TEST_RESULTS.md)<br>[RPI_LXI_FIXES_2026-11-10.md](../docs/RPI_LXI_FIXES_2026-11-10.md) |
| 8.11.1.1 / p.54 | DDNS無効化を提供する場合 | 適用外：RFC2136 DDNS UpdateとユーザーDDNS制御は採用しない。mDNS制御と区別。OSのDHCP hostname/server-side登録はCIVI DDNS機能とは宣言しない。採用時に再評価。 | [network.py](../civi/pi/network.py)<br>[IVI_6_1_COMPLETION_2026-11-12.md](../docs/IVI_6_1_COMPLETION_2026-11-12.md)<br>[LXI_DEVICE_CONFIGURATION.md](../docs/LXI_DEVICE_CONFIGURATION.md) |
| 8.13 / p.55 | 必須 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G05, G07 | [lci.py](../civi/pi/lci.py)<br>[transactions.py](../civi/pi/transactions.py)<br>[RPI_LCI_BOOT_2026-11-08.md](../docs/RPI_LCI_BOOT_2026-11-08.md)<br>[RPI_DHCP_BOOT_2026-11-11.md](../docs/RPI_DHCP_BOOT_2026-11-11.md) |
| 8.13/dhcp / p.55 | 親条項の内訳 | 実装確認：固定IP→ローカルLCIでsaved auto、手動IP除去、新規DHCP ACKと192.168.73.3取得を実機確認。 | [lci.py](../civi/pi/lci.py)<br>[transactions.py](../civi/pi/transactions.py)<br>[RPI_LCI_BOOT_2026-11-08.md](../docs/RPI_LCI_BOOT_2026-11-08.md)<br>[RPI_DHCP_BOOT_2026-11-11.md](../docs/RPI_DHCP_BOOT_2026-11-11.md) |
| 8.13/autoip / p.55 | 親条項の内訳 | 実装確認：AutoIPを有効化する。 | [lci.py](../civi/pi/lci.py)<br>[transactions.py](../civi/pi/transactions.py)<br>[RPI_LCI_BOOT_2026-11-08.md](../docs/RPI_LCI_BOOT_2026-11-08.md) |
| 8.13/ping / p.55 | 親条項の内訳 | 実装確認：Pingを再有効化する。 | [lci.py](../civi/pi/lci.py)<br>[transactions.py](../civi/pi/transactions.py)<br>[RPI_LCI_BOOT_2026-11-08.md](../docs/RPI_LCI_BOOT_2026-11-08.md) |
| 8.13/password / p.55 | 親条項の内訳 | 実装確認：ローカル表示の復旧用パスワードへの切替とライブ反映世代を確認。Pi内だけで保護Web GET認証200を確認。パスワードは収集/出力しない。 | [lci.py](../civi/pi/lci.py)<br>[transactions.py](../civi/pi/transactions.py)<br>[RPI_LCI_BOOT_2026-11-08.md](../docs/RPI_LCI_BOOT_2026-11-08.md)<br>[RPI_DHCP_BOOT_2026-11-11.md](../docs/RPI_DHCP_BOOT_2026-11-11.md) |
| 8.13/mdns / p.55 | 親条項の内訳 | 実装確認：mDNS/DNS-SDを再有効化する。 | [lci.py](../civi/pi/lci.py)<br>[transactions.py](../civi/pi/transactions.py)<br>[RPI_LCI_BOOT_2026-11-08.md](../docs/RPI_LCI_BOOT_2026-11-08.md) |
| 8.13/ddns / p.55 | 親条項の内訳 | 適用外：RFC2136 DDNS UpdateとユーザーDDNS制御は採用しない。mDNS制御と区別。OSのDHCP hostname/server-side登録はCIVI DDNS機能とは宣言しない。採用時に再評価。 | [network.py](../civi/pi/network.py)<br>[LXI_DEVICE_CONFIGURATION.md](../docs/LXI_DEVICE_CONFIGURATION.md) |
| 8.13/activation / p.55 | 親条項の内訳 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G05 | [lci.py](../civi/pi/lci.py)<br>[RPI_LCI_BOOT_2026-11-08.md](../docs/RPI_LCI_BOOT_2026-11-08.md)<br>[RPI_DHCP_BOOT_2026-11-11.md](../docs/RPI_DHCP_BOOT_2026-11-11.md) |
| 8.13/documentation / p.55 | 親条項の内訳 | 実装確認：LCIの変更項目と復旧認証をローカル文書に記載。 | [RPI_LAN_RESET.md](../docs/RPI_LAN_RESET.md) |
| 9.1 / p.57 | 必須 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G08 | [server.py](../civi/server.py)<br>[RPI_HTTPS_2026-11-07.md](../docs/RPI_HTTPS_2026-11-07.md)<br>[WEB_API_REVIEW_2026-11-10.md](../docs/WEB_API_REVIEW_2026-11-10.md)<br>[test_web_api_review.py](../tests/test_web_api_review.py)<br>[WEB_STATES_2026-11-10.md](../docs/WEB_STATES_2026-11-10.md)<br>[test_web_state_transitions.py](../tests/test_web_state_transitions.py) |
| 9.1.1 / p.57 | Deprecated | 廃止：現行必須の不足には数えない。後継条項を本表で追跡。 | [LXI.md](../docs/LXI.md) |
| 9.1.4 / p.57 | 必須 | 実装確認：Pi既定443。実Piで443/8443を確認。Windows8443構成は本表のLXI装置対象外。 | [config.pi.example.toml](../config.pi.example.toml)<br>[RPI_HTTPS_2026-11-07.md](../docs/RPI_HTTPS_2026-11-07.md) |
| 9.1.7 / p.58 | 必須 | 実装確認：/lxiと/lxi/を公開。 | [test_lxi.py](../tests/test_lxi.py)<br>[server.py](../civi/server.py) |
| 9.2 / p.58 | 必須 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G04 | [identification.py](../civi/identification.py) |
| 9.2/model / p.58 | 親条項の内訳 | 実装確認：Web識別情報の該当値をコード/HTML試験で確認。 | [identification.py](../civi/identification.py)<br>[test_lxi.py](../tests/test_lxi.py) |
| 9.2/manufacturer / p.58 | 親条項の内訳 | 実装確認：Web識別情報の該当値をコード/HTML試験で確認。 | [identification.py](../civi/identification.py)<br>[test_lxi.py](../tests/test_lxi.py) |
| 9.2/serial / p.58 | 親条項の内訳 | 実装確認：Web識別情報の該当値をコード/HTML試験で確認。 | [identification.py](../civi/identification.py)<br>[test_lxi.py](../tests/test_lxi.py) |
| 9.2/description / p.58 | 親条項の内訳 | 実装確認：Web識別情報の該当値をコード/HTML試験で確認。 | [identification.py](../civi/identification.py)<br>[test_lxi.py](../tests/test_lxi.py) |
| 9.2/software / p.59 | 親条項の内訳 | 実装確認：Web識別情報の該当値をコード/HTML試験で確認。 | [identification.py](../civi/identification.py)<br>[test_lxi.py](../tests/test_lxi.py) |
| 9.2/visa / p.59 | 親条項の内訳 | 実装確認：Web識別情報の該当値をコード/HTML試験で確認。 | [identification.py](../civi/identification.py)<br>[test_lxi.py](../tests/test_lxi.py) |
| 9.2/lxi-version / p.58 | 親条項の内訳 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G04 | [identification.py](../civi/identification.py) |
| 9.2/extensions / p.58 | 親条項の内訳 | 実装確認：未採用拡張を宣言しない。 | [identification.py](../civi/identification.py) |
| 9.2/hostname / p.58 | 親条項の内訳 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G08 | [identification.py](../civi/identification.py)<br>[MDNS_HOSTNAME_2026-11-08.md](../docs/MDNS_HOSTNAME_2026-11-08.md) |
| 9.2/mac-ip / p.58 | 親条項の内訳 | 実装確認：Piの対象有線NICをLXI扱い、他NICは管理用として明記。IP未割当の対象NICもWebに表示。 本番PiのXMLでもeth0だけであることを確認済み。 | [identification.py](../civi/identification.py)<br>[test_lxi_fixes.py](../tests/test_lxi_fixes.py)<br>[IMPLEMENTATION_AND_TEST_RESULTS.md](../docs/IMPLEMENTATION_AND_TEST_RESULTS.md)<br>[RPI_LXI_FIXES_2026-11-10.md](../docs/RPI_LXI_FIXES_2026-11-10.md) |
| 9.2.1 / p.59 | 必須 | 実装確認：表示SOCKETアドレスにboard番号を付けない。 | [test_lxi.py](../tests/test_lxi.py)<br>[identification.py](../civi/identification.py) |
| 9.2.3 / p.59 | 必須 | 実装確認：Hostname欄は有効・成功した広告済みmDNS名だけを表示。広告なし/無効/失敗時は対象NICのIPv4またはNot assigned。OS設定名を別欄とし、模擬Webで全条件を確認。 | [identification.py](../civi/identification.py)<br>[discovery.py](../civi/pi/discovery.py)<br>[MDNS_HOSTNAME_2026-11-08.md](../docs/MDNS_HOSTNAME_2026-11-08.md)<br>[WEB_API_REVIEW_2026-11-10.md](../docs/WEB_API_REVIEW_2026-11-10.md)<br>[test_web_api_review.py](../tests/test_web_api_review.py) |
| 9.2.3.2 / p.60 | 必須 | 実装確認：mDNS停止/失敗/未登録時はHostname欄を対象NICのIP代替とし、未検証のOS名を実ホスト名として出さない。模擬応答確認。 | [identification.py](../civi/identification.py)<br>[test_lxi.py](../tests/test_lxi.py)<br>[WEB_API_REVIEW_2026-11-10.md](../docs/WEB_API_REVIEW_2026-11-10.md)<br>[test_web_api_review.py](../tests/test_web_api_review.py) |
| 9.2.3.3 / p.61 | 必須 | 実装確認：取得mDNS名は.local.形式で表示し、実Avahi/Webで確認。 | [discovery.py](../civi/pi/discovery.py)<br>[MDNS_HOSTNAME_2026-11-08.md](../docs/MDNS_HOSTNAME_2026-11-08.md) |
| 9.2.3.5 / p.61 | 必須 | 実装確認：Descriptionは取得済みサービス名を優先して表示。 | [identification.py](../civi/identification.py)<br>[MDNS_HOSTNAME_2026-11-08.md](../docs/MDNS_HOSTNAME_2026-11-08.md) |
| 9.3 / p.61 | 必須 | 実装確認：認証付きWeb Start/Stopと本体の継続Identifyを実機確認。 | [test_indicator.py](../tests/test_indicator.py)<br>[RPI_PANEL_2026-11-07.md](../docs/RPI_PANEL_2026-11-07.md) |
| 9.4 / p.61 | 必須 | 実装確認：WelcomeからLAN設定へのリンクあり。同期機能を採用しないのでSyncリンクは不要。 | [identification.py](../civi/identification.py)<br>[test_lxi.py](../tests/test_lxi.py) |
| 9.5 / p.62 | 必須 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G05, G08 | [identification.py](../civi/identification.py)<br>[network.py](../civi/pi/network.py)<br>[RPI_LAN_SETTINGS.md](../docs/RPI_LAN_SETTINGS.md) |
| 9.5/hostname / p.62 | 親条項の内訳 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G05 | [identification.py](../civi/identification.py)<br>[network.py](../civi/pi/network.py)<br>[RPI_LAN_SETTINGS.md](../docs/RPI_LAN_SETTINGS.md) |
| 9.5/description / p.62 | 親条項の内訳 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G05 | [identification.py](../civi/identification.py)<br>[network.py](../civi/pi/network.py)<br>[RPI_LAN_SETTINGS.md](../docs/RPI_LAN_SETTINGS.md) |
| 9.5/mode / p.62 | 親条項の内訳 | 実装確認：実eth0でDHCPモードを確定保存し、Pi本体再起動後の保存auto・DHCP取得を確認。元の保存static設定にも一致するよう復元。初期起動時のstaticと合わせ保存モード保持を確認。 | [identification.py](../civi/identification.py)<br>[network.py](../civi/pi/network.py)<br>[RPI_LAN_SETTINGS.md](../docs/RPI_LAN_SETTINGS.md)<br>[RPI_DHCP_BOOT_2026-11-11.md](../docs/RPI_DHCP_BOOT_2026-11-11.md) |
| 9.5/address / p.62 | 親条項の内訳 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G05 | [identification.py](../civi/identification.py)<br>[network.py](../civi/pi/network.py)<br>[RPI_LAN_SETTINGS.md](../docs/RPI_LAN_SETTINGS.md) |
| 9.5/gateway / p.62 | 親条項の内訳 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G05 | [identification.py](../civi/identification.py)<br>[network.py](../civi/pi/network.py)<br>[RPI_LAN_SETTINGS.md](../docs/RPI_LAN_SETTINGS.md) |
| 9.5/dns / p.62 | 親条項の内訳 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G05 | [identification.py](../civi/identification.py)<br>[network.py](../civi/pi/network.py)<br>[RPI_LAN_SETTINGS.md](../docs/RPI_LAN_SETTINGS.md) |
| 9.5/subnet / p.62 | 親条項の内訳 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G05 | [identification.py](../civi/identification.py)<br>[network.py](../civi/pi/network.py)<br>[WEB_API_REVIEW_2026-11-10.md](../docs/WEB_API_REVIEW_2026-11-10.md)<br>[test_web_api_review.py](../tests/test_web_api_review.py) |
| 9.5.6 / p.62 | 必須 | 実装確認：mDNSのWeb停止/復帰と保持を実Piで確認。 | [RPI_MDNS.md](../docs/RPI_MDNS.md)<br>[test_pi_mdns.py](../tests/test_pi_mdns.py) |
| 9.5.7 / p.63 | 必須 | 実装確認：空白hostnameの既定値復帰を本番Webでユーザー確認。 | [LXI_DEFAULTS_API.md](../docs/LXI_DEFAULTS_API.md)<br>[test_lxi_defaults.py](../tests/test_lxi_defaults.py) |
| 9.5.8 / p.63 | 必須 | 実装確認：空白Descriptionの既定値復帰を本番Webでユーザー確認。 | [LXI_DEFAULTS_API.md](../docs/LXI_DEFAULTS_API.md)<br>[test_lxi_defaults.py](../tests/test_lxi_defaults.py) |
| 9.6 / p.64 | 同期/イベント拡張を採用した場合 | 適用外：Clock/Event/Wired Triggerを実装しない。 | [LXI.md](../docs/LXI.md) |
| 9.8 / p.64 | 必須 | 実装確認：全15 POST経路で未認証/不正認証/CSRFヘッダー欠落/異Origin/変更前パスワードを拒否する試験を追加。既存の受理/保存試験と併用。侵入試験や完全なセキュリティ評価ではない。 | [server.py](../civi/server.py)<br>[auth.py](../civi/auth.py)<br>[test_password.py](../tests/test_password.py)<br>[WEB_API_REVIEW_2026-11-10.md](../docs/WEB_API_REVIEW_2026-11-10.md)<br>[test_web_api_review.py](../tests/test_web_api_review.py) |
| 9.8/nonblank / p.64 | 親条項の内訳 | 実装確認：撤回された空パスワード許可を使用しない。 | [auth.py](../civi/auth.py)<br>[test_password.py](../tests/test_password.py) |
| 9.8.1 / p.64 | 撤回済Permissionの禁止事項 | 実装確認：空パスワードを許可しない。旧Permissionは撤回済み。 | [auth.py](../civi/auth.py)<br>[test_password.py](../tests/test_password.py) |
| 9.9 / p.64 | 必須 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G11 | [identification.py](../civi/identification.py) |
| 9.14 / p.65 | 必須 | 実装確認：独自JSONは/api/以下。/lxi以下の実ルートはWelcome/識別/規定XSDに限定。 | [server.py](../civi/server.py)<br>[lxi_api.py](../civi/lxi_api.py) |
| 10.2 / p.66 | 必須 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G04, G08 | [identification.py](../civi/identification.py)<br>[lxi_api.py](../civi/lxi_api.py)<br>[LXI_DEFAULTS_API.md](../docs/LXI_DEFAULTS_API.md) |
| 10.2.5 / p.66 | 拡張機能を実装した場合 | 適用外：採用拡張なし。未実装拡張のFunctionを宣言しない。 | [identification.py](../civi/identification.py) |
| 10.3 / p.66 | 必須 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G06 | [discovery.py](../civi/pi/discovery.py)<br>[MDNS_HOSTNAME_2026-11-08.md](../docs/MDNS_HOSTNAME_2026-11-08.md) |
| 10.3.1 / p.67 | 必須 | 実装確認：物理eth0で名前衝突回避・Web/XML/広告整合、再接続での3回の再プローブを確認。Avahiへの委譲範囲を維持。 | [discovery.py](../civi/pi/discovery.py)<br>[MDNS_HOSTNAME_2026-11-08.md](../docs/MDNS_HOSTNAME_2026-11-08.md)<br>[RPI_NAME_COLLISION_2026-11-11.md](../docs/RPI_NAME_COLLISION_2026-11-11.md)<br>[RPI_MDNS_RECONNECT_2026-11-11.md](../docs/RPI_MDNS_RECONNECT_2026-11-11.md)<br>[IVI_6_1_COMPLETION_2026-11-12.md](../docs/IVI_6_1_COMPLETION_2026-11-12.md) |
| 10.3.1.1 / p.67 | 必須 | 実装確認：物理名前衝突で番号付きホスト名を取得し、相手停止後のPi全体再起動でも保存名を再利用。 | [MDNS_HOSTNAME_2026-11-08.md](../docs/MDNS_HOSTNAME_2026-11-08.md)<br>[RPI_NAME_COLLISION_2026-11-11.md](../docs/RPI_NAME_COLLISION_2026-11-11.md)<br>[IVI_6_1_COMPLETION_2026-11-12.md](../docs/IVI_6_1_COMPLETION_2026-11-12.md) |
| 10.3.3 / p.67 | DDNS Updateを提供する場合 | 適用外：RFC2136 DDNS UpdateとユーザーDDNS制御は採用しない。mDNS制御と区別。OSのDHCP hostname/server-side登録はCIVI DDNS機能とは宣言しない。採用時に再評価。 | [network.py](../civi/pi/network.py)<br>[discovery.py](../civi/pi/discovery.py)<br>[LXI_DEVICE_CONFIGURATION.md](../docs/LXI_DEVICE_CONFIGURATION.md) |
| 10.3.4 / p.67 | 必須 | 実装確認：実eth0 DHCPで別hostname optionを返してもシステム/ユーザー名を維持することを確認済み。初回表の未試験記述を訂正。 | [discovery.py](../civi/pi/discovery.py)<br>[DHCP_2026-11-08.md](../docs/DHCP_2026-11-08.md)<br>[IVI_6_1_COMPLETION_2026-11-12.md](../docs/IVI_6_1_COMPLETION_2026-11-12.md) |
| 10.4 / p.67 | 必須 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G06 | [discovery.py](../civi/pi/discovery.py)<br>[MDNS_HOSTNAME_2026-11-08.md](../docs/MDNS_HOSTNAME_2026-11-08.md) |
| 10.4.1 / p.68 | 必須 | 実装確認：物理共通サービス名衝突と再接続プローブ/広告を確認。固定100候補制限を除去し、110連続衝突の模擬試験も成功。 | [discovery.py](../civi/pi/discovery.py)<br>[discovery_state.py](../civi/discovery_state.py)<br>[MDNS_HOSTNAME_2026-11-08.md](../docs/MDNS_HOSTNAME_2026-11-08.md)<br>[RPI_NAME_COLLISION_2026-11-11.md](../docs/RPI_NAME_COLLISION_2026-11-11.md)<br>[RPI_MDNS_RECONNECT_2026-11-11.md](../docs/RPI_MDNS_RECONNECT_2026-11-11.md)<br>[IVI_6_1_COMPLETION_2026-11-12.md](../docs/IVI_6_1_COMPLETION_2026-11-12.md) |
| 10.4.2 / p.68 | 必須 | 実装確認：HTTP/LXI/raw/HTTPSを同一取得名で広告。物理衝突後とPi全体再起動後も4サービスのSRV/IP/ポートを確認。 | [discovery.py](../civi/pi/discovery.py)<br>[MDNS_HOSTNAME_2026-11-08.md](../docs/MDNS_HOSTNAME_2026-11-08.md)<br>[RPI_NAME_COLLISION_2026-11-11.md](../docs/RPI_NAME_COLLISION_2026-11-11.md) |
| 10.4.2.1 / p.68 | 必須 | 実装確認：本番Webで64byte ASCII→63byte保存と4サービス再広告を確認し復元。UTF-8境界はPi模擬試験で確認。 | [network.py](../civi/network.py)<br>[test_lxi.py](../tests/test_lxi.py)<br>[test_lxi_fixes.py](../tests/test_lxi_fixes.py)<br>[IMPLEMENTATION_AND_TEST_RESULTS.md](../docs/IMPLEMENTATION_AND_TEST_RESULTS.md)<br>[RPI_LXI_FIXES_2026-11-10.md](../docs/RPI_LXI_FIXES_2026-11-10.md) |
| 10.4.2.3 / p.68 | 必須 | 実装確認：候補を逐次生成して衝突時に待機・継続。110衝突後(111)で4サービス登録と保存を確認。恒久衝突時の取消と資源解放も試験。 | [discovery_state.py](../civi/discovery_state.py)<br>[discovery.py](../civi/pi/discovery.py)<br>[MDNS_HOSTNAME_2026-11-08.md](../docs/MDNS_HOSTNAME_2026-11-08.md)<br>[IVI_6_1_COMPLETION_2026-11-12.md](../docs/IVI_6_1_COMPLETION_2026-11-12.md) |
| 10.4.3 / p.68 | 必須 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G08 | [discovery.py](../civi/pi/discovery.py)<br>[test_lxi.py](../tests/test_lxi.py)<br>[MDNS_HOSTNAME_2026-11-08.md](../docs/MDNS_HOSTNAME_2026-11-08.md) |
| 10.4.3/required / p.69 | 親条項の内訳 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G08 | [discovery.py](../civi/pi/discovery.py)<br>[network.py](../civi/network.py)<br>[test_lxi.py](../tests/test_lxi.py) |
| 10.4.3/recommended-raw / p.70 | 親条項の内訳 | 実装確認：採用したraw広告も同じ識別TXTを使用し、古いAddressキーを出力しない。 | [discovery.py](../civi/pi/discovery.py)<br>[network.py](../civi/network.py) |
| 10.4.3.1 / p.69 | 必須 | 実装確認：各サービスへTXTリストを渡す。 | [discovery.py](../civi/pi/discovery.py)<br>[test_lxi.py](../tests/test_lxi.py) |
| 10.4.3.2 / p.69 | 必須 | 実装確認：key=valueをUTF-8へ変換、255byte超過は広告前拒否。 | [discovery.py](../civi/pi/discovery.py) |
| 10.4.3.3 / p.69 | 必須 | 実装確認：送信キーは固定ASCII。受信キーを独自大小文字比較する機構なし。 | [discovery.py](../civi/pi/discovery.py)<br>[network.py](../civi/network.py) |
| 10.4.3.4 / p.70 | 必須 | 実装確認：値をUTF-8 bytesへ変換。ASCII識別値も同じ経路。 | [discovery.py](../civi/pi/discovery.py) |
| 10.4.3.6 / p.70 | 必須 | 実装確認：txtversを先頭に生成。 | [test_lxi.py](../tests/test_lxi.py)<br>[discovery.py](../civi/pi/discovery.py) |
| 10.4.3.7 / p.70 | 必須 | 実装確認：独自LXI接頭辞キーを出していない。 | [discovery.py](../civi/pi/discovery.py)<br>[network.py](../civi/network.py) |
| 10.4.3.8 / p.70 | 必須 | 実装確認：必須/推奨サービスには標準キーだけを使用、独自キーなし。 | [discovery.py](../civi/pi/discovery.py)<br>[network.py](../civi/network.py) |
| 10.4.3.11 / p.71 | Deprecated | 廃止：現行必須の不足には数えない。後継条項を本表で追跡。 | [LXI.md](../docs/LXI.md) |
| 10.5 / p.72 | 必須 | 実装確認：既定有効。無効保存値は利用者設定であり出荷既定とは分離。 | [config.pi.example.toml](../config.pi.example.toml)<br>[RPI_MDNS.md](../docs/RPI_MDNS.md) |
| 10.5.1 / p.72 | 必須 | 実装確認：本体LCIで装置全体のAvahiを有効化。 | [RPI_LCI_BOOT_2026-11-08.md](../docs/RPI_LCI_BOOT_2026-11-08.md)<br>[RPI_MDNS.md](../docs/RPI_MDNS.md) |
| 10.5.2 / p.72 | 必須 | 実装確認：装置全体停止/ソケット起動抑止/再起動保持/復帰を実機確認。 | [RPI_MDNS.md](../docs/RPI_MDNS.md) |
| 10.6 / p.72 | 必須 | 実装確認：Pi標準NSS/socketの.local正引きと169.254 PTR逆引きを有線で確認。実AutoIP割当相手でも隔離Piで正引き・逆引き・TCPを確認。物理AutoIP2台は追加試験。 | [IVI_6_1_COMPLETION_2026-11-12.md](../docs/IVI_6_1_COMPLETION_2026-11-12.md)<br>[RPI_MDNS_RESOLVER_2026-11-11.md](../docs/RPI_MDNS_RESOLVER_2026-11-11.md)<br>[RPI_MDNS_AUTOIP_2026-11-11.md](../docs/RPI_MDNS_AUTOIP_2026-11-11.md) |
| 10.7 / p.72 | 必須 | 実装確認：希望名/取得名を保存。物理衝突後、相手を停止してPi全体再起動し取得名再利用を確認。元のキャッシュ・設定・認証・固定IPへ復元。 | [discovery_state.py](../civi/discovery_state.py)<br>[MDNS_HOSTNAME_2026-11-08.md](../docs/MDNS_HOSTNAME_2026-11-08.md)<br>[RPI_NAME_COLLISION_2026-11-11.md](../docs/RPI_NAME_COLLISION_2026-11-11.md) |
| 10.7.1 / p.73 | 必須 | 実装確認：LCI世代更新で取得名を破棄し最終利用者名/既定値に戻す。 | [lci.py](../civi/pi/lci.py)<br>[test_pi_lci.py](../tests/test_pi_lci.py)<br>[test_discovery_names.py](../tests/test_discovery_names.py) |
| 10.8 / p.73 | 必須 | 実装確認：同一固定IPの物理再接続でホスト名/4サービスを各3回再プローブ後に再広告。新規DNS-SD/HTTPS/SCPIも確認。 | [network.py](../civi/network.py)<br>[discovery.py](../civi/pi/discovery.py)<br>[RPI_MDNS_RECONNECT_2026-11-11.md](../docs/RPI_MDNS_RECONNECT_2026-11-11.md)<br>[IVI_6_1_COMPLETION_2026-11-12.md](../docs/IVI_6_1_COMPLETION_2026-11-12.md) |
| 11.1 / p.74 | 必須 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G10 | [AUDIT.md](../drivers/civi-ic7300/src/civi_ic7300/AUDIT.md)<br>[COMPLIANCE.md](../drivers/civi-ic7300/src/civi_ic7300/COMPLIANCE.md)<br>[IVI_RECEIVE_ACCEPTANCE_2026-11-11.md](../docs/IVI_RECEIVE_ACCEPTANCE_2026-11-11.md)<br>[IVI_6_1_COMPLETION_2026-11-12.md](../docs/IVI_6_1_COMPLETION_2026-11-12.md)<br>[IVI_VERIFICATION_RECONCILED_2026-11-12.json](../docs/IVI_VERIFICATION_RECONCILED_2026-11-12.json)<br>[IVI_MENU_VERIFICATION_2026-11-12.csv](../docs/IVI_MENU_VERIFICATION_2026-11-12.csv) |
| 11.2 / p.74 | 必須 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G10 | [NAMING.md](../drivers/civi-ic7300/src/civi_ic7300/NAMING.md)<br>[COMPLIANCE.md](../drivers/civi-ic7300/src/civi_ic7300/COMPLIANCE.md) |

## 補足解釈

| 条項 / PDF頁 | 適用条件 | 判定・結果 | 根拠 |
|---|---|---|---|
| 8.14 / p.6 | 必須 | 実装確認：公式補足解釈で追加。IPv4 SCPI SOCKETによる制御を提供。 | [server.py](../civi/server.py)<br>[RPI_AUTOIP_TCP_2026-11-08.md](../docs/RPI_AUTOIP_TCP_2026-11-08.md) |

## 識別API

| 条項 / PDF頁 | 適用条件 | 判定・結果 | 根拠 |
|---|---|---|---|
| 23.5 / p.9 | 識別APIに適用 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G08 | [LXI_DEFAULTS_API.md](../docs/LXI_DEFAULTS_API.md) |
| 23.5.1 / p.9 | 識別APIに適用 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G08 | [InstrumentIdentification-2.0.xsd](../civi/schemas/InstrumentIdentification-2.0.xsd)<br>[LXIProblemDetails-1.0.xsd](../civi/schemas/LXIProblemDetails-1.0.xsd) |
| 23.6 / p.9 | 識別APIに適用 | 実装確認：WebでLXI APIを独立した拡張として列挙していない。 | [identification.py](../civi/identification.py) |
| 23.7 / p.9 | 識別APIに適用 | 実装確認：XMLでLXI API Functionを宣言しない。 | [identification.py](../civi/identification.py) |
| 23.10.1/public-get / p.11 | 識別APIに適用 | 実装確認：GET識別は認証不要。HTTP平文を別途提供する義務とはしない。 | [server.py](../civi/server.py)<br>[test_lxi.py](../tests/test_lxi.py) |
| 23.10.1.1 / p.11 | 保護されたLXI APIを提供した場合 | 適用外：識別だけでAPI Key機構をコア必須とはしない。保護された/lxi/apiエンドポイントは未採用。 | [server.py](../civi/server.py) |
| 23.10.1.2 / p.11 | 保護されたLXI APIを提供した場合 | 適用外：LXI-API realmは保護API採用時。独自/apiのCIVI realmを直ちに違反としない。 | [server.py](../civi/server.py) |
| 23.10.1.3 / p.12 | LXI Security設定変更を提供した場合 | 適用外：LXI Security設定変更APIなし。 | [server.py](../civi/server.py) |
| 23.10.2 / p.12 | 追加LXI API認可を提供した場合 | 適用外：独自のLXI API認可方式は追加しない。 | [server.py](../civi/server.py) |
| 23.10.3 / p.12 | 証明書/CSR管理APIを提供した場合 | 適用外：証明書/CSRをGUID管理するAPIなし。 | [server.py](../civi/server.py) |
| 23.10.4.1 / p.13 | 識別APIに適用 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G04, G08 | [identification.py](../civi/identification.py)<br>[test_lxi_defaults.py](../tests/test_lxi_defaults.py) |
| 23.10.4.2 / p.13 | 識別APIに適用 | 実装確認：識別text/xml、schema/ProblemDetails application/xml、405 Allow、GET/HEADの内容と長さ、no-storeを確認。認証/HTTP例外/ProblemDetailsにも共通保護ヘッダーを統一。 | [server.py](../civi/server.py)<br>[lxi_api.py](../civi/lxi_api.py)<br>[test_lxi_defaults.py](../tests/test_lxi_defaults.py)<br>[WEB_API_REVIEW_2026-11-10.md](../docs/WEB_API_REVIEW_2026-11-10.md)<br>[test_web_api_review.py](../tests/test_web_api_review.py) |
| 23.10.4.3 / p.13 | 識別APIに適用 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G08 | [server.py](../civi/server.py)<br>[LXI_DEFAULTS_API.md](../docs/LXI_DEFAULTS_API.md)<br>[WEB_API_REVIEW_2026-11-10.md](../docs/WEB_API_REVIEW_2026-11-10.md)<br>[test_web_api_review.py](../tests/test_web_api_review.py)<br>[WEB_STATES_2026-11-10.md](../docs/WEB_STATES_2026-11-10.md)<br>[test_web_state_transitions.py](../tests/test_web_state_transitions.py) |
| 23.10.4.4 / p.13 | 識別APIに適用 | 実装確認：規定資源のエラーをProblemDetails application/xmlにする。 | [lxi_api.py](../civi/lxi_api.py)<br>[test_lxi_defaults.py](../tests/test_lxi_defaults.py) |
| 23.10.4.5 / p.14 | LXI APIで202/保留操作を返す場合 | 適用外：識別GETは同期読み取りで202を返さずユーザー操作を要求しない。独自IPv4試行APIは別。 | [server.py](../civi/server.py) |
| 23.10.4.5.1 / p.14 | LXI APIで202/保留操作を返す場合 | 適用外：識別GETは同期読み取りで202を返さずユーザー操作を要求しない。独自IPv4試行APIは別。 | [server.py](../civi/server.py) |
| 23.10.4.5.2 / p.14 | LXI APIで202/保留操作を返す場合 | 適用外：識別GETは同期読み取りで202を返さずユーザー操作を要求しない。独自IPv4試行APIは別。 | [server.py](../civi/server.py) |
| 23.10.6.1 / p.16 | 識別APIに適用 | 実装確認：識別専用の互換XSD経路も保持。 | [server.py](../civi/server.py)<br>[test_lxi_defaults.py](../tests/test_lxi_defaults.py) |
| 23.10.6.2 / p.16 | 識別APIに適用 | 実装確認：提供schema名/版をURLへ含める。 | [server.py](../civi/server.py)<br>[identification.py](../civi/identification.py) |
| 23.10.6.3 / p.16 | 識別APIに適用 | 実装確認：識別とProblemDetailsの規定XSD経路を提供し取得試験あり。 | [server.py](../civi/server.py)<br>[test_lxi_defaults.py](../tests/test_lxi_defaults.py) |
| 23.10.7 / p.17 | 識別APIに適用 | 実装確認：認証不要GET、text/xml、旧XSD aliasを試験。全識別内容は別行。 | [server.py](../civi/server.py)<br>[test_lxi.py](../tests/test_lxi.py)<br>[test_lxi_defaults.py](../tests/test_lxi_defaults.py) |
| 23.11.1.1/identity / p.23 | 識別APIに適用 | 実装確認：Manufacturer/Model/SerialNumber/FirmwareRevisionを順序どおり出力しXSD試験。 | [identification.py](../civi/identification.py)<br>[test_lxi.py](../tests/test_lxi.py) |
| 23.11.1.1-1 / p.24 | 識別APIに適用 | 実装確認：対象有線InterfaceだけをLXIとして出力。アドレス未取得でもInterfaceを保持。lo/WLANをLXI宣言しない。XSD試験済み。 本番PiのXMLでもeth0だけであることを確認済み。 | [identification.py](../civi/identification.py)<br>[test_lxi_fixes.py](../tests/test_lxi_fixes.py)<br>[IMPLEMENTATION_AND_TEST_RESULTS.md](../docs/IMPLEMENTATION_AND_TEST_RESULTS.md)<br>[RPI_LXI_FIXES_2026-11-10.md](../docs/RPI_LXI_FIXES_2026-11-10.md) |
| 23.11.1.1-2 / p.25 | LXI Event Messagingを実装した場合 | 適用外：LXI Event Messaging未採用、Domain不要。 | [identification.py](../civi/identification.py) |
| 23.11.1.1-3 / p.26 | 識別APIに適用 | [完了計画](IVI_6_1_COMPLETION_2026-11-12.md): G04 | [identification.py](../civi/identification.py)<br>[test_lxi.py](../tests/test_lxi.py) |
| 23.11.2-1 / p.26 | 識別APIに適用 | 実装確認：識別済み無線機のbaseURLをConnectedDevicesへ出力。 | [identification.py](../civi/identification.py)<br>[test_lxi.py](../tests/test_lxi.py) |
| 23.11.2.1-1 / p.26 | 識別APIに適用 | 実装確認：baseURL/lxi/identificationを提供。未識別時404、識別後200を試験。 | [server.py](../civi/server.py)<br>[test_lxi.py](../tests/test_lxi.py) |
| 23.11.2.1-2 / p.26 | 識別APIに適用 | 実装確認：子のschemaLocationに装置上の絶対XSD URLを含める。 | [identification.py](../civi/identification.py)<br>[test_lxi.py](../tests/test_lxi.py) |
| 23.11.3.1-1 / p.27 | 識別APIに適用 | 実装確認：InterfaceType=LXIを対象有線NICだけに限定し、複数NIC模擬入力で確認。 本番PiのXMLでもeth0だけであることを確認済み。 | [identification.py](../civi/identification.py)<br>[test_lxi_fixes.py](../tests/test_lxi_fixes.py)<br>[IMPLEMENTATION_AND_TEST_RESULTS.md](../docs/IMPLEMENTATION_AND_TEST_RESULTS.md)<br>[RPI_LXI_FIXES_2026-11-10.md](../docs/RPI_LXI_FIXES_2026-11-10.md) |
| 23.11.3.2 / p.27 | 識別APIに適用 | 実装確認：採用したIPv4項目の順序/表現をXSD試験。省略可能な項目を必須不足とはしない。 | [identification.py](../civi/identification.py)<br>[test_lxi.py](../tests/test_lxi.py) |
| 23.11.5.1 / p.29 | 任意Extensionを採用した場合 | 適用外：Extensionを出力しない。 | [identification.py](../civi/identification.py) |
| 23.11.6.1 / p.29 | 任意拡張を採用した場合 | 適用外：拡張を宣言しない。将来採用時は各拡張のFunction形式が必要。 | [identification.py](../civi/identification.py) |
| 23.11.7 / p.29 | Subinstrumentsを提供した場合 | 適用外：サブ機器の別制御チャネルを宣言しない。無線機はConnectedDevicesとして扱う。 | [identification.py](../civi/identification.py) |
| 23.18-1 / p.77 | 識別APIに適用 | 実装確認：40x応答をProblemDetailsに変換、405/404をXSD検証。 | [lxi_api.py](../civi/lxi_api.py)<br>[test_lxi_defaults.py](../tests/test_lxi_defaults.py) |
| 23.18.1.1-1 / p.77 | 識別APIに適用 | 実装確認：Titleを必ず出力する。 | [lxi_api.py](../civi/lxi_api.py)<br>[test_lxi_defaults.py](../tests/test_lxi_defaults.py) |
| 23.19-1 / p.77 | 保留応答を返す場合 | 適用外：識別GETで202を返さないのでPending XML不要。 | [server.py](../civi/server.py) |
