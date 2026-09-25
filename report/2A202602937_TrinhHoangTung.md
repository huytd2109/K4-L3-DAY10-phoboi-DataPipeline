# Individual Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Trịnh Hoàng Tùng |
| MSSV | 2A202602937 |
| Khóa/Lớp | K4-L3-DAY10 |
| Tên nhóm | phoboi |
| Repository | https://github.com/huytd2109/K4-L3-DAY10-phoboi-DataPipeline |
| Ngày hoàn thành | 2026-09-25 |
| Vai trò trong nhóm | Observability & Reporting Owner |
| Module sở hữu | `quality.py`, `reporting.py`, GX 1.x và Freshness SLA |

---

## 2. Mô tả vai trò và trách nhiệm cá nhân

Tôi phụ trách toàn bộ tầng **quan sát dữ liệu (data observability)** và **sinh báo cáo tự động** trong pipeline. Vai trò này bao gồm hai module chính:

- **`src/observability/quality.py`** — Thiết kế và triển khai bộ kiểm định dữ liệu bằng Great Expectations 1.x (GX) và cơ chế theo dõi Freshness SLA.
- **`src/observability/reporting.py`** — Sinh báo cáo Markdown tự động từ các artifact thực tế (không nhập tay), bao gồm `phase1_report.md` và `corruption_report.md`.

Kết quả đầu ra tôi chịu trách nhiệm:
- `data/quality/baseline_quality_report.json`
- `data/quality/corrupted_quality_report.json`
- `data/quality/repaired_quality_report.json`
- `data/quality/freshness_report.json`
- `data/quality/corrupted_freshness_report.json`
- `data/quality/repaired_freshness_report.json`
- `data/reports/phase1_report.md`
- `data/reports/corruption_report.md`

---

## 3. Chi tiết kỹ thuật: `quality.py`

### 3.1. Thiết kế GX 1.x Expectations

Hàm `run_data_quality_checks()` nhận một DataFrame và chạy 6 expectations theo API GX 1.x (ephemeral context — không cần file config):

```python
expectations = [
    gxe.ExpectTableRowCountToBeBetween(min_value=5, max_value=5000),
    gxe.ExpectColumnValuesToNotBeNull(column="paper_id"),
    gxe.ExpectColumnValuesToNotBeNull(column="title"),
    gxe.ExpectColumnValuesToNotBeNull(column="text_for_embedding"),
    gxe.ExpectColumnValuesToBeUnique(column="paper_id"),
    gxe.ExpectColumnValueLengthsToBeBetween(column="summary", min_value=30),
]
```

**Lý do chọn từng expectation:**

| Expectation | Dimension | Lý do thiết kế |
|---|---|---|
| `RowCountToBeBetween(5, 5000)` | Volume | Phát hiện pipeline trả về quá ít/quá nhiều bản ghi |
| `paper_id not null` | Completeness | DOI là định danh duy nhất, không thể thiếu |
| `title not null` | Completeness | Thiếu title → không tạo được `text_for_embedding` |
| `text_for_embedding not null` | Completeness | Cột đầu vào trực tiếp cho MiniLM embedding |
| `paper_id unique` | Uniqueness | DOI trùng lặp gây xung đột trong ChromaDB |
| `summary length ≥ 30` | Validity | Summary quá ngắn → ngữ nghĩa không đủ cho RAG retrieval |

### 3.2. Quality Gate tích hợp

Hàm trả về một `payload` JSON chứa:
- `success`: kết hợp GX success **và** Freshness SLA
- `expectations_success`: kết quả 6 expectations GX
- `statistics`: đếm pass/fail
- `freshness`: thông tin stale ratio
- `results`: chi tiết từng expectation

Lý do tôi thiết kế quality gate dưới dạng **hàm đơn thuần** (không dùng GX Data Docs hay Suite file) là để pipeline có thể chạy trong môi trường không có UI, không phụ thuộc file system cụ thể, và dễ tích hợp với các bước tiếp theo.

### 3.3. Freshness SLA

Hàm `build_freshness_report()` tính toán và ghi ra JSON riêng biệt:

```
stale_rows = count(age_days > 180)
stale_ratio = stale_rows / total_rows
is_fresh = stale_ratio <= 0.25
```

**Quyết định thiết kế:** Ngưỡng 25% stale cho phép pipeline chấp nhận một số bài báo cũ hơn 180 ngày mà không báo động, phù hợp với thực tế Crossref snapshot có thể chứa bài báo biên giới. Ngưỡng `freshness_threshold_days = 180` được cấu hình trong `core/config.py` và truyền vào từ `Settings`, tránh hardcode trong observability.

