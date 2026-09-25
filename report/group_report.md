# Group Report — Day 10: Data Pipeline & Data Observability

> Báo cáo được tổng hợp từ mã nguồn và artifact sinh ra khi chạy pipeline ngày 2026-09-25.

## 1. Thông tin bài nộp

| Thông tin | Nội dung |
|---|---|
| Khóa/Lớp | K4-L3-DAY10 |
| Tên nhóm | phoboi |
| Repository | https://github.com/huytd2109/K4-L3-DAY10-phoboi-DataPipeline |
| Ngày hoàn thành | 2026-09-25 |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Đỗ Quốc An | 2A202602892 | Source owner | `crossref.py`, raw response, raw records và data lineage |
| 2 | Trịnh Đức Huy | 2A202602865 | Cleaning & test-set owner | `cleaning.py`, `testset.py`, clean schema và benchmark set |
| 3 | Trịnh Hoàng Tùng | 2A202602937 | Observability & reporting owner | `quality.py`, `reporting.py`, GX 1.x và Freshness SLA |
| 4 | Nguyễn Việt Dũng | 2A202602533 | Corruption & repair owner | `corruption.py`, corrupted/repaired datasets và corruption log |
| 5 | Nguyễn Hoàng Sơn | 2A202602457 | Pipeline integration & evidence owner | `phase1.py`, `corruption_flow.py`, ChromaDB, metrics và kiểm chứng end-to-end |

## 2. Tóm tắt kết quả

Nhóm đã hoàn thiện pipeline dữ liệu end-to-end cho hệ thống RAG sử dụng nguồn Crossref snapshot gồm 24 bài báo. Pipeline thực hiện bảo toàn raw data, chuẩn hóa schema, tính `age_days`, tạo `text_for_embedding`, kiểm định dữ liệu bằng Great Expectations 1.x, theo dõi Freshness SLA, tạo embedding MiniLM và lập chỉ mục ba collection ChromaDB. Bộ benchmark gồm 10 câu hỏi thuộc đủ bốn dạng bắt buộc: `summary`, `authors`, `date` và `categories`.

Trên dữ liệu sạch, Retrieval Hit Rate và Mean Token F1 đều đạt 1.0; Quality Gate và Freshness đều đạt. Sáu lỗi có kiểm soát làm Hit Rate giảm xuống 0.6, Token F1 giảm xuống 0.8, Quality Gate thất bại và tỷ lệ stale tăng từ 4.17% lên 29.17%. Sau khi repair từ raw snapshot, toàn bộ 24 bản ghi sạch được tái tạo, các metric trở lại mức baseline và dữ liệu repaired giống hoàn toàn dữ liệu clean. Benchmark 10 câu đáp ứng rubric nhưng vẫn còn nhỏ so với corpus; lượt xác minh cuối dùng `LLM_PROVIDER=mock` để tránh phụ thuộc quota mạng nên LLM Judge sử dụng heuristic fallback được ghi rõ trong answer artifacts.

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Crossref REST API hoặc offline snapshot
    -> parse và lưu raw records
    -> cleaning, deduplication, age_days, text_for_embedding
    -> Great Expectations 1.x + Freshness SLA
    -> all-MiniLM-L6-v2 embeddings
    -> ChromaDB: papers-baseline
    -> benchmark evaluation
    -> sáu controlled corruption scenarios
    -> ChromaDB: papers-corrupted + re-evaluation
    -> rebuild từ immutable raw records
    -> ChromaDB: papers-repaired + re-evaluation
    -> báo cáo so sánh ba trạng thái
