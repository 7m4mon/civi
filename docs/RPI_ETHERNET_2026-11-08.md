# Pi有線Ethernetの設定・試験結果

Pi4標準eth0、Windows直結、固定192.168.73.2/24。2026-11-08の保存/再起動と11-11の100Mbps試験を区別して記録。

| 項目 | 結果 |
|---|---|
| 自動交渉 | 保存profileをauto-negotiation有効・速度制限なしに設定。再活性化後1000Mbps Full |
| Pi再起動 | 保存設定・固定IP・WLAN管理経路を保持。HTTPS/SCPIとLAN Normalを確認 |
| 100Mbps Full/Half | 両条件で有線*IDN?と証明書/名前検証付きHTTPS /lxiが成功 |
| 復元 | 保存済みauto-negotiation profileへ戻し、1000Mbps Full・固定IP・サービス復帰を確認 |

- Auto-MDIXの構成根拠と物理ラベルの判定は[装置構成](LXI_DEVICE_CONFIGURATION.md#auto-mdix-applicability-decision)。
- 一時的なlink再交渉の待ち時間と、最終復帰後の確認を区別した。

[結果一覧](IMPLEMENTATION_AND_TEST_RESULTS.md)
