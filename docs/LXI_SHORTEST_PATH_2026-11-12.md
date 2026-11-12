# LXI対応への最短経路 — 2026-11-12

利用者の指示により、機能の追加実機試験はいったん止める。
[追加試験表](IVI_ADDITIONAL_TESTS_2026-11-12.md)は根拠・不足範囲のバックログとして
維持する。そこに挙げた全試験を、今から無条件で追加実行する計画にはしない。
同時に、試験を止めたことを理由に未確認APIを合格へ変更しない。

## ドキュメントだけで完了する状態か

**まだ文書だけでは完了しない。** 残る中心はIVI適合の扱い・最終配布物・登録である。
PiのLAN/Web/識別/状態表示等には既存の実装・範囲付き実機記録がある。
これらの試験を繰り返すより、残る正式なゲートへ作業を集中する。

| 順番 | 次に閉じるもの | 完了条件 |
|---|---|---|
| 1 | IVI名称・範囲・証拠の扱いの一次照会 | 個人nomulabo／NL候補、gatewayを制御するPython driver、公開機能の範囲と除外、必要な申請資料・証拠の扱いについて回答を得る |
| 2 | 最終IVI配布物と適合資料 | 回答を反映した名称・対応範囲、API/help/compliance/examplesが一致。残すAPIの必要な適合根拠を閉じ、最終artifactのclean install/build/exampleを確認 |
| 3 | IVI登録 | 実際に手続きを行い、driver registration databaseへの掲載を確認 |
| 4 | LXI最終判定 | 固定したPi装置構成・版・文書と全適用必須条項の根拠を一致させ、未達が残っていないことを確認。認証・ロゴは別途扱う |

名前候補への問い合わせと、完成済みドライバーの登録申請は別の段階である。
照会前に未確認を全て合格へ変えたり、NLの割当を既成事実にする必要はない。
未送信の具体的な草案は[申請準備資料](IVI_SUBMISSION_PREPARATION.md)へ更新した。
この文書の作成だけでは、メール送信・公開・登録は実行しない。

## 試験を増やす前に範囲を確認する理由

2026-11-12に公式原文を再確認した。
[IVI Core 1.0の機能範囲](https://github.com/IviFoundation/IviDrivers/blob/main/IviDriverCore/1.0/Spec/IviDriverCore.md#extent-of-instrument-functionality-covered-by-ivi-drivers)
には、サービス／工場校正や通信設定等を高水準driverへ露出しない例外が示されている。
これは校正項目を未試験のまま合格にできるという意味ではない。
現在公開している該当APIを残すなら、そのAPIの要求は未解消のままである。
例外を採用する場合は実装・API・対応表・文書が一貫する必要がある。
今ある機能をこの段階で勝手に削除したり、全体を受信専用と宣言し直したりはしない。

一方、一般の受信・送信機能を任意に全て省ける規定とは読まない。
[Coreの検証手順](https://github.com/IviFoundation/IviDrivers/blob/main/IviDriverCore/1.0/Spec/IviDriverCore.md#unit-test-procedure)
や、最終test setup・対応範囲に必要な根拠は残る。
追加試験表の95メモリー枠等は当方の保守的な適用判断も含むため、正式な扱いが
未確認のまま大量の再試験を先行させず、既存証拠の利用可否と範囲を先に確認する。
照会回答を得るまでは、試験不要や例外承認を得たとは記載しない。

## 外部手続きを文書で代用しない

[LXI Device 1.6.2](https://public.lxistandard.org/specifications/LXI_1.6_Specifications/LXI_Device_Specification_1.6.2_2026-04-02.pdf)
6.1はGeneration 2026または2014に適合するIVI driver、11.2はIVI登録DBへの掲載を
求めている。[IVI Python 1.0](https://github.com/IviFoundation/IviDrivers/blob/main/IviDriverPython/1.0/Spec/IviDriverPython.md#ivi-python-driver-conformance)
も、規定への適合とWeb登録を求める。SCPI/SOCKETが正常に動くことや文書が存在する
ことだけでは、この登録は済んだことにならない。

現時点の「LXI実装・検証中／準拠・認証未宣言」という表示は維持する。
APIの機能網羅試験の続行よりも、上記一次照会・配布物／適合資料の整理を次の作業にする。
新しい実機操作・無線機設定変更・メール送信は本方針の整理中には行っていない。
