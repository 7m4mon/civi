# メモリー書込試験結果 — 2026-11-12

Python driver0.13.1 → Pi → IC-7300 MAIN1.42。空99番を退避して使用。

| 確認項目 | 最終結果 |
|---|---|
| 全record書込 | 8組の39byte recordでmode/split/DATA/tone/FIL/group/nameを変更・完全読戻し |
| API | record setter、write_and_read、clear |
| 判定 | 実機/模擬24チェック成功。制御した再実行も24成功 |
| 表示中の空memory | 03FF/04FFを[空memoryの応答仕様](EMPTY_MEMORY_2026-11-12.md)として処理 |
| 復元 | 99番を空へ、両VFOを元へ復元。memory書込permissionを元のFalseへ戻し、PTT OFF・queue空 |

再現手順：`tools/ivi_memory_write_acceptance.py`。

[実装・試験結果一覧](IMPLEMENTATION_AND_TEST_RESULTS.md)
