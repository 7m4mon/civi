# CIVI LabVIEW driver

LabVIEW 2026 Q3 Community Edition（64-bit）で作成したCIVI用SCPIドライバーの開発版です。NI認証済みドライバーではありません。

## 開く

1. 作業中のVIを保存し、LabVIEWのVI・プロジェクトをすべて閉じます。
2. このフォルダーの **CIVI.lvproj** を開きます。
3. `My Computer → 03 Examples`から使用例を開きます。
4. 最初は読み取りだけの **CIVI Read Session Example.vi** で確認します。

同名VIを別フォルダーから同時に開くと、意図しない参照や名前の競合が起こる場合があります。今後はこのプロジェクトから作業してください。

## 接続

- 必要環境: LabVIEW 2026 Q3 64-bit、対応するNI-VISAとLabVIEWサポート。
- 接続先: `TCPIP0::127.0.0.1::5025::SOCKET`。別PCやPiではホストを変更します。
- LabVIEW起動前またはVI実行前にCIVIを起動し、無線機が使用できる状態にします。
- このWindowsの確認環境では、CIVIがCOM25のIC-7300を制御します。LabVIEWはCIVIへTCP接続します。
- LF終端、読み書きタイムアウト10000 ms。Write／Queryは末尾LFを必要な場合だけ付加します。

## プロジェクトの分類

| グループ | 内容 |
|---|---|
| 01 Basic API | Initialize、Set Frequency、Set Mode、Session版Read 3種、Error Query、Close |
| 02 Communication | Query、Write、Ensure LF |
| 03 Examples | 基本操作、読み取り、設定、周波数スイープとCSV保存の使用例 |
| 90 Legacy - experimental | 以前のQuery Once方式と試作VI。現行APIには使用しません |

`VIs/`内の実ファイルは同じ階層に保ち、プロジェクトの仮想フォルダーで分類しています。
プロジェクト全体を同じ構成で配置してください。

## 基本操作

```text
Initialize → Set Frequency → Set Mode → Query (*OPC?)
  → Read Frequency Session → Read Mode Session → Read S Meter Session
  → Error Query → Close
```

**CIVI Basic Control Example.viは、実行すると入力した周波数とモードを実機へ設定します。** 実行前に入力値を確認してください。
読み取りだけを試す場合はCIVI Read Session Example.viを使用します。

- 周波数: 整数Hz（I32）。現在のIC-7300対象範囲を表現できます。
- モード: AM、USB等の文字列。
- Sメーター: 未校正のraw整数（0～255）。dBmではありません。
- Set Frequency／Set Modeは送信を担当します。`*OPC?`、読み戻し、Error Queryで実行結果を確認します。
- Error Queryは同じ接続のエラーキューから1件取り出します。キュー全件が空であることを保証する処理ではありません。

## 周波数スイープとCSV保存

`CIVI Frequency Sweep Example.vi`は、基本APIを組み合わせて受信周波数ごとのSメーター値を取得する使用例です。実行時に周波数とモードを変更します。

| 入力 | 例 | 意味 |
|---|---|---|
| Start Frequency (kHz) | 500 | 開始周波数 |
| Stop Frequency (kHz) | 1000 | 終了周波数の上限 |
| Step (kHz) | 1 | 周波数間隔。正の整数を指定 |
| Mode Setpoint | AM | 掃引前に設定する受信モード |
| Settling Time (ms) | 0 | 各点で完了確認後に追加する待機時間 |

点数は `floor((Stop - Start) / Step) + 1`。上記の設定では501点です。Stopが刻みに一致しない場合、Stopを超えない最後の点まで測定します。StopはStart以上とし、無線機の受信可能範囲で使用してください。入力値の自動検証は未実装です。

モードの設定と読み戻しは掃引前に1回行います。各点では周波数設定、`*OPC?`、追加待機、周波数読み戻し、Sメーター取得、Error Queryを順に実行します。待機0 msでも通信時間はかかります。測定値には受信機のフィルターやAGC、Sメーターの追従が影響します。

