# LXI関連機能の使用と実装範囲

[IVIドライバー実機確認（11月11日）](IVI_RECEIVE_ACCEPTANCE_2026-11-11.md): MAIN1.41でCore/受信40・受信設定65チェック、216メニュー読取を確認。モード/ファーム依存とNR/PBT丸めを文書化し元へ復元。wheel新規導入と読取も確認済み。全IVI規定検証・登録は未完了。

[LXI最短経路の再判定（11月11日）](LXI_READINESS_2026-11-11.md): 名前衝突の固定上限を除去し電源表示を追加。有線100Mbps Full/Halfを確認。Windows603件/Pi594件成功（環境スキップ別記）。IVI規定の実機検証・登録と本体/宣言の最終ゲートは未完了。

[自動取得AutoIP相手の正引き・逆引き・TCP確認（11月11日）](RPI_MDNS_AUTOIP_2026-11-11.md): Piの隔離ネットワークでNetworkManagerが取得した実アドレスに対するNSS正引き・逆引き・TCP往復を確認。試験環境は削除済み、通常設定・認証情報は変更なし。物理AutoIP機器同士の試験とは区別。

[PiからのmDNS正引き・逆引き確認（11月11日）](RPI_MDNS_RESOLVER_2026-11-11.md): Pi標準NSS/socketで別機器の.local名と試験用169.254 PTRを有線経由で解決。逆引きは模擬レコードであり、実AutoIP機器の到達性確認とは分離。設定変更なし・応答器停止済み。

[有線再接続時のmDNS確認（11月11日）](RPI_MDNS_RECONNECT_2026-11-11.md): 同じ固定IPでケーブルを抜き挿しし、ホスト名・4サービスの各3回のプローブと約6秒後の再広告を実通信で確認。新規DNS-SD・HTTPS・SCPIも正常。設定・認証情報は変更なし。

[物理LANの名前衝突・再起動保持確認（11月11日）](RPI_NAME_COLLISION_2026-11-11.md): `civi-2.local.` と共通サービス名 `(2)` の取得、試験相手を停止した後のPi全体再起動での再利用を確認。元の名前・固定IPへ復元済み。設定・認証情報は変更なし。LXI適合の宣言ではありません。

[DHCP保存・再起動／LAN RESET確認（11月11日）](RPI_DHCP_BOOT_2026-11-11.md): Pi再起動後の保存保持と固定IPからのRESET後DHCP取得を確認。固定IP復元・試験サーバー停止済み。helper接続エラーを改善。Web認証はLAN RESET表示の復旧用パスワードです。

[実eth0のDHCP確認（11月10–11日）](RPI_DHCP_ETHERNET_2026-11-10.md): 取得・自然更新・失効/AutoIP/Fault・再取得を確認。一時設定時のLAN監視を修正。固定IP復元・試験サーバー停止済み。全体580成功・1スキップ。

[監査4件のPi反映・実機確認](RPI_LXI_FIXES_2026-11-10.md)を実施。Description復元、有線広告、Fault/Identifyと復旧、導入済みドライバーの実機読取を確認。無線機設定変更なし。LXI全体の適合は未達。

[監査4件の修正完了](LXI_FIXES_2026-11-10.md): クライアント0.13.1、全体522成功・Linux専用1スキップ。実Pi未反映/未確認、他の適合残件は継続。

2026-11-10 全条項監査: [現行RULE101件・175行の照合](LXI_REQUIREMENTS_2026-11-10.md)と[残件G01–G12](LXI_REMAINING_2026-11-10.md)。VISA位置指定/サービス名切り詰め/対象NIC宣言に差異を確認。未達。Piや無線機への操作は行っていません。

2026-11-10: [Python 0.13.0 API命名・繰り返し機能点検](PYTHON_STYLE_2026-11-10.md)。全体485成功・Linux専用1スキップ。キーヤー識別名追加、既存API維持。Pi/実機の操作なし、IVI適合・登録は未達。

2026-11-09追記: [0.12.1の限定実機試験](PYTHON_HARDWARE_2026-11-09.md)で774→775→774 kHz、AM→USB→AM（DATA OFF/FIL2）の変更/読戻し/復元を確認。別VFO・受信状態も一致。送信/保存値書込/resetは未実施。

