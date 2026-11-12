# LXI 6.1 / IVI適合検証の全件完了計画 — 2026-11-12

対象はLXI Device Specification 1.6.2の6.1が要求するGeneration2026適合driver（Core1.0＋Python1.0）。本表は現在のCIVI/IC-7300 driver全公開機能を保持する場合の、検証・レビュー・正式適合の完了条件を固定する。LXI全体認証や無限の信頼性試験は対象に含めない。

**状態：計画を確定した段階。試験の追加実行・実機操作・適合宣言は行っていない。**

## 完了の定義

- 下の全確認ID、API全方向、menu全番号、各値域/instance展開を最終artifactの一setupで完了し、条件付き契約も含め未判定0件にする。合格には実際の結果と根拠が必要。
- 過去の成功記録はケース設計と根拠に再利用する。ただし同一setupで全unit testを最低一回実行する要求は、異なる版/FWの寄せ集めで代用しない。既存手順を最終版で一括再実行する。
- 失敗した場合は実装/契約/文書を修正して影響する試験を再実行。単なる未実行をN/Aにしない。抽象契約とlocal-only・read-only・simulation専用の正当な適用差は明記する。
- R-04と全検証/文書義務が閉じれば「Core/Pythonに対する必要な検証を完了」と記録できる。REG-01と名称要件まで閉じて初めてdriver適合の全要求を閉じる。試験だけでIVI登録完了にはならない。
- 本リストは固定規格・固定公開範囲に対する開発者の完了判定基準。Foundationの認定や例外承認を先取りしない。規格改訂/公開API/対応範囲変更は基準改訂として明示する。

## 固定した対象と規格

- gateway CIVI 0.1.0、driver0.13.1を出発点とする。最終release版/hashをS-01で確定。機器はCIVI/IC-7300＋IC-7300 MAIN1.42、Pi eth0経由TCP SOCKET。
- driver実行はWindows11 x64 / CPython3.14.5を既存基準とする。gatewayがPiで動くことと、Python clientのLinux正式対応を分離。正式対応OS/bitnessを確定し、R-01の条件を適用する。
- VISAを必要としないstdlib TCP clientであるためVISA vendor/version、IVI Shared Componentsは非使用として記録。別実装を採用した場合は再評価。
- 最終完全setupにはOS名/版/build、Python/bitness、gateway/driver/profile版、FW、bus、permissions、テスト日時、全入力と結果、復元結果を保存。

