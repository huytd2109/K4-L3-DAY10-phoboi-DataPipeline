# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Trịnh Đức Huy |
| MSSV | 2A202602865 |
| Khóa/Lớp | K4-L3-DAY10 |
| Tên nhóm | phoboi |
| Vai trò chính | Cleaning & test-set owner |
| Repository | https://github.com/huytd2109/K4-L3-DAY10-phoboi-DataPipeline |
| Ngày hoàn thành | 2026-09-25 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
|---|---|---|---|---|
| Cleaning và clean schema | `src/ingestion/cleaning.py` — `build_clean_dataframe()` | Raw records và `run_date` | Clean DataFrame, được pipeline lưu thành `data/clean/papers_clean.csv` và `.json` | Hoàn thành theo báo cáo nhóm |
| Benchmark set | `src/evaluation/testset.py` — `build_test_set()`, `load_or_create_test_set()` | Clean DataFrame | `data/eval/test_set.json` gồm 5 câu và DOI ground truth | Hoàn thành theo báo cáo nhóm |

Theo phân công trong `group_report.md`, tôi nhận dữ liệu từ phần ingestion của Đỗ Quốc An, chuẩn hóa để bàn giao cho observability của Trịnh Hoàng Tùng, corruption/repair của Nguyễn Việt Dũng và pipeline/index của Nguyễn Hoàng Sơn. Phạm vi chính của tôi là cleaning, clean schema và test set; kết quả end-to-end là kết quả chung của nhóm.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
|---|---|---|
| Cung cấp cleaning dùng lại khi repair | Nguyễn Việt Dũng — corruption/repair | Luồng repair tái tạo dữ liệu sạch từ raw snapshot |
| Cung cấp benchmark dùng chung | Nguyễn Hoàng Sơn — pipeline/evaluation | Cố định câu hỏi và ground truth giữa ba trạng thái |

Đây là sự phối hợp thông qua đầu ra của module; báo cáo nhóm không ghi nhận thêm hoạt động debug riêng của cá nhân ngoài phạm vi trên.

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
|---|---|---|---|
| Chuẩn hóa văn bản, DOI và ngày | `src/ingestion/cleaning.py` | 24 bản ghi sạch, 24 DOI duy nhất | Đối chiếu mã nguồn và `data/clean/papers_clean.json` |
| Tạo trường phục vụ embedding và quality | `build_clean_dataframe()` | `text_for_embedding`, `age_days`, `summary_chars` | Đối chiếu clean schema và quality/freshness artifacts |
| Xây dựng evaluation set | `data/eval/test_set.json` | 5 loại: summary, authors, date, category, multi_hop | Kiểm tra loại câu và DOI tham chiếu |
| Hỗ trợ repair bằng cleaning dùng chung | `data/clean/papers_clean_repaired.json` | Dữ liệu repaired trùng clean | So sánh nội dung hai artifact |

Output cụ thể là bộ test gồm 5 mẫu, mỗi mẫu có `id`, `type`, `question_type`, `question`, `ground_truth` và `ground_truth_doc_ids`. Câu multi-hop tham chiếu hai tài liệu; các câu còn lại tham chiếu một tài liệu. Mọi DOI ground truth đều tồn tại trong tập clean hiện có.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Raw data có thể chứa HTML/JATS, khoảng trắng thừa, ngày sai, trường thiếu hoặc DOI trùng. Phần cleaning tạo đầu vào thống nhất cho kiểm định và embedding; test set tạo mục tiêu đánh giá có thể truy ngược về tài liệu nguồn.

### Cách triển khai

Cleaning giải mã HTML entities, loại thẻ và chuẩn hóa khoảng trắng; đưa DOI về chữ thường. Bản ghi thiếu ID, title, summary hoặc có ngày xuất bản không hợp lệ bị loại. Ngày được parse theo UTC và xuất dạng `YYYY-MM-DD`; `updated` không hợp lệ được thay bằng `published`.

Authors/categories được làm sạch; chuỗi ghép dùng `Unknown` hoặc `Uncategorized` khi thiếu. `age_days` tính theo chênh lệch giữa ngày chạy và ngày xuất bản sau khi chuẩn hóa UTC. `text_for_embedding` ghép Title, Authors, Published, Categories, Summary. Hàm khử trùng theo `paper_id`, giữ dòng đầu tiên rồi sắp xếp ngày xuất bản giảm dần và DOI tăng dần.

