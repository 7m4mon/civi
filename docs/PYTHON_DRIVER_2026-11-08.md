# Pythonクライアント基礎実装 — 2026-11-08

後続更新: クライアント0.2.0とCIVIに[受信基準状態へのreset](RECEIVE_RESET.md)を
実装しました。以下の0.1.0時点で未実装だったresetは模擬検証済みです。
その後[本体パーシャルリセット後の実測・復元試験](PARTIAL_RESET_CAPTURE_2026-11-08.md)も
完了し、両VFO・運用/スコープ57項目の復元を確認しました。最終要件照合は残ります。
最新全体試験は293成功・1スキップ。

LXIの必須未達であるドライバーを進めるため、CIVI本体とは別に
`drivers/civi-ic7300`へ実験用Pythonクライアントを追加した。
**IVI適合ドライバーの完成・登録ではなく、6.1/11.1/11.2は引き続き未達。**

## 方針と規格

[LXI 1.6.2 §6.1](https://public.lxistandard.org/specifications/LXI_1.6_Specifications/LXI_Device_Specification_1.6.2_2026-04-02.pdf)
はIVI Generation 2026または2014のドライバーを要求する。
[公式IVI仕様一覧](https://www.ivifoundation.org/specifications/default.html)の
Generation 2026にはCore 1.0とPython 1.0があり、その組合せを目標とする。
PythonドライバーはPC側でも使えるため、Piのネットワーク試験とは分離する。

接続先はCIVIゲートウェイであり、メーカー/モデルは`CIVI Project` /
`CIVI/IC-7300`。Icom USBポートや無線機のファームウェアを直接扱うものではない。
既存のLabVIEW用VIとは別の配布物。

## 今回の範囲

- `TCPIP[0]::<host>::<port>::SOCKET`を解釈し、標準socketで接続。
- ID照会、基本的なutility/direct I/O階層、タイムアウト設定、エラー例外。
- 選択中VFOの周波数/モード設定と取得、未校正Sメーター取得。
- 設定後の`*OPC?`待機。任意の操作後エラー照会（既定OFF）。
- 基本機能の模擬動作ではネットワークI/Oを行わない。
- 同一セッションの高水準操作/照会をロックで直列化。
- タイムアウト/切断後はセッションを閉じ、遅延応答を次の操作に流用しない。
- 独立したPython配布パッケージ、型ヒント、導入/API/未達一覧。

低水準のwrite/readを別々に使う場合、組全体の同期は呼出側の責任。
全VISAトランスポートやバイナリブロック、任意の無線機は対象にしていない。

## 実施した検証

Windows Python 3.14のCIVI開発環境でクライアント試験 **8成功**。
CIVIの実際のControlService＋SCPIハンドラー＋模擬バックエンドにTCP接続し、
設定→読取、エラーキュー、30回の並行照会、入力検証を確認した。
遅延応答サーバーではタイムアウト後のセッション再利用拒否を確認した。
模擬動作ではsocket生成を禁止して試験した。

追加後の全体回帰試験は **283成功・1スキップ（27.50秒）**。
スキップは従来からのLinux用Unix socket試験で、Windowsでは実行しない。

起動中の実Pi `192.168.73.2:5025`へ同じクライアントで接続し、
メーカー`CIVI Project`、モデル`CIVI/IC-7300`、774000 Hz、AM、
Sメーターraw 72、エラー空を確認した。これは読み取りのみで、
無線機設定・IP設定・パスワード・起動プロセスは変更していない。
実機の設定/復元は今回のドライバーでは試験していない。
ローカル記録はgit対象外の`tmp/python-driver-live-20261108.json`。

ソース配布物と、それから生成したwheelのビルドに成功した。
`tmp/python-driver-clean`の新規仮想環境へwheelだけをオフライン導入し、
`python -I`でソースツリー/PYTHONPATHを使わず模擬周波数設定・読取を確認。
README、Introduction、API、COMPLIANCE、py.typedの同梱も確認した。
生成物はgit対象外の`tmp/python-driver-dist/`。これはWindows Python 3.14での
配布検証で、他OS/全Python版のドライバー導入確認を意味しない。

## 必須未達の次段階

1. Resetをどの状態への復帰とするか定義し、実装と検証を行う。
   CIVIには`*RST`がなく、今回は`NotImplementedError`。
   `*CLS`や無線機のパーシャルリセットへ無断で置き換えていない。
2. 残りの適用対象CIVIコマンドを高水準APIで網羅する。
   生SCPIを送れるだけではCoreの機能網羅要件を満たさない。
3. Python規定インターフェース継承、命名/VPP-9、文書、全型情報、
   対応環境でのインストールとビルド、全必須条項を照合する。
4. 完成した適合資料をレビューし、IVI登録を行う。外部への登録申請は未実施。

詳細は配布物の[COMPLIANCE.md](../drivers/civi-ic7300/src/civi_ic7300/COMPLIANCE.md)。
次の実装作業にPiの再起動やケーブル抜き差しは必要ない。