2026-11-09追記: [クライアント0.12.1のヘルプ整備](PYTHON_HELP_2026-11-09.md)。43型・310メンバー/フィールド、告知文、実装/模擬/実機の範囲を整理。不正エラー応答のProtocolError化も修正。Pi・無線機の操作なし、IVI適合・登録は未達。

2026-11-09追記: [クライアント0.12.0の基本/別名監査](PYTHON_BASIC_2026-11-09.md)。拡張339＋基本/専用11系統を統合し、別名と対象外理由を整理。基本APIの不足を追加。Pi・無線機の操作や実送信は行わず、IVI適合・登録は未達。

2026-11-09追記: [クライアント0.11.0の階層追加](PYTHON_HIERARCHY_2026-11-09.md)。バンド→保存枠の階層と物理名を追加。旧tuple指定/列挙/33枠の件数は維持。Pi・無線機の操作なし。IVI適合・登録は未達。

2026-11-09追記: [クライアント0.10.0の状態照会修正](PYTHON_STATUS_2026-11-09.md)。OFFは自動エラー照会なし、checked()で一時的にON。QueryErrorはキューを保持。ゲートウェイ権限/停止制御は維持し、Pi・無線機の操作なし。IVI適合・登録は未達。

2026-11-09追記: Pythonクライアント0.9.0で[Core/Python一次監査](../drivers/civi-ic7300/src/civi_ic7300/AUDIT.md)を実施。型付きオプション、READMEへの適合資料埋込み、文書/配布物検査を追加。状態照会OFFの差異と命名/文書/実機検証の不足は残り、IVI適合・登録は未達。Pi・無線機の変更なし。

2026-11-09追記: [Pythonクライアント0.8.0](PYTHON_OPERATIONS_2026-11-09.md)で残る11定義を追加。拡張339定義すべてに型付きAPIが全方向対応、部分/未対応0。Windowsの模擬検証のみ、実送信・実機電源操作・Piの変更なし。実機とIVI全要件の監査/登録は未達。

2026-11-09追記: [Pythonクライアント0.7.0](PYTHON_BANDS_2026-11-09.md)でバンド端5定義、DATAとIP+別コマンドを追加。拡張328全方向・部分0・11未対応。Windowsの模擬検証のみ、Pi・実無線機の変更なし。IVI適合/登録は未達。

2026-11-09追記: [Pythonクライアント0.6.0](PYTHON_SCAN_2026-11-09.md)でスキャン21定義、トーン周波数2定義とスコープ書込2方向を追加。拡張321全方向・部分0・18未対応。Windowsの模擬検証のみ、Pi・実無線機の変更なし。IVI適合/登録は未達。

2026-11-09追記: [Pythonクライアント0.5.0の保存データAPI](PYTHON_STORAGE_2026-11-09.md)を追加。メモリー101、バンドスタック33、キーヤー8枠を両模擬系で変更/読戻し/復元。拡張296全方向・2部分・41未対応。Pi・実無線機の変更なし、IVI適合/登録は未達。

2026-11-08の最新更新: [Pythonクライアント0.4.0](PYTHON_MENUS_2026-11-08.md)でメニュー216項目を
追加し、型・範囲・読戻し・既存権限の維持を模擬検証しました。[方向別対応](PYTHON_DRIVER_COVERAGE.md)
は288全方向・2部分対応・49未対応。今回はPi側を変更していません。

2026-11-08の後続更新: [Pythonクライアント0.3.0](PYTHON_CONTROLS_2026-11-08.md)へ型付き
操作APIを追加し、Windows＋模擬バックエンドで検証しました。[339定義の対応表](PYTHON_DRIVER_COVERAGE.md)
は72全方向・2部分対応・265未対応で、IVIドライバー要件全体は未達です。Pi側は変更していません。

2026-11-08追記: [独立Pythonクライアント](PYTHON_DRIVER_2026-11-08.md)を追加。0.2.0では[受信reset](RECEIVE_RESET.md)を実装し、本体パーシャルリセット後の実測値へ更新。両VFO・運用/スコープ57項目の復元と保護メニュー不変を[実機確認](PARTIAL_RESET_CAPTURE_2026-11-08.md)しました。全機能API、resetを含む最終要件照合と登録は残り、IVI/LXI適合ドライバーとは表示しません。

