# VI説明と参照確認

以下は現行API・通信VIの11個とFrequency Sweep Exampleへ入力した英語のVI説明です。LabVIEWのVI Properties → Documentationで入力し、コンテキストヘルプへの表示を確認しています。端子名も既存の接続を保ったまま統一・確認しました。

## 実際の参照先を確認する

1. 変更を保存し、すべてのVIとプロジェクトを閉じる。
2. この配布フォルダーの`CIVI.lvproj`を開き、Frequency Sweep Exampleを開く。ロード時に不足VIの検索・置換が出ないことを確認する。
3. Project ExplorerのFiles表示で、CIVIの現行APIとCommunicationのVIが配布フォルダーの`VIs`内にあることを確認する。旧`Documents/LabVIEW Data`への参照があれば記録して修正する。
4. NI-VISA、LabVIEW標準VI、Stall Data Flow.vim、File Dialog、Write Delimited SpreadsheetなどのNI提供部品はLabVIEWインストール先への参照でよい。配布用にコピーしない。
5. Sweepが`03 Examples`内にあることを確認する。グループへの移動とプロジェクトの保存は完了している。VI実ファイルの移動は不要。

静的確認では23件すべてのプロジェクト参照が存在し、抽出したCIVIのVI名にも不足はなかった。LabVIEWのFiles表示でも、CIVIのVI一式が配布フォルダーの`VIs`配下にあり、NI標準部品はLabVIEWインストール先にあることを確認した。旧`LabVIEW Data`の参照は表示されなかった。別PCでのクリーン環境確認は未実施。

## 共通の端子名と配置

現行Session APIは次の名前に統一・確認済み。コネクタの配置変更や型変更は行っていない。

| 位置 | 名前 | 用途 |
|---|---|---|
| 左上 | VISA Session in | Initializeで開いたセッション |
| 左下 | error in | 上流エラーと実行順序 |
| 右上 | VISA Session out | 次の操作へ渡すセッション |
| 右中央 | 各測定値・応答 | Frequency (Hz)、Mode、S Meter (raw)等 |
| 右下 | error out | 通信・解析・機器エラー |

Initializeは`VISA Resource Name`入力、Closeはセッション出力なし。文字列ラベルは英語、単位はラベルに含める。アイコンは`CIVI`と機能の略称（INIT、CLOSE、QUERY、WRITE、FREQ、MODE、SMET、ERR、LF）を基準とする。

現行API・通信VIの11個は無線機風アイコンへ変更済み。SET／READを文字で区別する。ExampleとLegacyは従来のアイコンを保持する。全23種類の完成PNGは`icons/complete-v2`にあり、`manifest.csv`で対応を確認できる。

## VI Documentation用の英文

### CIVI Initialize.vi

Opens a VISA connection to the CIVI SCPI gateway. Enables LF read termination (ASCII 10) and sets the I/O timeout to 10000 ms. Returns the open VISA session and error status. Does not reset or identify the instrument. Close the session with CIVI Close.vi.

### CIVI Close.vi

Closes the VISA session using VISA Close. Accepts an upstream error so cleanup can still run. Returns the error status from VISA Close.

### CIVI Query.vi

Sends a SCPI query through an existing VISA session and reads a response of up to 4096 bytes. CIVI Ensure LF.vi appends LF when needed. Read termination and timeout are configured by CIVI Initialize.vi. Does not open or close the session. Returns the response string and communication error status.

### CIVI Write.vi

Sends a SCPI command through an existing VISA session. CIVI Ensure LF.vi appends LF when needed. Does not read a response or verify instrument acceptance. Use completion checking, readback and CIVI Error Query.vi as appropriate. Does not open or close the session.

### CIVI Ensure LF.vi

Returns Command unchanged if it already ends with LF; otherwise appends one LF byte. Does not interpret literal backslash-n text or normalize repeated trailing line endings.

### CIVI Set Frequency.vi

Formats and sends SENS:FREQ with an integer frequency in Hz. Sends the command only; does not perform readback or query the instrument error queue. Use CIVI Read Frequency Session.vi and CIVI Error Query.vi to verify the result.

### CIVI Set Mode.vi

Formats and sends RAD:MODE with the supplied mode string, such as AM or USB. Sends the command only; does not validate the string, perform readback or query the instrument error queue. Use CIVI Read Mode Session.vi and CIVI Error Query.vi to verify the result.

### CIVI Read Frequency Session.vi

Queries SENS:FREQ? through an existing VISA session and parses the response as an integer frequency in Hz. Returns communication and parsing errors. Does not open or close the session.

### CIVI Read Mode Session.vi

Queries RAD:MODE? through an existing VISA session and returns the response as a mode string. Does not open or close the session.

### CIVI Read S Meter Session.vi

Queries READ:SMET? through an existing VISA session and parses the response as an integer raw S-meter value. The raw value is not a calibrated dBm measurement. Returns communication and parsing errors. Does not open or close the session.

### CIVI Error Query.vi

Queries SYST:ERR? and parses one entry from the error queue for the current connection. Returns the SCPI error code separately. A nonzero SCPI code produces LabVIEW error 5000 with the full response in source. Communication and parsing errors take precedence. This VI does not drain the entire queue. Check error out before interpreting the numeric SCPI code.

### CIVI Frequency Sweep Example.vi

Sweeps integer frequencies specified by Start, Stop and Step in kHz and records raw S-meter values. Sets and reads back the mode once before the sweep. Displays the XY graph after the loop finishes. The panel STOP button ends the loop after the current iteration. On normal completion or panel STOP, restores and verifies the original frequency; the mode is not restored. After closing the connection, offers a CSV save dialog. CSV columns are frequency in kHz and raw S-meter value, without a header. Cancel skips saving. Error recovery and automatic input validation are not implemented.

## 配布対象

現行API、Communication、Examplesを記事の対象とする。Legacyは試作として区別し、現行APIから参照しない。Legacyファイルの物理移動・削除は参照確認後に判断する。測定CSV、個人用UI状態、作業日記はドライバーの配布対象に含めない。
