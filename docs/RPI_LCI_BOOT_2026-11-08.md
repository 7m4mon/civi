# LAN RESET後の未接続起動試験 — 2026-11-08

Pi本体でLAN RESET、有線ケーブルを抜いてPi全体再起動、デスクトップから手動で3プロセスを起動。WLAN管理接続を使用。

| 項目 | 結果 |
|---|---|
| 保存 | DHCP/AutoIP、discovery有効、復旧認証を再起動後も保持 |
| ケーブルなし | 本体LAN Fault、ローカル復旧操作へ到達 |
| 挿し直し | AutoIPのkernel/helper状態、ローカルHTTPSと有線上の新規discovery受信を確認 |
| 復元 | 元の固定192.168.73.2へ戻した後、外部PCからTCP/HTTPS/SCPI成功 |

- AutoIP自体への外部TCPは[別試験](RPI_AUTOIP_TCP_2026-11-08.md)に記録。

[結果一覧](IMPLEMENTATION_AND_TEST_RESULTS.md)
