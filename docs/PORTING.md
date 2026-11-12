# Raspberry Piへの導入

Raspberry Pi OS 64bit、Pi4、有線LAN、IC-7300のUSB接続を使用します。

1. ソースをPiへ配置し、Python3.11以上で仮想環境を作成する。
2. `python -m pip install -e '.[pi]'`で導入する。
3. `config.pi.example.toml`を`config.toml`へコピーし、`/dev/serial/by-id/`の安定したパスを指定する。利用者は`dialout`グループに所属させる。
4. [HTTPS設定](RPI_HTTPS.md)で証明書と443番への権限を準備する。
5. [デスクトップ起動](RPI_DESKTOP.md)に従い、`bash desktop.sh --install`でアイコンを配置する。

起動は手動です。CIVIアイコンからgateway/helper/panelを開き、必要なsudoパスワードはhelperの端末へ入力します。パネルは本体画面に表示したまま使います。

- [設定例](../config.pi.example.toml)
- [LAN設定](RPI_LAN_SETTINGS.md)
- [Webパスワード](WEB_PASSWORD.md)
- [実装・試験結果](IMPLEMENTATION_AND_TEST_RESULTS.md)
