# LXI 1.6.2 全必須条項の照合 — 2026-11-10

**結論: 未達。LXI準拠・認証済みとは表示しない。**

[最新の優先順位・必須ゲート再判定](LXI_READINESS_2026-11-11.md)。
追加の信頼性試験と、規定の必須検証・登録手続きを区別する。

対象はPi 4のeth0をLXI用NICとする手動起動構成、付属画面とローカル入力手段、
ゲートウェイ0.1.0と独立クライアント0.13.1。WLANは管理経路として扱う計画。
初回は作業ツリーと既存記録の照合。その後、修正版を実Piへ反映し範囲付き実機確認を実施。

[確定した残件と完了条件](LXI_REMAINING_2026-11-10.md) · [機械可読データ](LXI_REQUIREMENTS_2026-11-10.json)

初回監査後の[4件の修正・模擬検証](LXI_FIXES_2026-11-10.md)を反映。
JSONのinitial_findings/initial_code_fingerprints/local_probesは初回監査の履歴で、
現在の判定はrowsとcode_fingerprints。反映/実機確認は明記された範囲だけに限定する。
[Pi反映と実機確認の続報](RPI_LXI_FIXES_2026-11-10.md)あり。未試験条件は合格扱いにしない。

## 数え方と判定

Device本文の現行RULE見出し **101件を全件収録**。
目次は除外し、本文の小条項まで採用。廃止RULE4件は別行。撤回Permission、
推奨節内の必須文、公式補足解釈8.14、識別APIから参照される要件、複合条項の
内訳を合わせて **175行**。親子行は重複集計のため達成率には使わない。

「実装確認」は記載したコード/限定的証拠の確認であり、規格全体の合格ではない。
「追加検証」は機能があっても条項全体の証拠が不足。「未達」は確認した差異/未完成。
「適用判定待ち」は装置構成やOS機能の採用範囲を確定しないと判定できない。
「手続待ち」は登録・許諾・最終宣言等。「適用外」には採用時の条件を残す。

実装確認: 97 | 廃止: 4 | 手続待ち: 6 | 未達: 7 | 追加検証: 26 | 適用外: 35

## 出典と再現性

ページ番号はPDFの1始まりのページ。条項原文を転載せず、CIVI側の観察・判断を記載。

