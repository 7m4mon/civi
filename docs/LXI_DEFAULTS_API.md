# 既定名と識別API

| 機能 | 動作 |
|---|---|
| 空のDescription | CIVIの工場既定サービス名へ戻して保存・再広告 |
| 空のSystem hostname | Piの既定名civiへ戻して保存。取得mDNS名は競合処理に従う |
| 識別GET | gateway本体と子無線機の状態を分離。詳細は装置構成を参照 |
| 識別schema | `/lxi/schemas/InstrumentIdentification/2.0` |
| 互換schema | `/InstrumentIdentification/2.0`。上記と同じ内容 |
| エラーschema | `/lxi/schemas/LXIProblemDetails/1.0` |

Description/hostnameの空欄復帰は自動試験・Pi模擬HTTPS・利用者による本番Web操作で確認しました。識別XML、状態コード、HEAD/405、認証の最終結果は[Web/API試験](WEB_API_REVIEW_2026-11-10.md)にまとめています。

[LAN設定](RPI_LAN_SETTINGS.md) / [HTTP応答の装置契約](LXI_DEVICE_CONFIGURATION.md)
