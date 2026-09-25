# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Nguyễn Hoàng Sơn |
| MSSV | 2A202602457 |
| Khóa/Lớp | K4-L3-DAY10 |
| Tên nhóm | phoboi |
| Vai trò chính | Pipeline Integration & Evidence Owner |
| Repository | https://github.com/huytd2109/K4-L3-DAY10-phoboi-DataPipeline |
| Ngày hoàn thành | 2026-09-25 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
|---|---|---|---|---|
| Baseline orchestration | `src/pipelines/phase1.py` — `main()` | Settings, raw records và output từ các module cleaning/quality/evaluation | Clean artifacts, baseline index, metrics và `phase1_report.md` | Hoàn thành |
| Corruption/repair orchestration | `src/pipelines/corruption_flow.py` — `main()` | Baseline artifacts, corruption function và raw snapshot | Corrupted/repaired datasets, metrics và comparison report | Hoàn thành |
| Vector index integration | `src/retrieval/index.py` — `LocalEmbeddingIndex` | Clean DataFrame và embedding model | Ba Chroma collections cùng embedding manifests | Hoàn thành |
| Evidence verification | `data/results/`, `data/quality/`, `data/reports/` | Artifacts của hai pipeline | Bằng chứng định lượng cho Baseline → Corrupted → Repaired | Hoàn thành |

Tôi chịu trách nhiệm nhận đầu ra từ các thành viên phụ trách ingestion, cleaning, observability và corruption để tích hợp thành hai luồng chạy end-to-end. Phạm vi chính của tôi là orchestration, reproducibility, vector-index integration và kiểm tra tính nhất quán giữa code, artifacts, metrics và báo cáo.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
|---|---|---|
| Kiểm tra contract giữa raw và clean schema | Đỗ Quốc An, Trịnh Đức Huy | Pipeline đọc đủ 24 raw records và sinh 24 clean records với DOI duy nhất |
| Kết nối Quality Gate trước bước indexing | Trịnh Hoàng Tùng — `quality.py` | Baseline chỉ build Chroma sau khi Quality Gate đạt; corrupted state được quan sát là Fail |
| Tích hợp corruption và repair vào cùng benchmark | Nguyễn Việt Dũng — `corruption.py` | Ba trạng thái dùng chung test set 10 câu; metrics có thể so sánh trực tiếp |
| Kiểm tra portability của vector artifacts | `retrieval/index.py`, embedding manifests | Manifest dùng `data/chroma`; loader mở database của clone hiện tại thay vì đường dẫn máy khác |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
|---|---|---|---|
| Điều phối baseline pipeline | `src/pipelines/phase1.py`, `script/run_phase1.py` | 24 papers, test set 10 câu, baseline metrics và report | Chạy `python script/run_phase1.py` với exit code 0 |
| Điều phối corruption và repair | `src/pipelines/corruption_flow.py`, `script/run_corruption_flow.py` | Đủ corrupted/repaired artifacts và báo cáo ba trạng thái | Chạy `python script/run_corruption_flow.py` với exit code 0 |
| Quản lý ba vector collections | `data/chroma/`, `data/embeddings/*.json` | `papers-baseline`, `papers-corrupted`, `papers-repaired`, mỗi collection 24 documents | Load từng manifest và kiểm tra `collection.count() == 24` |
| Kiểm tra suy giảm và phục hồi | `data/results/*_metrics.json` | Hit Rate 1.0 → 0.6 → 1.0; Token F1 1.0 → 0.8 → 1.0 | Đối chiếu ba metrics files |
| Kiểm tra idempotent repair | `papers_clean_repaired.json`, `repaired_metrics.json` | Hash dataset và metrics không đổi sau lần chạy repair thứ hai | So sánh SHA-256 trước/sau lần chạy lặp |

Output cụ thể tôi chịu trách nhiệm tích hợp và kiểm chứng là bộ ba metrics `baseline_metrics.json`, `corrupted_metrics.json`, `repaired_metrics.json` cùng `data/reports/corruption_report.md`. Các artifact này chứng minh corruption làm chất lượng retrieval/answer suy giảm và repair từ raw snapshot khôi phục kết quả về baseline.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Các module riêng lẻ chỉ có ý nghĩa khi được nối đúng thứ tự và thống nhất contract. Pipeline phải bảo đảm dữ liệu xấu bị quan sát trước khi phục vụ, ba trạng thái không ghi đè vector index của nhau, cùng một benchmark được dùng xuyên suốt và report không chứa số liệu nhập tay khác với JSON artifacts.

