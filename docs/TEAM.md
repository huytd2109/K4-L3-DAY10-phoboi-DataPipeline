# Danh Sách Thành Viên & Báo Cáo Phân Công Nhóm

- **Tên Nhóm:** `phoboi`
- **Mã Nhóm / Lớp:** `K4-L3-DAY10`
- **Tên Repository Nộp Bài:** `K4-L3-DAY10-phoboi-DataPipeline`
- **Repository:** `https://github.com/huytd2109/K4-L3-DAY10-phoboi-DataPipeline`

## Thành viên

| STT | Họ và tên | MSSV | Vai trò & Phân công công việc | Báo cáo cá nhân |
|---:|---|---|---|---|
| 1 | Đỗ Quốc An | 2A202602892 | Source owner: `crossref.py`, raw response, raw records và data lineage | `report/2A202602892_DoQuocAn.md` |
| 2 | Trịnh Đức Huy | 2A202602865 | Cleaning & test-set owner: `cleaning.py`, `testset.py`, clean schema và benchmark 10 câu | `report/2A202602865_TrinhDucHuy.md` |
| 3 | Trịnh Hoàng Tùng | 2A202602937 | Observability & reporting owner: `quality.py`, `reporting.py`, GX 1.x và Freshness SLA | `report/2A202602937_TrinhHoangTung.md` |
| 4 | Nguyễn Việt Dũng | 2A202602533 | Corruption & repair owner: `corruption.py`, corrupted/repaired datasets và corruption log | `report/2A202602533_NguyenVietDung.md` |
| 5 | Nguyễn Hoàng Sơn | 2A202602457 | Pipeline integration & evidence owner: `phase1.py`, `corruption_flow.py`, ChromaDB, metrics và kiểm chứng end-to-end | `report/2A202602457_NguyenHoangSon.md` |

## Tự khai đóng góp cá nhân

### Đỗ Quốc An — 2A202602892

- **Vai trò:** Source owner.
- **Phần việc:** Parse Crossref payload, loại JATS/XML, chuẩn hóa DOI/tác giả/ngày, retry API và fallback snapshot offline.
- **Đầu ra:** `data/raw/crossref_response.json`, `data/raw/crossref_records.json` gồm 24 bản ghi.
- **Cách xác minh:** Kiểm tra raw artifacts và chạy lệnh ingestion trong `docs/CHECKPOINTS.md`.

### Trịnh Đức Huy — 2A202602865

- **Vai trò:** Cleaning & test-set owner.
- **Phần việc:** Chuẩn hóa clean schema, tính `age_days`, tạo `text_for_embedding`, khử trùng lặp và xây dựng benchmark 10 câu thuộc bốn loại bắt buộc.
- **Đầu ra:** `data/clean/papers_clean.csv`, `data/clean/papers_clean.json`, `data/eval/test_set.json`.
- **Cách xác minh:** Clean data có 24 DOI duy nhất; test set có 10 câu thuộc `summary`, `authors`, `date`, `categories`.

### Trịnh Hoàng Tùng — 2A202602937

- **Vai trò:** Observability & reporting owner.
- **Phần việc:** Xây dựng sáu GX validations, Freshness SLA và báo cáo Markdown từ artifacts thực tế.
- **Đầu ra:** Các JSON trong `data/quality/` và hai báo cáo trong `data/reports/`.
- **Cách xác minh:** Quality/Freshness thể hiện chuỗi Pass → Fail → Pass.

### Nguyễn Việt Dũng — 2A202602533

- **Vai trò:** Corruption & repair owner.
- **Phần việc:** Triển khai sáu kịch bản corruption có tính xác định và phục hồi từ raw snapshot.
- **Đầu ra:** Corrupted/repaired datasets và `data/results/corruption_log.json`.
- **Cách xác minh:** Corruption log có đủ sáu scenario; clean và repaired dataset giống nhau.

### Nguyễn Hoàng Sơn — 2A202602457

- **Vai trò:** Pipeline integration & evidence owner.
- **Phần việc:** Điều phối baseline/corruption flow, build ba Chroma collection, chạy evaluation và kiểm tra tính nhất quán artifact.
- **Đầu ra:** Ba bộ metrics/answers, embedding manifests và báo cáo so sánh ba trạng thái.
- **Cách xác minh:** Hai entrypoint exit code 0; corrupted metrics suy giảm và repaired metrics trở lại baseline.

## Cam kết nhóm

- Mỗi thành viên chỉ nhận ownership cho phần việc được phân công ở trên.
- Mọi metric trong báo cáo phải khớp với JSON artifact được pipeline sinh ra.
- Không commit `.env`, API key, token hoặc secret.
- Mỗi thành viên chịu trách nhiệm có commit của chính mình trên nhánh mặc định `main` trước khi nộp.