Test set yêu cầu ít nhất 5 clean records, sắp xếp theo DOI để chọn mẫu xác định. Ground truth lấy từ trường đã chuẩn hóa; summary dùng câu đầu của tóm tắt, multi-hop ghép thông tin hai bài. Nếu file test tồn tại và `refresh=False`, module đọc lại file thay vì tạo mới.

### Input, output và contract

| Thành phần | Mô tả |
|---|---|
| Input | Raw `PaperRecord`, `run_date`; clean DataFrame cho bước tạo test |
| Output | DataFrame gồm DOI, title, summary, authors/categories, ngày ISO, `age_days`, các trường ghép và `text_for_embedding`; danh sách 5 mẫu đánh giá |
| Module phụ thuộc | `ingestion.crossref.PaperRecord`, `core.utils`, pandas |
| Module sử dụng output | Observability, embedding/index, `pipelines/phase1.py`, `pipelines/corruption_flow.py` |
| Điều kiện lỗi cần xử lý | Thiếu trường bắt buộc, ngày sai, DOI trùng; dưới 5 clean records khiến tạo test set báo `ValueError` |

### Cách xác minh

Các lệnh sau được báo cáo nhóm ghi nhận đã chạy; khi biên soạn báo cáo cá nhân chỉ đối chiếu mã nguồn và artifacts, không chạy lại pipeline:

