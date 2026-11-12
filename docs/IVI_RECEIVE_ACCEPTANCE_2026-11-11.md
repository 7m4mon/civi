# Core・受信試験結果 — 2026-11-11

Python driver0.13.1 / Windows CPython3.14.5 x64 → Pi CIVI0.1.0 TCP5025 → IC-7300 MAIN1.41。

| 確認項目 | 最終結果 |
|---|---|
| Core/受信 | 実機40、独立模擬39チェック成功 |
| 受信設定 | 16property、実機/模擬とも65チェック成功 |
| descriptor/menu読取 | 実機292件中290成功。全216menu読取成功 |
| AM filter shape | AMはNAK。USB/CW/LSBで成功 |
| TX Inhibit | MAIN1.41のNAKは機種FW条件。[MAIN1.42結果](IVI_TX_INHIBIT_2026-11-11.md)を参照 |
| NR raw | 要求0/128/255 → 8/136/248 |
| 内/外PBT raw | 要求0/128/255 → 2/128/253 |
| 復元 | 選択927000Hz/AM/FIL2、他14100000Hz/USB/FIL2、DATA OFFへ復元。66非meter読取結果も一致 |
| 配布物 | 記録したwheelを新規環境へ導入し、source hash照合・読取smoke成功 |

- 各raw読戻しは有界・単調・安定。要求値の厳密echoとは区別し、実適用値を取得する。
- PTT/VOX/BK-IN/tunerはOFF。変更対象は受信設定に限定し、退避値へ復元した。

再現手順：`tools/ivi_receive_acceptance.py`, `tools/ivi_receiver_settings_acceptance.py`, `tools/ivi_readonly_acceptance.py`。

[実装・試験結果一覧](IMPLEMENTATION_AND_TEST_RESULTS.md)