---

## 4. Chi tiết kỹ thuật: `reporting.py`

### 4.1. `generate_phase1_report()`

Hàm `generate_phase1_report()` nhận đầu vào là các dict artifact thực tế và sinh Markdown thuần túy. **Không có giá trị nào được nhập tay** — toàn bộ nội dung đến từ `source_summary`, `metrics`, `quality`, `freshness` do các module khác tạo ra.

Cấu trúc báo cáo:
1. Bảng thông tin nguồn dữ liệu và số bản ghi
2. Bảng metric đánh giá (`retrieval_hit_rate`, `mean_token_f1`, `judge_accuracy`, `mean_judge_score`)
3. Tổng hợp GX success, Freshness SLA, publication range

### 4.2. `generate_corruption_report()`

Hàm `generate_corruption_report()` so sánh ba trạng thái baseline/corrupted/repaired trong một báo cáo duy nhất:
- Bảng metric so sánh 4 chỉ số retrieval
- Bảng Quality Gate và Freshness SLA cho ba trạng thái
- Phần diễn giải tự động tính delta và trình bày kết quả phục hồi

**Lý do thiết kế hai hàm riêng biệt thay vì một hàm chung:** Phase 1 và corruption flow có cấu trúc báo cáo khác nhau căn bản — phase 1 tập trung vào baseline, còn corruption flow cần bảng so sánh ba chiều. Tách ra giúp mỗi hàm đơn giản và dễ unit test.

---

## 5. Kết quả artifact thực tế

### 5.1. Baseline Quality Report

| Check | Kết quả | Observed value |
|---|---|---|
| Row count (5–5000) | ✅ Pass | 24 rows |
| `paper_id` not null | ✅ Pass | 0 unexpected |
| `title` not null | ✅ Pass | 0 unexpected |
| `text_for_embedding` not null | ✅ Pass | 0 unexpected |
| `paper_id` unique | ✅ Pass | 0 unexpected |
| `summary` length ≥ 30 | ✅ Pass | 0 unexpected |
| **GX Overall** | ✅ **6/6 Pass** | 100% |
| **Quality Gate** | ✅ **Pass** | success=true |

### 5.2. Freshness SLA — Baseline

| Thuộc tính | Giá trị |
|---|---|
| Threshold | 180 ngày |
| Publication range | 2026-03-28 → 2026-07-22 |
| Total rows | 24 |
| Stale rows | 1 |
| Stale ratio | 4.17% |
| Maximum allowed | 25% |
| **is_fresh** | ✅ **true** |

### 5.3. Corrupted Quality Report

| Check | Kết quả | Chi tiết |
|---|---|---|
| Row count (5–5000) | ✅ Pass | 24 rows |
| `paper_id` not null | ✅ Pass | 0 unexpected |
| `title` not null | ✅ Pass | 0 unexpected |
| `text_for_embedding` not null | ✅ Pass | 0 unexpected |
| `paper_id` unique | ❌ **Fail** | 10 unexpected (41.67%) — 5 DOI bị nhân bản |
| `summary` length ≥ 30 | ❌ **Fail** | 8 unexpected (33.33%) — summary bị blank |
| **GX Overall** | ❌ **4/6 Pass** | 66.67% |
| **Quality Gate** | ❌ **Fail** | success=false |
| Stale ratio | ❌ **Fail** | 29.17% > 25% threshold |

### 5.4. Repaired Quality Report

Sau khi rebuild từ `data/raw/crossref_records.json`:
- Tất cả 6 GX expectations: **Pass**
- Stale ratio: **4.17%** (khôi phục về baseline)
- Quality Gate: **Pass**
- is_fresh: **true**

---

## 6. Phân tích: Tại sao Quality Gate phát hiện được corruption?

### Cơ chế phát hiện

**Blank summary** (4 records bị tiêm) → `ExpectColumnValueLengthsToBeBetween(min_value=30)` fail ngay lập tức vì summary trở thành chuỗi rỗng (length = 0 < 30).

**Duplicate rows** (5 records bị nhân bản) → `ExpectColumnValuesToBeUnique(column="paper_id")` phát hiện 10 giá trị vi phạm uniqueness (5 DOI × 2 lần xuất hiện).

**Stale date** (7 records bị lùi ngày 5 năm) → `age_days` tăng vọt → stale_ratio từ 4.17% lên 29.17% → `is_fresh = false`.

