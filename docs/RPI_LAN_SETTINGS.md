# Pi有線LANの一時適用・確認・保存

`codex/rpi-lxi`ブランチの機能です。Windows版では既定無効です。対象はNetworkManagerで管理された1つの有線NICで、WLANの設定やWi-Fi資格情報は変更しません。

## 手動起動

Pi上でプロジェクトのディレクトリーへ移動し、別のターミナルで次を実行します。

```bash
sudo python3 -m civi.pi.broker --owner nom --interface eth0
```

これは有線LAN設定だけを受け付ける補助プロセスです。TCPポートは開かず、root所有ディレクトリー内のUnixソケットを指定ユーザーだけに公開します。CIVI本体をrootで起動する必要はありません。sudo権限の永続的な緩和やサービス登録は行いません。

CIVIのconfig.tomlへ追加します。

```toml
[pi_network]
enabled = true
socket = "/run/civi-lan/control.sock"
```

CIVIを通常ユーザーで手動起動し、`/network`のPi wired LAN configurationを開きます。

1. 管理パスワードを入力してRead wired LANで現在値を確認する。
2. 固定IPv4またはDHCP＋AutoIPを入力し、Previewで確認する。
3. Apply temporarilyで一時適用する。ここではプロファイルをディスクへ保存しない。
4. 新しい有線IPv4アドレスのHTTPS画面へ接続し、パスワード入力・Read wired LANの後、Confirm and saveで保存する。
5. 確認しなかった場合は90秒後にNetworkManagerが元へ戻す。Restore previous settingsでは即時に復元する。

確認操作は、変更後の有線IPv4宛てに接続したWebリクエストだけを受け付けます。WLAN経由の管理画面から適用や復元はできますが、確定はできません。新しいIPに合う証明書が必要です。ユーザーの証明書は自動で作り直しません。

## 復元方式と制限

NetworkManagerのCheckpointCreateで対象NICだけのチェックポイントを作り、確認期限を設定してからプロファイルを一時変更します。時間切れの復元はCIVIのタイマーではなくNetworkManagerが行うため、Web接続やCIVI本体が終了しても期限が残ります。確定前のプロファイルはメモリー内だけを変更します。

復元後は保存項目と現在のIPv4を読み戻します。チェックポイントが消えただけでは復元成功とせず、値が一致しなければrecovery_requiredです。NetworkManagerやOS自体の障害、物理切断まで回復を保証するものではありません。

ホスト名変更はチェックポイントの復元対象と一致しないため、現段階では拒否します。LCI・機器識別表示もまだありません。LXIの全LAN設定要件を満たしたものではありません。

補助プロセスもCtrl+Cで終了します。未確定の変更があれば復元を試みます。異常終了してソケットが残った場合は、対象の補助プロセスが停止していることを確認した上で、そのソケットだけを管理者が削除して再起動します。自動起動は追加しません。

## 実装上の参照

- [NetworkManagerチェックポイントAPI](https://networkmanager.dev/docs/api/latest/gdbus-org.freedesktop.NetworkManager.html)
- [nmcliの一時プロファイル変更](https://networkmanager.dev/docs/api/latest/nmcli.html)
