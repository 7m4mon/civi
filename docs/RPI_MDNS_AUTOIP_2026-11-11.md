# AutoIP相手の名前解決・TCP結果 — 2026-11-11

Pi内の隔離network namespaceとvirtual Ethernet。NetworkManagerがAutoIPを割当し、Avahiと実TCP socketで確認。

| 確認項目 | 最終結果 |
|---|---|
| 正引き | getent ahostsv4 civi-autoip-peer.local → 169.254.127.84 |
| 逆引き | getent hosts 169.254.127.84 → civi-autoip-peer.local |
| TCP | port18881へrequest/reply payload一致 |
| 保存設定 | automatic、static addressなし |
| 終了 | 両namespace削除、host networkはbaseline一致 |

再現手順：`tools/pi_mdns_autoip_check.py`。

[実装・試験結果一覧](IMPLEMENTATION_AND_TEST_RESULTS.md)
