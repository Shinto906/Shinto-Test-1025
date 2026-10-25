# LedgerVault — 意図的に脆弱なマルチテナントSaaS(セキュリティ検証用ターゲット)

LedgerVault は、脅威モデリング・コードレビュー・ペネトレーションテストを行う
ツール(例: AWS Continuum)の検出能力・真陽性率を測定するために作られた、
**意図的に脆弱な** 社内文書/経費管理SaaSの模倣アプリです。OWASP Top 10 (2025)
相当の脆弱性を **15個**、単純には突破できない形(多段チェーン含む)で作り込んでいます。

```
会社(テナント) ── ユーザー(member/manager/admin) ── 文書 / 経費 / コメント
                                   └ super-admin(全テナント横断)
```

> ⚠️ **安全上の注意 — 必ず隔離環境で**
> このアプリは設計上、致命的な脆弱性を含みます。公開ネットワークや業務環境、共有
> ホストで起動しないでください。ホストポートはすべて `127.0.0.1`(ローカルのみ)に
> バインドしています。検証が終わったら必ず停止・破棄してください。DVWA / OWASP
> Juice Shop と同じ扱い(ローカル隔離ラボ専用)です。

## 構成

| サービス | 役割 | 公開 |
|---|---|---|
| frontend (nginx) | 最小SPA(XSS描画面あり) | http://localhost:8080 |
| backend (FastAPI) | API本体(脆弱性の大半) | http://localhost:8000 |
| db (PostgreSQL) | データ | 127.0.0.1:5432 |
| redis | セッション等 | 127.0.0.1:6379 |
| minio | S3互換ストレージ | 127.0.0.1:9000 / 9001 |
| metadata-mock | SSRF標的(内部ネットのみ) | 非公開 |

## 起動方法

### A. Docker Compose(推奨)
```bash
docker compose up --build
# frontend: http://localhost:8080
# backend : http://localhost:8000  (OpenAPI: /docs)
```
初回起動時に自動でテーブル作成とシード投入を行います。

### B. Terraform(ローカルDockerプロバイダ / IaCレビュー用)
`terraform/README.md` を参照。クラウド不要・無料で同じ構成を立てます。

停止・破棄:
```bash
docker compose down -v        # またはローカルデータも含めて削除
```

## シード済みアカウント(全員パスワード `Password123!`)

| メール | テナント | ロール |
|---|---|---|
| alice@aozora.example | Aozora Corp | member |
| mallory@aozora.example | Aozora Corp | member |
| manager@aozora.example | Aozora Corp | manager |
| admin@aozora.example | Aozora Corp | admin |
| bob@beacon.example | Beacon Inc | member |
| root@system.example | Beacon Inc | admin + super-admin |

越境ターゲットとして、Beacon Inc に機密文書「Beacon Inc - Q3 Financials (confidential)」を
用意しています(Aozora の一般ユーザーから到達できれば越境成功)。

## AWS Continuum の当て方

- **コードレビュー / 脅威モデリング**: このリポジトリを GitHub に push し、ソース一式
  (`backend/`, `frontend/`, `terraform/`, `docker-compose.yml`)をレビュー対象にする。
- **ペネトレ / 動的診断**: `docker compose up` 後、`http://localhost:8080`(UI)と
  `http://localhost:8000`(API)へ直接接続させる。OpenAPI は `/docs` / `/openapi.json`。

## 検証の進め方(真陽性率測定)

1. Continuum に診断させ、報告された指摘を収集する。
2. `GROUND_TRUTH.md` の V01〜V20 および Chain 1〜5 と突き合わせる。
3. TP(正解一致)/ FN(見逃し)/ FP(誤検知)を集計。SAST向け・DAST向けの区分は
   `GROUND_TRUTH.md` 末尾の「集計観点」を参照。

## ドキュメント
- `GROUND_TRUTH.md` — 仕込んだ脆弱性の正解一覧(所在・再現・検出手段・チェーン)
- `THREAT_MODEL.md` — 資産・信頼境界・STRIDE(脅威シナリオ特定の評価用)

## ライセンス / 用途
教育・自組織内のセキュリティ検証専用。第三者システムへの攻撃や、本番相当環境での
運用には使用しないこと。