- [Device](https://public.lxistandard.org/specifications/LXI_1.6_Specifications/LXI_Device_Specification_1.6.2_2026-04-02.pdf) — SHA-256 `97e65b8baf38a8aa9f57eec1c8cf7b0b35b74d33ee63dd046d01e1253775474b`
- [API](https://public.lxistandard.org/specifications/LXI_1.6_Specifications/LXI_API_Extended_Function_1.1_2025-03-10.pdf) — SHA-256 `7e9ca8fb33e9af13827ebe25986b79d1e1ea11185da2e4b4054e296c8cd2d8d0`
- [Interpretations](https://public.lxistandard.org/specifications/LXI_1.6_Specifications/LXI_Interpretations_and_Clarifications_for_LXI_Standard_1.6.1_2025-02-16.pdf) — SHA-256 `ee68abe3a10500e5ec576603459824259b7c76fa60278ee21d5f5b0c93f3ce19`

Deviceは1.6.2（表紙2026-04-04、URL名2026-04-02）。APIは1.1（2025-03-10）。
補足解釈は1.6.1向け2025-02-16版を1.6系列の補足として照合。
API全体・Security・IPv6・HiSLIP等をコア必須には拡大しない。イベント/同期も未採用。
ただし識別に関係するCommon Method/スキーマの必須意味要件は取り込む。
RFC/IEEE/IVI参照文書の全必須文をここだけで検証済みとはせず、各依存要件の
未確認を残件へ明記する。正式認証時は適用版と最新補足を再確認する。

```text
python tools/lxi_audit_check.py --check
python tools/lxi_audit_check.py --check --device-pdf <official-device-1.6.2.pdf>
```

通常チェックは行漏れ/重複/参照先と71コード・設定・テスト入力の内容ハッシュを検査。
PDF指定時はpypdfで本文を再抽出し101見出しと4廃止見出し・ページを再照合する。
これは条項の意味的正しさやハード動作を自動判定する仕組みではない。

## Device本文と条項内訳

| 条項 / PDF頁 | 適用条件 | 状態 | CIVIの証拠・判定 | 根拠ファイル | 残件 |
|---|---|---|---|---|---|
| 1.4.1 / p.10 | 必須 | 追加検証 | 本表でDevice/API/補足解釈を版固定。認証時の適用版・RFC/IVI参照版の確定が残る。 | [LXI.md](../docs/LXI.md) | G12 |
| 1.4.4.2 / p.14 | 必須 | 未達 | 全行の証拠を整理したが総合適合は未達。未採用拡張をコア必須に追加しない。 | [LXI.md](../docs/LXI.md) | G12 |
| 1.4.4.2.1 / p.14 | 必須 | 未達 | Deviceの残件とIVI従属要件の最終確認が残る。 | [AUDIT.md](../drivers/civi-ic7300/src/civi_ic7300/AUDIT.md) | G10, G12 |
| 1.4.5 / p.14 | 必須 | 手続待ち | 未適合表示を維持。完了後に資料上の機能宣言を整える。 | [identification.py](../civi/identification.py)<br>[LXI.md](../docs/LXI.md) | G11 |
| 1.4.6 / p.14 | 必須 | 手続待ち | WebにLXI版を宣言していない。完成前に数値を入れない。 | [identification.py](../civi/identification.py) | G11 |
| 1.4.7 / p.15 | 必須 | 手続待ち | 用語/商標表示を最終公開時に点検。ロゴは未使用。 | [identification.py](../civi/identification.py)<br>[LXI.md](../docs/LXI.md) | G11 |
| 2.4.5.1 / p.16 | 必須 | 実装確認 | ローカルLAN RESETの機構と初期化・実機復旧を確認。条項が規定する機構は実装済み。 | [lci.py](../civi/pi/lci.py)<br>[RPI_LCI_BOOT_2026-11-08.md](../docs/RPI_LCI_BOOT_2026-11-08.md)<br>[LXI_READINESS_2026-11-11.md](../docs/LXI_READINESS_2026-11-11.md) | — |
| 2.4.5.2 / p.16 | 必須 | 実装確認 | 付属画面とローカル入力を恒久的な装置構成に固定。LAN非依存のLCI実機証拠あり。この構成以外へ適合判断を広げない。 | [RPI_LAN_RESET.md](../docs/RPI_LAN_RESET.md)<br>[RPI_DESKTOP.md](../docs/RPI_DESKTOP.md)<br>[LXI_READINESS_2026-11-11.md](../docs/LXI_READINESS_2026-11-11.md) | — |
| 2.4.5.3 / p.17 | 必須 | 実装確認 | LAN RESET文字列による本体確認を要求する。 | [lci.py](../civi/pi/lci.py)<br>[RPI_LAN_RESET.md](../docs/RPI_LAN_RESET.md) | — |
| 2.4.9.1 / p.17 | 必須 | 追加検証 | Pi 4のEthernet/RJ45で通信済み。採用ハードの仕様・電気条件を製品構成へ固定。 | [RPI_ETHERNET_2026-11-08.md](../docs/RPI_ETHERNET_2026-11-08.md) | G09 |
| 2.5.1.1 / p.19 | 必須 | 実装確認 | 付属本体画面を装置前面表示として固定し、POWER ONを追加。2026-11-11にユーザーが緑色POWER ONとLAN状態の表示を目視受入。 | [panel.py](../civi/pi/panel.py)<br>[RPI_PANEL.md](../docs/RPI_PANEL.md)<br>[LXI_DEVICE_CONFIGURATION.md](../docs/LXI_DEVICE_CONFIGURATION.md)<br>[LXI_READINESS_2026-11-11.md](../docs/LXI_READINESS_2026-11-11.md) | — |
| 2.5.2.1 / p.20 | 必須 | 実装確認 | 本体パネルを必須構成に固定。Normal/Fault/Identifyを実機確認。RJ45のリンクLEDとは区別。 | [indicator.py](../civi/indicator.py)<br>[RPI_PANEL_2026-11-07.md](../docs/RPI_PANEL_2026-11-07.md)<br>[LXI_READINESS_2026-11-11.md](../docs/LXI_READINESS_2026-11-11.md) | — |
| 2.6.1.1 / p.22 | 必須 | 手続待ち | 本体ロゴなし。使用許諾/認証経路確定後に電子表示等を整える。 | [panel.py](../civi/pi/panel.py) | G11 |
| 3.5.1 / p.24 | イベント/同期機能を実装した場合 | 適用外 | LXIイベントによる実行機構なし。通常のSCPI設定はLXI Eventではない。 | [LXI.md](../docs/LXI.md) | — |
| 3.5.1.3 / p.25 | イベント/同期機能を実装した場合 | 適用外 | LXIイベントで起動する測定機能なし。イベント応答時間仕様は対象外。 | [LXI.md](../docs/LXI.md) | — |
| 3.5.2.1 / p.27 | イベント/同期機能を実装した場合 | 適用外 | LXIイベント送出/トリガー出力を実装しない。 | [LXI.md](../docs/LXI.md) | — |
| 3.7 / p.27 | イベント/同期機能を実装した場合 | 適用外 | LXIイベントの生成/処理なし。通常の通信ログとは区別。 | [LXI.md](../docs/LXI.md) | — |
| 6.1 / p.31 | 必須 | 未達 | Python 0.13.1で実機Core/受信40チェック、受信設定16項目65チェック、216メニュー含む290成功読取を追加。MAIN1.41未対応の16 66とAM依存、NR/PBT丸めを区別。全API規定検証・正式名/登録は未完了。 MAIN1.42への更新後、16 66のON/OFF読戻し・不正型・復元の5項目を追加確認。他APIの1.41証拠とは区別。 2026-11-12: 352行を全件照合し、根拠未対応204行を分類した。旧SCPI189メニュー書込みと現行typed経路、getter/setter、ローカル処理を区別。未分類0は全試験完了ではなく、追加試験IDを確定した。 | [AUDIT.md](../drivers/civi-ic7300/src/civi_ic7300/AUDIT.md)<br>[COMPLIANCE.md](../drivers/civi-ic7300/src/civi_ic7300/COMPLIANCE.md)<br>[IVI_RECEIVE_ACCEPTANCE_2026-11-11.md](../docs/IVI_RECEIVE_ACCEPTANCE_2026-11-11.md)<br>[IVI_VERIFICATION_WORKLIST_2026-11-11.csv](../docs/IVI_VERIFICATION_WORKLIST_2026-11-11.csv)<br>[IVI_TX_INHIBIT_2026-11-11.md](../docs/IVI_TX_INHIBIT_2026-11-11.md)<br>[IVI_ADDITIONAL_TESTS_2026-11-12.md](../docs/IVI_ADDITIONAL_TESTS_2026-11-12.md)<br>[IVI_VERIFICATION_RECONCILED_2026-11-12.json](../docs/IVI_VERIFICATION_RECONCILED_2026-11-12.json)<br>[IVI_MENU_VERIFICATION_2026-11-12.csv](../docs/IVI_MENU_VERIFICATION_2026-11-12.csv) | G01, G10 |
| 6.1.1 / p.31 | イベント/同期機能を実装した場合 | 適用外 | IviLxiSyncを要する同期/イベント拡張なし。 | [LXI.md](../docs/LXI.md) | — |
| 6.2 / p.32 | 必須 | 実装確認 | 0.13.1で位置指定を修正。導入済みWindowsドライバーからINSTR/省略形/HiSLIP位置指定で実Pi・IC-7300を読取。通信はraw TCP。 | [driver.py](../drivers/civi-ic7300/src/civi_ic7300/driver.py)<br>[test_python_driver.py](../tests/test_python_driver.py)<br>[test_lxi_fixes.py](../tests/test_lxi_fixes.py)<br>[LXI_FIXES_2026-11-10.md](../docs/LXI_FIXES_2026-11-10.md)<br>[RPI_LXI_FIXES_2026-11-10.md](../docs/RPI_LXI_FIXES_2026-11-10.md) | — |
| 6.3 / p.34 | イベント/同期機能を実装した場合 | 適用外 | LXIイベント/有線トリガー入力のSource APIなし。 | [LXI.md](../docs/LXI.md) | — |
| 6.4 / p.34 | イベント/同期機能を実装した場合 | 適用外 | LXIイベント用Arm/Trigger機構なし。無線機のスキャンとは区別。 | [LXI.md](../docs/LXI.md) | — |
| 6.4.2 / p.34 | イベント/同期機能を実装した場合 | 適用外 | LXIイベント/有線トリガーへのルーティングなし。 | [LXI.md](../docs/LXI.md) | — |
| 6.4.3 / p.34 | イベント/同期機能を実装した場合 | 適用外 | LXIイベントパケットを送出しない。 | [LXI.md](../docs/LXI.md) | — |
| 6.4.4 / p.35 | イベント/同期機能を実装した場合 | 適用外 | LXIイベント信号名を実装しない。 | [LXI.md](../docs/LXI.md) | — |
| 6.4.4.1 / p.38 | イベント/同期機能を実装した場合 | 適用外 | Arm/Trigger信号を公開しない。 | [LXI.md](../docs/LXI.md) | — |
| 6.4.4.2 / p.38 | イベント/同期機能を実装した場合 | 適用外 | 対応イベント信号なしと本表に明記。 | [LXI.md](../docs/LXI.md) | — |
| 6.4.5 / p.38 | イベント/同期機能を実装した場合 | 適用外 | LXI予約イベント名をベンダー信号に使用しない。 | [LXI.md](../docs/LXI.md) | — |
| 6.4.6 / p.38 | イベント/同期機能を実装した場合 | 適用外 | LXIイベント宛先パスを使用しない。 | [LXI.md](../docs/LXI.md) | — |
| 6.5 / p.39 | イベント/同期機能を実装した場合 | 適用外 | IEEE 1588時刻/タイムスタンプ/アラームをAPI公開しない。無線機の時計設定とは別。 | [LXI.md](../docs/LXI.md) | — |
| 6.5.1 / p.39 | Deprecated | 廃止 | 現行必須の不足には数えない。後継条項を本表で追跡。 | [LXI.md](../docs/LXI.md) | — |
| 6.5.2 / p.39 | Deprecated | 廃止 | 現行必須の不足には数えない。後継条項を本表で追跡。 | [LXI.md](../docs/LXI.md) | — |
| 6.6 / p.39 | イベント/同期機能を実装した場合 | 適用外 | LXIイベントのドメイン機能なし。 | [LXI.md](../docs/LXI.md) | — |
| 7.1 / p.41 | 必須 | 実装確認 | 実Piで100/1000 Mb/s通信を確認。 | [RPI_ETHERNET_2026-11-08.md](../docs/RPI_ETHERNET_2026-11-08.md) | — |
| 7.1.2 / p.41 | 必須 | 実装確認 | 物理100Mbps Full/HalfでSCPI/証明書検証HTTPSを確認し、1000Mbps Full自動交渉へ復元。10Mbps全条件の実測は主張しない。 | [RPI_ETHERNET_2026-11-08.md](../docs/RPI_ETHERNET_2026-11-08.md)<br>[LXI_READINESS_2026-11-11.md](../docs/LXI_READINESS_2026-11-11.md) | — |
| 7.2 / p.41 | 必須 | 実装確認 | 対象有線MACを本体/Webに表示。公開写真のマスクは実機表示と別。 | [identification.py](../civi/identification.py)<br>[RPI_PANEL_2026-11-07.md](../docs/RPI_PANEL_2026-11-07.md) | — |
| 7.3 / p.42 | 必須 | 追加検証 | リンク切断/復帰と固定IP復帰を実機確認。再接続時の重複チェックは経路別に追試。 | [indicator.py](../civi/indicator.py)<br>[RPI_UNPLUGGED_BOOT_2026-11-08.md](../docs/RPI_UNPLUGGED_BOOT_2026-11-08.md) | G05 |
| 7.5 / p.42 | Auto-MDIX非対応の場合 | 適用外 | 標準Pi 4/BCM54213PEの製品情報にあるMDIクロス配線の検出・補正をAuto-MDIX対応の根拠とする。非対応機向けの物理ラベルは当該構成では不要。新たなケーブル実測を主張せず、別NIC採用時は再評価。 | [RPI_ETHERNET_2026-11-08.md](../docs/RPI_ETHERNET_2026-11-08.md)<br>[LXI_DEVICE_CONFIGURATION.md](../docs/LXI_DEVICE_CONFIGURATION.md) | — |
| 7.6 / p.43 | 必須 | 実装確認 | 見出しRULEだが本文should。保存値と再起動後の自動交渉onを実機確認。 | [RPI_ETHERNET_2026-11-08.md](../docs/RPI_ETHERNET_2026-11-08.md) | — |
| 7.7 / p.43 | 必須 | 実装確認 | Piへ反映。実識別XMLはeth0だけ。4サービスを有線で新規取得しWLANでは未取得、WLANのIP管理HTTPSは維持。 | [identification.py](../civi/identification.py)<br>[network.py](../civi/network.py)<br>[config.pi.example.toml](../config.pi.example.toml)<br>[test_lxi_fixes.py](../tests/test_lxi_fixes.py)<br>[LXI_FIXES_2026-11-10.md](../docs/LXI_FIXES_2026-11-10.md)<br>[RPI_LXI_FIXES_2026-11-10.md](../docs/RPI_LXI_FIXES_2026-11-10.md) | — |
| 8.1 / p.45 | 必須 | 実装確認 | Linux TCP/UDP/IPv4を利用。実機HTTPS/SCPI/mDNS通信証拠あり。 | [__main__.py](../civi/__main__.py)<br>[RPI_AUTOIP_TCP_2026-11-08.md](../docs/RPI_AUTOIP_TCP_2026-11-08.md) | — |
| 8.2 / p.45 | 必須 | 実装確認 | 有線/WLANのPing応答を確認。 | [ping.py](../civi/pi/ping.py)<br>[RPI_PING.md](../docs/RPI_PING.md)<br>[test_ping_control.py](../tests/test_ping_control.py) | — |
| 8.3 / p.45 | 必須 | 実装確認 | 既定有効とLCI再有効化を実装・確認。 | [ping.py](../civi/pi/ping.py)<br>[RPI_PING.md](../docs/RPI_PING.md)<br>[test_ping_control.py](../tests/test_ping_control.py) | — |
| 8.4 / p.45 | 必須 | 実装確認 | Web無効化/保存/再起動保持/復帰を実機確認。 | [ping.py](../civi/pi/ping.py)<br>[RPI_PING.md](../docs/RPI_PING.md)<br>[test_ping_control.py](../tests/test_ping_control.py) | — |
| 8.6 / p.46 | 必須 | 追加検証 | DHCP確定保存後の実Pi再起動・新起動ID/ACK/アドレス取得を追加確認。固定IPからのLCIでも新規取得。リンク再接続/物理重複/特殊オプション等は継続。 | [network.py](../civi/pi/network.py)<br>[DHCP_2026-11-08.md](../docs/DHCP_2026-11-08.md)<br>[RPI_DHCP_ETHERNET_2026-11-10.md](../docs/RPI_DHCP_ETHERNET_2026-11-10.md)<br>[test_applied_ipv4.py](../tests/test_applied_ipv4.py)<br>[RPI_DHCP_BOOT_2026-11-11.md](../docs/RPI_DHCP_BOOT_2026-11-11.md) | G05 |
| 8.6.1 / p.47 | 必須 | 実装確認 | Automatic(DHCP+AutoIP)とManualを提供。物理/隔離Piの取得・保存・再起動・LCI記録あり。全組合せを合格と主張しない。 | [network.py](../civi/pi/network.py)<br>[DHCP_2026-11-08.md](../docs/DHCP_2026-11-08.md)<br>[RPI_DHCP_ETHERNET_2026-11-10.md](../docs/RPI_DHCP_ETHERNET_2026-11-10.md)<br>[test_applied_ipv4.py](../tests/test_applied_ipv4.py)<br>[RPI_DHCP_BOOT_2026-11-11.md](../docs/RPI_DHCP_BOOT_2026-11-11.md)<br>[LXI_READINESS_2026-11-11.md](../docs/LXI_READINESS_2026-11-11.md) | — |
| 8.6.3 / p.47 | 必須 | 実装確認 | 使用するIP設定パラメーター1/3/6を実eth0の要求リストで確認。OSの全任意オプションの網羅試験を追加必須にはしない。 | [DHCP_2026-11-08.md](../docs/DHCP_2026-11-08.md)<br>[RPI_DHCP_ETHERNET_2026-11-10.md](../docs/RPI_DHCP_ETHERNET_2026-11-10.md)<br>[test_applied_ipv4.py](../tests/test_applied_ipv4.py)<br>[LXI_READINESS_2026-11-11.md](../docs/LXI_READINESS_2026-11-11.md) | — |
| 8.6.5 / p.47 | 必須 | 実装確認 | gateway/DNS省略の実ACKでも取得・Normal、異なるhostname optionでシステム名維持を確認。追加オプションに動作を依存させない。 | [DHCP_2026-11-08.md](../docs/DHCP_2026-11-08.md)<br>[RPI_DHCP_ETHERNET_2026-11-10.md](../docs/RPI_DHCP_ETHERNET_2026-11-10.md)<br>[test_applied_ipv4.py](../tests/test_applied_ipv4.py)<br>[LXI_READINESS_2026-11-11.md](../docs/LXI_READINESS_2026-11-11.md) | — |
| 8.6.6 / p.48 | 必須 | 実装確認 | 実eth0でリース失効時のアドレス/gateway/DNS破棄、AutoIP移行とFault保持を確認。本体表示の共通ロジックは試験済み。 | [DHCP_2026-11-08.md](../docs/DHCP_2026-11-08.md)<br>[indicator.py](../civi/indicator.py)<br>[test_indicator.py](../tests/test_indicator.py)<br>[RPI_DHCP_ETHERNET_2026-11-10.md](../docs/RPI_DHCP_ETHERNET_2026-11-10.md)<br>[test_applied_ipv4.py](../tests/test_applied_ipv4.py)<br>[LXI_READINESS_2026-11-11.md](../docs/LXI_READINESS_2026-11-11.md) | — |
| 8.6.7 / p.48 | 必須 | 実装確認 | 実eth0の自然更新ACKでgateway/DNS変更と実効OS設定への反映を確認。保存/再起動は別の既存記録で確認。 | [DHCP_2026-11-08.md](../docs/DHCP_2026-11-08.md)<br>[RPI_DHCP_ETHERNET_2026-11-10.md](../docs/RPI_DHCP_ETHERNET_2026-11-10.md)<br>[test_applied_ipv4.py](../tests/test_applied_ipv4.py)<br>[LXI_READINESS_2026-11-11.md](../docs/LXI_READINESS_2026-11-11.md) | — |
| 8.6.10 / p.49 | 必須 | 追加検証 | AutoIPと固定アドレスPC間の実TCP往復を確認。RFC3927 2.6.2の送信元/ARP/転送全条件は未完。 | [linklocal.py](../civi/pi/linklocal.py)<br>[RPI_AUTOIP_TCP_2026-11-08.md](../docs/RPI_AUTOIP_TCP_2026-11-08.md) | G05 |
| 8.7 / p.50 | 必須 | 実装確認 | 隔離Piの実NetworkManager/ARP/DHCPで開始前重複拒否、使用中切断とFaultを確認。物理NICの全経路組合せは追加信頼性試験として区別。 | [conflict.py](../civi/pi/conflict.py)<br>[RPI_CONFLICT.md](../docs/RPI_CONFLICT.md)<br>[LXI_READINESS_2026-11-11.md](../docs/LXI_READINESS_2026-11-11.md) | — |
| 8.9/legal-name / p.51 | 本文の必須文 | 実装確認 | 推奨節内のshallも追跡。共通既定名はDNSラベルとして検証。 | [network.py](../civi/pi/network.py)<br>[defaults.py](../civi/defaults.py) | — |
| 8.10 / p.51 | 必須 | 実装確認 | DHCP失効後のFault保持と新リースのNormal復帰を実eth0で確認。本体状態遷移とFault優先は共通ロジック・既存実機記録で確認。 | [indicator.py](../civi/indicator.py)<br>[test_indicator.py](../tests/test_indicator.py)<br>[DHCP_2026-11-08.md](../docs/DHCP_2026-11-08.md)<br>[RPI_DHCP_ETHERNET_2026-11-10.md](../docs/RPI_DHCP_ETHERNET_2026-11-10.md)<br>[test_applied_ipv4.py](../tests/test_applied_ipv4.py)<br>[LXI_READINESS_2026-11-11.md](../docs/LXI_READINESS_2026-11-11.md) | — |
| 8.10/initial-autoip / p.51 | 親条項の内訳 | 実装確認 | 初回DHCP不在からAutoIP取得時はNormalを単体/実機で確認。 | [indicator.py](../civi/indicator.py)<br>[test_indicator.py](../tests/test_indicator.py)<br>[RPI_LCI_BOOT_2026-11-08.md](../docs/RPI_LCI_BOOT_2026-11-08.md) | — |
| 8.10/expired-autoip / p.52 | 親条項の内訳 | 追加検証 | 実eth0の期限切れ→AutoIP/Fault保持→新リース/Normalを確認。固定IPロールバックでもNormalに復帰。起動/LCI等の解除経路と本体目視の残条件は継続。 | [indicator.py](../civi/indicator.py)<br>[test_indicator.py](../tests/test_indicator.py)<br>[DHCP_2026-11-08.md](../docs/DHCP_2026-11-08.md)<br>[RPI_DHCP_ETHERNET_2026-11-10.md](../docs/RPI_DHCP_ETHERNET_2026-11-10.md)<br>[test_applied_ipv4.py](../tests/test_applied_ipv4.py) | G05 |
| 8.10/identify-fault / p.52 | 親条項の状態遷移図 | 実装確認 | 実PiでIdentify中に有線を抜きFault優先・Identify解除・本体ACKを確認。再接続でNormal/Identify OFF、利用者の再開始/停止も確認。DHCP失効等は別行。 | [panel.py](../civi/pi/panel.py)<br>[indicator.py](../civi/indicator.py)<br>[indicator.js](../civi/static/indicator.js)<br>[test_indicator.py](../tests/test_indicator.py)<br>[test_lxi_fixes.py](../tests/test_lxi_fixes.py)<br>[LXI_FIXES_2026-11-10.md](../docs/LXI_FIXES_2026-11-10.md)<br>[RPI_LXI_FIXES_2026-11-10.md](../docs/RPI_LXI_FIXES_2026-11-10.md) | — |
| 8.11.1.1 / p.54 | DDNS無効化を提供する場合 | 適用外 | RFC2136 DDNS UpdateとユーザーDDNS制御は採用しない。mDNS制御と区別。OSのDHCP hostname/server-side登録はCIVI DDNS機能とは宣言しない。採用時に再評価。 | [network.py](../civi/pi/network.py)<br>[LXI_AUDIT_2026-11-07.md](../docs/LXI_AUDIT_2026-11-07.md)<br>[LXI_DEVICE_CONFIGURATION.md](../docs/LXI_DEVICE_CONFIGURATION.md) | — |
| 8.13 / p.55 | 必須 | 追加検証 | 固定IP→ローカルLCIでDHCP新規取得、復旧世代更新、稼働中の認証/発見設定反映を確認。既にDHCPのLCIでは有効リースを継続。DDNS採用範囲等は継続。 | [lci.py](../civi/pi/lci.py)<br>[transactions.py](../civi/pi/transactions.py)<br>[RPI_LCI_BOOT_2026-11-08.md](../docs/RPI_LCI_BOOT_2026-11-08.md)<br>[RPI_DHCP_BOOT_2026-11-11.md](../docs/RPI_DHCP_BOOT_2026-11-11.md) | G05, G07 |
| 8.13/dhcp / p.55 | 親条項の内訳 | 実装確認 | 固定IP→ローカルLCIでsaved auto、手動IP除去、新規DHCP ACKと192.168.73.3取得を実機確認。 | [lci.py](../civi/pi/lci.py)<br>[transactions.py](../civi/pi/transactions.py)<br>[RPI_LCI_BOOT_2026-11-08.md](../docs/RPI_LCI_BOOT_2026-11-08.md)<br>[RPI_DHCP_BOOT_2026-11-11.md](../docs/RPI_DHCP_BOOT_2026-11-11.md) | — |
| 8.13/autoip / p.55 | 親条項の内訳 | 実装確認 | AutoIPを有効化する。 | [lci.py](../civi/pi/lci.py)<br>[transactions.py](../civi/pi/transactions.py)<br>[RPI_LCI_BOOT_2026-11-08.md](../docs/RPI_LCI_BOOT_2026-11-08.md) | — |
| 8.13/ping / p.55 | 親条項の内訳 | 実装確認 | Pingを再有効化する。 | [lci.py](../civi/pi/lci.py)<br>[transactions.py](../civi/pi/transactions.py)<br>[RPI_LCI_BOOT_2026-11-08.md](../docs/RPI_LCI_BOOT_2026-11-08.md) | — |
| 8.13/password / p.55 | 親条項の内訳 | 実装確認 | ローカル表示の復旧用パスワードへの切替とライブ反映世代を確認。Pi内だけで保護Web GET認証200を確認。パスワードは収集/出力しない。 | [lci.py](../civi/pi/lci.py)<br>[transactions.py](../civi/pi/transactions.py)<br>[RPI_LCI_BOOT_2026-11-08.md](../docs/RPI_LCI_BOOT_2026-11-08.md)<br>[RPI_DHCP_BOOT_2026-11-11.md](../docs/RPI_DHCP_BOOT_2026-11-11.md) | — |
| 8.13/mdns / p.55 | 親条項の内訳 | 実装確認 | mDNS/DNS-SDを再有効化する。 | [lci.py](../civi/pi/lci.py)<br>[transactions.py](../civi/pi/transactions.py)<br>[RPI_LCI_BOOT_2026-11-08.md](../docs/RPI_LCI_BOOT_2026-11-08.md) | — |
| 8.13/ddns / p.55 | 親条項の内訳 | 適用外 | RFC2136 DDNS UpdateとユーザーDDNS制御は採用しない。mDNS制御と区別。OSのDHCP hostname/server-side登録はCIVI DDNS機能とは宣言しない。採用時に再評価。 | [network.py](../civi/pi/network.py)<br>[LXI_DEVICE_CONFIGURATION.md](../docs/LXI_DEVICE_CONFIGURATION.md) | — |
| 8.13/activation / p.55 | 親条項の内訳 | 追加検証 | 実行中CIVIでローカルLCIの新世代反映とDHCP取得/Normalを確認。全初期化経路の残条件はG05で継続。 | [lci.py](../civi/pi/lci.py)<br>[RPI_LCI_BOOT_2026-11-08.md](../docs/RPI_LCI_BOOT_2026-11-08.md)<br>[RPI_DHCP_BOOT_2026-11-11.md](../docs/RPI_DHCP_BOOT_2026-11-11.md) | G05 |
| 8.13/documentation / p.55 | 親条項の内訳 | 実装確認 | LCIの変更項目と復旧認証をローカル文書に記載。 | [RPI_LAN_RESET.md](../docs/RPI_LAN_RESET.md) | — |
| 9.1 / p.57 | 必須 | 追加検証 | HTTP1.1/TLS1.2/1.3を実機確認。HTML5構文確認済み。WindowsとスマホChromeの表示はユーザー確認済み。各ブラウザーの設定操作/異常状態確認は残る。 未接続/隔離/状態取得失敗/復帰、LAN試行期限切れとhelper停止時を実JS・模擬HTTPで追加確認。実ブラウザーの異常状態表示と完成構成での判定は残る。 更新後の切断時受信値消去とLAN確定の期限切れ/状態取得失敗時の無効化はユーザー実機確認済み。 | [server.py](../civi/server.py)<br>[RPI_HTTPS_2026-11-07.md](../docs/RPI_HTTPS_2026-11-07.md)<br>[WEB_API_REVIEW_2026-11-10.md](../docs/WEB_API_REVIEW_2026-11-10.md)<br>[test_web_api_review.py](../tests/test_web_api_review.py)<br>[WEB_STATES_2026-11-10.md](../docs/WEB_STATES_2026-11-10.md)<br>[test_web_state_transitions.py](../tests/test_web_state_transitions.py) | G08 |
| 9.1.1 / p.57 | Deprecated | 廃止 | 現行必須の不足には数えない。後継条項を本表で追跡。 | [LXI.md](../docs/LXI.md) | — |
| 9.1.4 / p.57 | 必須 | 実装確認 | Pi既定443。実Piで443/8443を確認。Windows8443構成は本表のLXI装置対象外。 | [config.pi.example.toml](../config.pi.example.toml)<br>[RPI_HTTPS_2026-11-07.md](../docs/RPI_HTTPS_2026-11-07.md) | — |
| 9.1.7 / p.58 | 必須 | 実装確認 | /lxiと/lxi/を公開。 | [test_lxi.py](../tests/test_lxi.py)<br>[server.py](../civi/server.py) | — |
| 9.2 / p.58 | 必須 | 未達 | NIC宣言のコード差異は修正。識別/版/アドレスは表示するがLXI版はNot claimedで、正式宣言が残る。 | [identification.py](../civi/identification.py) | G04 |
| 9.2/model / p.58 | 親条項の内訳 | 実装確認 | Web識別情報の該当値をコード/HTML試験で確認。 | [identification.py](../civi/identification.py)<br>[test_lxi.py](../tests/test_lxi.py) | — |
| 9.2/manufacturer / p.58 | 親条項の内訳 | 実装確認 | Web識別情報の該当値をコード/HTML試験で確認。 | [identification.py](../civi/identification.py)<br>[test_lxi.py](../tests/test_lxi.py) | — |
| 9.2/serial / p.58 | 親条項の内訳 | 実装確認 | Web識別情報の該当値をコード/HTML試験で確認。 | [identification.py](../civi/identification.py)<br>[test_lxi.py](../tests/test_lxi.py) | — |
| 9.2/description / p.58 | 親条項の内訳 | 実装確認 | Web識別情報の該当値をコード/HTML試験で確認。 | [identification.py](../civi/identification.py)<br>[test_lxi.py](../tests/test_lxi.py) | — |
| 9.2/software / p.59 | 親条項の内訳 | 実装確認 | Web識別情報の該当値をコード/HTML試験で確認。 | [identification.py](../civi/identification.py)<br>[test_lxi.py](../tests/test_lxi.py) | — |
| 9.2/visa / p.59 | 親条項の内訳 | 実装確認 | Web識別情報の該当値をコード/HTML試験で確認。 | [identification.py](../civi/identification.py)<br>[test_lxi.py](../tests/test_lxi.py) | — |
| 9.2/lxi-version / p.58 | 親条項の内訳 | 未達 | 未適合表示を維持し、最終適合判定後に正しい版を宣言。 | [identification.py](../civi/identification.py) | G04 |
| 9.2/extensions / p.58 | 親条項の内訳 | 実装確認 | 未採用拡張を宣言しない。 | [identification.py](../civi/identification.py) | — |
| 9.2/hostname / p.58 | 親条項の内訳 | 追加検証 | mDNS FQDN/IP代替とOS情報の表示上の役割を最終確認。 | [identification.py](../civi/identification.py)<br>[MDNS_HOSTNAME_2026-11-08.md](../docs/MDNS_HOSTNAME_2026-11-08.md) | G08 |
| 9.2/mac-ip / p.58 | 親条項の内訳 | 実装確認 | Piの対象有線NICをLXI扱い、他NICは管理用として明記。IP未割当の対象NICもWebに表示。 本番PiのXMLでもeth0だけであることを確認済み。 | [identification.py](../civi/identification.py)<br>[test_lxi_fixes.py](../tests/test_lxi_fixes.py)<br>[LXI_FIXES_2026-11-10.md](../docs/LXI_FIXES_2026-11-10.md)<br>[RPI_LXI_FIXES_2026-11-10.md](../docs/RPI_LXI_FIXES_2026-11-10.md) | — |
| 9.2.1 / p.59 | 必須 | 実装確認 | 表示SOCKETアドレスにboard番号を付けない。 | [test_lxi.py](../tests/test_lxi.py)<br>[identification.py](../civi/identification.py) | — |
| 9.2.3 / p.59 | 必須 | 実装確認 | Hostname欄は有効・成功した広告済みmDNS名だけを表示。広告なし/無効/失敗時は対象NICのIPv4またはNot assigned。OS設定名を別欄とし、模擬Webで全条件を確認。 | [identification.py](../civi/identification.py)<br>[discovery.py](../civi/pi/discovery.py)<br>[MDNS_HOSTNAME_2026-11-08.md](../docs/MDNS_HOSTNAME_2026-11-08.md)<br>[WEB_API_REVIEW_2026-11-10.md](../docs/WEB_API_REVIEW_2026-11-10.md)<br>[test_web_api_review.py](../tests/test_web_api_review.py) | — |
| 9.2.3.2 / p.60 | 必須 | 実装確認 | mDNS停止/失敗/未登録時はHostname欄を対象NICのIP代替とし、未検証のOS名を実ホスト名として出さない。模擬応答確認。 | [identification.py](../civi/identification.py)<br>[test_lxi.py](../tests/test_lxi.py)<br>[WEB_API_REVIEW_2026-11-10.md](../docs/WEB_API_REVIEW_2026-11-10.md)<br>[test_web_api_review.py](../tests/test_web_api_review.py) | — |
| 9.2.3.3 / p.61 | 必須 | 実装確認 | 取得mDNS名は.local.形式で表示し、実Avahi/Webで確認。 | [discovery.py](../civi/pi/discovery.py)<br>[MDNS_HOSTNAME_2026-11-08.md](../docs/MDNS_HOSTNAME_2026-11-08.md) | — |
| 9.2.3.5 / p.61 | 必須 | 実装確認 | Descriptionは取得済みサービス名を優先して表示。 | [identification.py](../civi/identification.py)<br>[MDNS_HOSTNAME_2026-11-08.md](../docs/MDNS_HOSTNAME_2026-11-08.md) | — |
| 9.3 / p.61 | 必須 | 実装確認 | 認証付きWeb Start/Stopと本体の継続Identifyを実機確認。 | [test_indicator.py](../tests/test_indicator.py)<br>[RPI_PANEL_2026-11-07.md](../docs/RPI_PANEL_2026-11-07.md) | — |
| 9.4 / p.61 | 必須 | 実装確認 | WelcomeからLAN設定へのリンクあり。同期機能を採用しないのでSyncリンクは不要。 | [identification.py](../civi/identification.py)<br>[test_lxi.py](../tests/test_lxi.py) | — |
| 9.5 / p.62 | 必須 | 追加検証 | hostname/description/mode/IP/prefix/gateway/DNSの入力あり。prefixがsubnet maskに対応する説明と全保存条件を確認。 | [identification.py](../civi/identification.py)<br>[network.py](../civi/pi/network.py)<br>[RPI_LAN_SETTINGS.md](../docs/RPI_LAN_SETTINGS.md) | G05, G08 |
| 9.5/hostname / p.62 | 親条項の内訳 | 追加検証 | 入力と保存経路あり。実NICで変更/読取/再起動保持の組合せを確認。 | [identification.py](../civi/identification.py)<br>[network.py](../civi/pi/network.py)<br>[RPI_LAN_SETTINGS.md](../docs/RPI_LAN_SETTINGS.md) | G05 |
| 9.5/description / p.62 | 親条項の内訳 | 追加検証 | 入力と保存経路あり。実NICで変更/読取/再起動保持の組合せを確認。 | [identification.py](../civi/identification.py)<br>[network.py](../civi/pi/network.py)<br>[RPI_LAN_SETTINGS.md](../docs/RPI_LAN_SETTINGS.md) | G05 |
| 9.5/mode / p.62 | 親条項の内訳 | 実装確認 | 実eth0でDHCPモードを確定保存し、Pi本体再起動後の保存auto・DHCP取得を確認。元の保存static設定にも一致するよう復元。初期起動時のstaticと合わせ保存モード保持を確認。 | [identification.py](../civi/identification.py)<br>[network.py](../civi/pi/network.py)<br>[RPI_LAN_SETTINGS.md](../docs/RPI_LAN_SETTINGS.md)<br>[RPI_DHCP_BOOT_2026-11-11.md](../docs/RPI_DHCP_BOOT_2026-11-11.md) | — |
| 9.5/address / p.62 | 親条項の内訳 | 追加検証 | 入力と保存経路あり。実NICで変更/読取/再起動保持の組合せを確認。 | [identification.py](../civi/identification.py)<br>[network.py](../civi/pi/network.py)<br>[RPI_LAN_SETTINGS.md](../docs/RPI_LAN_SETTINGS.md) | G05 |
| 9.5/gateway / p.62 | 親条項の内訳 | 追加検証 | 入力と保存経路あり。実NICで変更/読取/再起動保持の組合せを確認。 | [identification.py](../civi/identification.py)<br>[network.py](../civi/pi/network.py)<br>[RPI_LAN_SETTINGS.md](../docs/RPI_LAN_SETTINGS.md) | G05 |
| 9.5/dns / p.62 | 親条項の内訳 | 追加検証 | 入力と保存経路あり。実NICで変更/読取/再起動保持の組合せを確認。 | [identification.py](../civi/identification.py)<br>[network.py](../civi/pi/network.py)<br>[RPI_LAN_SETTINGS.md](../docs/RPI_LAN_SETTINGS.md) | G05 |
| 9.5/subnet / p.62 | 親条項の内訳 | 追加検証 | prefix変更/読取時に対応subnet maskを表示。/1,/16,/24,/31,/32と不正入力を実JSで確認。物理NICの保存/再起動保持はG05に継続。 | [identification.py](../civi/identification.py)<br>[network.py](../civi/pi/network.py)<br>[WEB_API_REVIEW_2026-11-10.md](../docs/WEB_API_REVIEW_2026-11-10.md)<br>[test_web_api_review.py](../tests/test_web_api_review.py) | G05 |
| 9.5.6 / p.62 | 必須 | 実装確認 | mDNSのWeb停止/復帰と保持を実Piで確認。 | [RPI_MDNS.md](../docs/RPI_MDNS.md)<br>[test_pi_mdns.py](../tests/test_pi_mdns.py) | — |
| 9.5.7 / p.63 | 必須 | 実装確認 | 空白hostnameの既定値復帰を本番Webでユーザー確認。 | [LXI_DEFAULTS_API.md](../docs/LXI_DEFAULTS_API.md)<br>[test_lxi_defaults.py](../tests/test_lxi_defaults.py) | — |
| 9.5.8 / p.63 | 必須 | 実装確認 | 空白Descriptionの既定値復帰を本番Webでユーザー確認。 | [LXI_DEFAULTS_API.md](../docs/LXI_DEFAULTS_API.md)<br>[test_lxi_defaults.py](../tests/test_lxi_defaults.py) | — |
| 9.6 / p.64 | 同期/イベント拡張を採用した場合 | 適用外 | Clock/Event/Wired Triggerを実装しない。 | [LXI.md](../docs/LXI.md) | — |
| 9.8 / p.64 | 必須 | 実装確認 | 全15 POST経路で未認証/不正認証/CSRFヘッダー欠落/異Origin/変更前パスワードを拒否する試験を追加。既存の受理/保存試験と併用。侵入試験や完全なセキュリティ評価ではない。 | [server.py](../civi/server.py)<br>[auth.py](../civi/auth.py)<br>[test_password.py](../tests/test_password.py)<br>[WEB_API_REVIEW_2026-11-10.md](../docs/WEB_API_REVIEW_2026-11-10.md)<br>[test_web_api_review.py](../tests/test_web_api_review.py) | — |
| 9.8/nonblank / p.64 | 親条項の内訳 | 実装確認 | 撤回された空パスワード許可を使用しない。 | [auth.py](../civi/auth.py)<br>[test_password.py](../tests/test_password.py) | — |
| 9.8.1 / p.64 | 撤回済Permissionの禁止事項 | 実装確認 | 空パスワードを許可しない。旧Permissionは撤回済み。 | [auth.py](../civi/auth.py)<br>[test_password.py](../tests/test_password.py) | — |
| 9.9 / p.64 | 必須 | 手続待ち | 必須Webのロゴなし。未認証のため意図的に掲載しない。 | [identification.py](../civi/identification.py) | G11 |
| 9.14 / p.65 | 必須 | 実装確認 | 独自JSONは/api/以下。/lxi以下の実ルートはWelcome/識別/規定XSDに限定。 | [server.py](../civi/server.py)<br>[lxi_api.py](../civi/lxi_api.py) | — |
| 10.2 / p.66 | 必須 | 未達 | 識別GETとXSD/エラーあり。参照APIの版宣言不足・共通動作を下表へ分解。 | [identification.py](../civi/identification.py)<br>[lxi_api.py](../civi/lxi_api.py)<br>[LXI_DEFAULTS_API.md](../docs/LXI_DEFAULTS_API.md) | G04, G08 |
| 10.2.5 / p.66 | 拡張機能を実装した場合 | 適用外 | 採用拡張なし。未実装拡張のFunctionを宣言しない。 | [identification.py](../civi/identification.py) | — |
| 10.3 / p.66 | 必須 | 追加検証 | PiではAvahiを使用し実広告/応答を確認。RFC6762/6763全条件の証拠ではない。 | [discovery.py](../civi/pi/discovery.py)<br>[MDNS_HOSTNAME_2026-11-08.md](../docs/MDNS_HOSTNAME_2026-11-08.md) | G06 |
| 10.3.1 / p.67 | 必須 | 実装確認 | 物理eth0で名前衝突回避・Web/XML/広告整合、再接続での3回の再プローブを確認。Avahiへの委譲範囲を維持。 | [discovery.py](../civi/pi/discovery.py)<br>[MDNS_HOSTNAME_2026-11-08.md](../docs/MDNS_HOSTNAME_2026-11-08.md)<br>[RPI_NAME_COLLISION_2026-11-11.md](../docs/RPI_NAME_COLLISION_2026-11-11.md)<br>[RPI_MDNS_RECONNECT_2026-11-11.md](../docs/RPI_MDNS_RECONNECT_2026-11-11.md)<br>[LXI_READINESS_2026-11-11.md](../docs/LXI_READINESS_2026-11-11.md) | — |
| 10.3.1.1 / p.67 | 必須 | 実装確認 | 物理名前衝突で番号付きホスト名を取得し、相手停止後のPi全体再起動でも保存名を再利用。 | [MDNS_HOSTNAME_2026-11-08.md](../docs/MDNS_HOSTNAME_2026-11-08.md)<br>[RPI_NAME_COLLISION_2026-11-11.md](../docs/RPI_NAME_COLLISION_2026-11-11.md)<br>[LXI_READINESS_2026-11-11.md](../docs/LXI_READINESS_2026-11-11.md) | — |
| 10.3.3 / p.67 | DDNS Updateを提供する場合 | 適用外 | RFC2136 DDNS UpdateとユーザーDDNS制御は採用しない。mDNS制御と区別。OSのDHCP hostname/server-side登録はCIVI DDNS機能とは宣言しない。採用時に再評価。 | [network.py](../civi/pi/network.py)<br>[discovery.py](../civi/pi/discovery.py)<br>[LXI_DEVICE_CONFIGURATION.md](../docs/LXI_DEVICE_CONFIGURATION.md) | — |
| 10.3.4 / p.67 | 必須 | 実装確認 | 実eth0 DHCPで別hostname optionを返してもシステム/ユーザー名を維持することを確認済み。初回表の未試験記述を訂正。 | [discovery.py](../civi/pi/discovery.py)<br>[DHCP_2026-11-08.md](../docs/DHCP_2026-11-08.md)<br>[LXI_READINESS_2026-11-11.md](../docs/LXI_READINESS_2026-11-11.md) | — |
| 10.4 / p.67 | 必須 | 追加検証 | Avahiで発見とSRV接続先を実試験。相互接続/パケットの全条件は未確認。 | [discovery.py](../civi/pi/discovery.py)<br>[MDNS_HOSTNAME_2026-11-08.md](../docs/MDNS_HOSTNAME_2026-11-08.md) | G06 |
| 10.4.1 / p.68 | 必須 | 実装確認 | 物理共通サービス名衝突と再接続プローブ/広告を確認。固定100候補制限を除去し、110連続衝突の模擬試験も成功。 | [discovery.py](../civi/pi/discovery.py)<br>[discovery_state.py](../civi/discovery_state.py)<br>[MDNS_HOSTNAME_2026-11-08.md](../docs/MDNS_HOSTNAME_2026-11-08.md)<br>[RPI_NAME_COLLISION_2026-11-11.md](../docs/RPI_NAME_COLLISION_2026-11-11.md)<br>[RPI_MDNS_RECONNECT_2026-11-11.md](../docs/RPI_MDNS_RECONNECT_2026-11-11.md)<br>[LXI_READINESS_2026-11-11.md](../docs/LXI_READINESS_2026-11-11.md) | — |
| 10.4.2 / p.68 | 必須 | 実装確認 | HTTP/LXI/raw/HTTPSを同一取得名で広告。物理衝突後とPi全体再起動後も4サービスのSRV/IP/ポートを確認。 | [discovery.py](../civi/pi/discovery.py)<br>[MDNS_HOSTNAME_2026-11-08.md](../docs/MDNS_HOSTNAME_2026-11-08.md)<br>[RPI_NAME_COLLISION_2026-11-11.md](../docs/RPI_NAME_COLLISION_2026-11-11.md) | — |
| 10.4.2.1 / p.68 | 必須 | 実装確認 | 本番Webで64byte ASCII→63byte保存と4サービス再広告を確認し復元。UTF-8境界はPi模擬試験で確認。 | [network.py](../civi/network.py)<br>[test_lxi.py](../tests/test_lxi.py)<br>[test_lxi_fixes.py](../tests/test_lxi_fixes.py)<br>[LXI_FIXES_2026-11-10.md](../docs/LXI_FIXES_2026-11-10.md)<br>[RPI_LXI_FIXES_2026-11-10.md](../docs/RPI_LXI_FIXES_2026-11-10.md) | — |
| 10.4.2.3 / p.68 | 必須 | 実装確認 | 候補を逐次生成して衝突時に待機・継続。110衝突後(111)で4サービス登録と保存を確認。恒久衝突時の取消と資源解放も試験。 | [discovery_state.py](../civi/discovery_state.py)<br>[discovery.py](../civi/pi/discovery.py)<br>[MDNS_HOSTNAME_2026-11-08.md](../docs/MDNS_HOSTNAME_2026-11-08.md)<br>[LXI_READINESS_2026-11-11.md](../docs/LXI_READINESS_2026-11-11.md) | — |
| 10.4.3 / p.68 | 必須 | 追加検証 | HTTP/LXIの必須サービスとTXTを実装。NIC対象と全TXT境界を確認する。 | [discovery.py](../civi/pi/discovery.py)<br>[test_lxi.py](../tests/test_lxi.py)<br>[MDNS_HOSTNAME_2026-11-08.md](../docs/MDNS_HOSTNAME_2026-11-08.md) | G08 |
| 10.4.3/required / p.69 | 親条項の内訳 | 追加検証 | HTTP/LXI TXT識別4項目と*IDN?の対応あり。未接続/接続後の更新も含め最終ワイヤ確認。 | [discovery.py](../civi/pi/discovery.py)<br>[network.py](../civi/network.py)<br>[test_lxi.py](../tests/test_lxi.py) | G08 |
| 10.4.3/recommended-raw / p.70 | 親条項の内訳 | 実装確認 | 採用したraw広告も同じ識別TXTを使用し、古いAddressキーを出力しない。 | [discovery.py](../civi/pi/discovery.py)<br>[network.py](../civi/network.py) | — |
| 10.4.3.1 / p.69 | 必須 | 実装確認 | 各サービスへTXTリストを渡す。 | [discovery.py](../civi/pi/discovery.py)<br>[test_lxi.py](../tests/test_lxi.py) | — |
| 10.4.3.2 / p.69 | 必須 | 実装確認 | key=valueをUTF-8へ変換、255byte超過は広告前拒否。 | [discovery.py](../civi/pi/discovery.py) | — |
| 10.4.3.3 / p.69 | 必須 | 実装確認 | 送信キーは固定ASCII。受信キーを独自大小文字比較する機構なし。 | [discovery.py](../civi/pi/discovery.py)<br>[network.py](../civi/network.py) | — |
| 10.4.3.4 / p.70 | 必須 | 実装確認 | 値をUTF-8 bytesへ変換。ASCII識別値も同じ経路。 | [discovery.py](../civi/pi/discovery.py) | — |
| 10.4.3.6 / p.70 | 必須 | 実装確認 | txtversを先頭に生成。 | [test_lxi.py](../tests/test_lxi.py)<br>[discovery.py](../civi/pi/discovery.py) | — |
| 10.4.3.7 / p.70 | 必須 | 実装確認 | 独自LXI接頭辞キーを出していない。 | [discovery.py](../civi/pi/discovery.py)<br>[network.py](../civi/network.py) | — |
| 10.4.3.8 / p.70 | 必須 | 実装確認 | 必須/推奨サービスには標準キーだけを使用、独自キーなし。 | [discovery.py](../civi/pi/discovery.py)<br>[network.py](../civi/network.py) | — |
| 10.4.3.11 / p.71 | Deprecated | 廃止 | 現行必須の不足には数えない。後継条項を本表で追跡。 | [LXI.md](../docs/LXI.md) | — |
| 10.5 / p.72 | 必須 | 実装確認 | 既定有効。無効保存値は利用者設定であり出荷既定とは分離。 | [config.pi.example.toml](../config.pi.example.toml)<br>[RPI_MDNS.md](../docs/RPI_MDNS.md) | — |
| 10.5.1 / p.72 | 必須 | 実装確認 | 本体LCIで装置全体のAvahiを有効化。 | [RPI_LCI_BOOT_2026-11-08.md](../docs/RPI_LCI_BOOT_2026-11-08.md)<br>[RPI_MDNS.md](../docs/RPI_MDNS.md) | — |
| 10.5.2 / p.72 | 必須 | 実装確認 | 装置全体停止/ソケット起動抑止/再起動保持/復帰を実機確認。 | [RPI_MDNS.md](../docs/RPI_MDNS.md) | — |
| 10.6 / p.72 | 必須 | 実装確認 | Pi標準NSS/socketの.local正引きと169.254 PTR逆引きを有線で確認。実AutoIP割当相手でも隔離Piで正引き・逆引き・TCPを確認。物理AutoIP2台は追加試験。 | [LXI_AUDIT_2026-11-07.md](../docs/LXI_AUDIT_2026-11-07.md)<br>[RPI_MDNS_RESOLVER_2026-11-11.md](../docs/RPI_MDNS_RESOLVER_2026-11-11.md)<br>[RPI_MDNS_AUTOIP_2026-11-11.md](../docs/RPI_MDNS_AUTOIP_2026-11-11.md)<br>[LXI_READINESS_2026-11-11.md](../docs/LXI_READINESS_2026-11-11.md) | — |
| 10.7 / p.72 | 必須 | 実装確認 | 希望名/取得名を保存。物理衝突後、相手を停止してPi全体再起動し取得名再利用を確認。元のキャッシュ・設定・認証・固定IPへ復元。 | [discovery_state.py](../civi/discovery_state.py)<br>[MDNS_HOSTNAME_2026-11-08.md](../docs/MDNS_HOSTNAME_2026-11-08.md)<br>[RPI_NAME_COLLISION_2026-11-11.md](../docs/RPI_NAME_COLLISION_2026-11-11.md) | — |
| 10.7.1 / p.73 | 必須 | 実装確認 | LCI世代更新で取得名を破棄し最終利用者名/既定値に戻す。 | [lci.py](../civi/pi/lci.py)<br>[test_pi_lci.py](../tests/test_pi_lci.py)<br>[test_discovery_names.py](../tests/test_discovery_names.py) | — |
| 10.8 / p.73 | 必須 | 実装確認 | 同一固定IPの物理再接続でホスト名/4サービスを各3回再プローブ後に再広告。新規DNS-SD/HTTPS/SCPIも確認。 | [network.py](../civi/network.py)<br>[discovery.py](../civi/pi/discovery.py)<br>[RPI_MDNS_RECONNECT_2026-11-11.md](../docs/RPI_MDNS_RECONNECT_2026-11-11.md)<br>[LXI_READINESS_2026-11-11.md](../docs/LXI_READINESS_2026-11-11.md) | — |
| 11.1 / p.74 | 必須 | 追加検証 | 実機条件・操作別の証拠を追加し110行へ対応付け。MAIN1.41の制約と丸め、復元結果、wheel導入確認を文書化。全APIの規定検証と最終適合文書は未完了。 2026-11-12: 352行を全件照合し、根拠未対応204行を分類した。旧SCPI189メニュー書込みと現行typed経路、getter/setter、ローカル処理を区別。未分類0は全試験完了ではなく、追加試験IDを確定した。 | [AUDIT.md](../drivers/civi-ic7300/src/civi_ic7300/AUDIT.md)<br>[COMPLIANCE.md](../drivers/civi-ic7300/src/civi_ic7300/COMPLIANCE.md)<br>[IVI_RECEIVE_ACCEPTANCE_2026-11-11.md](../docs/IVI_RECEIVE_ACCEPTANCE_2026-11-11.md)<br>[IVI_ADDITIONAL_TESTS_2026-11-12.md](../docs/IVI_ADDITIONAL_TESTS_2026-11-12.md)<br>[IVI_VERIFICATION_RECONCILED_2026-11-12.json](../docs/IVI_VERIFICATION_RECONCILED_2026-11-12.json)<br>[IVI_MENU_VERIFICATION_2026-11-12.csv](../docs/IVI_MENU_VERIFICATION_2026-11-12.csv) | G10 |
| 11.2 / p.74 | 必須 | 手続待ち | IVIドライバーDB未登録。NLの略号照会/登録だけでは本要件を満たさない。 | [NAMING.md](../drivers/civi-ic7300/src/civi_ic7300/NAMING.md)<br>[COMPLIANCE.md](../drivers/civi-ic7300/src/civi_ic7300/COMPLIANCE.md) | G10 |

## 公式補足解釈

| 条項 / PDF頁 | 適用条件 | 状態 | CIVIの証拠・判定 | 根拠ファイル | 残件 |
|---|---|---|---|---|---|
| 8.14 / p.6 | 必須 | 実装確認 | 公式補足解釈で追加。IPv4 SCPI SOCKETによる制御を提供。 | [server.py](../civi/server.py)<br>[RPI_AUTOIP_TCP_2026-11-08.md](../docs/RPI_AUTOIP_TCP_2026-11-08.md) | — |

## 識別に関係するAPI要件

| 条項 / PDF頁 | 適用条件 | 状態 | CIVIの証拠・判定 | 根拠ファイル | 残件 |
|---|---|---|---|---|---|
| 23.5 / p.9 | 識別APIに適用 | 追加検証 | GET識別とエラーの意味的要件を本表へ取り込み。全Security/API実装を要求する解釈にはしない。 | [LXI_DEFAULTS_API.md](../docs/LXI_DEFAULTS_API.md) | G08 |
| 23.5.1 / p.9 | 識別APIに適用 | 追加検証 | 識別XSDは現行公式と一致。ProblemDetailsも編集日を現行へ同期。版/配布出典の確認と記録を継続。 | [InstrumentIdentification-2.0.xsd](../civi/schemas/InstrumentIdentification-2.0.xsd)<br>[LXIProblemDetails-1.0.xsd](../civi/schemas/LXIProblemDetails-1.0.xsd) | G08 |
| 23.6 / p.9 | 識別APIに適用 | 実装確認 | WebでLXI APIを独立した拡張として列挙していない。 | [identification.py](../civi/identification.py) | — |
| 23.7 / p.9 | 識別APIに適用 | 実装確認 | XMLでLXI API Functionを宣言しない。 | [identification.py](../civi/identification.py) | — |
| 23.10.1/public-get / p.11 | 識別APIに適用 | 実装確認 | GET識別は認証不要。HTTP平文を別途提供する義務とはしない。 | [server.py](../civi/server.py)<br>[test_lxi.py](../tests/test_lxi.py) | — |
| 23.10.1.1 / p.11 | 保護されたLXI APIを提供した場合 | 適用外 | 識別だけでAPI Key機構をコア必須とはしない。保護された/lxi/apiエンドポイントは未採用。 | [server.py](../civi/server.py) | — |
| 23.10.1.2 / p.11 | 保護されたLXI APIを提供した場合 | 適用外 | LXI-API realmは保護API採用時。独自/apiのCIVI realmを直ちに違反としない。 | [server.py](../civi/server.py) | — |
| 23.10.1.3 / p.12 | LXI Security設定変更を提供した場合 | 適用外 | LXI Security設定変更APIなし。 | [server.py](../civi/server.py) | — |
| 23.10.2 / p.12 | 追加LXI API認可を提供した場合 | 適用外 | 独自のLXI API認可方式は追加しない。 | [server.py](../civi/server.py) | — |
| 23.10.3 / p.12 | 証明書/CSR管理APIを提供した場合 | 適用外 | 証明書/CSRをGUID管理するAPIなし。 | [server.py](../civi/server.py) | — |
| 23.10.4.1 / p.13 | 識別APIに適用 | 追加検証 | 既存XSD適合試験あり。XSD通過と必須意味要件は別で、LXIVersionが未達。 | [identification.py](../civi/identification.py)<br>[test_lxi_defaults.py](../tests/test_lxi_defaults.py) | G04, G08 |
| 23.10.4.2 / p.13 | 識別APIに適用 | 実装確認 | 識別text/xml、schema/ProblemDetails application/xml、405 Allow、GET/HEADの内容と長さ、no-storeを確認。認証/HTTP例外/ProblemDetailsにも共通保護ヘッダーを統一。 | [server.py](../civi/server.py)<br>[lxi_api.py](../civi/lxi_api.py)<br>[test_lxi_defaults.py](../tests/test_lxi_defaults.py)<br>[WEB_API_REVIEW_2026-11-10.md](../docs/WEB_API_REVIEW_2026-11-10.md)<br>[test_web_api_review.py](../tests/test_web_api_review.py) | — |
| 23.10.4.3 / p.13 | 識別APIに適用 | 追加検証 | Gateway識別はradio各状態でも完全な読取を200で返し、shutdownは503。未識別child404、既知だが切断child503。同期GETは202を返さない。完成装置のnormal operation境界の最終判定は継続。 未接続/隔離/状態取得失敗/復帰、LAN試行期限切れとhelper停止時を実JS・模擬HTTPで追加確認。実ブラウザーの異常状態表示と完成構成での判定は残る。 | [server.py](../civi/server.py)<br>[LXI_DEFAULTS_API.md](../docs/LXI_DEFAULTS_API.md)<br>[WEB_API_REVIEW_2026-11-10.md](../docs/WEB_API_REVIEW_2026-11-10.md)<br>[test_web_api_review.py](../tests/test_web_api_review.py)<br>[WEB_STATES_2026-11-10.md](../docs/WEB_STATES_2026-11-10.md)<br>[test_web_state_transitions.py](../tests/test_web_state_transitions.py) | G08 |
| 23.10.4.4 / p.13 | 識別APIに適用 | 実装確認 | 規定資源のエラーをProblemDetails application/xmlにする。 | [lxi_api.py](../civi/lxi_api.py)<br>[test_lxi_defaults.py](../tests/test_lxi_defaults.py) | — |
| 23.10.4.5 / p.14 | LXI APIで202/保留操作を返す場合 | 適用外 | 識別GETは同期読み取りで202を返さずユーザー操作を要求しない。独自IPv4試行APIは別。 | [server.py](../civi/server.py) | — |
| 23.10.4.5.1 / p.14 | LXI APIで202/保留操作を返す場合 | 適用外 | 識別GETは同期読み取りで202を返さずユーザー操作を要求しない。独自IPv4試行APIは別。 | [server.py](../civi/server.py) | — |
| 23.10.4.5.2 / p.14 | LXI APIで202/保留操作を返す場合 | 適用外 | 識別GETは同期読み取りで202を返さずユーザー操作を要求しない。独自IPv4試行APIは別。 | [server.py](../civi/server.py) | — |
| 23.10.6.1 / p.16 | 識別APIに適用 | 実装確認 | 識別専用の互換XSD経路も保持。 | [server.py](../civi/server.py)<br>[test_lxi_defaults.py](../tests/test_lxi_defaults.py) | — |
| 23.10.6.2 / p.16 | 識別APIに適用 | 実装確認 | 提供schema名/版をURLへ含める。 | [server.py](../civi/server.py)<br>[identification.py](../civi/identification.py) | — |
| 23.10.6.3 / p.16 | 識別APIに適用 | 実装確認 | 識別とProblemDetailsの規定XSD経路を提供し取得試験あり。 | [server.py](../civi/server.py)<br>[test_lxi_defaults.py](../tests/test_lxi_defaults.py) | — |
| 23.10.7 / p.17 | 識別APIに適用 | 実装確認 | 認証不要GET、text/xml、旧XSD aliasを試験。全識別内容は別行。 | [server.py](../civi/server.py)<br>[test_lxi.py](../tests/test_lxi.py)<br>[test_lxi_defaults.py](../tests/test_lxi_defaults.py) | — |
| 23.11.1.1/identity / p.23 | 識別APIに適用 | 実装確認 | Manufacturer/Model/SerialNumber/FirmwareRevisionを順序どおり出力しXSD試験。 | [identification.py](../civi/identification.py)<br>[test_lxi.py](../tests/test_lxi.py) | — |
| 23.11.1.1-1 / p.24 | 識別APIに適用 | 実装確認 | 対象有線InterfaceだけをLXIとして出力。アドレス未取得でもInterfaceを保持。lo/WLANをLXI宣言しない。XSD試験済み。 本番PiのXMLでもeth0だけであることを確認済み。 | [identification.py](../civi/identification.py)<br>[test_lxi_fixes.py](../tests/test_lxi_fixes.py)<br>[LXI_FIXES_2026-11-10.md](../docs/LXI_FIXES_2026-11-10.md)<br>[RPI_LXI_FIXES_2026-11-10.md](../docs/RPI_LXI_FIXES_2026-11-10.md) | — |
| 23.11.1.1-2 / p.25 | LXI Event Messagingを実装した場合 | 適用外 | LXI Event Messaging未採用、Domain不要。 | [identification.py](../civi/identification.py) | — |
| 23.11.1.1-3 / p.26 | 識別APIに適用 | 未達 | LXIVersionは意図的に省略。接続無線機には不要でも親ゲートウェイには必要。適合前には宣言しない。 | [identification.py](../civi/identification.py)<br>[test_lxi.py](../tests/test_lxi.py) | G04 |
| 23.11.2-1 / p.26 | 識別APIに適用 | 実装確認 | 識別済み無線機のbaseURLをConnectedDevicesへ出力。 | [identification.py](../civi/identification.py)<br>[test_lxi.py](../tests/test_lxi.py) | — |
| 23.11.2.1-1 / p.26 | 識別APIに適用 | 実装確認 | baseURL/lxi/identificationを提供。未識別時404、識別後200を試験。 | [server.py](../civi/server.py)<br>[test_lxi.py](../tests/test_lxi.py) | — |
| 23.11.2.1-2 / p.26 | 識別APIに適用 | 実装確認 | 子のschemaLocationに装置上の絶対XSD URLを含める。 | [identification.py](../civi/identification.py)<br>[test_lxi.py](../tests/test_lxi.py) | — |
| 23.11.3.1-1 / p.27 | 識別APIに適用 | 実装確認 | InterfaceType=LXIを対象有線NICだけに限定し、複数NIC模擬入力で確認。 本番PiのXMLでもeth0だけであることを確認済み。 | [identification.py](../civi/identification.py)<br>[test_lxi_fixes.py](../tests/test_lxi_fixes.py)<br>[LXI_FIXES_2026-11-10.md](../docs/LXI_FIXES_2026-11-10.md)<br>[RPI_LXI_FIXES_2026-11-10.md](../docs/RPI_LXI_FIXES_2026-11-10.md) | — |
| 23.11.3.2 / p.27 | 識別APIに適用 | 実装確認 | 採用したIPv4項目の順序/表現をXSD試験。省略可能な項目を必須不足とはしない。 | [identification.py](../civi/identification.py)<br>[test_lxi.py](../tests/test_lxi.py) | — |
| 23.11.5.1 / p.29 | 任意Extensionを採用した場合 | 適用外 | Extensionを出力しない。 | [identification.py](../civi/identification.py) | — |
| 23.11.6.1 / p.29 | 任意拡張を採用した場合 | 適用外 | 拡張を宣言しない。将来採用時は各拡張のFunction形式が必要。 | [identification.py](../civi/identification.py) | — |
| 23.11.7 / p.29 | Subinstrumentsを提供した場合 | 適用外 | サブ機器の別制御チャネルを宣言しない。無線機はConnectedDevicesとして扱う。 | [identification.py](../civi/identification.py) | — |
| 23.18-1 / p.77 | 識別APIに適用 | 実装確認 | 40x応答をProblemDetailsに変換、405/404をXSD検証。 | [lxi_api.py](../civi/lxi_api.py)<br>[test_lxi_defaults.py](../tests/test_lxi_defaults.py) | — |
| 23.18.1.1-1 / p.77 | 識別APIに適用 | 実装確認 | Titleを必ず出力する。 | [lxi_api.py](../civi/lxi_api.py)<br>[test_lxi_defaults.py](../tests/test_lxi_defaults.py) | — |
| 23.19-1 / p.77 | 保留応答を返す場合 | 適用外 | 識別GETで202を返さないのでPending XML不要。 | [server.py](../civi/server.py) | — |
