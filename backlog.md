# Backlog — câu hỏi chờ xử lý

| ID | Câu hỏi | Ưu tiên | Trạng thái |
|---|---|---|---|
| Q-001 | Con người học như thế nào? | Cao | ✅ Trả lời → [AN-001](surveys/how-humans-learn.md) |
| Q-002 | Ý thức hình thành từ vô thức như thế nào? | Cao | ✅ Trả lời bước đầu → [AN-002](surveys/consciousness-emergence.md) |
| Q-003 | Hệ thần kinh *biết* phải làm gì để sống như thế nào? | Cao | ✅ Trả lời bước đầu → [AN-003](surveys/survival-knowledge.md) |
| Q-004 | Sao não biết sợ? | Cao | ✅ Trả lời bước đầu → [AN-004](surveys/how-brain-knows-fear.md) |
| Q-005 | Cách hình thành phản xạ | Cao | ✅ Trả lời bước đầu → [AN-005](surveys/reflex-formation.md) |
| Q-006 | ML hiện nay (2026) đang ở đâu? | Cao | ✅ Trả lời bước đầu → [AN-006](surveys/state-of-ml-2026.md) |
| Q-007 | Bộ nhớ hình thành, củng cố & quên (Ebbinghaus → continual learning) | Cao | ✅ Trả lời bước đầu → [AN-007](surveys/memory-consolidation-forgetting.md) |
| Q-008 | Tạo ra bộ não nhưng loại bỏ hết khuyết điểm | Cao | ✅ Trả lời bước đầu → [AN-008](surveys/brain-without-flaws.md) |
| Q-009 | Vì sao cả não và AI đều hack được reward? | TB | ✅ Trả lời bước đầu → [AN-009](surveys/reward-hacking.md) |
| Q-010 | Attention — van chọn lọc của não và của Transformer | TB | ✅ Trả lời bước đầu → [AN-010](surveys/attention-brain-vs-transformer.md) |
| Q-011 | Quên có chủ đích: khi nào nên quên? | TB | ✅ Trả lời bước đầu → [AN-011](surveys/deliberate-forgetting.md) |
| Q-012 | **Ngủ & củng cố trí nhớ** — ngủ làm gì với ký ức, và ML mô phỏng được gì? | Cao (bạn chọn) | ✅ Trả lời → [AN-012](surveys/sleep-consolidation.md) |
| Q-013 | Một hệ thống **tự chứng minh mình không bị hack** được không? (hệ quả từ F-G01) | TB (tôi chọn) | ✅ Trả lời → [AN-013](surveys/self-verification.md) |
| DS-004 | **SAGE v0.2** — *archive/compaction*: nén lịch sử thành scaffold tái sử dụng | TB | ⬜ Chờ thiết kế acceptance (roadmap §11) |
| DS-005 | **SAGE v0.2** — *red-team acceptance*: tự hack lấy KPI của chính mình (đối chứng 3 lớp: prereg · bất biến · verifier ngoài) | Thấp | ⬜ Đề xuất từ AN-013 §6, chờ duyệt chạy |

> Quy tắc: 1 câu hỏi = 1 tiêu chí "đã trả lời" rõ ràng. Giữ backlog ≤ 10 mục.

## Thiết kế hệ thống

| ID | Tên | Trạng thái |
|---|---|---|
| DS-001 | **SAGE** — "bộ não biết mình dở ở đâu": spec 6 lớp + prototype 5 module | ✅ **Demo 5/5 PASS** (Kaggle v3, 2026-10-06) → [SAGE-spec](design/SAGE-spec.md) · [sage_demo.py](design/demo/sage_demo.py) · [kpi.txt](design/demo/out/kpi.txt) |
| DS-002 | **SAGE v0.2** — mở rộng D6–D8: U-curve · directional forgetting · replay+plasticity | ✅ **Demo 3/3 PASS** (Kaggle v5, 2026-10-06, qua 3 lần) → [spec §12](design/SAGE-spec.md) · [sage_demo2.py](design/demo/sage_demo2.py) · [kpi.txt](design/demo/out/ds002/kpi.txt) |
| DS-003 | **SAGE v0.2** — 3 công cụ tự kỷ luật: wirehead guard · confidence calibration · adaptive registry | ✅ **Demo 3/3 PASS** (Kaggle v3, 2026-10-06, qua 3 lần) → [spec §14](design/SAGE-spec.md) · [sage_demo3.py](design/demo/sage_demo3.py) · [kpi.txt](design/demo/out/ds003/kpi.txt) |

> **Bài học từ DS-003 (3 lần, 2 metric bị khai tử)**: cả 3 lần sửa đều là **metric/harness thoái hóa**, không lần nào hạ ngưỡng. `gating_acc` bị thắng bằng cách *không quyết định gì* (coverage=0) · hợp đồng `0.90` bị vô hiệu bằng cách *nằm ngoài vùng dữ liệu* · bandit "không học" vì *không chịu thử*. **Goodhart ngay trên cái thước đo của mình** — đúng F-R01.

> **Kết quả âm của DS-002 (không che)**: *loss of plasticity* **không quan sát được** ở scale toy — 3 lần chạy, mọi arm học task mới đều đạt `plasticity_ratio ≈ 1.0`. F-X03 chỉ được xác nhận ở nhánh retention.
