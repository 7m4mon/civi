# Raspberry Pi移植段階

初期版はWindowsで検証します。共通PythonコードはPython 3.11以上を対象にし、COM依存の処理はpyserial設定に閉じ込めています。Linuxでは`/dev/serial/by-id/...`を設定できます。NIC情報はpsutil、機器発見はzeroconfで取得します。

移植段階で以下を実装・納品します。現時点ではPiで導入・自動起動できることを完了条件にしていません。

- Raspberry Pi OS 64bitのPython環境、権限（dialout）、安定したデバイスパス、証明書配備とファイアウォールを含む導入手順。
- systemdサービス、専用ユーザー、パスワード環境ファイル、終了時の停止処理、再起動ポリシー、ログ運用。
- NetworkManager等を分離したLAN設定バックエンド。DHCP/AutoIP/固定IP、保存、妥当性確認、設定復旧。
- GPIOのLAN状態表示・機器識別・LAN設定初期化ボタン。
- LinuxのUSB切断・再接続・権限エラー、マルチNIC、LANケーブル差し替え検証。

systemdユニットやOSネットワークを変更する未検証スクリプトは初期版へ含めません。USB通信後の隔離を、OSの自動再起動で不用意に解除する問題も移植時に扱います。
