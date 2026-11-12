# スキャン・バンドスタック・キーヤー試験 — 2026-11-12

Python driver0.13.1、Pi TCP SOCKET、IC-7300 MAIN1.42。PTT/VOX/BK-IN/tuner OFF、保存領域は私有backupへ退避。

| 項目 | 結果 |
|---|---|
| VFO scan | PROGRAM/FINEPROGRAM/DELTA/FINEDELTA/AUTO。実機23、模擬32チェック成功 |
| MEM scan | MEMORY/SELECTMEM/AUTO。実機22、模擬25チェック成功 |
| 動作 | 全7開始値・8回の実走行で周波数移動。各STOP後3サンプル安定 |
| バンドスタック | 11band×3slot全33件を14byte完全読戻し・即時復元 |
| キーヤー | M1–M8のテキストを書込・読戻し・即時復元。全原文は非公開backupへ保持 |
| 保存領域の結果 | 実機/模擬89チェック成功。最後に33record＋8textを全件再読取しbackup一致 |
| 復元 | P1/P2=500000/29999999Hzを維持。memory94–99は空、SQL65、両VFO一致、memory permission=False |

- 保存文字列の確認とCW実送信は別の操作。ここでは文字保存を確認した。
- ΔF・select設定の最終結果は[スキャン設定](IVI_SCAN_SETTINGS_2026-11-12.md)。
- 使用手順：tools/ivi_vfo_scan_acceptance.py、ivi_memory_scan_acceptance.py、ivi_stack_keyer_write_acceptance.py。

[結果一覧](IMPLEMENTATION_AND_TEST_RESULTS.md)
