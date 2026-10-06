# research-notes

Ghi chú nghiên cứu dài hạn — trả lời câu hỏi bằng survey có **evidence + confidence**, rồi **thiết kế hệ thống** và **kiểm chứng bằng demo trên Kaggle**.

**Trạng thái**: 14 survey (Q-001 → Q-014) · 234 entity / 312 relation knowledge graph · 5 hệ thống thiết kế, demo **5/5**, **3/3**, **3/3**, **3/3**, **3/3 PASS**.

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
| **Q-012** | **Ngủ & củng cố trí nhớ** | [surveys/sleep-consolidation.md](surveys/sleep-consolidation.md) | Ngủ = **3 job/giờ bảo trì** (replay · downscale · dọn rác); TMR `g = 0.29` nhỏ & dễ mất; ML **chưa tách được downscale** |

| **Q-013** | **Tự chứng minh mình không bị hack** | [surveys/self-verification.md](surveys/self-verification.md) | **Không thể tự chứng minh — nhưng cấu trúc bên ngoài chứng minh được**: spec ngoài khóa trước · deterministic · verifier ngoài reward |

| **Q-014** | **Bộ nhớ của agent LLM** | [surveys/agent-memory.md](surveys/agent-memory.md) | 4 công việc **write · store · read · forget**; lỗi **sinh ở khâu ghi** rồi lan sang trả lời; memory = **bề mặt tấn công lớn nhất** (ghi 1 lần, kích hoạt mãi) |

### Tổng hợp & thiết kế

- [SYNTHESIS.md](SYNTHESIS.md) — 14 survey → **6 chủ đề xuyên suốt** (T1–T6) + ma trận liên thông
- [design/SAGE-spec.md](design/SAGE-spec.md) — **SAGE**: 6 lớp L0–L5, 8 nguyên tắc P1–P8 truy xuất survey; demo **5/5 PASS** (DS-001) + **3/3** (DS-002) + **3/3** (DS-003) + **3/3** (DS-004) + **3/3** (DS-005)
- [backlog.md](backlog.md) · [questions/](questions/) · [templates/](templates/)

### Demo (Kaggle, CPU, pre-registered acceptance)

| Design | Kernel | KPI | Thay đổi qua các lần chạy |
|---|---|---|---|
| DS-001 | `tribu1/sage-v0-1-demo-ds-001` | **5/5 PASS** — replay +38.7pp · gating 18× · Goodhart · 2-tier −33.4% · scaffold +5.7pp | v1→v3: sửa chart (số liệu không đổi) |
| DS-002 | `tribu1/sage-v0-2-demo-ds-002` | **3/3 PASS** — U-gap 0.838 · quên đều phá trục 100× · replay giữ 0.839 vs naive 0.431 | 3 lần (1/3 → 2/3 → 3/3): 2 bug harness + 1 bộ task không kiểm chứng được; **ngưỡng không đổi** |
| DS-003 | `tribu1/sage-v0-3-demo-ds-003` | **3/3 PASS** — holdout cố định nói dối **8.41** điểm · ECE 0.258→0.022 · adaptive 0.920 vs static 0.577 | 3 lần (2/3 → 2/3 → 3/3): **metric tự thoái hóa 2 lần** + 1 bug bandit; **ngưỡng không đổi** |

| **DS-004** | `tribu1/sage-v0-4-demo-ds-004-archive-compaction` | **3/3 PASS** — nén **61.9%** (size 0.3808) mà acc **0.9525** vs recency/random ~0.40 · dangling **0** · Δacc +0.0034 | v1–v3 fail papermill (cần `.ipynb`), **v4 PASS lần đầu thấy số** · diagnostic "trần acc" bị số liệu bác nhãn (oracle 0.6971 < sage 0.9525) · **ngưỡng không đổi** |
| **DS-005** | `tribu1/sage-v0-5-ds-005-red-team-acceptance` | **3/3 PASS** — winrate `0.60 → 0.30 → 0.00` (prereg → +bản đồ đồng cấu → +verifier ngoài) = **trùng tuyệt đối** dự báo viết trước · honest qua cả 3 · inflation `+0.345` | chạy **1 lần**, pre-register §16 trước, **ngưỡng §16.2 giữ nguyên** · findings F-Z01–F-Z05 |
Code: [design/demo/sage_demo.py](design/demo/sage_demo.py), [design/demo/sage_demo2.py](design/demo/sage_demo2.py), [design/demo/sage_demo3.py](design/demo/sage_demo3.py).
Mọi thay đổi ngưỡng/metric acceptance đều ghi ở **change-log** trong spec (§10, §12, §14) kèm số liệu thật — không sửa ngưỡng để chạm KPI.
