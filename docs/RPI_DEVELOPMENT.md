# Raspberry Pi LXI開発ブランチ

2026-11-06から`codex/rpi-lxi`で開発します。Windows用の作業フォルダーと分けたGit worktreeを使います。同じリポジトリの履歴を共有し、共通のSCPI・CI-V・Web機能は引き継ぎます。LXI準拠を宣言する段階ではありません。

## 分離の範囲

- 元のWindows作業フォルダーはそのまま維持します。Pi固有の変更をmainへ自動でマージしません。
- PiのOS依存処理は`civi/pi/`に置きます。通常の`python -m civi`はこの処理を呼び出しません。
- 手動起動を維持します。systemd・ログイン時起動・常駐サービスは追加しません。
- 設定ファイル、TLS秘密鍵、保存パスワードは分岐にコピーしません。

## 最初の実装: NetworkManagerの読み取りと変更プレビュー

Pi上で現在の有線LAN設定を読み取れます。sudo不要の読み取りコマンドだけを呼び出します。

```bash
python3 -m civi.pi --interface eth0
```

実行環境の仮想環境を使用する場合は、そのPythonを指定してください。インターフェース名は実機に合わせます。

バージョン、接続プロファイルUUID、保存されたIPv4設定、現在のIPv4アドレス・ゲートウェイ・DNS・ホスト名をJSON出力します。Windowsでは明示的に非対応エラーを返します。未接続・複数の有効プロファイル・無線LANは初期対象外としてエラーにします。

次のようなJSONを用意すると、入力を検証して変更コマンドの配列を出力します。

```json
{
  "mode": "static",
  "hostname": "civi",
  "address": "192.0.2.20",
  "prefix": 24,
  "gateway": "192.0.2.1",
  "dns": ["192.0.2.1"]
}
```

```bash
python3 -m civi.pi --interface eth0 --plan network.json
```

これは変更プレビューです。出力されたコマンドは実行せず、保存も適用も行いません。`applied`は必ず`false`です。設定適用と再接続確認、時間切れのロールバックを実装するまでは、Web設定の保存先につなぎません。

自動設定の入力は`{"mode":"automatic"}`です。DHCPに加えてAutoIPフォールバックを含む計画にし、対応しないバージョンでは拒否します。NetworkManagerの`ipv4.link-local=fallback`は1.52以降のため、古いOSでAutoIPを省略したまま成功扱いにはしません。実際のDHCP失敗・AutoIP切替動作は未検証です。

入力検証では、ホスト名、IPv4アドレス、プレフィックス、同一サブネット内ゲートウェイ、DNSを確認します。nmcliは引数配列とタイムアウト付きで呼び出し、シェルには渡しません。プロファイル名ではなくUUIDを使います。

## 次の開発段階

1. Pi側のOS・NetworkManager版・対象有線NICを記録し、読み取りを実機で確認する。
2. 権限を限定した適用処理と、再接続確認・時間切れ時の復元を実装する。
3. Pi用Web設定画面とOS設定を結合する。
4. LANが使えなくても操作できるLCIと、状態・Identify表示を作る。
5. mDNSの残要件、IVIドライバー、必須条項の検証を進める。

今回は実機のネットワーク設定を変更していません。読み取り・入力検証・変更プレビューは模擬コマンド応答で検証します。これだけでLXIのLAN設定要件を満たしたとは扱いません。

## 参照

- [NetworkManager nmcli](https://networkmanager.pages.freedesktop.org/NetworkManager/NetworkManager/nmcli.html)
- [NetworkManager IPv4設定とバージョン条件](https://networkmanager.pages.freedesktop.org/NetworkManager/NetworkManager/nm-settings-nmcli.html)
