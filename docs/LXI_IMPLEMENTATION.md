# LXI関連機能の実装

SCPI・Web・機器発見は共通の機器情報と制御サービスを使います。Pi固有のネットワーク操作はローカルLANヘルパーに分離しています。

| URL/機能 | 用途 |
|---|---|
| `/lxi` | 機器のWelcomeページ |
| `/lxi/identification` | 機器・LAN情報の識別XML |
| `/devices/radio/lxi/identification` | 接続無線機の識別 |
| `/lxi/schemas/InstrumentIdentification/2.0` | 識別XSD |
| `/lxi/schemas/LXIProblemDetails/1.0` | エラーXSD |
| `/network` | 認証付きLAN・発見・パスワード・Identify操作 |
| `/api/...` | CIVI独自API |
| HTTPS443 / 8443 | Piの主ポート / 追加互換ポート。Windows例は8443 |

有線IPv4の変更はNetworkManager checkpointを使い、新アドレスから確定します。期限内に確定しなければ復元します。mDNSはPiでAvahi、Windowsでzeroconfを使います。希望名と衝突後の取得名を分けて保存し、LXI用広告はeth0へ限定します。

実装一覧は[LXI機能](LXI.md)、動作結果は[試験結果](IMPLEMENTATION_AND_TEST_RESULTS.md)、次の確認は[完了計画](IVI_6_1_COMPLETION_2026-11-12.md)を参照してください。
