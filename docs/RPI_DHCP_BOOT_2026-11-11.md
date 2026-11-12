# DHCP保存・再起動・LAN RESETの結果 — 2026-11-11

Pi4 eth0、Windows直結DHCP試験器、WLAN管理接続を維持。

| 確認項目 | 最終結果 |
|---|---|
| DHCP確定保存 | 新有線アドレスのHTTPSから確認・保存成功 |
| Pi再起動 | boot ID変更、保存auto mode、192.168.73.3/24、新しいACK、LAN Normal・HTTPSを確認 |
| DHCP中のLAN RESET | 復旧credential・discovery再読込、リース更新を確認 |
| 固定IPからLAN RESET | 初回DHCP ACK、192.168.73.3/24、保存auto mode、LAN Normalを確認 |
| 復元 | 192.168.73.2/24、元profile・HTTPS・LAN Normalへ復元。試験server停止 |

- LAN RESETはhelperへ接続できない場合と、初期化中に通信を失った場合を区別して報告する。

再現手順：`tools/windows_dhcp_lab.py`。

[実装・試験結果一覧](IMPLEMENTATION_AND_TEST_RESULTS.md)