### Cách triển khai

Baseline flow thực hiện theo thứ tự:

1. Load settings và raw records.
2. Clean dữ liệu, lưu CSV/JSON.
3. Chạy GX Quality Gate và Freshness SLA.
4. Dừng pipeline nếu baseline Quality Gate thất bại.
5. Build collection `papers-baseline` bằng MiniLM.
6. Load hoặc tạo test set 10 câu.
7. Evaluate và ghi metrics/answers.
8. Sinh báo cáo Phase 1 từ artifacts thực tế.

Corruption/repair flow thực hiện:

1. Kiểm tra đủ baseline dataset, test set, metrics, quality và freshness artifacts.
2. Tạo corrupted dataset, chạy lại quality/freshness, build `papers-corrupted` và evaluate.
3. Repair bằng cách đọc lại `crossref_records.json`, chạy lại cleaning và build `papers-repaired`.
4. Evaluate repaired state bằng đúng test set baseline.
5. Sinh bảng so sánh Baseline/Corrupted/Repaired.

Chroma sử dụng ba collection riêng biệt. Manifest chỉ lưu đường dẫn tương đối `data/chroma`, còn loader resolve database theo `settings.paths.chroma_dir`, giúp artifact hoạt động sau khi clone sang máy khác.

### Input, output và contract

| Thành phần | Mô tả |
|---|---|
| Input | Raw records, clean schema, test set 10 câu, quality/freshness functions và corruption function |
| Output | Ba datasets, ba Chroma collections, ba metrics/answers bundles và hai Markdown reports |
| Module phụ thuộc | `core.config`, `ingestion.*`, `observability.*`, `evaluation.*`, `retrieval.*` |
| Module sử dụng output | Reporting, demo/Q&A và quá trình nghiệm thu cuối |
| Điều kiện lỗi cần xử lý | Thiếu baseline artifact; baseline quality fail; Chroma path thuộc máy khác; embedding model chưa cache; LLM provider không khả dụng |

### Cách xác minh

