# Piホスト名の保存試験 — 2026-11-07

Pi4 / Debian13.7 / NetworkManager1.52.1。固定192.168.73.2/24、WLAN管理接続を使用。

| 項目 | 結果 |
|---|---|
| backend保存 | civi→civi-hostname-test→civi。NetworkManager・kernel・/etc/hostnameの3値が一致 |
| LAN維持 | 保存profile UUID、IPv4、WLAN設定が一致 |
| 本番Web | 利用者がcivi2へ保存し、Pi再起動後のhostnameと/etc/hostnameがcivi2で一致 |
| 発見 | 再起動後のSRV接続先civi2.local.と機器TXTを外部PCで取得 |

保存はNetworkManagerの永続system hostname操作です。IPv4の90秒checkpointとは別に即時反映します。操作は[LAN設定](RPI_LAN_SETTINGS.md)、現在の設定項目は[装置構成](LXI_DEVICE_CONFIGURATION.md)を参照してください。
