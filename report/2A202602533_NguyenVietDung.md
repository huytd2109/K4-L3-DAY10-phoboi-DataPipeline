# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Nguyễn Việt Dũng |
| MSSV | 2A202602533 |
| Khóa/Lớp | K4-L3-DAY10 |
| Tên nhóm | phoboi |
| Vai trò chính | Corruption & repair owner |
| Repository | https://github.com/huytd2109/K4-L3-DAY10-phoboi-DataPipeline |
| Ngày hoàn thành | 2026-09-25 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
|---|---|---|---|---|
| Bộ tạo lỗi dữ liệu (Corruption Suite) | `src/ingestion/corruption.py` — `corrupt_clean_dataframe()` | Clean DataFrame từ `cleaning.py` | Corrupted DataFrame (`data/clean/papers_clean_corrupted.csv` và `.json`), kèm audit log `data/results/corruption_log.json` | Hoàn thành |
| Dữ liệu phục hồi (Repaired Dataset) | `src/pipelines/corruption_flow.py` (phần repair logic) | Raw records snapshot `crossref_records.json` | Repaired DataFrame (`data/clean/papers_clean_repaired.csv` và `.json`) | Hoàn thành |
| Nhật ký kiểm toán tiêm lỗi | `data/results/corruption_log.json` | Chi tiết 6 kịch bản lỗi | Audit trail JSON chứa danh sách DOI bị ảnh hưởng | Hoàn thành |

Theo phân công trong `group_report.md`, tôi nhận dữ liệu sạch đã được chuẩn hóa từ Trịnh Đức Huy (`cleaning.py`), xây dựng bộ 6 kịch bản tiêm lỗi dữ liệu có chủ đích (Controlled Data Corruption) để giả lập các sự cố dữ liệu thực tế trong sản xuất. Đồng thời, tôi phối hợp với Nguyễn Hoàng Sơn (`corruption_flow.py`) triển khai quy trình tự phục hồi dữ liệu an toàn (Idempotent Repair) bằng cách đọc lại từ bản sao lưu thô bất biến của Đỗ Quốc An (`crossref_records.json`), cung cấp đầu vào cho Trịnh Hoàng Tùng đối chiếu chất lượng qua Great Expectations và Freshness SLA.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
|---|---|---|
| Cung cấp kịch bản lỗi để kiểm thử Data Quality Gate | Trịnh Hoàng Tùng — `quality.py` | Kiểm chứng Great Expectations 1.x bắt chính xác lỗi null, blank summary và duplicate DOI |
| Cung cấp dataset lỗi và phục hồi cho luồng Phase 2 | Nguyễn Hoàng Sơn — `corruption_flow.py` | Thực thi end-to-end đo lường suy giảm (Hit Rate 1.0 → 0.6) và phục hồi hoàn toàn (0.6 → 1.0) |
| Tối ưu hóa offline embedding fallback | Cả nhóm — `retrieval/embeddings.py` | Khắc phục timeout mạng HuggingFace, giúp pipeline chạy offline ổn định |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
|---|---|---|---|
| Triển khai 6 kịch bản tiêm lỗi | `src/ingestion/corruption.py` | Corrupted DataFrame với 6 dạng lỗi chuẩn hóa | Kiểm tra mã nguồn và `data/results/corruption_log.json` |
| Tái tính toán các trường dẫn xuất | `corrupt_clean_dataframe()` | Cập nhật `age_days`, `summary_chars`, `text_for_embedding` trên dữ liệu hỏng | Đối chiếu các cột trong `data/clean/papers_clean_corrupted.json` |
| Xuất log kiểm toán chi tiết | `data/results/corruption_log.json` | Ghi nhận chi tiết 6 kịch bản và danh sách DOI bị tác động | Kiểm tra file log JSON trong thư mục results |
| Thực hiện Idempotent Repair | `src/pipelines/corruption_flow.py` | 24 bản ghi sạch được tái sinh từ raw snapshot | So sánh `papers_clean.json` và `papers_clean_repaired.json` |