```powershell
$env:LLM_PROVIDER = "mock"
$env:LLM_MODEL = "mock"
python script/run_phase1.py
python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Hai lệnh exit code 0; Quality/Freshness Pass → Fail → Pass; corrupted metrics thấp hơn baseline; repaired metrics trở lại baseline.
- **Kết quả thực tế:** Baseline hoàn tất với 24 papers và 10 questions; corruption flow hoàn tất với Hit Rate 1.0 → 0.6 → 1.0 và Token F1 1.0 → 0.8 → 1.0.
- **Artifact/log:** `data/results/`, `data/quality/`, `data/reports/`, không chứa secret.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần so sánh ba trạng thái mà không để lần build sau ghi đè index trước, đồng thời artifact phải dùng được trên máy khác.
- **Các phương án đã cân nhắc:** Dùng một collection rồi rebuild tại chỗ; dùng ba collection riêng nhưng lưu absolute path; dùng ba collection riêng với path được resolve từ project hiện tại.
- **Phương án đã chọn:** Ba collection `papers-baseline`, `papers-corrupted`, `papers-repaired`; manifest lưu `data/chroma` và loader dùng `settings.paths.chroma_dir`.
- **Lý do:** Cô lập trạng thái, dễ truy vết, chạy lại idempotent và không phụ thuộc đường dẫn ổ đĩa của người tạo artifact.
- **Bằng chứng quyết định phù hợp:** Cả ba manifest load được trên workspace hiện tại và mỗi collection có 24 documents.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Embedding manifests cũ chứa `D:\\Thuc hanh AI\\...\\data\\chroma`, không trùng workspace hiện tại; corruption flow cũng có thể đọc quality report chưa tồn tại.
- **Lệnh hoặc bước tái hiện:** Đọc trường `persist_path` trong `data/embeddings/*.json` và đối chiếu danh sách `required_baseline` với các file được đọc ngay sau đó.
- **Nguyên nhân gốc:** Persist path được serialize trực tiếp dưới dạng absolute path; prerequisite list chưa bao phủ `baseline_quality_report.json` và `freshness_report.json`.
- **Cách xử lý:** Lưu path tương đối, loader luôn mở Chroma của project hiện tại và bổ sung hai report vào `required_baseline`.
- **Cách xác minh sau khi sửa:** Ba manifest đều ghi `data/chroma`; ba collection load thành công với 24 documents; hai pipeline exit code 0.
- **Điều học được:** Artifact portability và prerequisite validation là một phần của correctness, không chỉ là vấn đề cấu hình.

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?** Crossref payload được lưu làm raw snapshot, parse thành `PaperRecord`, clean thành schema ổn định, kiểm định bằng GX/Freshness, ghép `text_for_embedding`, tạo MiniLM vector và lưu vào Chroma.
2. **Evaluation set và ground-truth document IDs dùng thế nào?** Mỗi câu hỏi giữ đáp án chuẩn và DOI mục tiêu. DOI được so với danh sách tài liệu retrieve để tính Hit Rate; câu trả lời được so với ground truth để tính Token F1 và judge metrics.
3. **Quality checks khác freshness monitoring ở đâu?** Quality kiểm tra volume, completeness, uniqueness và summary length; freshness đo tỷ lệ `age_days > 180` và cảnh báo khi stale ratio vượt 25%.
4. **Vì sao dùng cùng test set?** Nếu đổi câu hỏi giữa ba trạng thái, metric có thể thay đổi do độ khó benchmark thay vì do corruption/repair.
5. **Repair thành công dựa trên gì?** Repaired dataset bằng clean dataset, Quality/Freshness trở lại Pass, Hit Rate/F1 trở lại baseline và kết quả không đổi khi chạy repair lặp.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
|---|---:|---:|---:|---|
| `retrieval_hit_rate` | 1.0000 | 0.6000 | 1.0000 | 40% câu hỏi mất DOI ground truth trong top-k sau corruption |
| `mean_token_f1` | 1.0000 | 0.8000 | 1.0000 | Nội dung bị drop/blank/truncate làm đáp án suy giảm |
| `judge_accuracy` | 1.0000 | 0.8000 | 1.0000 | Judge dùng heuristic fallback trong lượt chạy `mock` |
| `mean_judge_score` | 5.0000 | 4.2000 | 5.0000 | Phục hồi về mức baseline |
| Quality checks | Pass (6/6) | Fail (4/6) | Pass (6/6) | Corrupted vi phạm uniqueness và summary length |
| Freshness status | Pass, 4.17% stale | Fail, 29.17% stale | Pass, 4.17% stale | Stale-date corruption vượt ngưỡng 25% |

### Kết luận từ số liệu

1. Drop latest records, blank summary, title truncation và text noise → DOI/nội dung mục tiêu bị thiếu hoặc méo trong index → Hit Rate giảm từ 1.0 xuống 0.6 và Token F1 giảm từ 1.0 xuống 0.8.
2. Rebuild từ immutable raw snapshot → khôi phục DOI/title/summary/date, loại duplicate và re-index → Quality/Freshness trở lại Pass, Hit Rate và Token F1 trở lại 1.0.

Corruption ảnh hưởng rõ nhất đến retrieval là `drop_latest_records`, vì tài liệu đã bị loại khỏi corpus thì không thể xuất hiện trong top-k. `truncate_title` và `blank_summary` tiếp tục làm giảm khả năng exact lookup và chất lượng câu trả lời. `stale_date` thể hiện rõ nhất ở observability vì làm stale ratio tăng từ 4.17% lên 29.17%.

Kết quả khác với trực giác ban đầu là corrupted dataset vẫn có 24 dòng. Corruption log cho thấy năm dòng mới nhất bị xóa nhưng năm dòng khác được duplicate để giữ nguyên row count. Vì vậy chỉ kiểm tra volume sẽ bỏ sót lỗi mất coverage và trùng dữ liệu; cần kết hợp uniqueness, completeness, freshness và RAG metrics.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Orchestration phải thực thi quality gate đúng vị trí và xác minh đủ prerequisite, nếu không pipeline có thể chạy bằng artifact thiếu hoặc stale.
2. Tách ba Chroma collections và dùng cùng test set là điều kiện để phép so sánh Baseline/Corrupted/Repaired có ý nghĩa.
3. Report chỉ đáng tin khi được đối chiếu với artifacts; exit code 0 không đủ để kết luận dữ liệu và metrics đúng.

### Nếu có thêm thời gian

Tôi sẽ bổ sung pytest integration chạy trên temporary Chroma directory, kiểm tra tự động số collection/documents, test-set contract, Pass → Fail → Pass và clean = repaired. Sau đó đưa test vào GitHub Actions, đặt mục tiêu coverage trên 80% để phát hiện regression trước khi merge.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Hoàng Sơn
**Ngày xác nhận:** 25/09/2026