2026-11-07更新。Windows/Linux共通機能に加えPi用の設定・回復・表示を実装しました。最新の実機確認と残件は[監査記録](LXI_AUDIT_2026-11-07.md)を参照してください。LXI Device Specification 1.6.2全体の実装・検証は完了していません。認証・適合を主張せず、LXIロゴは使用しません。

## Webと識別API

Piは主HTTPSポート443と互換8443、Windowsの設定例は8443で利用します。

| パス | 内容 | 認証 |
|---|---|---|
| `/` | 従来の無線機操作画面。各情報ページへのリンクを追加 | 操作APIは必要 |
| `/lxi`、`/lxi/` | 機器識別、版、説明、IP、MAC、VISAアドレス、発見の状態 | 不要、読み取り専用 |
| `/lxi/identification` | LXI InstrumentIdentification 2.0形式のXML | 不要、読み取り専用 |
| `/devices/radio/lxi/identification` | 識別済み接続無線機のXML。未識別時404 | 不要、読み取り専用 |
| `/InstrumentIdentification/2.0` | XMLのschemaLocationが参照する公式XSDのローカルコピー | 不要 |
| `/network` | LAN情報と発見設定フォーム | 閲覧不要、保存時必要 |
| `/api/network`（POST） | 機器説明とmDNS/DNS-SD有効・無効の保存と反映 | admin認証、同一Origin、X-CIVI-Request必要 |
| `/help` | SCPI・スコープ・接続・実装範囲のローカル文書 | 不要 |

Piブランチでは、任意の`pi_network.enabled`設定により`/network`へ有線IPv4の一時適用・確認保存・復元を追加しています。別途手動起動する補助プロセスが必要です。[起動方法と制限](RPI_LAN_SETTINGS.md)、[実機試験](RPI_LAN_2026-11-07.md)を参照してください。既存の`/api/network`は説明と発見の設定だけで、OSのIP変更は`/api/pi/network`配下に分離しています。

識別APIの機器識別フィールドは現在の`*IDN?`の4項目に合わせます。無線機識別は既存のバックグラウンド処理によるキャッシュを使い、公開APIから新たな無線機操作を発行しません。起動直後・未接続ではモデルは`CIVI/Unknown`です。接続無線機の製造番号は取得できないため`Unknown`、無線機ファームウェア版は従来どおり手動設定または`Unknown`です。

XMLは公式XSDで検証しますが、未適合の版を宣言しないため`LXIVersion`を省略しています。XSD上は許されても、LXI Deviceとしては版の宣言が必要であり、この点を含め全要件を満たしたものではありません。LXI API Extended Functionの全Common Method要件も未検証です。LXI Extended Functionsの実装を宣言する要素は出しません。

Webでは、未検証のOSホスト名を有効なDNS名として表示せず、ホスト名欄にIPを代替表示します。VISA文字列は規格の表示形式に合わせ、ボード番号を含まない`TCPIP::<IP>::<port>::SOCKET`です。

## 発見と設定の保存

Windowsはzeroconf、Piは既存Avahiを利用し、`_http._tcp`、`_lxi._tcp`、`_scpi-raw._tcp`、`_https._tcp`を広告します。HTTPの平文サーバーは起動せず、Webサービス広告は実際のHTTPS主ポートを指します。`txtvers`を先頭に置き、識別用TXTには`Manufacturer`、`Model`、`SerialNumber`、`FirmwareVersion`を設定します。モデルの識別状態やIP変更は約5秒間隔で再広告へ反映します。

サービス名が競合すると全サービスを同じ番号付き名で再登録し、取得名を保存します。PiはAvahiにホスト名競合処理を任せ、希望名と取得名を分離保存・再利用します。サービス名競合は実機試験済みです。さらに[Pi隔離環境の実Avahi試験](MDNS_HOSTNAME_2026-11-08.md)でホスト名競合、動作中の改名、CIVI/Avahi再起動後の取得名再利用・復元を確認しました。物理NIC・実Pi全体の再起動は未検証です。Piのスイッチは[Avahi本体の停止・永続的な自動再起動抑止](RPI_MDNS.md)も行い、WindowsはCIVIサービス群だけを解除します。[処理と制限](DISCOVERY_NAMES.md)を参照してください。

`/network`の機器説明はサービス名にも使います。1–63 UTF-8バイトで設定してください。保存するとconfig.tomlと同じディレクトリーの`.civi-network.json`へ原子的に書き込み、現在の広告へ反映します。次の手動起動でも読み込み、config.tomlの`description`と`discovery`より優先します。書き込みに失敗した場合は成功扱いにしません。保存後に広告できなかった場合は、保存成功と広告失敗を分けて表示します。