Output cụ thể mà phần việc của tôi tạo ra là file nhật ký [data/results/corruption_log.json](file:///d:/AI20K_LABS/K4-L3-DAY10-phoboi-DataPipeline/data/results/corruption_log.json) và 2 bộ dữ liệu: dữ liệu lỗi `papers_clean_corrupted.json` và dữ liệu sau phục hồi `papers_clean_repaired.json`. Log kiểm toán ghi nhận chính xác 5 bài báo mới nhất bị loại bỏ, 4 bài bị xóa summary, 4 bài bị chèn nhiễu, 4 bài bị cắt ngắn tiêu đề, 7 bài bị lùi ngày xuất bản về 5 năm trước và 5 bản ghi bị nhân bản để kiểm thử tính duy nhất.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Trong các hệ thống RAG thực tế, dữ liệu hiếm khi giữ được trạng thái hoàn hảo mãi mãi. Lỗi cào dữ liệu thiếu trường, lỗi crawl lặp bản ghi, dữ liệu cũ không được cập nhật hoặc nhiễu ký tự thường gây ra hiện tượng **Silent Failure** — AI vẫn sinh câu trả lời tự tin nhưng nội dung hoàn toàn sai lệch (Hallucination) mà không ném ra exception nào.

Module `corruption.py` giải quyết bài toán giả lập có chủ đích các dạng lỗi này để kiểm tra xem "chốt kiểm dịch" (Quality Gate) có phát hiện được không, và hệ thống có khả năng tự phục hồi mà không phụ thuộc vào dữ liệu đã bị hỏng hay không.

### Cách triển khai

Hàm `corrupt_clean_dataframe()` thực hiện tuần tự 6 bước biến đổi có tính tất định (deterministic):

1. **Drop latest records:** Xác định 20% bản ghi có ngày xuất bản mới nhất (`ceil(original_count * 0.20) = 5` bản ghi) dựa trên `pd.to_datetime` và loại bỏ chúng. Điều này mô phỏng sự cố đứt gãy pipeline thu thập tài liệu mới.
2. **Blank summary:** Chọn 4 bản ghi đầu tiên và gán `summary = ""` để mô phỏng lỗi parser cào trúng thẻ rỗng.
3. **Inject noise:** Chọn 4 bản ghi kế tiếp và nối thêm chuỗi nhiễu `" ###@@@ CORRUPTED-NOISE 0000 ??? ###@@@"` vào trường `summary`.
4. **Truncate title:** Chọn 4 bản ghi tiếp theo và cắt ngắn tiêu đề xuống còn 7 ký tự (`str.slice(0, 7)`).
5. **Stale date:** Chọn 7 bản ghi và lùi ngày xuất bản về 5 năm trước (`- pd.DateOffset(years=5)`), khiến `age_days` tăng vọt để kích hoạt cảnh báo Freshness SLA.
6. **Duplicate rows:** Lấy 5 bản ghi đầu tiên của tập hiện tại và ghép nối ngược lại (`pd.concat`) để tạo ra 5 dòng trùng lặp hoàn toàn về `paper_id`.

Sau khi biến đổi các trường gốc, hàm **bắt buộc phải tái tính toán** các trường phụ thuộc:
- `age_days = (now - published).days`
- `summary_chars = len(summary)`
- `text_for_embedding`: Nối lại toàn bộ Title, Authors, Published, Categories, Summary để Vector Store phản ánh đúng dữ liệu đã bị làm hỏng.

Về phía **Idempotent Repair**, thay vì cố gắng sửa chữa cục bộ trên dữ liệu bẩn (vốn không thể hồi phục lại 5 bài báo đã bị xóa), cơ chế phục hồi quay trở lại cội nguồn dữ liệu: đọc trực tiếp từ `crossref_records.json` (bản snapshot bất biến), gọi lại hàm `build_clean_dataframe()` với cùng logic chuẩn hóa, sau đó ghi đè collection trong ChromaDB.

### Input, output và contract

| Thành phần | Mô tả |
|---|---|
| Input | Clean DataFrame 24 dòng từ `build_clean_dataframe()`, đường dẫn lưu audit log |
| Output | Corrupted DataFrame (24 dòng chứa dữ liệu lỗi và trùng lặp), file `corruption_log.json` |
| Module phụ thuộc | `pandas`, `math.ceil`, `core.utils.write_json` |
| Module sử dụng output | `observability/quality.py` (đánh giá lỗi), `retrieval/index.py` (tạo collection `papers-corrupted`), `pipelines/corruption_flow.py` |
| Điều kiện lỗi cần xử lý | DataFrame rỗng gây `ValueError`; chỉ số xoay vòng `(start + offset) % len(corrupted)` đảm bảo không bị `IndexError` khi số dòng thay đổi |

### Cách xác minh

Quy trình được xác minh tự động thông qua kịch bản:

```bash
python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** 
  - File `data/results/corruption_log.json` xuất hiện đầy đủ 6 scenario.
  - Quality Gate chuyển từ `True` sang `False`.
  - Freshness SLA cảnh báo dữ liệu mốc (Stale ratio tăng vượt 25%).
  - Retrieval Hit Rate tụt giảm rõ rệt.
  - Sau bước repair, toàn bộ chỉ số và dữ liệu trở lại khớp 100% với Baseline.
- **Kết quả thực tế:**
  - `corruption_log.json` ghi nhận đầy đủ 6 kịch bản.
  - Quality Gate: `True` → `False` → `True`.
  - Freshness SLA: `True` (4.17%) → `False` (29.17%) → `True` (4.17%).
  - Hit Rate: `1.000` → `0.600` → `1.000`.
  - File `papers_clean_repaired.json` trùng khớp hoàn toàn nội dung với `papers_clean.json`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần quyết định cơ chế phục hồi dữ liệu (Data Repair): nên viết hàm "vá lỗi" trực tiếp trên tập dữ liệu bẩn (in-place repair/imputation) hay tái tạo lại toàn bộ từ raw snapshot (re-ingestion from immutable raw).
- **Các phương án đã cân nhắc:**
  1. *Phương án A (In-place patch):* Loại bỏ các dòng duplicate, điền giá trị mặc định cho summary rỗng, lọc bỏ chuỗi noise.
  2. *Phương án B (Rebuild from Raw Lineage):* Coi dữ liệu thô ban đầu là bất biến (Immutable Raw Lake). Khi phát hiện hỏng hóc, kích hoạt pipeline chạy lại từ raw snapshot và ghi đè index vector.
- **Phương án đã chọn:** Chọn **Phương án B (Rebuild from Raw Lineage)**.
- **Lý do:** Phương án A không thể giải quyết được triệt để bài toán: những bài báo mới nhất đã bị xóa mất (`drop_latest_records`) thì không thể nào tự "mọc" lại nếu chỉ nhìn vào dữ liệu bẩn. Hơn nữa, việc cố vá lỗi nội dung bị cắt ngắn hoặc lùi ngày rất dễ để lại các vector rác ("ghost vectors"). Phương án B đảm bảo tính **Idempotent** (tính bất biến theo thời gian): chạy lại bao nhiêu lần thì kết quả đầu ra vẫn luôn đúng chuẩn 100% như ban đầu.
- **Bằng chứng quyết định phù hợp:** Kết quả đối chiếu tại `corruption_report.md` cho thấy sau khi repair bằng phương án B, Retrieval Hit Rate hồi phục tuyệt đối từ `0.6000` về `1.0000`, Token F1 từ `0.8000` về `1.0000`, và file dữ liệu repaired trùng khớp từng ký tự với clean baseline ban đầu.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:**
  ```text
  Traceback (most recent call last):
    File "src/retrieval/agent.py", line 5, in <module>
      from langchain.agents import create_agent
  ImportError: cannot import name 'create_agent' from 'langchain.agents'
  ```
  Kèm theo lỗi timeout khi gọi model embeddings:
  ```text
  OSError: We couldn't connect to 'https://huggingface.co' to load the files... Read timed out.
  ```
- **Lệnh hoặc bước tái hiện:** Chạy lệnh `python script/run_phase1.py` hoặc `python script/run_corruption_flow.py` trên môi trường máy trạm.
- **Nguyên nhân gốc:** 
  1. Trong LangChain phiên bản mới (0.3.x / 1.x), hàm `create_agent` đã được tách sang `langgraph.prebuilt.create_react_agent`.
  2. Thư viện `SentenceTransformer` cố gắng tải weights `all-MiniLM-L6-v2` từ CDN HuggingFace (`us.aws.cdn.hf.co`) nhưng bị timeout do mạng quốc tế không ổn định.
- **Cách xử lý:** 
  1. Viết adapter bọc an toàn trong `src/retrieval/agent.py`: bắt `ImportError` và ánh xạ tham số `system_prompt` sang `prompt` của `create_react_agent`.
  2. Chuyển các import provider trong `src/retrieval/llm.py` thành lazy import (chỉ import khi cấu hình provider đó).
  3. Bổ sung cơ chế **Deterministic Offline Embedding Fallback** trong `src/retrieval/embeddings.py` (tạo vector 384 chiều dựa trên token hashing và character n-grams) khi weights Hugging Face chưa có sẵn trong local cache.
- **Cách xác minh sau khi sửa:** Chạy lại `python script/run_corruption_flow.py`, pipeline thực thi trơn tru với exit code 0 mà không cần kết nối mạng bên ngoài, in ra:
  ```text
  Corruption and repair pipeline complete.
  Retrieval hit rate — baseline: 1.000, corrupted: 0.600, repaired: 1.000.
  ```
- **Điều học được:** Môi trường production và phòng lab luôn tiềm ẩn rủi ro về dependency mismatch và network timeout. Thiết kế module luôn phải có cơ chế fallback mềm (graceful degradation) để đảm bảo pipeline không bị gián đoạn.

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**  
   *Trả lời:* Dữ liệu metadata được kéo từ Crossref REST API (hoặc nạp từ snapshot JSON có sẵn), lưu nguyên bản tại `data/raw/`. Sau đó, module cleaning tiến hành giải mã HTML, chuẩn hóa chuỗi, tính `age_days` và ghép thành đoạn văn bản `text_for_embedding`. Dữ liệu sau đó đi qua chốt kiểm dịch Great Expectations 1.x và Freshness SLA. Khi đạt chuẩn, mô hình embedding biến đổi văn bản thành vector 384 chiều và nạp vào database ChromaDB tương ứng.

2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**  
   *Trả lời:* Mỗi câu hỏi trong benchmark có danh sách `ground_truth_doc_ids` (chứa DOI của bài báo gốc). Khi truy vấn, hệ thống tìm ra top-k tài liệu. Nếu trong top-k có chứa DOI mục tiêu, lượt truy vấn được tính là 1 điểm **Retrieval Hit**. Nội dung văn bản retrieved sau đó được đưa vào prompt LLM để sinh câu trả lời; câu trả lời được đối chiếu với `ground_truth` thông qua Token F1 và LLM Judge.

3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**  
   *Trả lời:* Quality checks (Great Expectations) tập trung vào tính toàn vẹn cấu trúc và nội dung (schema, độ dài, null, unique). Ngược lại, Freshness monitoring đo lường chiều không gian thời gian (temporal drift): một bản ghi có thể hoàn toàn hợp lệ về mặt cấu trúc (không null, tiêu đề dài) nhưng đã được xuất bản quá lâu (`age_days > 180`). Freshness bảo vệ AI khỏi việc đưa ra lời khuyên dựa trên tri thức đã lỗi thời.

4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**  
   *Trả lời:* Để đảm bảo tính khách quan khoa học (Controlled Experiment). Nếu mỗi trạng thái dùng một bộ đề thi khác nhau, ta không thể biết điểm số thay đổi là do dữ liệu tốt/xấu hay do câu hỏi dễ/khó. Giữ nguyên bộ test set giúp cô lập biến số duy nhất là **chất lượng của kho dữ liệu**.

5. **Repair được xem là thành công dựa trên artifact và metric nào?**  
   *Trả lời:* Phục hồi thành công khi và chỉ khi thỏa mãn đồng thời:
   - File dữ liệu `papers_clean_repaired.json` trùng khớp với `papers_clean.json`.
   - Quality Gate và Freshness SLA từ `Fail` chuyển lại thành `Pass`.
   - Retrieval Hit Rate từ mức suy giảm (`0.600`) phục hồi hoàn toàn về mức ban đầu (`1.000`).

## 8. Phân tích kết quả

### Metrics chính

| Metric / Tín hiệu | Baseline (Sạch) | Corrupted (Lỗi) | Repaired (Phục Hồi) | Nhận xét cá nhân |
|---|---:|---:|---:|---|
| `retrieval_hit_rate` | **1.0000** | **0.6000** | **1.0000** | Rơi 40% do 5 bài báo mới bị xóa; phục hồi 100% sau repair |
| `mean_token_f1` | **1.0000** | **0.8000** | **1.0000** | Câu trả lời bị suy giảm độ chính xác khi thiếu ngữ cảnh |
| `judge_accuracy` | **1.0000** | **0.8000** | **1.0000** | Đánh giá tính chính xác của câu trả lời |
| `mean_judge_score` | **5.0000** | **4.2000** | **5.0000** | Điểm số sụt giảm tương ứng khi dữ liệu bị lỗi |
| Great Expectations Quality Gate | **Pass (True)** | **Fail (False)** | **Pass (True)** | Bắt được lỗi summary rỗng và trùng khóa `paper_id` |
| Freshness Status | **Pass (True)** | **Fail (False)** | **Pass (True)** | Bắt được sự cố dữ liệu cũ vượt ngưỡng |
| Tỷ lệ bài quá hạn (Stale Ratio) | **4.17%** | **29.17%** | **4.17%** | Vượt ngưỡng SLA 25% (đạt 29.17%) nên bị cảnh báo |

### Kết luận từ số liệu

1. **Hiểm họa Silent Failure được chứng minh rõ ràng:** Khi dữ liệu bị tiêm lỗi, hệ thống không hề ném lỗi runtime exception mà vẫn trả về kết quả; tuy nhiên Hit Rate sụt giảm nghiêm trọng từ `1.0` xuống `0.6` và Token F1 giảm xuống `0.8`. Nếu không có Data Observability Gate gióng chuông báo động (`Fail`), người dùng cuối sẽ phải hứng chịu các câu trả lời sai lệch từ AI.
2. **Cơ chế Idempotent Repair đạt hiệu quả tuyệt đối:** Việc khôi phục từ nguồn raw snapshot bất biến đã tái sinh chính xác 100% dữ liệu gốc, đưa toàn bộ chỉ số Retrieval Hit Rate và Token F1 quay trở lại mức `1.0000`.

**Corruption nào ảnh hưởng rõ nhất và vì sao?**  
Kịch bản `drop_latest_records` (xóa 20% bài mới nhất) gây tác động trực tiếp và nghiêm trọng nhất lên Retrieval Hit Rate. Các câu hỏi trong benchmark nhắm vào các bài báo mới không thể tìm thấy tài liệu gốc trong kho vector (do tài liệu đã biến mất hoàn toàn), dẫn đến việc Hit Rate bị đánh rớt trực tiếp từ 1.0 xuống 0.6.

**Kết quả nào khác với kỳ vọng ban đầu?**  
Điểm bất ngờ và thú vị nhất là: **Tổng số dòng của dataset bị lỗi vẫn giữ nguyên là 24 dòng!**  
Lý do nằm ở chỗ: ta đã xóa 5 dòng mới nhất nhưng đồng thời nhân bản thêm 5 dòng khác (`duplicate_rows`). Nếu một kỹ sư dữ liệu chỉ kiểm tra số lượng dòng (`len(df) == 24`), họ sẽ hoàn toàn bị đánh lừa và tin rằng dữ liệu vẫn ổn. Điều này chứng minh rằng việc kiểm tra số dòng đơn thuần là không đủ, bắt buộc phải có các Expectation về tính duy nhất (`ExpectColumnValuesToBeUnique`) và kiểm tra độ tươi (`Freshness SLA`).

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Dữ liệu thô là "bảo hiểm trọn đời":** Luôn lưu trữ nguyên vẹn dữ liệu gốc (Raw Preservation) ở tầng lưu trữ bất biến (Immutable Storage). Đây là chìa khóa duy nhất để thực hiện Idempotent Repair khi hệ thống gặp thảm họa dữ liệu.
2. **Data Observability là bắt buộc đối với RAG:** Không thể tin tưởng mù quáng vào dữ liệu đầu vào. Chốt kiểm dịch Great Expectations và Freshness SLA là lớp phòng ngự đầu tiên và quan trọng nhất để ngăn chặn rác lọt vào Vector Store.
3. **Số lượng không phản ánh chất lượng:** Một dataset đủ số lượng dòng vẫn có thể chứa toàn dữ liệu rác, trùng lặp hoặc tri thức đã hết hạn.

### Nếu có thêm thời gian

Tôi muốn phát triển thêm kịch bản kiểm thử tác động độc lập (Ablation Study): chạy riêng lẻ từng kịch bản lỗi trong 6 loại để đo lường chính xác "mức độ sát thương" định lượng của từng dạng lỗi lên điểm số Token F1 và Hit Rate, thay vì tiêm đồng thời cả 6 lỗi cùng lúc như hiện tại.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Việt Dũng  
**Ngày xác nhận:** 25/09/2026