### Corruption không bị GX phát hiện trực tiếp

| Corruption | GX phát hiện? | Lý do |
|---|---|---|
| Drop latest records | ❌ (gián tiếp) | Row count vẫn = 24 do duplicate bù vào |
| Inject text noise | ❌ | GX không check nội dung ngữ nghĩa |
| Truncate title | ❌ | GX không check độ dài title |

Đây là hạn chế có chủ ý của thiết kế hiện tại: GX kiểm định **schema và structural integrity**, còn semantic quality (embedding similarity, title coherence) cần metric đánh giá retrieval.

---

## 7. Đóng góp vào kiến trúc pipeline

Hai module của tôi được tích hợp vào pipeline qua hai điểm gọi trong `phase1.py` và `corruption_flow.py`:

```python
# phase1.py
quality = run_data_quality_checks(clean_df, settings, "baseline")
freshness = build_freshness_report(clean_df, settings, settings.paths.freshness_report)
if not quality["success"]:
    raise RuntimeError("Baseline data failed the quality gate.")
generate_phase1_report(...)
```

Thiết kế `if not quality["success"]: raise RuntimeError(...)` đảm bảo pipeline **dừng lại** nếu baseline không đạt quality gate, thay vì tiếp tục index dữ liệu xấu vào ChromaDB. Đây là **fail-fast pattern** quan trọng cho data pipeline.

---

## 8. Thách thức kỹ thuật đã gặp

### 8.1. API GX 1.x khác biệt với GX 0.x

Great Expectations 1.x thay đổi cách khởi tạo context và batch so với các tutorial phổ biến. Tôi phải dùng `gx.get_context(mode="ephemeral")` thay vì `DataContext`, và `batch_definition.get_batch(batch_parameters={"dataframe": df})` thay vì `RuntimeBatchRequest`. Việc đặt tên source/asset/batch đúng định dạng `{source_name}-{asset_name}` (thể hiện trong `batch_id` trong kết quả JSON) mất thời gian debug.

### 8.2. Thiết kế report_name linh hoạt

Hàm `_quality_report_path()` cho phép gọi `run_data_quality_checks()` với bất kỳ tên nào (`"baseline"`, `"corrupted"`, `"repaired"`, hoặc tên tùy chỉnh) và tự động tạo đường dẫn file phù hợp. Điều này cho phép `corruption_flow.py` gọi cùng hàm cho cả ba trạng thái mà không cần hardcode path.

### 8.3. Tên GX context phải unique trong cùng session

GX 1.x ephemeral context có hành vi: nếu cùng session gọi `add_pandas(name=...)` với tên đã tồn tại, sẽ bị lỗi. Giải pháp là nối `report_name` vào tên source/asset/batch để đảm bảo uniqueness: `f"papers_source_{report_name}"`.

---

## 9. Bài học rút ra

1. **Observability là lớp bảo vệ, không phải addon:** Quality Gate được thiết kế để block pipeline ngay ở baseline nếu dữ liệu xấu. Cách làm này giúp corruption scenarios có tác động rõ ràng và đo lường được.

2. **Separation of concerns giữa quality check và reporting:** `quality.py` chỉ tính và lưu JSON; `reporting.py` chỉ đọc JSON và sinh Markdown. Việc tách này cho phép test từng phần độc lập và tái sử dụng reporting cho các pipeline khác.

3. **Freshness SLA cần ngưỡng có căn cứ:** Chọn 25% maximum stale ratio không phải ngẫu nhiên — ngưỡng này đủ chặt để phát hiện `stale_date` corruption (29.17%) nhưng đủ rộng để chấp nhận data source thực tế có một số bài báo biên giới.

4. **GX 1.x phù hợp cho pipeline tự động hơn GX 0.x:** Mode ephemeral không cần file config, không cần `great_expectations.yml`, phù hợp cho pipeline chạy trong môi trường CI/CD hoặc container.

---

## 10. Checklist cá nhân

- [x] `quality.py` triển khai đúng GX 1.x API với 6 expectations
- [x] `reporting.py` sinh báo cáo hoàn toàn từ artifact, không có giá trị hardcode
- [x] Quality Gate block pipeline khi baseline fail
- [x] Freshness SLA tích hợp vào `quality["success"]`
- [x] Báo cáo ba trạng thái baseline/corrupted/repaired chính xác và khớp với `data/results/`
- [x] Tên GX source/asset/batch unique cho mỗi lần gọi
- [x] Không có API key hay secret trong module
