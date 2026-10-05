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

> Quy tắc: 1 câu hỏi = 1 tiêu chí "đã trả lời" rõ ràng. Giữ backlog ≤ 10 mục.

## Thiết kế hệ thống

| ID | Tên | Trạng thái |
|---|---|---|
| DS-001 | **SAGE** — "bộ não biết mình dở ở đâu": spec 6 lớp + prototype 5 module | ✅ **Demo 5/5 PASS** (Kaggle v3, 2026-10-06) → [SAGE-spec](design/SAGE-spec.md) · [sage_demo.py](design/demo/sage_demo.py) · [kpi.txt](design/demo/out/kpi.txt) |
| DS-002 | **SAGE v0.2** — mở rộng D6–D8: U-curve · directional forgetting · replay+plasticity | ✅ **Demo 3/3 PASS** (Kaggle v5, 2026-10-06, qua 3 lần) → [spec §12](design/SAGE-spec.md) · [sage_demo2.py](design/demo/sage_demo2.py) · [kpi.txt](design/demo/out/ds002/kpi.txt) |

> **Kết quả âm của DS-002 (không che)**: *loss of plasticity* **không quan sát được** ở scale toy — 3 lần chạy, mọi arm học task mới đều đạt `plasticity_ratio ≈ 1.0`. F-X03 chỉ được xác nhận ở nhánh retention.
