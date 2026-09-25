# Individual Report — Nguyễn Hoàng Sơn

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Nguyễn Hoàng Sơn |
| MSSV | 2A202602457 |
| Khóa/Lớp | K4-L3-DAY10 |
| Tên nhóm | phoboi |
| Vai trò chính | Pipeline integration & evidence owner |
| Repository | https://github.com/huytd2109/K4-L3-DAY10-phoboi-DataPipeline |
| Ngày hoàn thành | 2026-09-25 |

## 2. Vai trò và phạm vi công việc

| Module/deliverable | File/hàm phụ trách | Input | Output | Trạng thái |
|---|---|---|---|---|
| Baseline orchestration | `src/pipelines/phase1.py` | Raw records và settings | Clean/index/test/metrics/report artifacts | Hoàn thành |
| Corruption/repair orchestration | `src/pipelines/corruption_flow.py` | Baseline artifacts | Corrupted/repaired metrics và comparison report | Hoàn thành |
| Vector index integration | `src/retrieval/index.py` | Clean DataFrame | Ba Chroma collections và manifests | Hoàn thành |
| Evidence verification | `data/results/`, `data/reports/` | Pipeline outputs | Bảng so sánh ba trạng thái | Hoàn thành |

Tôi nhận output từ source, cleaning, observability và corruption owners; nhiệm vụ chính là giữ đúng thứ tự thực thi, dùng cùng test set và cấu hình cho ba trạng thái, đồng thời bảo đảm report phản ánh đúng JSON metrics.

## 3. Kết quả bàn giao và xác minh

- Baseline chỉ build index sau khi Quality Gate pass.
- Corruption flow kiểm tra đủ baseline prerequisites trước khi chạy.
- Ba collection tách biệt: `papers-baseline`, `papers-corrupted`, `papers-repaired`.
- Embedding manifest dùng đường dẫn tương đối; loader mở Chroma của clone hiện tại.
- Baseline, corrupted và repaired dùng cùng `data/eval/test_set.json`.

```bash
python script/run_phase1.py
python script/run_corruption_flow.py
```

Kết quả mong đợi: hai lệnh exit code 0, Quality/Freshness Pass → Fail → Pass, repaired metrics trở lại baseline.

## 4. Quyết định kỹ thuật

- **Bối cảnh:** Ba trạng thái không được ghi đè collection của nhau và artifacts phải dùng được sau khi clone sang máy khác.
- **Phương án:** Một collection dùng chung, hoặc ba collection riêng với manifest portable.
- **Lựa chọn:** Ba collection riêng và resolve Chroma qua `settings.paths.chroma_dir`.
- **Lý do:** So sánh khách quan, chạy lại idempotent và tránh phụ thuộc đường dẫn tuyệt đối của máy tạo artifact.

## 5. Lỗi/blocker và cách xử lý

- **Triệu chứng:** Manifest cũ lưu đường dẫn tuyệt đối từ máy khác; corruption flow có thể đọc quality report chưa tồn tại.
- **Nguyên nhân:** Persist path được serialize trực tiếp và danh sách prerequisite chưa bao phủ mọi file được đọc.
- **Xử lý:** Lưu persist path tương đối, loader dùng project path hiện tại và bổ sung quality/freshness vào prerequisite.
- **Xác minh:** Manifest không còn ký tự ổ đĩa Windows; hai pipeline chạy lại thành công từ workspace hiện tại.

## 6. Hiểu biết end-to-end

Baseline tạo dữ liệu và chuẩn đánh giá trước. Corruption và repair bắt buộc reuse cùng test set để thay đổi metric phản ánh thay đổi dữ liệu. Quality checks phát hiện completeness/uniqueness, Freshness phát hiện dữ liệu quá tuổi; hai loại tín hiệu bổ sung cho retrieval và answer metrics. Repair thành công khi clean và repaired tương đương, Quality/Freshness pass và metrics trở lại baseline.

## 7. Phân tích kết quả

Corruption làm mất DOI mục tiêu, làm rỗng summary, nhiễu embedding, cắt title, làm cũ ngày và tạo duplicate. Kết quả phải thể hiện retrieval/answer metric suy giảm, trong khi repair từ raw khôi phục cả dữ liệu và chỉ số. Judge chạy ở chế độ heuristic fallback khi dùng provider `mock`; kết luận này được ghi rõ thay vì trình bày như kết quả LLM thật.

## 8. Điều học được và cam kết

Tôi hiểu orchestration, artifact contracts, isolation giữa vector collections và cách dùng evidence để kết luận. Nội dung trên chỉ nhận ownership cho tích hợp/evidence, không chứa secret và có thể kiểm chứng bằng lệnh cùng artifacts nêu trên.
