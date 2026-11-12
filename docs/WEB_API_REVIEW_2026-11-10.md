# Web・識別APIの試験結果 — 2026-11-10

Windows mock/JavaScript試験、隔離Pi試験、本番Pi eth0の証明書/名前検証付きHTTPS、利用者のWindows/スマホChrome表示確認。

| 項目 | 結果 |
|---|---|
| 共通header | 成功/認証失敗/HTTP例外/XML errorにno-store、nosniff、frame-denial、same-origin CSP。認証challenge/Allowを保持 |
| 識別応答 | gatewayはradio状態と独立した200。停止中gateway/利用不能な既知子機器503、不明子機器404。XSD検証成功 |
| GET/HEAD/method | text/xml識別、application/xml schema/ProblemDetails、HEAD bodyなし、405＋Allow、live情報を304 cacheにしない |
| 変更API認証 | 15 POST経路：Identify/discovery/password、Pi preview/apply/confirm/rollback/hostname/Ping、session/heartbeat/SCPI/serial/recovery/release |
| 拒否条件 | credentialなし/壊れたBasic/誤password、X-CIVI-Requestなし、foreign Origin、更新前password。拒否操作で設定変更なし |
| 表示 | 取得mDNS名/IP fallback、system hostname分離、prefix1–32に対応するsubnet mask、HTML5構文・ID・escaping |
| 自動試験 | 当該Windows全体534成功・Linux専用1スキップ。隔離Pi41成功・Node専用1スキップ |
| 本番確認 | Welcome/LAN/親子識別/XSD200、HEAD/405/404/401、eth0のみLXI、LAN Normal・panel ACK・Identify OFF、774000Hz/AM/PTT OFF/queue空 |
| 復元 | config・認証・network保存ファイルはbyte一致 |
| 画面 | 利用者がWindowsとスマホChromeの表示を確認 |

- 変更APIの受理/拒否はmockと隔離試験、本番は識別・表示・読取を確認した。
- API契約は[装置構成](LXI_DEVICE_CONFIGURATION.md)、動作中の障害表示は[Web状態試験](WEB_STATES_2026-11-10.md)。

[結果一覧](IMPLEMENTATION_AND_TEST_RESULTS.md)
