# VFO・保存データ・スコープ試験結果 — 2026-11-12

Python driver0.13.1 → Pi TCP SOCKET → IC-7300 MAIN1.42。開始時VFO Aは利用者が確認。

| 確認項目 | 最終結果 |
|---|---|
| VFO | 実機/模擬57チェック。両view、周波数上下限、8mode、DATA/FIL、swap、復元 |
| 保存データ | memory101＋stack33＋keyer8＝142読取。実機200、模擬198の関連チェック成功 |
| スコープ | 実機/模擬72チェック、475点波形、固定edge52件読取、14設定復元 |
| scan STOP/resume | 15チェック。menu0179経由でresume読戻し・復元 |
| 送信band edge | factory10＋user30＝40件読取、49チェック。空user14件を含む |
| 空user応答 | USERの正しいFFはNoneへ変換。factory応答や不正payloadは通常の解析エラー |
| 最終状態 | 元の両VFO・scope設定へ復元。PTT OFF、queue空 |

- 固定edgeは読取、保存データは当該キャンペーンでは読取。書込の結果は個別のメモリー/stack/keyer試験を参照。

再現手順：`tools/ivi_vfo_acceptance.py`, `tools/ivi_storage_read_acceptance.py`, `tools/ivi_scope_acceptance.py`, `tools/ivi_scan_safe_acceptance.py`, `tools/ivi_band_read_acceptance.py`。

[実装・試験結果一覧](IMPLEMENTATION_AND_TEST_RESULTS.md)
