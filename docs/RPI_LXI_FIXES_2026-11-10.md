# Piでの設定・識別・表示試験 — 2026-11-10

Pi gateway0.1.0、Windows driver0.13.1、IC-7300、eth0固定192.168.73.2。有線TLSは信頼した証明書のcivi.local名を検証。

| 項目 | 結果 |
|---|---|
| VISA位置指定 | 導入済みdriverで3種類のINSTR形からraw TCP5025へ解決。774000Hz/AM/PTT OFF/queue空 |
| Description | 本番WebでASCII64文字保存→先頭63byteへ正規化、4サービスへ再広告、元へ復元 |
| NIC | 識別XMLのLXI interfaceはeth0のみ。有線から4サービス取得、WLAN HTTPS管理は維持 |
| Identify/Fault | 開始→本体点滅→ケーブル抜去→LAN FAULT、挿し直し→Normal/Identify OFF、再開始/停止も成功 |
| 広告 | HTTP/LXI/SCPI/HTTPSのports443/443/5025/443、SRV civi.local.、TXTのmodel/version一致 |
| Pi関連自動試験 | 72成功、Node専用1スキップ。対応JavaScriptはWindowsで成功 |
| 復元 | Description、IP、認証・設定ファイルhashが試験前一致。3プロセス稼働、PTT OFF |

[結果一覧](IMPLEMENTATION_AND_TEST_RESULTS.md)
