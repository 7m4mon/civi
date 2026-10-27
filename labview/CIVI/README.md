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
| 03 Examples | 基本操作、読み取り、設定などの使用例 |
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
全VIの内部依存パスの厳密な点検は未完了です。

残作業: 応答の厳密な形式・範囲検証、Mode文字列の検証、入力値の検証、アイコン・端子・VI説明の統一、配布版の依存関係確認。自動テストやNI認証は未実施です。
