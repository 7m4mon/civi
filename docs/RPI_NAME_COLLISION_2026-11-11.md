# 物理LANの名前衝突・再起動結果 — 2026-11-11

Windows/Pi有線直結。Pi eth0固定192.168.73.2/24、AvahiとCIVIの4サービスを観測。

| 確認項目 | 最終結果 |
|---|---|
| hostname競合 | civi-2.local.を取得 |
| service競合 | 4サービス共通CIVI CIVI-0001 (2)を取得 |
| 希望値 | OS hostname civiとDescription CIVI CIVI-0001を維持 |
| 再起動 | 競合peerを停止後、Pi全体再起動でも取得名を再利用 |
| 復元 | 元の名前・固定IP・設定へ復元。試験peerを停止 |

再現手順：`tools/mdns_collision_peer.py`。

[実装・試験結果一覧](IMPLEMENTATION_AND_TEST_RESULTS.md)
