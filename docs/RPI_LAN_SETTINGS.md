# Pi有線LANの一時適用・確認・保存

`codex/rpi-lxi`ブランチの機能です。Windows版では既定無効です。対象はNetworkManagerで管理された1つの有線NICで、WLANの設定やWi-Fi資格情報は変更しません。

## 手動起動

PiのLAN設定画面には、現在のWebパスワードで操作するIPv4 Ping応答の読取・有効/無効・保存もあります。Pi全体のIPv4応答に作用し、LAN RESETで有効へ戻ります。[操作と検証](RPI_PING.md)を参照してください。

更新したWebでは、System hostnameの空欄/空白保存で工場既定の`civi`へ戻せます。Descriptionは`CIVI <識別番号>`へ戻ります。これらはLAN RESETの「最後のユーザー設定名を保持する」動作とは別です。[既定値と識別APIの仕様](LXI_DEFAULTS_API.md)を参照してください。この更新を使うにはヘルパーとCIVIを再起動し、Webページを再読み込みします。

Pi上でプロジェクトのディレクトリーへ移動し、別のターミナルで次を実行します。

```bash
sudo python3 -m civi.pi.broker --owner nom --interface eth0
```

これは有線LAN設定だけを受け付ける補助プロセスです。TCPポートは開かず、root所有ディレクトリー内のUnixソケットを指定ユーザーだけに公開します。CIVI本体をrootで起動する必要はありません。sudo権限の永続的な緩和やサービス登録は行いません。

起動時に対象の有線プロファイルUUIDを検証し、root所有の`/var/lib/civi/lan-eth0.json`へ保存します。以後は未接続でも同じプロファイルを読み取り、本体LAN RESETでDHCP＋AutoIPへ初期化できます。異なるアクティブUUIDや他NICに紐づくプロファイルは拒否します。初回から未接続なら`--profile-uuid <有線UUID>`を明示してください。[設定と実機試験](RPI_DISCONNECTED_RESET.md)を参照してください。Webの一時適用は引き続きアクティブ接続が必要です。

標準出力へ時刻付きログを表示します。起動時はCIVI版・作者・PID・対象NIC・ソケット・許可ユーザー・現在のホスト名/IPを表示します。設定変更、確定、復元、LAN RESET、エラーと状態変化を記録し、何も操作しない間も60秒ごとに稼働時間・要求件数を表示します。通常の状態読取要求は抑制し、`--verbose`で各読取要求も表示します。要求本文・パスワード・確認用トークンはログへ出しません。

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

NetworkManagerのCheckpointCreateで対象NICだけのチェックポイントを作り、確認期限を設定してから`nmcli device modify`で稼働中の設定だけを一時変更します。時間切れの復元はCIVIのタイマーではなくNetworkManagerが行うため、Web接続やCIVI本体が終了しても期限が残ります。確定前の接続プロファイルは変更しません。この間は保存プロファイルの値とactive_ipv4が異なります。

Netplan管理のプロファイルを`connection modify --temporary`で変更した後に保存すると、実Piでプロファイルが削除扱いになる問題を検出しました。この方式は使用せず、デバイスへの一時適用とプロファイルへの確定保存を分けています。確定時にはプロファイルと有線アドレスが維持されていることを再確認してからチェックポイントを解除します。

復元後は保存項目と現在のIPv4を読み戻します。チェックポイントが消えただけでは復元成功とせず、値が一致しなければrecovery_requiredです。NetworkManagerやOS自体の障害、物理切断まで回復を保証するものではありません。

### ホスト名の変更・保存

Read wired LANで現在のホスト名も読み込みます。System hostname欄へ1–63文字の英数字とハイフンによる単一の名前（例: `civi-pi`）を入力し、Save hostnameで保存します。大文字は小文字へ統一します。空欄は既定名へ戻し、localhost・数字だけ・ドメイン付きの名前は拒否します。

この操作はPi全体の永続ホスト名を`nmcli general hostname`で変更します。IP変更の90秒タイマーとは別の即時保存です。IP変更の確定待ち中やCIVIの送信操作中は拒否します。保存後に名前を読み戻し、有線プロファイルと稼働IPv4が変わっていないことを確認します。失敗時は以前の名前の復元を試み、復元を確認できない場合も明示的なエラーにします。OS停止・プロセス強制終了時までのホスト名復元は保証しません。

Pi用機能が有効な場合、AvahiへmDNS広告を集約し、CIVIのSRVターゲットはAvahiが実際に取得した名前に追従します（例: `civi-pi.local.`、競合時は`civi-pi-2.local.`）。希望するOSホスト名と取得後のmDNS名を分けて表示・保存します。Windows共通版はzeroconfを維持します。DHCPサーバーのDNS更新、既存HTTPS証明書の更新は含みません。[競合処理と保存の範囲](DISCOVERY_NAMES.md)を参照してください。

設定は起動中のLANヘルパーとCIVIを通じて適用します。[ローカルLAN RESET](RPI_LAN_RESET.md)はPi付属キーボード/画面から実行できます。本体表示とIdentifyは[RPI_PANEL.md](RPI_PANEL.md)を参照してください。

補助プロセスもCtrl+Cで終了します。未確定の変更があれば復元を試みます。異常終了してソケットが残った場合は、対象の補助プロセスが停止していることを確認した上で、そのソケットだけを管理者が削除して再起動します。自動起動は追加しません。

## 実装上の参照

- [NetworkManagerチェックポイントAPI](https://networkmanager.dev/docs/api/latest/gdbus-org.freedesktop.NetworkManager.html)
- [nmcliの一時プロファイル変更](https://networkmanager.dev/docs/api/latest/nmcli.html)

## 使用中IPの重複検出

更新したヘルパーは対象有線NICでARPを受信監視し、使用中IPへの別MACの名乗りを検出すると切断します。CIVIはFaultを保持し、監視不能を正常扱いしません。反映にはCIVIとヘルパーの両方を手動再起動します。自動起動は追加しません。[動作・復旧・隔離環境での検証](RPI_CONFLICT.md)を参照してください。

## AutoIPの返信経路

更新した手動ヘルパーは、対象有線NICに現在割り当てられたAutoIP送信元の返信を、有線上の相手へ直接返す経路を管理します。通常のWLAN経路は変更しません。AutoIPが消えたら所有する追加経路も除去し、監視失敗は正常扱いしません。[実TCP試験・予約する経路表・範囲](RPI_AUTOIP_TCP_2026-11-08.md)を参照してください。
