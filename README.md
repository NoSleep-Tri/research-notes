# research-notes

Ghi chú nghiên cứu dài hạn — trả lời câu hỏi bằng survey có **evidence + confidence**, rồi **thiết kế hệ thống** và **kiểm chứng bằng demo trên Kaggle**.

**Trạng thái**: 11 survey (Q-001 → Q-011) · 189 entity / 231 relation knowledge graph · 2 hệ thống thiết kế, demo **5/5** và **3/3 PASS**.

## Chỉ mục

### Survey

| ID | Câu hỏi | File | Kết luận 1 dòng |
|---|---|---|---|
| Q-001 | Con người học thế nào? | [surveys/how-humans-learn.md](surveys/how-humans-learn.md) | 7 kỹ thuật phân tầng; practice testing + distributed practice là 2 cái "miễn phí" |
| Q-002 | Ý thức hình thành từ vô thức? | [surveys/consciousness-emergence.md](surveys/consciousness-emergence.md) | Rõ **điều kiện cần**, chưa ai giải **điều kiện đủ** |
| Q-003 | Não biết phải làm gì để sống? | [surveys/survival-knowledge.md](surveys/survival-knowledge.md) | **4 lớp**, phần lớn vô thức; dopamine = RPE |
| Q-004 | Sao não biết sợ? | [surveys/how-brain-knows-fear.md](surveys/how-brain-knows-fear.md) | **3 hệ cảnh báo độc lập** |
| Q-005 | Cách hình thành phản xạ? | [surveys/reflex-formation.md](surveys/reflex-formation.md) | Phản xạ được lắp ráp, bị gỡ, luôn bị gating |
| Q-006 | ML 2026 ở đâu? | [surveys/state-of-ml-2026.md](surveys/state-of-ml-2026.md) | Post-train + test-time compute; **evaluation yếu nhất** |
| Q-007 | Bộ nhớ hình thành & quên? | [surveys/memory-consolidation-forgetting.md](surveys/memory-consolidation-forgetting.md) | Củng cố 2 pha + replay; ML vẫn chưa giải xong |
| Q-008 | Tạo bộ não không khuyết điểm? | [surveys/brain-without-flaws.md](surveys/brain-without-flaws.md) | **No-free-lunch**: lỗi gắn với tính năng |
| Q-009 | Vì sao cả não và AI hack được reward? | [surveys/reward-hacking.md](surveys/reward-hacking.md) | 3 case cùng một cấu trúc; chỉ hằng số mới unhackable |
| Q-010 | Attention — não ↔ Transformer | [surveys/attention-brain-vs-transformer.md](surveys/attention-brain-vs-transformer.md) | Chỉ cùng tên; nhưng **cùng hình dạng lỗi**: U-curve |
| Q-011 | Quên có chủ đích? | [surveys/deliberate-forgetting.md](surveys/deliberate-forgetting.md) | 4 nghĩa; não **ức chế chứ không xóa** |

### Tổng hợp & thiết kế

- [SYNTHESIS.md](SYNTHESIS.md) — 11 survey → 5 chủ đề xuyên suốt + ma trận liên thông
- [design/SAGE-spec.md](design/SAGE-spec.md) — **SAGE**: 6 lớp L0–L5, 8 nguyên tắc P1–P8, demo **5/5 PASS** (DS-001) + **3/3 PASS** (DS-002 D6–D8)
- [backlog.md](backlog.md) · [questions/](questions/) · [templates/](templates/)

### Demo (Kaggle, CPU, pre-registered acceptance)

| Design | Kernel | KPI |
|---|---|---|
| DS-001 | `tribu1/sage-v0-1-demo-ds-001` | **5/5 PASS** — replay +38.7pp · gating 18× · Goodhart · 2-tier −33.4% · scaffold +5.7pp |
| DS-002 | `tribu1/sage-v0-2-demo-ds-002` | **3/3 PASS** — U-gap 0.838 · quên đều phá trục 100× · replay giữ 0.839 vs naive 0.431 |

Code: [design/demo/sage_demo.py](design/demo/sage_demo.py), [design/demo/sage_demo2.py](design/demo/sage_demo2.py).
Mọi thay đổi ngưỡng acceptance đều ghi ở **change-log** trong spec — không sửa ngưỡng để chạm KPI.
