# 物理有線LANのDHCP試験結果 — 2026-11-10–11

Pi4の実eth0とWindows DHCP試験器。WLANと元profileを保持。

| 確認項目 | 最終結果 |
|---|---|
| 取得 | 192.168.73.3/24、LAN Normal。要求option1/3/6を実通信で確認 |
| 自然更新 | 初回ACKから60.01秒後に更新。新gateway .254・DNS .54を再活性化なしで反映 |
| 失効 | server無応答でleased address/gateway/DNSを破棄、AutoIPへ移行しFaultを保持 |
| 再取得 | server復帰で新lease取得、client再活性化なしでNormalへ復帰 |
| option省略 | gateway/DNSなしでも取得、該当値は空、Normal |
| hostname option | other-dhcp-name受信後もsystem hostname civiを維持 |
| 復元 | 全trial後に192.168.73.2/24へrollback、profile UUID/settings一致 |

- LAN監視は保存profileと実効IPv4を区別して評価する。

再現手順：`tools/windows_dhcp_lab.py`。

[実装・試験結果一覧](IMPLEMENTATION_AND_TEST_RESULTS.md)
