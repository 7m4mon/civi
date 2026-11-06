# LXI関連機能の使用と実装範囲

2026-10-29時点。Windows/Linux共通のソフトウェア機能を追加しました。LXI Device Specification 1.6.2全体の実装・検証は完了していません。認証・適合を主張せず、LXIロゴは使用しません。

## Webと識別API

通常のHTTPSポート（既存設定では8443）で利用します。

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

識別APIの機器識別フィールドは現在の`*IDN?`の4項目に合わせます。無線機識別は既存のバックグラウンド処理によるキャッシュを使い、公開APIから新たな無線機操作を発行しません。起動直後・未接続ではモデルは`CIVI/Unknown`です。接続無線機の製造番号は取得できないため`Unknown`、無線機ファームウェア版は従来どおり手動設定または`Unknown`です。

XMLは公式XSDで検証しますが、未適合の版を宣言しないため`LXIVersion`を省略しています。XSD上は許されても、LXI Deviceとしては版の宣言が必要であり、この点を含め全要件を満たしたものではありません。LXI API Extended Functionの全Common Method要件も未検証です。LXI Extended Functionsの実装を宣言する要素は出しません。

Webでは、未検証のOSホスト名を有効なDNS名として表示せず、ホスト名欄にIPを代替表示します。VISA文字列は規格の表示形式に合わせ、ボード番号を含まない`TCPIP::<IP>::<port>::SOCKET`です。

## 発見と設定の保存

zeroconfで`_http._tcp`、`_lxi._tcp`、`_scpi-raw._tcp`、`_https._tcp`を広告します。HTTPの平文サーバーは起動せず、Webサービス広告は実際のHTTPSポートを指します。`txtvers`を先頭に置き、識別用TXTには`Manufacturer`、`Model`、`SerialNumber`、`FirmwareVersion`を設定します。モデルの識別状態やIP変更は約5秒間隔で再広告へ反映します。

サービス名が競合すると、全サービスを取り消して同じ番号付き名で再登録します。これはサービス名の競合処理です。mDNSホスト名の独立した競合解決・解決名の永続化・DHCP等との名前統合は未実装で、発見全体の規格適合は未確認です。

`/network`の機器説明はサービス名にも使います。1–63 UTF-8バイトで設定してください。保存するとconfig.tomlと同じディレクトリーの`.civi-network.json`へ原子的に書き込み、現在の広告へ反映します。次の手動起動でも読み込み、config.tomlの`description`と`discovery`より優先します。書き込みに失敗した場合は成功扱いにしません。保存後に広告できなかった場合は、保存成功と広告失敗を分けて表示します。

この設定はOSのIP、DNS、DHCP、ホスト名、ネットワークアダプター設定を変更しません。保存ファイルを削除すると次回起動ではconfig.tomlの値に戻りますが、これは規格のLAN Configuration Initialize（LCI）ではありません。自動起動やsystemd登録も行いません。

## HTTPS 443の準備

新規設定ではトップレベルを次のように指定すれば、443を主ポートにしつつ8443も同じ証明書・認証・アプリで受け付けられます。

```toml
web_port = 443
web_extra_ports = [8443]
```

既存のconfig.tomlやポートは自動変更しません。開発用の既定値は8443のため、インストールしただけで9.1.4の既定443要件を満たすわけではありません。OSのポート利用権限・既存サービスとの競合・ファイアウォール・証明書の配備は別途必要です。試験では空きポート2個で本番起動経路のHTTPSを起動し、証明書検証を有効にして両方の応答を確認しました。実際の443、別LAN端末、Windows/Linuxでのマルチキャスト発見は今回未試験です。

## 残る要件

IP設定ページとOSバックエンド、DHCP/AutoIP/固定IPの運用、重複IP検出、LAN初期化、物理的な状態・識別表示、mDNSホスト名処理、IVIドライバー、登録、セキュリティの詳細要件、全条項へのマッピングと実機適合試験は残っています。[対応表](LXI.md)を参照してください。

## 参照

- [LXI Device Specification 1.6.2](https://public.lxistandard.org/specifications/LXI_1.6_Specifications/LXI_Device_Specification_1.6.2_2026-04-02.pdf)
- [識別スキーマ2.0の説明](https://public.lxistandard.org/schemas/InstrumentIdentification/2.0.html)
- [公式XSD](https://public.lxistandard.org/schemas/InstrumentIdentification/2.0)
