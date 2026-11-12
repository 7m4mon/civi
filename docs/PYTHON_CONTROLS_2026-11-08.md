# Pythonドライバー0.3.0 操作API拡張 — 2026-11-08

Pi側を操作せず、Windowsと模擬バックエンドでIVI向けPythonクライアントを拡張した。
**IVI適合/登録済みではない。** 原仕様は[IVI Driver Python 1.0](https://github.com/IviFoundation/IviDrivers/blob/main/IviDriverPython/1.0/Spec/IviDriverPython.md)。

## 実装

- `vfos["SELECTED"/"OTHER"]`: 周波数とモード/DATA/フィルターの完全レコード。
  `select("A"/"B")`、VFOモード、コピー、交換。現在のA/Bは問い合わせできないためキャッシュしない。
- `radio`: Split/RIT/⊿TX、offset Hz、PREAMP/AGC、受信スイッチ、フィルター/ATT等。
- `gains`: AF/RF/SQL/PBT/NR等18種類のraw設定。
- `meters`: rawメーターとスケルチ/OVFフラグ。校正せずdBmやW等へ変換しない。
- `scope`: メインスコープ設定、Hz単位のSPAN、相対dBのREFERENCE、固定エッジHz、
  開始/停止、475点の完全スイープ読取。欠損/範囲外値の応答を正常データと扱わない。
- `VfoMode`、`ScopeEdges`、`ScopeSweep`の不変レコードと型情報。
- utility/direct-I/Oの抽象契約と、再代入できないルートのインターフェース参照。
- ゲートウェイをimportせず、ネットワークI/Oもしない独立模擬状態モデル。

入力は送信前に型/範囲を検証。機器からの不正な値はProtocolError。
スカラー操作後の状態照会は従来どおり既定OFFで、ONにするとエラーキューも確認する。
scope開始/停止とresetはOFFでもエラーを確認する。
scope開始の2段目失敗時は転送設定を開始前へ復元する試みを行い、復元失敗は元例外へ追記する。
複数メソッドの一連操作は同じドライバー内で直列化するが、別TCPクライアントや本体操作をロックしない。
新しい送信開始API、保護メニューや校正書込みの迂回は追加していない。

## 対応表

[全339拡張定義の方向別一覧](PYTHON_DRIVER_COVERAGE.md)を生成した。
**72定義が全方向対応、2定義が読取のみ、265定義が未対応**。
DISPLAY/DUALの定数設定方向は未提供。基礎コマンド・resetはこの拡張数とは別。
同義命令、条件付き/対象外の機能は最終要件照合で整理する。
生SCPIを送れることだけで専用APIの実装済みとは数えない。

再生成: `python tools/python_driver_docs.py`、整合確認は末尾に`--check`。
パッケージ内のCONTROLS.mdとAPI.mdにも公開API・値・単位・SCPI対応を記載。

## 検証

- クライアント専用 **27成功**。独立模擬と実CIVI TCPハンドラー＋MockBackendで往復。
- 全宣言済みプロパティを、独立したゲートウェイカタログのCodecで検証。
- VFO切替・別クライアントによる選択変更、異なる応答の並行照会、read-only/不正入力を確認。
- BCDの独立ベクトルとしてSPAN 25 kHz=`0050020000`、REFERENCE -0.5 dB=`005001`、
  固定エッジ7.0–7.3 MHzの値を送信ログで確認。不完全スイープや不正応答も検証。
- 公開ソース6モジュールをmypy 2.4.1 `--strict`で検証、エラー0。
- 全体回帰 **312成功・1スキップ（28.29秒）**。

スキップはLinux専用パネルUnixソケット試験。別途この会話中にPiで **1成功（0.59秒）**
を確認済みで、今回はPi全体試験や新APIの実機試験を行っていない。
模擬メーター/波形は合成値でありRF性能の検証ではない。ゲートウェイ模擬機のTXFREQは
固定値、独立クライアント模擬はSplitのVFO値から算出する。実送信の裏付けにはしない。

## 残件

メニュー・メモリー・送信関連等の残りの適用対象API、規定文書/命名/VPP-9、全条項照合と登録。
旧バージョンで行った実機reset等の証拠を、新APIの全機能検証へ拡大解釈しない。
