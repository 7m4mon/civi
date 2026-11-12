# LAN RESET試験 — 2026-11-07

Pi4の有線reset backend、本番Webによる利用者操作、独立mock gatewayの認証再読込を分けて確認。

| 項目 | 結果 |
|---|---|
| wired backend | auto/link-local fallbackへ変更、AutoIP169.254.108.9/16、最後に元profile・192.168.73.2/24へ復元 |
| Ping/他interface | 元のruntime/保存file・active profile一覧・WLANが復元後一致 |
| runtime再読込 | mock gatewayがreset ACK、旧password401・復旧password200、discovery有効 |
| 本番local reset | 利用者実行後にAutoIP広告、WLAN/hostname経由SCPI、復旧password認証を確認 |
| AutoIP維持 | DHCP timeoutを長期継続へ設定。60秒間7回の読取でアドレス・profileを保持 |

自動modeはipv4.dhcp-timeout=2147483647、staticは0。読取では対象deviceのconnection UUIDを使い、過渡期のactive一覧欠落時も保存profileを推測しません。

[再起動を含む最終結果](RPI_LCI_BOOT_2026-11-08.md) / [DHCP保存・再取得](RPI_DHCP_BOOT_2026-11-11.md) / [操作方法](RPI_LAN_RESET.md)