- グラフは掃引終了後に表示します。横軸は読み戻した周波数のkHz、縦軸はSメーターraw値です。
- パネルのSTOP（Abort）は現在の反復が終了した時点で掃引を止め、取得済みの点を表示します。LabVIEWツールバーの実行中断ボタンとは異なります。
- 正常終了とパネルのSTOPでは、開始時に取得した周波数へ戻し、読み戻しとError Queryで確認します。モードは自動復元しません。
- 上流でエラーが発生した場合、復帰用の設定・問い合わせはスキップされる可能性があります。エラー時の周波数復帰は保証しません。
- 復帰処理とCloseの後に保存ダイアログを表示します。初期ファイル名は`sweep.csv`、フィルターは`*.csv`です。キャンセルすると保存せず、ダイアログ前のエラー状態を保持して終了します。
- CSVは見出しなしの2列で、順序は **Frequency (kHz), S Meter (raw)**。整数形式で保存します。STOP時も取得済みデータを保存できます。エラーが起きた点を配列から除く処理は未実装です。

```csv
500,0
501,12
502,40
```

## エラー

- VISAコード1073676293は、終端文字を受信した正常完了通知です。
- タイムアウト: VISAエラー-1073807339。
- SCPIコード非ゼロ: Error Queryがstatus=True、LabVIEWコード5000、sourceにSCPI応答全文を返します。
- SCPIコードはError Queryの数値出力でも確認できます。上流の通信・解析エラーがある場合、この数値だけを成功判定に使わず、error outを優先してください。
- VISA Closeは上流エラーがあっても接続を閉じる仕様で、Close VIは直接接続しています。OS側の解放を計測した試験はまだありません。

## 保存とコピー

別の機能を作る場合は **Save As → Copy → Open additional copy** を使います。
`Substitute copy for original`は、開いている呼び出し元も新しいファイルへ差し替えるため用途を区別してください。

Legacyグループは以前の試作VIです。現行のSession版を使用してください。

## 検証範囲と制限

IC-7300で基本3項目の取得、周波数・モードの変更と復元、SCPI正常／異常応答、タイムアウトと復帰、およびBasic Control Exampleの基本操作を確認しています。
周波数スイープの500～1000 kHz・1 kHz刻み、途中STOP、元の周波数への復帰、CSV保存と保存キャンセルも実機操作で確認しています。

プロジェクト登録23件の実ファイルと、VIバイナリから抽出できるCIVI参照名の存在を確認しています。LabVIEWのProject ExplorerのFiles表示でも、CIVIのVIがこのフォルダーの`VIs/`配下にあり、旧`LabVIEW Data`への参照が表示されないことを確認しました。NI標準部品はLabVIEWインストール先を参照します。別PCでのクリーン環境検証は未実施です。

現行API・通信VIの11個とFrequency Sweep Exampleには英語のVI説明を入力済みです。コンテキストヘルプで説明の表示を確認し、Session APIの端子名を`VISA Session in/out`に統一・確認しています。説明文と参照確認手順は[VI_REFERENCE.md](VI_REFERENCE.md)を参照してください。

現行API・通信VIの11個には、無線機風の共通アイコンを適用済みです。ExampleとLegacyのアイコンは従来のままです。完成済みの全23種類の32×32 PNGと対応表は[icons/complete-v2](icons/complete-v2)にあります。白文字、画面下の赤線（`#EC1E48`）、上端のMONのモールス符号、銀縁のつまみを共通にしています。PNGは文字を含む完成画像です。

測定CSV、個人用UI状態、作業日記は配布対象に含めません。VIはNI標準部品を含む実行環境を必要とし、PNGを別途取り込まなくても適用済みアイコンを表示できます。

残作業: 応答の厳密な形式・範囲検証、Mode文字列と入力値の検証、異常終了時の周波数復帰、別PCでの動作確認。自動テストやNI認証は未実施です。