```

### Trách nhiệm của từng khối

| Khối | Input | Xử lý chính | Output/artifact | Owner |
|---|---|---|---|---|
| Ingestion | Crossref API hoặc snapshot | Retry 429/5xx, fallback offline, parse DOI/JATS/authors/date | `data/raw/crossref_response.json`, `crossref_records.json` | TV1 |
| Cleaning | Raw `PaperRecord` | Normalize text, ISO date, deduplicate, tính `age_days` | `data/clean/papers_clean.*` | TV2 |
| Evaluation set | Clean dataframe | Tạo năm loại câu hỏi và ground-truth document IDs | `data/eval/test_set.json` | TV2 |
| Observability | Clean/corrupted/repaired dataframe | GX 1.x expectations và Freshness SLA | `data/quality/*.json` | TV3 |
| Embedding/index | `text_for_embedding` | MiniLM embedding, idempotent Chroma upsert | `data/chroma/`, `data/embeddings/*.json` | TV5 |
| Corruption/repair | Clean data và raw snapshot | Tiêm sáu lỗi, rebuild repaired data từ raw | Corruption log và ba bộ dữ liệu | TV4 |
| Orchestration | Toàn bộ module | Chạy đúng thứ tự, đánh giá và sinh report | `data/results/`, `data/reports/` | TV5 |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình | Giá trị sử dụng |
|---|---|
| Python | 3.13.1 ở lượt xác minh cuối (project hỗ trợ 3.11–3.13) |
| `LLM_PROVIDER` khi xác minh cuối | `mock` |
| LLM production support | Gemini, OpenAI, Anthropic, OpenRouter, Ollama, Custom, Mock |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Số Crossref records | 24 |
| Retrieval `top_k` | 4 |
| Freshness threshold | 180 ngày |
| Maximum stale ratio | 25% |
| Random seed | Không dùng; corruption chọn vị trí xác định |

Không đưa API key hoặc nội dung `.env` vào báo cáo.

### Lệnh cài đặt và chạy
### Lệnh cài đặt

```bash
python -m pip install -e .
```

### Lệnh chạy

Baseline:

```bash
python script/run_phase1.py
```

Corruption flow:

```bash
python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh | Trạng thái | Thời điểm chạy gần nhất | Bằng chứng |
|---|---|---|---|
| Baseline pipeline | Thành công, exit code 0 | 2026-09-25 | `baseline_metrics.json`, `phase1_report.md` |
| Corruption/repair flow | Thành công, exit code 0 | 2026-09-25 | `corruption_log.json`, ba metrics files, `corruption_report.md` |
| Final artifact assertions | PASS | 2026-09-25 | 24 rows/collection, Pass → Fail → Pass, clean = repaired |
| Dependency validation | PASS | 2026-09-25 | `python -m pip check`: no broken requirements |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính | Giá trị |
|---|---|
| Source | Crossref REST API với offline fallback |
| Offline snapshot | `data/raw/crossref_response.json` |
| Query | `agentic retrieval augmented generation large language model` |
| Filter | Từ 180 ngày gần nhất và có abstract |
| Số record nhận được | 24 |
| Retry/backoff | Tối đa 3 lần, backoff factor 1.0 cho 429/500/502/503/504 |

### Raw và clean schema

| Trường | Kiểu dữ liệu | Bắt buộc? | Ý nghĩa | Xử lý khi thiếu/sai |
|---|---|---:|---|---|
| `paper_id` | string | Có | DOI chuẩn hóa, document identity | Loại record nếu rỗng; deduplicate khi clean |
| `title` | string | Có | Tiêu đề bài báo | Bỏ HTML/JATS, normalize whitespace; loại nếu rỗng |
| `summary` | string | Có | Abstract/tóm tắt | Bỏ HTML/JATS; baseline loại nếu rỗng |
| `authors` | list[string] | Không | Danh sách tác giả | Chuẩn hóa và dùng `Unknown` nếu rỗng |
| `categories` | list[string] | Không | Các lĩnh vực chuyên môn | Dùng `Uncategorized` nếu rỗng |
| `published` | ISO date | Có | Ngày xuất bản | Parse UTC, loại record nếu không hợp lệ |
| `updated` | ISO date | Không | Ngày cập nhật | Fallback về `published` |
| `age_days` | integer | Có | Tuổi dữ liệu tại ngày chạy | Tính từ `run_date - published` |
| `text_for_embedding` | string | Có | Nội dung đưa vào MiniLM | Ghép từ năm thành phần chuẩn hóa |

### Quy tắc cleaning

| Quy tắc | Quality dimension | Số record bị tác động | Cách xác minh |
|---|---|---:|---|
| Loại HTML/JATS và normalize whitespace | Validity | 24 | Clean JSON không còn thẻ `<jats:...>` |
| Loại record thiếu ID/title/summary/ngày hợp lệ | Completeness | 0 | Raw và clean đều có 24 dòng |
| Deduplicate theo `paper_id` | Uniqueness | 0 ở baseline | 24 ID duy nhất |
| Chuẩn hóa ngày ISO 8601 | Consistency | 24 | `YYYY-MM-DD` trong clean artifacts |
| Tính `age_days` | Timeliness | 24 | Freshness report |

`text_for_embedding` có cấu trúc cố định:

```text
Title: <title>
Authors: <authors_joined>
Published: <published>
Categories: <categories_joined>
Summary: <summary>
```

Document ID được giữ ổn định bằng DOI (`paper_id`). Chroma record ID dùng `<paper_id>::<row_index>` để vẫn quan sát được duplicate trong tập corrupted mà không gây xung đột khóa nội bộ.

## 6. Evaluation setup

| Thành phần | Cấu hình thực tế |
|---|---|
| Số câu hỏi | 10 |
| `question_type` | `summary`, `authors`, `date`, `categories` |
| Ground-truth document ID | DOI lấy trực tiếp từ clean dataframe |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store | ChromaDB persistent local |
| Collections | `papers-baseline`, `papers-corrupted`, `papers-repaired` |
| Retrieval `top_k` | 4 |
| LLM mode của lượt xác minh cuối | Mock + heuristic judge fallback |
| Test set chung | `data/eval/test_set.json` |

Giải thích vì sao test set được giữ nguyên khi đánh giá baseline, corrupted và repaired:

Cùng một file test set được sử dụng cho baseline, corrupted và repaired. Việc giữ nguyên câu hỏi, ground truth và DOI mục tiêu giúp thay đổi metric phản ánh tác động của dữ liệu thay vì thay đổi độ khó của bài kiểm tra.

## 7. Kết quả baseline

### Artifact checklist

| Artifact | Đường dẫn thực tế | Trạng thái | Ghi chú |
|---|---|---|---|
| Raw response/records | `data/raw/` | Có | Gồm `crossref_response.json` và `crossref_records.json`; đã parse đủ 24 bài báo với 24 DOI duy nhất. |
| Cleaned dataset | `data/clean/` | Có | Có `papers_clean.csv` và `papers_clean.json`; 24 dòng đã chuẩn hóa, tính `age_days`, khử trùng lặp và tạo `text_for_embedding`. |
| Embedding manifest/index | `data/embeddings/` | Có | Có manifest cho baseline, corrupted và repaired; sử dụng `sentence-transformers/all-MiniLM-L6-v2`. Vector index được lưu tại `data/chroma/`. |
| Evaluation set | `data/eval/` | Có | `test_set.json` gồm 10 câu hỏi thuộc các loại `summary`, `authors`, `date` và `categories`. |
| Baseline metrics | `data/results/baseline_metrics.json` | Có | Ghi nhận Retrieval Hit Rate = 1.0000, Mean Token F1 = 1.0000, Judge Accuracy = 1.0000 và Mean Judge Score = 5.0000. |
| Quality/freshness | `data/quality/` | Có | Baseline Quality Gate đạt 6/6 validations; stale ratio = 4.17%, thấp hơn ngưỡng cảnh báo 25%, nên `is_fresh = true`. |
| Baseline report | `data/reports/phase1_report.md` | Có | Báo cáo được sinh tự động từ artifact thực tế, gồm thông tin nguồn, metrics, kết quả GX và Freshness SLA. |
### Baseline metrics

| Metric | Giá trị | Diễn giải |
|---|---:|---|
| `retrieval_hit_rate` | 1.0000 | Cả 10 câu đều retrieve được DOI ground truth |
| `mean_token_f1` | 1.0000 | Câu trả lời trùng khớp ground truth theo token |
| `judge_accuracy` | 1.0000 | 10/10 câu được đánh giá đúng |
| `mean_judge_score` | 5.0000 | Điểm trung bình tối đa |
| Ragas | Skipped | Chỉ chạy khi đặt `RUN_RAGAS=1` |

## 8. Data quality và freshness

### Quality checks

| Check | Dimension | Ngưỡng | Baseline | Corrupted | Repaired |
|---|---|---|---|---|---|
| Row count | Volume | 5–5000 | Pass | Pass | Pass |
| `paper_id`, `title`, `text_for_embedding` not null | Completeness | 100% | Pass | Pass | Pass |
| `paper_id` unique | Uniqueness | 100% | Pass | Fail | Pass |
| Summary length | Completeness/Validity | ≥30 ký tự | Pass | Fail | Pass |
| Freshness | Timeliness | stale ratio ≤25% | Pass | Fail | Pass |

### Freshness

| Thuộc tính | Baseline | Corrupted | Repaired |
|---|---:|---:|---:|
| Total rows | 24 | 24 | 24 |
| Stale rows (`age_days > 180`) | 1 | 7 | 1 |
| Stale ratio | 4.17% | 29.17% | 4.17% |
| Trạng thái | Fresh | Stale | Fresh |

## 9. Corruption scenarios và repair

| Corruption | Cách tạo | Records bị tác động | Signal kỳ vọng | Tác động thực tế | Repair |
|---|---|---:|---|---|---|
| Drop latest records | Bỏ 20% bản ghi mới nhất | 5 | Giảm retrieval/freshness coverage | Một số ground-truth DOI không còn trong index | Rebuild từ raw |
| Blank summary | Gán summary rỗng | 4 | Summary length fail | GX fail, context thiếu nội dung | Rebuild từ raw |
| Inject text noise | Chèn chuỗi ký tự rác | 4 | Giảm chất lượng embedding | Nội dung vector bị nhiễu | Rebuild từ raw |
| Truncate title | Cắt title còn 7 ký tự | 4 | Exact-title lookup/retrieval suy giảm | Câu hỏi theo title khó match | Rebuild từ raw |
| Stale date | Lùi ngày 5 năm | 7 | Freshness fail | Stale ratio tăng lên 29.17% | Rebuild từ raw |
| Duplicate rows | Nhân bản các dòng | 5 | Uniqueness fail | `paper_id` bị trùng | Deduplicate khi clean lại |

### Corruption log

- **Đường dẫn:** `data/results/corruption_log.json`
- **Trạng thái:** Có
- **Nhận xét:** Log ghi nhận đầy đủ 6 loại corruption gồm `drop_latest_records`, `blank_summary`, `inject_text_noise`, `truncate_title`, `stale_date` và `duplicate_rows`. Mỗi loại đều có số lượng record bị tác động, danh sách `paper_id` tương ứng và mô tả tham số/hành động đã áp dụng. Tổng số dòng trước và sau corruption đều là 24 do 5 dòng mới nhất bị loại và 5 dòng khác được nhân bản.

Giải thích cách repair đảm bảo dữ liệu được phục hồi từ nguồn đáng tin cậy thay vì chỉ che kết quả lỗi:

Repair không chỉnh tay corrupted data mà gọi lại cleaning trên `data/raw/crossref_records.json`; vì vậy chạy lặp lại vẫn sinh cùng clean dataset và 24 vectors.



## 10. So sánh baseline, corrupted và repaired

| Metric/signal | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi |
|---|---:|---:|---:|---:|---:|
| `retrieval_hit_rate` | 1.0000 | 0.6000 | 1.0000 | -0.4000 | 100% baseline |
| `mean_token_f1` | 1.0000 | 0.8000 | 1.0000 | -0.2000 | 100% baseline |
| `judge_accuracy` | 1.0000 | 0.8000 | 1.0000 | -0.2000 | 100% baseline |
| `mean_judge_score` | 5.0000 | 4.2000 | 5.0000 | -0.8000 | 100% baseline |
| Quality Gate | Pass | Fail | Pass | Phát hiện summary rỗng và duplicate | Phục hồi hoàn toàn |
| Freshness | Pass | Fail | Pass | Stale ratio +25 điểm phần trăm | Phục hồi hoàn toàn |

Nêu ít nhất hai kết luận có quan hệ nhân quả được hỗ trợ bởi artifacts:

Hai chuỗi nguyên nhân–bằng chứng chính:

1. Drop latest records, title truncation và summary corruption → thiếu/méo nội dung trong vector index → Retrieval Hit Rate giảm từ 1.0 xuống 0.6 và Token F1 giảm xuống 0.8.
2. Rebuild từ raw snapshot → loại duplicate, phục hồi title/summary/date và re-index → Quality/Freshness trở lại Pass, Hit Rate và Token F1 trở lại 1.0.

## 11. Vấn đề tích hợp quan trọng

- **Triệu chứng:** `pip install -e .` báo Python 3.14 không thuộc khoảng `>=3.11,<3.14`.
- **Nguyên nhân:** `.venv` ban đầu được tạo bằng Python 3.14, trong khi project và một số dependency chỉ hỗ trợ đến Python 3.13.
- **Cách xử lý:** Tạo lại `.venv` bằng một phiên bản được hỗ trợ; lượt xác minh cuối dùng Python 3.13.1 và package ở editable mode.
- **Cách xác minh:** `python --version`, `python -m pip check`, compile toàn bộ source và chạy hai pipeline với exit code 0.

Ngoài ra, lần tải MiniLM đầu tiên cần kết nối Hugging Face. Sau khi model được cache, `HF_HUB_OFFLINE=1` cho phép chạy lại không cần mạng. LLM client được cấu hình timeout 30 giây và tối đa hai retry để tránh treo pipeline khi provider không phản hồi.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng | Hướng cải thiện có thể kiểm chứng |
|---|---|---|
| Benchmark 10 câu vẫn nhỏ so với corpus 24 tài liệu | Đáp ứng rubric nhưng độ bao phủ còn hạn chế | Mở rộng lên ≥20 câu, stratify theo loại và báo cáo metric từng nhóm |
| Final verification dùng mock judge | Judge metric dựa trên heuristic fallback | Chạy lại cả ba trạng thái với cùng provider thật và lưu model/config |
| Snapshot nhỏ và có tính mô phỏng | Chưa phản ánh hết schema drift Crossref | Chạy `REFRESH_SOURCE=true`, lưu timestamp và so sánh live/offline |
| Chưa có pytest CI | Regression có thể chỉ xuất hiện khi chạy pipeline | Thêm unit/integration tests và GitHub Actions |
| Freshness dùng một ngưỡng toàn cục | Chưa phân biệt tốc độ thay đổi theo lĩnh vực | Thiết lập SLA theo category và kiểm tra drift theo thời gian |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
