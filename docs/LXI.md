# LXI関連機能

対象構成はPi4・有線eth0・付属画面とローカル入力・手動起動のCIVI/helper/panelです。

| 分野 | 実装 |
|---|---|
| 接続と設定 | 有線LAN、DHCP/AutoIP/固定IPv4、DNS/ゲートウェイ、保存・確定・復元 |
| 名前と発見 | ホスト名変更、mDNS/DNS-SD、衝突回避、取得名保存、再接続時の再広告 |
| Webと識別 | HTTPS443、Welcome、LAN設定、識別XML、ローカルXSD、認証 |
| 本体 | POWER ON、LAN NORMAL/FAULT、Identify、LAN RESET、パスワード復旧 |
| driver | 全339拡張定義の型付きPython API、基本命令、配布文書と使用例 |

- [実装・試験結果](IMPLEMENTATION_AND_TEST_RESULTS.md)
- [全条項対応表](LXI_REQUIREMENTS_2026-11-10.md)
- [完了計画・手続き](IVI_6_1_COMPLETION_2026-11-12.md)

運用方法は[LAN設定](RPI_LAN_SETTINGS.md)、[HTTPS](RPI_HTTPS.md)、[装置構成](LXI_DEVICE_CONFIGURATION.md)を参照してください。
