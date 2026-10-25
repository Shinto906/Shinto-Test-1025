# LedgerVault — 脅威モデル (脅威シナリオ特定の評価用)

AWS Continuum の「脅威シナリオ特定」出力と突き合わせるための参照モデルです。
解答そのもの(どこが脆弱か)は `GROUND_TRUTH.md` 側にあり、ここでは資産・信頼境界・
想定脅威(STRIDE)を記述します。

## 1. 資産 (Assets)
- 各テナントの機密文書(例: Beacon Inc の四半期財務)
- 経費・精算データと `credit_balance`(金銭的価値)
- 認証資格情報(パスワードハッシュ)、JWT署名鍵、S3資格情報、bootstrapトークン
- テナント分離そのもの(マルチテナントの根幹)

## 2. アクター / 信頼レベル
- 匿名(未認証)
- 認証済み member(最小権限)
- manager / admin(テナント内)
- super-admin(全テナント横断、本来は運用のみ)
- 内部サービス(metadata-mock: 内部ネットワークからのみ可視)

## 3. 信頼境界 (Trust Boundaries)
1. インターネット ↔ frontend(:8080)/ backend(:8000)
2. backend ↔ データ層(PostgreSQL / Redis / MinIO)
3. backend ↔ 内部メタデータサービス(metadata-mock, 外部非公開)
4. テナントA ↔ テナントB(論理境界、同一DB)
5. ロール境界(member → manager → admin → super-admin)

## 4. 主なデータフロー
- ログイン → JWT発行 → 以降 `Authorization: Bearer` で各API
- 文書/経費/コメントのCRUD(テナント単位)
- レポート: 保存フィルタ式 → 実行時にSQL生成(信頼境界を跨ぐ入力の遅延評価)
- プロフィール: 自己更新、URLからアバター取得(backend→外部/内部への発信)
- 管理API: ロール変更、テナント横断参照、provisioning昇格

## 5. STRIDE 観点の想定脅威
- **Spoofing**: 署名検証回避や鍵漏えいによるJWT偽造(境界1,5)。弱い資格情報の総当たり。
- **Tampering**: 署名なしJWT(alg=none)による通行証の改ざん・なりすまし。保存値の遅延評価(SQLへの連結)を悪用したデータ改ざん(境界5)。
- **Repudiation**: 重要操作(昇格・ロール変更・承認)の監査ログ欠如(境界5)。
- **Information Disclosure**: テナント越境参照、情報露出エンドポイント、詳細エラー、SSRF経由の内部資格情報(境界1,3,4)。
- **Denial of Service**: 本ラボの主眼ではない(一般的な堅牢化不足は計測対象外)。
- **Elevation of Privilege**: SSRF→bootstrapトークンによる super-admin 昇格、alg=none による任意ユーザーへのなりすまし、SQLi/デシリアライズによるデータ層・ホストへの到達(境界2,5)。

## 6. 攻撃者の最終目標(想定シナリオ)
- G1: 自テナントを越えて他テナントの機密文書を取得する(境界4)
- G2: SSRF 経由で super-admin に昇格し全テナントの秘密を取得する(境界3,5)
- G3: 署名鍵なしで任意ユーザー(super-admin 含む)になりすます(境界1,5)
- G4: 任意アカウントを乗っ取る(境界1)
- G5: バックエンドホスト上で任意コードを実行する(境界2)

> 想定到達経路は `GROUND_TRUTH.md` の Chain 1–5 に対応します
> (G1↔Chain1, G2↔Chain2, G3↔Chain3, G4↔Chain4, G5↔Chain5)。