この設定はOSのIP、DNS、DHCP、ホスト名、ネットワークアダプター設定を変更しません。保存ファイルを削除すると次回起動ではconfig.tomlの値に戻りますが、これは規格のLAN Configuration Initialize（LCI）ではありません。自動起動やsystemd登録も行いません。

## PiでのHTTPS 443

新規設定ではトップレベルを次のように指定すれば、443を主ポートにしつつ8443も同じ証明書・認証・アプリで受け付けられます。

```toml
web_port = 443
web_extra_ports = [8443]
```

Pi用の`config.pi.example.toml`は上記設定を既定とし、Windows用の`config.example.toml`は8443を維持します。Piでは443だけを一般ユーザーに許可するauthbindを導入し、更新した`start.sh`で手動起動します。[導入・復元手順](RPI_HTTPS.md)を参照してください。実Piの443と追加18443へ別PCから証明書検証付き接続・認証・SCPI同時操作を確認し、443のmDNS広告も受信しました。模擬バックエンドによる試験であり、その後の本番プロセスの443/8443移行も確認済みです。[試験記録と未確認事項](RPI_HTTPS_2026-11-07.md)に分けて記載しています。

2026-11-07の追試で本番の443/8443への移行、mDNS/Ping無効状態での実Pi再起動と、その後のWeb再有効化も確認済みです。[当日の最終まとめ](PROGRESS_2026-11-07.md)を参照してください。

2026-11-08には、隔離したPi仮想EthernetでDHCP取得・自然な更新・期限切れ・AutoIPへの移行・再取得を確認しました。[条件と限界](DHCP_2026-11-08.md)を参照してください。

2026-11-08に[重複IP保護](RPI_CONFLICT.md)を追加し、Pi隔離環境で候補アドレスの拒否、使用中の固定IP/AutoIPの切断とFault反映を確認しました。適用にはCIVIとヘルパーの手動再起動が必要です。

有線の自動交渉は、保存値noが速度/duplex未指定ではOS設定を維持する意味と確認しました。現在の対象Piはyes/速度0/duplex未指定へ明示設定し、再読込・再有効化後も1000Mb/s Full/onと通信を確認しています。[導入・範囲](RPI_ETHERNET_2026-11-08.md)。

AutoIPを送信元とする返信だけを有線直結経路へ向ける処理を手動ヘルパーに追加しました。PCを固定IPのまま、実AutoIPへのHTTPS/SCPIを確認し、試験後の経路削除と固定IP復元も確認済みです。[処理・範囲](RPI_AUTOIP_TCP_2026-11-08.md)。

## 残る要件

Pi有線IPv4・ホスト名保存・LAN RESET・パスワード変更・本体状態/Identify表示・mDNS名処理・443の基本動作は追加済みです。空欄による既定値復帰と識別APIの規定XSD URL/エラーXMLは[実装・試験済み](LXI_DEFAULTS_API.md)です。装置全体のAvahi停止も[実装済み](RPI_MDNS.md)です。固定IPの実Pi未接続起動・再接続は[確認済み](RPI_UNPLUGGED_BOOT_2026-11-08.md)です。完全なLCI後の実Pi未接続起動と再接続AutoIPも[確認済み](RPI_LCI_BOOT_2026-11-08.md)です。DHCPサーバー有りの実Pi起動組合せとAutoIP全通信条件の追加確認、DHCPの物理LAN/起動時の追加試験、重複IPの物理NIC/起動時確認、名前衝突後のリンク再接続・多数衝突等の追加運用試験、IVIドライバー/登録と全条項照合が残っています。[対応表](LXI.md)と[監査記録](LXI_AUDIT_2026-11-07.md)を参照してください。拡張機能の条件付き要件をコアの必須要件と混同しません。

## 参照

- [LXI Device Specification 1.6.2](https://public.lxistandard.org/specifications/LXI_1.6_Specifications/LXI_Device_Specification_1.6.2_2026-04-02.pdf)
- [識別スキーマ2.0の説明](https://public.lxistandard.org/schemas/InstrumentIdentification/2.0.html)
- [公式XSD](https://public.lxistandard.org/schemas/InstrumentIdentification/2.0)