- [core 1.0](https://raw.githubusercontent.com/IviFoundation/IviDrivers/0d6db45c99f89ebeec06bae2d24f70c65f491ea7/IviDriverCore/1.0/Spec/IviDriverCore.md) · SHA-256 `cab7e93878277213fd543af4b2dcf0daa3d670b81be0d7012acec8e876ecfa67`
- [python 1.0](https://raw.githubusercontent.com/IviFoundation/IviDrivers/0d6db45c99f89ebeec06bae2d24f70c65f491ea7/IviDriverPython/1.0/Spec/IviDriverPython.md) · SHA-256 `3e2aaa8e472a71a17332af185ea8503ae4c1f2d913d565262c8603321ea558fe`

規格本文は再配布せず、固定commit・章・行・段落hashで要求を追跡する。

## 実施順序と全チェック項目

| ID | 確認するもの／手順 | 合格条件 | 環境・分類 |
|---|---|---|---|
| S-01 | 最終版のdriver/gateway/profile・対応機種/FW・クライアントOS/Python/bitness・TCP経路・許可設定を固定。wheel/sdist/sourceと依存版のhashを保存。 | MAIN1.42、最終artifact hash、setup IDが全試験記録から一意に追跡できる。変更があれば影響範囲を再判定。 | 文書・配布物 |
| S-02 | 本計画の全規格段落、全API、全コマンド、全menu、全instanceを一行ずつ適用判定。対象はGeneration2026 Core1.0/Python1.0。 | 必須要求が未分類0件。非採用条件・推奨事項と必須を区別。公開APIを残すものは検証対象に残す。 | 静的レビュー |
| B-01 | constructorのid_query/reset/simulate/status-check各boolの全組合せ。options=None/dict/TypedDict/string、大小文字・空白・重複・未知key・不正型。resource/timeout正負、ID不一致・接続失敗は模擬応答で確認。 | simulate既定False、checks既定False、id_query/resetの交通が指定通り。失敗時socket解放。実機は正常ID・reset両値の接続を記録。 | 模擬＋実接続、resetは退避後 |
| B-02 | driver_version/vendor/manufacturer/model/supported_models/identification/simulation状態とaliasを全て取得。 | ASCII version形式、gateway実IDとの一致、package metadata・help・complianceとの一致。無線機とgatewayの識別を混同しない。 | 模擬＋実接続 |
| B-03 | 状態照会OFF/ONとchecked()を全typed I/O familyへ適用。正常・device-error・Python例外、nested block、別threadで確認。 | OFFで余分なqueue queryなし、ONでI/O終了後に照会・例外化、scope終了で元状態復帰。raw I/Oの文書化されたqueue保持も一致。 | 実接続＋交通観測mock |
| B-04 | error_query/error_query_all/raise_on_device_error/clear_status/wait_for_completeを空queue・複数error・正常操作・拒否操作で実行。 | 一回一件、FIFO、checksに左右されない明示取得、正しい例外/完了。壊れたcode/CSV/count/ERROR応答はmockでProtocolError等。 | 実接続＋mock異常返信 |
| B-05 | reset()とconstructor reset=Trueを退避後実行。基準両VFOと57設定、driver依存設定、完了待ち・timeout復帰を確認。 | 定義済みknown state、214非clock保護menuが不変。依存設定がreset範囲外なら実装/文書を修正して再試験。元状態を復元。 | 模擬＋実接続 |
| B-06 | DirectIo read_bytes/read_string/write_bytes/write_string/queryとtimeout GET/SET。LF、複数応答、長い応答、ASCII/bytes、待ち時間、close後を確認。 | 応答一件を完全取得、余剰は次へ保持、書込み内容一致。不正値・異常応答・遅延返信をmockで確認。 | 模擬＋実接続、障害注入はmock |
| B-07 | withのenter/exit、明示close・二重close、例外exit、失敗後の再利用/再生成と全childのclose後I/Oを確認。 | 資源解放と一貫した例外。終了sessionからのI/Oなし、local metadataは文書通り。 | 模擬＋実接続 |
| G-01 | 全API台帳の模擬側を実行。socket/serial作成を禁止して全機能・出力・permission ON/OFFを確認。 | 各concrete entry pointを正常呼出し。hardware専用では明示した拒否契約、模擬専用では正常動作。実機I/O0件。 | 独立simulation＋mock TCP |
| G-02 | 同一sessionを複数threadからtyped GET/SET、error照会、checked、write_and_read、closeの競合で使用。 | 応答混線・deadlock・途中入替なし。raw write/read一組は文書化したcaller同期で実行。共通lockの全経路を静的点検。 | mockで決定的競合＋実接続の非破壊競合 |
| G-03 | 全APIの不正引数と全応答decoderを、短い/長い/不正BCD・JSON・型・EOF・timeout・NAK・ERRORで確認。 | 標準Python例外で報告、return値へerrorを混在させない。error_queryだけはqueue情報の返却。失敗を成功にせず遅延応答を次操作へ誤対応しない。 | 既存fixture再実行＋decoder単体 |
| G-04 | 350 canonical headerの全方向とaliasをtyped API、SCPI parser、helpで突合。全339extendedを維持。未実装command/除外の記述も照合。 | Direct I/Oに逃がしたmapped判定なし。公開方向の漏れなし。機器範囲はCIVI/IC-7300で、OS管理操作の除外を説明。 | 静的＋parser/mock |
| G-05 | 全設定引数/propertyにG-APIの正常値・range端/中間/直外・全enum/bool・離散間/不正値を適用。値域はAPI.csvのsource_contractとD-*で固定。 | 各parameterの展開値と実値を保存。未展開のvalue domainが0件。合法値NAKはmode/FW条件の確定または修正後再試験。 | 模擬＋実接続。無効入力は送出前拒否も合格 |
| F-01 | RadioとVfo両経路のfrequency/mode/DATA/FIL、RIT/XIT/split、COPY両方向・swap・selectionを実行。 | D-VFO/RC-01の全条件、値・選択・副作用・元状態を確認。A/Bはowner確認済みbaselineを使用。 | 模擬＋実接続 |
| F-02 | Radio全read/write設定とGains全18設定をtyped経路で変更・読戻し・復元。source_contractの全choices/rangeを展開。 | 旧SCPI結果だけで代用せず、各setter/GETの現行artifactと条件を記録。モード依存は正しいmodeへ切替・復元。 | 模擬＋実接続 |
| F-03 | 全10meter、radio S-meter/PTT/TX frequency/FWを取得。bool/raw/範囲、変化時の妥当性を確認。 | 返却型・単位・未校正表示が一致。全meterを上限まで振らせる要求にはしない。必要なTX状態読取はX-02と共用。 | 模擬＋実接続 |
| F-04 | Scope全property GET/SET、start/stop stream、read_sweep、fixed edgesのGET/SETをD-SCOPE/RC-06で実行。 | 475点または明示out-of-range、全setting domain、52edge組、通信エラー・部分開始失敗時の復元を確認。 | 実接続＋mock失敗注入 |
| F-05 | MemoryItem record setter/write_and_read/clear、selected-memory store/display/copy/clear、空recordの03FF/04FFとVFO復帰。 | D-MEM/RC-02の全条件、39byte完全一致、空はNone/文書化error、接続維持、全backupと一致する復元。 | 模擬＋実接続 |
| F-06 | BandStackItem settings setter/write_and_read、階層/legacy facadeをD-MEM/RC-04で確認。 | 全33組のmethod/property、lossless往復、別slotへの誤書込なし、全件復元一致。 | 模擬＋実接続 |
| F-07 | KeyerItem text setter/write_and_read、全M1..M8とD-KEYの文字境界を確認。 | 全8枠一致、空/上限/不正入力、contest記号処理が契約一致。文字保存だけではCW送信合格にしない。 | 模擬＋実接続、CW再生はX-03 |
| F-08 | ScanControl全7start enum（AUTOはVFO/MEM）、STOP、7ΔF幅、resume/select bool・番号1..3・filter0..3を確認。 | 周波数移動とSTOP後安定、ΔF範囲内・選択groupへの一致。書込専用値はbaselineを目視保存し復元。 | 模擬＋実接続 |
| F-09 | Bands default/factory_count/user_count/read_factory/read_user/write_user/write_and_read_userをD-BAND/RC-07で確認。 | 全返却範囲と空FF、保存済みuser recordの変更・読戻し・復元。工場表は書き換えない。 | 実接続、protected書込は別許可 |
| F-10 | MenuItem全216のGET、全215 writableのvalue setter/write_and_read。MENU.csvの合法/不正値と各権限を展開。 | 全番号の方法/property、codec・mode・副作用・復元一致。0074はGETとSET拒否を確認。17通常副作用・10link・2calibrationも個別記録。 | 通常/副作用/link/calibを分けた実接続 |
| F-11 | 全constructor、value record/enum/exception/metadata、十種類menu helperを台帳順に実行。 | D-LOCAL/D-VALUESの正負vector、typed view/codec一致、read-only参照不変、I/Oなしguard。抽象型は具象実装へ委譲。 | simulation＋実接続sessionに結び付けたlocal操作 |
| RC-01 | VFO SELECTED/OTHERの各propertyと少なくとも一methodを各instanceに実行。A/B選択・alias、誤名拒否。 | 両instanceのGET/SET、select/COPY/swapで実作用を確認。aliasは同じ実体/宛先。 | 模擬＋実接続 |
| RC-02 | memory1..99,P1,P2の全101でrecord GET/SETとwrite_and_read。通常1..99はclearも実行。int/string/P1/P2 alias・不正指定を確認。 | 各instanceでpropertyとmethodの両方を確認。P1/P2 clearは仕様通り拒否。空/非空の元状態を完全復元。 | 模擬＋実接続。95残枠だけでなく最終一式は全101を記録 |
| RC-03 | 全M1..M8でtext propertyとwrite_and_readを実行。number/name/iterator、誤指定も確認。 | 8instanceで正常往復・復元、0/9/未知名を拒否。 | 模擬＋実接続 |
| RC-04 | 11band×3slot全33組でsettings propertyとwrite_and_read。band/slot/name・階層、tuple alias、iteratorを確認。 | nested selector混同なし。band0/12,slot0/4、誤tuple/typeを拒否。 | 模擬＋実接続 |
| RC-05 | 全216menu番号でvalue propertyと、writableではwrite_and_read。read-onlyはview/helper取得method＋GET、SET拒否理由を記録。 | 各instanceのmethod/property対応。int/四桁文字列/名前の許可aliasと未定義番号を確認。typed helperは合うkind/違うkindを全種類確認。 | 模擬＋実接続 |
| RC-06 | fixed-edge band1..13×edge1..4全52組をread/write/restore。scope selectorは0のみを確認。 | 各組の宛先と値を一致。不正band0/14,edge0/5、selector1をgatewayで拒否。profile/contextが許さない値は明示拒否契約とする。 | 模擬＋実接続 |
| RC-07 | factory1..実count、user1..実countを全件読取。user全有効indexで保存済みrecordを使うwrite/read/restore。 | 未設定user枠の正の書込が消去不能なら実行せず、当該APIの全instance検証を閉じる設計/復元手段を先に確定。未解決のままPASS不可。 | protected実接続。対象範囲・復元手段の確定が先行 |
| Q-01 | 全setterでrequestと実readbackの差を分類。NR/PBT/COMPを含む全離散化parameterの合法出力列を公式表/実測で確定。 | 各隣接離散値間に最低一値、範囲両端と不正値を確認。丸め規則・許容差を文書化し境界ごとの実値を保存。全raw値総当たりとは別。 | 実接続＋独立encode/decode vectors |
| X-01 | transmit/memory/keyer/bandstack/menu/link/calibration/powerの全既定拒否、明示許可、型拒否、simulation専用permission APIの実session拒否。 | 拒否で操作未実行・適切なerror。許可だけでは操作成功扱いにせず、各正のケースへ対応。終了時全permissionを元へ復元。 | mock＋実接続、正の危険操作は該当Xケース |
| X-02 | PTT ON→RF/状態確認→OFF。TX Inhibit False/Trueで開始許可/抑止を実確認し、元へ戻す。 | typed start/stop・状態・外部RF観測が一致。禁止状態ではRFなし。OFFだけの試験で代用しない。 | ダミーロード/適切なRF観測、明示許可後 |
| X-03 | send_cw長さ境界/全許可文字群とescaping、開始中stop_cw。 | 送出符号/終了/停止を観測し入力と一致。空/31文字/禁止文字は拒否。 | 負荷・CW観測・明示許可後 |
| X-04 | T1..T8へ識別可能な音声を準備しplay_voice各slotと再生中stop_voice。 | 指定slotの送出/停止を観測、0/9拒否。SD/音声が未準備なら合格にせずfixture準備。 | SD/音声素材・負荷・明示許可後 |
| X-05 | VOX False/Trueを適切な音声入力で、BK-IN OFF/SEMI/FULLをキー入力で確認し各停止。 | 指定動作と実送信・復帰が一致、driverが所有する開始経路の停止を確認。 | 外部audio/key fixture・負荷・明示許可後 |
| X-06 | tuner OFF/ON/TUNEを適切な整合負荷で実行し、実チューン中の停止を確認。 | 設定/実チューン/停止が一致。機種/負荷条件付き動作を明記しNAKを無条件PASSにしない。 | 適切な負荷・明示許可後 |
| X-07 | CIVIが開始したPTT/CW/voice/VOX/BK-IN/tuner各経路でdeadline・所有client切断・別client停止を確認。 | 実停止と所有権拒否が契約一致。USB断で停止を保証できない制約は明記し、停止保証を捏造しない。USB障害注入は外部停止手段付き別手順。 | gateway動作契約の検証、制御されたRF環境 |
| X-08 | antenna_output_enabled両値とlink menu10件を、通信復旧/外部端子条件を準備して変更・読戻し・復元。 | 各API・列挙値が意図した端子/通信動作を示し、切断時も復旧してbackupと一致。 | ローカル復旧経路・端子fixture・明示許可後 |
| X-09 | speak0/1/2の実音声、power_off→power_onの一往復とUSB wakeを確認。 | 可聴出力と実電源状態、再接続後のidentity/正常読取が一致。 | owner立会い・音声/電源観測 |
| X-10 | 校正menu0057/0058とuser-band書込を、許可・完全backup・復元確認手段を確定してから試験。 | 保持する公開APIを試験しないまま適合完了にしない。省略する場合はCoreの範囲例外に基づく正式scope/実装/API/help変更と再監査が必要。 | 現方針では変更未許可。計画作成は実行許可ではない |
| D-01 | 登録vendor略号・manufacturer/model/vendor token、DriverIdentifier/root/import/distribution/Introduction名を全箇所で照合。 | VPP-9に基づく有効略号とPython文法、大小文字・separatorの一貫性。NLは承認済みとして扱わない。 | 規格/名称レビュー、必要な外部手続き |
| D-02 | 全module/公開class/member/parameterのPEP8命名・layoutをlintと目視で確認。hierarchyとread-only child参照を検査。 | 必須規則の差異を解消。推奨class名/複数形等の例外は必須違反にしない。 | 静的レビュー |
| D-03 | 全公開signature/return/field/overload/genericの型、py.typed、installed consumerをstrict type checkerで確認。 | 全公開型を提供し、実値/型注釈一致、依存漏れなし。PSFサポート中のPythonを少なくとも一版確認。 | source＋clean installed package |
| D-04 | 指定名Introductionの全必須section、source/build/examples/connect/ADE/driver setting/DirectIO/coverage/known issues/supportと、存在する商標欄を目視確認。 | 所定section名・ファイル名・リンク先が正しく、最終名・最終API・実際の導入方法と一致。 | 文書の内容レビュー |
| D-05 | 全352APIのhelpを本文まで読む。各parameterの用途/合法値、返却/例外、property型/access、GET/SETのSCPI、ADE制限、copyright noticeを照合。 | 索引があるだけで合格にしない。各項目の意味・数値・mode/FW条件・例外が実装と実試験に一致。 | 全件文書レビュー |
| D-06 | ComplianceのCategory/Identification/Hardware/Software prerequisites/Unit test setup/Installation/Buildability/Failures/Additional情報を最終結果へ更新。README内包と同期。 | version/vendor/bitness/source条件/model/bus/OS版/依存/失敗が全て実記録と一致。複数setupの未試験直積を暗示しない。 | 文書＋結果照合 |
| D-07 | sdist/wheelを展開しdriver一個、__init__.py、README、help、compliance、Introduction、空py.typed、source/build説明と必要JSONを点検。 | source/installed data一致、importパス名正当、keywordsのmanufacturer/modelと実API一致、license/公開条件が明示。 | artifact静的＋新規導入 |
| D-08 | runtime/package/source metadata版とファイル版規則、該当時の32/64版の版/文書同一性を照合。 | numeric versionとASCII suffixが規則通り。DLLなし・64bit限定などの適用外は理由を記録。 | 静的レビュー |
| R-01 | 確定した対応OS/bitnessの各導入環境でclean install→instantiate/run。一OS限定でなければ最低二OS、32bit非対応を宣言しなければ32/64bitを含める。 | OSは規定の更新条件を満たす。対応範囲と実施環境が一致し、repoのsys.pathで依存欠落を隠さない。 | 新規仮想環境、最終wheel |
| R-02 | 配布物/README/help/Introduction中の実行可能な全exampleを一覧化し、同梱した全件をclean installから実行。 | 例ごとの入力/出力/期待値を保存。危険操作例は適切なfixture/許可で実行。単一simulation例のみで全例合格にしない。 | R-01の全導入環境 |
| R-03 | 配布・導入したsourceから記載手順でsdist→wheelを再buildし、別clean環境にinstall/run。 | 最低一OS/bitnessで再buildしたdriverが動作。元repo未導入でもsource/help/dataを入手可能。 | installed source、公開build環境 |
| R-04 | 固定した一setupでAPI全件のsimulation/実接続、menu/instance/value展開と全global義務を一式実行し、結果を集計。 | 全適用行PASS、残SKIP/未実行/未解決FAIL/仮の適用外0件。過去1.41と1.42の寄せ集めを一回の完全setupと呼ばない。 | 最終artifact＋MAIN1.42の一setup |
| REG-01 | IVI Python Driver Conformanceが要求するWeb登録を行い、最終driver/連絡先/complianceとの対応と掲載を確認。 | 登録DB掲載が確認できる。試験完了とは別の手続きだが、LXI6.1のdriver適合・LXI11.2を最終的に閉じる条件。 | 外部手続き、試験ケースとは別 |

## 全API・全メニューの実施台帳

- [API台帳](IVI_6_1_COMPLETION_2026-11-12_API.csv)：352項目を方向別に分けた**667行**。setter/getterを別に記録し、全行に模擬と実接続の欄を持つ。
- [メニュー台帳](IVI_6_1_COMPLETION_2026-11-12_MENU.csv)：**216項目**。番号・権限・型・具体的な合法／非合法ベクトルを展開。
- [規格要求の照合台帳](IVI_6_1_COMPLETION_2026-11-12_REQUIREMENTS.csv)：**134段落**の必須語・禁止語を含む要求と確認IDの対応。表／箇条書きで定義されるAPI・検証条件は同じ章の確認IDで全体を確認する。
- [同梱例の台帳](IVI_6_1_COMPLETION_2026-11-12_EXAMPLES.csv)：**21コードブロック**。実行例・前提sessionが必要な断片・出力/構文例を全件判別し、実行例を導入環境ごとに確認する。
- 数は試験成功数ではない。複合値・列挙値・instanceの展開実績を結果添付に残し、行だけPASSにしない。

## 共通実行規則 G-API

- API.csvの全行についてsimulationと実接続を別々に記録。property GET/SETを別件、constructor/methodとfieldも漏らさない。
- 各設定parameterは最低一合法値、range両端と内部、上下の非合法値、離散値の全候補と最低一不正値、量子化の隣接値間入力を確認。無限/連続rangeは総当たりしない。
- 複合recordは各fieldを独立に変え、他fieldを合法値固定。mode/FW依存条件は適用contextを固定し、公開範囲全体を覆う。
- 書込は退避→変更→実読戻し/外部観測→元へ復元→復元読戻し。書込専用は実動作とowner baselineで確認。ACKだけで実動作合格にしない。
- 不正型/不正値の送出前拒否は、実機へ違法値を送ることを要求しない。transport破損や通信不能はmockで注入し、実接続正常経路とは別に記録。
- local-onlyのfield/metadata/codecは、実session由来のobjectまたは実sessionと組み合わせたlocal評価で閉じる。抽象APIは対応具象APIの証拠へ委譲し、理由を明記。
- 実機が未対応のenum/valueは成功にせず、文書化したsupported context/拒否の契約へ反映するか実装修正。単に拒否した正の公開機能は未達。
- 最終runの機械可読結果は生成台帳とは別ファイルへ記録し、case ID、実入力、期待/実結果、setup ID、artifact hash、時刻、ログ、復元を含める。生成を再実行して結果を消さない。

## 値域・レコード・instanceの全条件

### D-VFO VFO・receiver・gains

- 周波数はprofile 30000/中間7100000/60000000、直外29999/60000001、非有限・不正型。whole-Hz変換は文書通り。両relative viewとRadio facadeで実行。
- modeはLSB/USB/AM/CW/RTTY/FM/CW-R/RTTY-R。DATA bool、filter1/2/3、DataFilter専用1A06経路を独立確認。modeに依存する合法条件を記録し、非対応組合せの拒否も確認。
- 全descriptorのbool False/True、choice_setting全候補、int_settingのmin/max/中間/直外。API台帳のsource_contractを正とし、型と表現可能範囲と実機で合法な範囲を区別。
- toneは67.0/内部88.5/254.1 Hz、0.1Hz刻み、下上直外・非刻みを確認。実機が更に離散化するならQ-01の全離散間の確認へ展開。
- rawは0/128/255,-1/256。NR/PBT/COMP以外も差が出たsetterをQ-01へ追加し、その未解決差があれば合格しない。

### D-SCOPE スコープ全値域

- enabled/stream/hold/TX display/VBW/markerはFalse/True、mode0..3、edge1..4、speed0..2、center0..2、display/dualは0のみ。各コード候補と最低一不正値を確認。
- spanは2500/5000/10000/25000/50000/100000/250000/500000Hz全件。referenceは-20..20dBの全0.5刻み、隣接刻み間一値と直外。不正型/NaN/inf。
- ScopeEdgesの表現は0..74800000Hz・whole kHz・lower<=upper。各辺の端/内部/順序逆/非kHzを確認。実機書込はband別の合法範囲を優先し、全13×4の組を保存・変更・読戻し・復元。
- sweep mode0..3、frequencyの符号付き範囲、475点0..160、out-of-range時0点、finite timestampを独立vectorで確認。不正長/型/点範囲/JSONの拒否。実機ではcomplete sweepを取得してmetadataを照合。

### D-MEM メモリー・バンドスタックの全record条件

- memory1..99,P1=100,P2=101。各instanceでrecord propertyとwrite_and_readの正例、通常99枠でclear。selected操作は選択とMEM modeを明示し、元のselectionと両VFOを復元。
- MemorySettings表現30000..74800000Hzとgateway profile30000..60000000Hzを別検査。全8mode、FIL1/2/3、DATA bool、TONE OFF/TONE/TSQL、tone67.0..254.1刻み0.1を一因子ずつ変える。
- 39byte recordはreceive/transmit両blockを別値にし、split False/True、select_group0/1/2/3、nameをcp932で0/1/5/10byte（ASCII/半角kana）、11byte/全角/禁止byte/不正型。paddingとdisplay_name、予約flag/BCDを確認。
- 14byte settings/39byte record、28/78桁hex、正しいlittle-endian/BCDと独立既知vector、各長さ直外、無効mode/FIL/DATA/tone flags、None/不正型。simpleとfrom/to bytes/hexを全件呼ぶ。
- bandstack全11×3をproperty/methodで確認。P1/P2のclearは拒否が正。空slotのNoneと03FF/04FF、通常VFO復帰を最終setupでも確認。

### D-KEY キーヤーと文字データ

- 全M1..M8のtext property/write_and_read、name/number/iterator。text空/1/中間/70/71文字、許可文字群全体と禁止文字/不正型/escapingを確認。
- contest記号*は記録だけと再生時の番号進行を区別し、counterを退避して専用ケースへ。実送信を伴う再生はX-03。原文8件は私有backupへ保存し公開ログへ転載しない。

### D-BAND 送信バンド境界

- factoryは実count（記録値10）、userは実count（30）を取得し有効全件とcount外/0/31/不正型を確認。コードのindex1..30とfactoryの実有効数を区別。
- BandEdgesの各端0..74800000、lower<=upper、0/内部/上限/直外/逆順、11byteの2D separatorとBCD、不正長/hex/型をlocalで確認。実機に違法band設定を押し付けない。
- 全有効user instanceでpositive write/read/restoreを実施するのが本計画の保守的判定。空slotを元へ消せない場合は、復元可能な仕様/実装を先に整えるか、正当な公開scopeを再確定する。空の上書き放置や拒否だけを成功扱いにしない。

### D-MENU メニュー全216項目

- 同名MENU.csvが番号/権限/型/合法/不正vectorの全一覧。整数はmin/max/中間/直外、choicesまたは列挙nameがあれば全候補。repeater offsetは1000Hz刻み。
- AudioFilter、Bandwidth、RgbColor、ScopeEdges、opening text、date/time/timezoneは各csvの成分別vectorを使用。複合値は一成分ずつ変え、全parameter直積の総当たりはしない。
- 215 writableでvalue setterとwrite_and_readを実行。0074はread-onlyのGET/書込拒否。十typed helperは正しいkindと異なるkind、各alias、未知番号/誤名/誤型を確認。
- 通常203件のうち副作用17件=0025,0046,0068,0069,0070,0094,0095,0163,0164,0165,0182,0183,0184,0185,0186,0187,0217を分離。clock/録音/外部キー/PTT端子状態を準備・復元。link10件、calibration0057/0058もcsvで全番号を固定。
- 既定permission拒否と明示許可の正例を区別。日付/時計は経過時間を考慮した復元を記録。通信/校正を黙って変更しない。

### D-VALUES 値オブジェクトと型

- AudioFilter: HPF0/内部10/20、LPF5/内部15/25、bypass0/25、HPF>=LPF非bypass拒否、直外。Bandwidth各0/1/2/3と-1/4。RGB各0/128/255と-1/256。
- DataFilterはboolとFIL1/2/3、0/4/誤型、encode/decode vector。VfoMode・各record・例外型は全fieldの型、構築、返却とserializationをAPI台帳で確認。
- dateは2000/2099境界・閏日・不正年/日付、timeは00:00/内部/23:59と秒/μ秒/timezone/fold拒否、UTC offsetは±14h/0/±1minと直外/秒端数。

### D-LOCAL local-onlyと抽象契約の閉じ方

- DriverOptions各keyと未知key/重複、metadata/enumの全member、ErrorQueryResult/DeviceError/ProtocolError/QueryErrorの構築・field・表示・標準例外継承を確認。
- IviUtility/IviDirectIoはabstractの直接構築拒否とUtility/DirectIoによる全具象method/propertyの実行を紐付ける。同じ物理操作を抽象宣言の分だけ重複しない。
- read-only field/referenceは値と型・変更拒否・sessionとの結び付き、local変換は独立vector/不正入力を確認。local-onlyのためにRFやmeter全scaleを作らない。
- simulation専用permission APIはsimでFalse/Trueと各不正型、実sessionでI/O0の拒否を確認。実機に適用されない正常系を架空の成功にせず、その条件付き契約を記録。

## 既存不足項目の全件対応

以下は旧残件の完全な列挙。上の最終一式試験へ統合する。既存成功記録は削除しない。

### L-FACTORIES

対応確認ID：F-11, RC-05

- `MenuCollection.audio_filter_item`
- `MenuCollection.bandwidth_item`
- `MenuCollection.boolean_item`
- `MenuCollection.date_item`
- `MenuCollection.rgb_item`
- `MenuCollection.scope_edges_item`
- `MenuCollection.time_item`
- `MenuCollection.utc_offset_item`

### R-CORE

対応確認ID：B-01, B-03, B-05, X-01

- `CiviIc7300.constructor`
- `CiviIc7300.checked`
- `Utility.query_instrument_status`
- `Utility.query_instrument_status_enabled`
- `Utility.reset`
- `MenuCollection.set_simulated_write_permissions`
- `RadioOperations.set_simulated_permissions`
- `IviUtility.query_instrument_status_enabled`
- `IviUtility.reset`

### R-RECEIVE

対応確認ID：F-02, G-05

- `Radio.agc_time_code`
- `Radio.compressor_enabled`
- `Radio.data_filter`
- `Radio.filter_width_code`
- `Radio.frequency_check_enabled`
- `Radio.ip_plus_alternate_enabled`
- `Radio.ip_plus_enabled`
- `Radio.lock_enabled`
- `Radio.monitor_enabled`
- `Radio.repeater_tone_hz`
- `Radio.split_enabled`
- `Radio.tone_enabled`
- `Radio.tone_squelch_enabled`
- `Radio.tone_squelch_hz`
- `Radio.tuning_step_code`
- `Radio.twin_peak_filter_enabled`
- `Radio.tx_bandwidth`
- `Radio.xit_enabled`
- `Gains.af_raw`
- `Gains.anti_vox_raw`
- `Gains.backlight_raw`
- `Gains.compression_raw`
- `Gains.cw_delay_raw`
- `Gains.cw_pitch_raw`
- `Gains.cw_speed_raw`
- `Gains.microphone_raw`
- `Gains.monitor_raw`
- `Gains.noise_blanker_raw`
- `Gains.notch_raw`
- `Gains.rf_power_raw`
- `Gains.vox_raw`

### R-COERCION

対応確認ID：Q-01

- `Gains.noise_reduction_raw`
- `Gains.pbt_inner_raw`
- `Gains.pbt_outer_raw`

### R-SCOPE

対応確認ID：F-04, RC-06

- `Scope.write_fixed_edges`

### R-STORAGE

対応確認ID：F-05, F-06, F-07, RC-02, RC-03, RC-04

- `MemoryItem.clear`
- `MemoryItem.record`
- `MemoryItem.write_and_read`
- `KeyerItem.text`
- `KeyerItem.write_and_read`
- `BandStackItem.settings`
- `BandStackItem.write_and_read`

### R-MENUS

対応確認ID：F-10, RC-05

- `MenuItem.value`
- `MenuItem.write_and_read`

### C-MENU

対応確認ID：F-10, RC-05

- `MenuItem.value`
- `MenuItem.write_and_read`

### C-POWER-AUDIO

対応確認ID：X-09

- `RadioOperations.power_off`
- `RadioOperations.power_on`
- `RadioOperations.speak`

### C-RF

対応確認ID：X-02, X-03, X-04, X-05, X-06, X-07

- `RadioOperations.break_in`
- `RadioOperations.play_voice`
- `RadioOperations.send_cw`
- `RadioOperations.start_transmit`
- `RadioOperations.stop_cw`
- `RadioOperations.stop_transmit`
- `RadioOperations.stop_voice`
- `RadioOperations.tuner`
- `RadioOperations.vox_enabled`

### C-LINK

対応確認ID：X-08, F-10

- `MenuItem.value`
- `MenuItem.write_and_read`
- `RadioOperations.antenna_output_enabled`

### C-CALIB

対応確認ID：X-10, F-09, RC-07

- `MenuItem.value`
- `MenuItem.write_and_read`
- `Bands.write_and_read_user`
- `Bands.write_user`

## LXI全体の最終照合・手続き

IVI以外の旧監査項目もここへ集約する。次は既存結果の条項照合であり、全組合せの追加実機試験を指示するものではない。

### G01 確認の扱い

VISA位置指定の修正結果は実装表へ統合。driver適合の最終判定は本表B/R/D/REGで行う。

### G02 確認の扱い

UTF-8名の切り詰め・保存は実装と試験結果へ統合。

### G03 確認の扱い

LXI対象NICはeth0に固定し、XMLと広告の実装結果へ統合。

### G04 確認の扱い

全適用要求を閉じた後、Web・XML・文書のLXI版/機能宣言を一致させる。

### G05 確認の扱い

DHCP/AutoIP/固定IP・重複検出・LCIの既存記録を条項ごとに最終照合。別組合せの全再試験を自動的に追加しない。

### G06 確認の扱い

発見・名前解決・再接続・リンク条件の既存記録を照合。RFC境界条件は明確な差異があれば対象を特定して補う。

### G07 確認の扱い

DDNS制御は非採用として装置構成へ統合。

### G08 確認の扱い

Web/識別APIは既存記録と最終版の意味・条件付き項目を照合。ProblemDetailsの配布出典・版も確認する。

### G09 確認の扱い

Pi4、eth0、付属画面/入力、手動3プロセスの装置構成を最終成果物へ一致させる。Auto-MDIXの条件付きラベル判定は構成文書に固定。

### G10 確認の扱い

IVIの検証・名称・配布物・登録は本表56項目と各台帳で管理。

### G11 確認の扱い

機能宣言・商標・ロゴ・最終公開表示は登録/許諾/認証の実際の状況に合わせる。

### G12 確認の扱い

固定した装置版でLXI全適用条項の証拠を最終照合し、宣言の可否を判定する。

元の条項別所見は同名JSONの `lxi_followup_rows` に保存。状態の変更や合格への読み替えは行っていない。

## 判定・記録・範囲変更

- これ以上の通常組合せ試験を後から無制限に必須へ追加しない。追加が必要なのは、固定規格の取り落とし判明・試験での不具合・実装/公開契約/対象環境変更の場合。その理由と影響IDを記録する。
- 現在の全機能を維持する計画なので、校正・link・RF・電源も対象。これまで未許可の操作を本計画で勝手に許可しない。危険操作は準備と個別許可後に別途実行する。
- 全memory/user-band/fixed-edgeでmethod/propertyを実行する扱いはCore repeated-capability要求の保守的適用。特にuser空slotの復元手段は実行前の必須設計条件。解釈緩和や例外が正式に確認できれば、根拠付きで基準改訂できるが、今は免除しない。
- 校正等を除外する方針へ変更するなら、Coreのfunctionality例外、公開API/command coverage/help/compliance/試験台帳を一貫させて再判定。未試験APIを公開対応のままPASSにしない。
- LXI11.1の文書整合と11.2の登録は関連する。LXIのLAN/Web等の再試験・最終機能宣言・商標/認証はこの6.1計画の全件PASSだけで完了したことにしない。

## 台帳整合性の確認

`python tools/ivi_completion_plan.py --check`

このコマンドは在庫・リンク・hash・生成一致を検査するだけで、試験を実行せず、PASSや適合を認定しない。