```bash
uv run python script/run_phase1.py
uv run python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Clean schema hợp lệ; DOI ground truth thuộc tập clean; cùng test set cho ba trạng thái; repaired khôi phục clean.
- **Kết quả thực tế:** Artifacts hiện có chứa 24 DOI duy nhất, 5 câu hỏi với DOI hợp lệ; clean và repaired trùng nội dung. Báo cáo nhóm ghi nhận hai pipeline exit code 0.
- **Artifact/log:** `data/clean/`, `data/eval/test_set.json`, `data/results/*_metrics.json`, `data/quality/`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần đo ảnh hưởng của corruption và repair trên cùng bài toán retrieval.
- **Các phương án đã cân nhắc:** Hai phương án về mặt thiết kế là tạo lại test set theo từng dataset hoặc giữ test set từ clean baseline. Báo cáo nhóm không ghi lại lịch sử thảo luận lựa chọn.
- **Phương án đã chọn:** Tạo benchmark từ clean và dùng chung cho baseline, corrupted, repaired.
- **Lý do:** Tạo lại câu hỏi từ corrupted data có thể bỏ qua tài liệu đã mất, che khuất suy giảm retrieval. DOI ổn định giúp giữ mục tiêu đánh giá nhất quán.
- **Bằng chứng quyết định phù hợp:** Cùng benchmark ghi nhận Hit Rate 1.0 → 0.6 → 1.0; `load_or_create_test_set()` hỗ trợ đọc lại file khi không refresh.

## 6. Một lỗi hoặc blocker đã xử lý

Báo cáo nhóm không ghi nhận lỗi lập trình riêng do tôi xử lý. Tình huống dưới đây là lỗi dữ liệu có kiểm soát trong thử nghiệm chung, được khắc phục qua luồng repair sử dụng lại module cleaning tôi phụ trách.

- **Triệu chứng/lỗi nguyên văn:** Không có log lỗi cá nhân được trích dẫn; artifact ghi nhận Quality Gate thất bại khi dữ liệu có summary rỗng và DOI trùng.
- **Lệnh hoặc bước tái hiện:** Chạy corruption flow; log ghi nhận 4 bản ghi bị làm rỗng summary và 5 dòng được nhân bản.
- **Nguyên nhân gốc:** Dữ liệu bị biến đổi sau cleaning, vi phạm yêu cầu nội dung summary và tính duy nhất của DOI.
- **Cách xử lý:** Luồng repair của nhóm đọc lại raw snapshot, gọi cleaning để tái tạo dataset rồi re-index. Chỉ loại dòng lỗi trong corrupted data không thể khôi phục tài liệu đã bị xóa.
- **Cách xác minh sau khi sửa:** Clean/repaired trùng nội dung; quality trở lại Pass; Hit Rate trở lại 1.0 theo artifacts.
- **Điều học được:** Raw bất biến là cơ sở phục hồi đáng tin cậy. Muốn tái tạo cả `age_days` giống nhau cần dùng cùng `run_date`.

## 7. Hiểu biết về luồng end-to-end

1. Dữ liệu đi từ Crossref đến vector index như thế nào?
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
5. Repair được xem là thành công dựa trên artifact và metric nào?

**Câu trả lời:**

1. Crossref API hoặc snapshot cung cấp dữ liệu; ingestion lưu raw, cleaning tạo schema chuẩn, quality/freshness kiểm tra, MiniLM tạo embedding và ChromaDB lưu index.
2. DOI mục tiêu dùng đánh giá retrieval; đáp án tham chiếu dùng tính Token F1 và judge. Tìm đúng tài liệu chưa tự động chứng minh trả lời đúng.
3. Quality checks kiểm tra volume, trường bắt buộc, uniqueness và độ dài summary. Freshness kiểm tra tuổi dữ liệu: stale khi `age_days > 180`, SLA đạt khi stale ratio không vượt 25%.
4. Cố định câu hỏi và ground truth giúp thay đổi metric phản ánh thay đổi dữ liệu thay vì thay đổi bài kiểm tra.
5. Repair đạt khi dữ liệu khôi phục từ raw, clean/repaired trùng nhau, quality/freshness trở lại Pass và metric trở về baseline.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
|---|---:|---:|---:|---|
| `retrieval_hit_rate` | 1.0000 | 0.6000 | 1.0000 | Giảm 0.4 khi dữ liệu hỏng, phục hồi về baseline |
| `mean_token_f1` | 1.0000 | 0.8000 | 1.0000 | Nội dung đáp án suy giảm cùng biến đổi dữ liệu |
| `judge_accuracy` | 1.0000 | 0.8000 | 1.0000 | Lượt cuối sử dụng heuristic judge fallback |
| `mean_judge_score` | 5.0000 | 4.2000 | 5.0000 | Không phải xác nhận độc lập từ LLM thật |
| Quality checks | Pass | Fail | Pass | Phát hiện summary không đạt và DOI trùng |
| Freshness status | Pass | Fail | Pass | Stale ratio: 4.17% → 29.17% → 4.17% |

Số liệu là kết quả chung của nhóm với 24 bản ghi, 5 câu hỏi và `top_k=4`. Lượt xác minh cuối dùng `LLM_PROVIDER=mock`, judge dùng heuristic fallback; Ragas chưa chạy. Chưa thể suy rộng thành chất lượng của hệ thống dùng LLM thật.

### Kết luận từ số liệu

1. Sáu corruption áp dụng chung làm thiếu tài liệu, biến dạng nội dung, trùng DOI và lùi ngày → quality/freshness chuyển sang Fail → Hit Rate giảm 1.0 xuống 0.6, Token F1 giảm 1.0 xuống 0.8.
2. Rebuild từ raw qua cleaning và re-index → clean data, quality/freshness phục hồi → Hit Rate và Token F1 trở lại 1.0.

Corruption nào ảnh hưởng rõ nhất và vì sao?

Xóa 5 bản ghi mới nhất làm mất một số DOI ground truth khỏi index, tạo cơ chế ảnh hưởng trực tiếp đến retrieval. Tuy nhiên, sáu lỗi được áp dụng chung nên chưa đủ bằng chứng xếp hạng lỗi ảnh hưởng lớn nhất; cần chạy từng lỗi riêng để định lượng.

Kết quả nào khác với kỳ vọng ban đầu?

Điểm đáng chú ý là tổng số dòng vẫn bằng 24 dù dữ liệu đã hỏng. Corruption log giải thích điều này: 5 dòng bị xóa và 5 dòng khác được nhân bản. Vì vậy, kiểm tra row count đơn lẻ sẽ bỏ sót mất tài liệu và duplicate. Báo cáo nhóm không ghi lại kỳ vọng cá nhân trước thử nghiệm.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Clean schema là giao diện chung giữa ingestion, observability và retrieval; DOI ổn định giúp truy vết dữ liệu xuyên suốt pipeline.
2. Đủ số dòng không đồng nghĩa dữ liệu đúng. Cần kết hợp kiểm tra nội dung, uniqueness và freshness.
3. Benchmark cố định giúp quan sát tác động của dữ liệu đến RAG, nhưng benchmark nhỏ và Mock chưa chứng minh khả năng tổng quát.

### Nếu có thêm thời gian

Mở rộng benchmark lên ít nhất 20 câu, phân bổ theo 5 loại và nhiều tài liệu hơn; bổ sung cách hỏi diễn đạt lại thay vì chỉ dùng đúng tiêu đề. Giữ nguyên benchmark cho ba trạng thái, đo metric từng loại và thử từng corruption riêng để xác định mức suy giảm do mỗi lỗi. Đây là cải thiện đề xuất, chưa triển khai.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Trịnh Đức Huy
**Ngày xác nhận:** 25/09/2026
