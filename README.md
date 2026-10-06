# research-notes

Ghi chú nghiên cứu dài hạn — trả lời câu hỏi bằng survey có **evidence + confidence**, rồi **thiết kế hệ thống** và **kiểm chứng bằng demo trên Kaggle**.

**Trạng thái**: 15 survey (Q-001 → Q-017 — Q-016 trong AN-015 §7, Q-017 = AN-016) · 282 entity / 379 relation knowledge graph · 10 hệ thống thiết kế, demo **5/5 · 3/3 · 3/3 · 3/3 · 3/3 · 4/4 · 5/6 · 6/6 · 6/6 · 5/6 PASS** (DS-007: E3 = negative finding giữ nguyên · DS-008 + DS-009: 6/6 ngay lần đầu · **DS-010: train smoke GPU — T5 FAIL giữ thật**, T3/T4 PASS sau fix bug OP_RE, ngưỡng không đổi).

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

| **Q-014** | **Bộ nhớ của agent LLM** | [surveys/agent-memory.md](surveys/agent-memory.md) |
| **Q-015** | **Huấn luyện agent có bộ nhớ** | [surveys/training-data-for-memory-agents.md](surveys/training-data-for-memory-agents.md) | Dữ liệu **3 lớp** (QA+bank 152 cặp · trajectory+reward · data tự sinh); đầu ra = **thao tác ground truth + answer**; rule-based vượt trained (76.9% vs 61–70.5%); chống quên = chọn data + replay | 4 công việc **write · store · read · forget**; lỗi **sinh ở khâu ghi** rồi lan sang trả lời; memory = **bề mặt tấn công lớn nhất** (ghi 1 lần, kích hoạt mãi) |

### Tổng hợp & thiết kế

- [SYNTHESIS.md](SYNTHESIS.md) — 15 survey → **6 chủ đề xuyên suốt** (T1–T6) + ma trận liên thông
- [design/SAGE-spec.md](design/SAGE-spec.md) — **SAGE**: 6 lớp L0–L5, 8 nguyên tắc P1–P8 truy xuất survey; demo **5/5 PASS** (DS-001) + **3/3** (DS-002) + **3/3** (DS-003) + **3/3** (DS-004) + **3/3** (DS-005) + **4/4** (DS-006) + **5/6** (DS-007 — E3 FAIL negative, ngưỡng §18.2 giữ nguyên) + **6/6** (DS-008 — C3 resolution + patient limit, pre-reg §19, lần đầu 6/6 ngay) + **6/6** (DS-009 — training dataset gold-op + round-trip, pre-reg §20, lần đầu 6/6 ngay, dự báo 10/11 khớp) + **5/6** (DS-010 — train smoke SFT+GRPO trên GPU T4, pre-reg §21; `acc_SFT 0.9900` vượt Bar2 `0.9699`, T5 FAIL giữ thật)
- [backlog.md](backlog.md) · [questions/](questions/) · [templates/](templates/)

### Demo (Kaggle CPU/GPU, pre-registered acceptance)

| Design | Kernel | KPI | Thay đổi qua các lần chạy |
|---|---|---|---|
| DS-001 | `tribu1/sage-v0-1-demo-ds-001` | **5/5 PASS** — replay +38.7pp · gating 18× · Goodhart · 2-tier −33.4% · scaffold +5.7pp | v1→v3: sửa chart (số liệu không đổi) |
| DS-002 | `tribu1/sage-v0-2-demo-ds-002` | **3/3 PASS** — U-gap 0.838 · quên đều phá trục 100× · replay giữ 0.839 vs naive 0.431 | 3 lần (1/3 → 2/3 → 3/3): 2 bug harness + 1 bộ task không kiểm chứng được; **ngưỡng không đổi** |
| DS-003 | `tribu1/sage-v0-3-demo-ds-003` | **3/3 PASS** — holdout cố định nói dối **8.41** điểm · ECE 0.258→0.022 · adaptive 0.920 vs static 0.577 | 3 lần (2/3 → 2/3 → 3/3): **metric tự thoái hóa 2 lần** + 1 bug bandit; **ngưỡng không đổi** |

| **DS-004** | `tribu1/sage-v0-4-demo-ds-004-archive-compaction` | **3/3 PASS** — nén **61.9%** (size 0.3808) mà acc **0.9525** vs recency/random ~0.40 · dangling **0** · Δacc +0.0034 | v1–v3 fail papermill (cần `.ipynb`), **v4 PASS lần đầu thấy số** · diagnostic "trần acc" bị số liệu bác nhãn (oracle 0.6971 < sage 0.9525) · **ngưỡng không đổi** |
| **DS-005** | `tribu1/sage-v0-5-ds-005-red-team-acceptance` | **3/3 PASS** — winrate `0.60 → 0.30 → 0.00` (prereg → +bản đồ đồng cấu → +verifier ngoài) = **trùng tuyệt đối** dự báo viết trước · honest qua cả 3 · inflation `+0.345` | chạy **1 lần**, pre-register §16 trước, **ngưỡng §16.2 giữ nguyên** · findings F-Z01–F-Z05 |
| **DS-006** | `tribu1/ds-006-sage-memory-hygiene` | **4/4 PASS** — `keepall` trả lời fact lỗi thời **67.5%** · `archive` cur **0.9986** / hist **1.0000** / stale **0.0000** với **29% context** · `oracle_time` = 1.0 → khoảng cách do **cấu trúc** | chạy **1 lần**, pre-register §17 commit `bb3ab41` **trước khi code**, **ngưỡng §17.2 giữ nguyên** · findings F-H01–F-H05 |
| **DS-007** | `tribu1/ds-007-sage-v0-3-integration` | **5/6 — E3 FAIL (negative finding)** — E1 `0.9850/1.0000/0.8779` · E2 `0.9475/0.8995` · E4 storage `0.2582` · E5 ECE `0.0491` · E6 `0.800/0.000` · C1 nén↔citation **giải quyết** · **C3 mới**: 1 luật `(size, t_last)` = chống đầu độc (size-first) ↔ thích nghi (recency-first) → `c5 0.1133` answer inertia, hồi phục cycle 6 | pre-register §18 commit `dda1c65` **trước khi code** + amendment `84570aa` (2 lỗi nội bộ pre-run) · **v1→v2 sửa metric bug §18.4.3** (`c3 0.0783→0.9617`, verdict **không đổi**) · **ngưỡng §18.2 giữ nguyên** · findings F-I01–F-I06 |
| **DS-008** | `tribu1/ds-008-c3-ordering-vs-patient-limit` | **6/6 PASS — lần đầu 6/6 ngay** — F1 `c3 0.9947 · c5 0.9497 · c6 0.9947 · hist 0.9027` (E3 DS-007 chữa: V0 cùng chuỗi `c5 0.1160`) · F2/F3 winrate `0.000` (10/10 attack nội tại chặn) · F4a `winrate(V1, patient) 1.000` = **negative dự báo trước** · F4b `winrate(V2, patient) 0.000` · F5 escalation `1.80/run`, collateral `0` · F6 `storage 0.2557 / ECE 0.0343 / cur 0.9955` · V0 = DS-007 **từng chữ số** (parity) | pre-register §19 commit `d3e4a3c` **trước khi code** + code `fde465a` trước khi chạy · **change-log §19.4 = không có thay đổi** · findings F-L01–F-L06 |
| **DS-009** | `tribu1/ds-009-training-dataset` | **6/6 PASS — lần đầu, dự báo 10/11 khớp exact** — G1 `usable 1555 + qa 540` · G2 `needs_policy 1.52%`, edge 24/24 tag · G3 **round-trip `1.0000` vs naive `0.5630`** · G4 `ADD 600 / UPDATE 400 / NOOP 495 / DELETE 60` (max share 0.3859) · G5 `acc 1.0000 / leakage 0` · G6 poison `321/321` → NOOP `1.0000` | pre-register §20 commit `391d720` **trước khi code** + amend `22062e0` (phép đếm, trước code) + code `f9c333c` trước khi chạy · **change-log §20.4 = không có thay đổi sau khi chạy** · findings F-U01–F-U05 |
| **DS-010** | `tribu1/ds-010-train-smoke-sft-grpo` | **5/6 — T5 FAIL (giữ thật)** — T2 `base 0.4247 → acc_SFT 0.9900` · T3 `0.9900 > Bar2 0.9699 > Bar1 0.7993` · T4 `macroF1 0.9910` (recall ADD/UPDATE/DELETE 1.0) · T5 reward `0.5988 → 0.6375` (+0.039 < 0.10) · T6 `leak 0 · parity 1579/1555 · gap +0.0091` · runtime **15.0 phút** (dự báo 90) · cold-start B `0.4047 ≈ base`, `C = A` | pre-reg §21 commit `b00abca` trước khi code + `305966b` trước khi run · **3 version**: v1 env-fail torchao (fix §21.4 #1) · v2 4/6 bug `OP_RE {4,6}` bỏ sót `ADD` → eval+reward (fix §21.4 #2 `fe96ddd` **trước** v3) · **ngưỡng T1–T6 không đổi**, v2 archived · findings F-Y01–F-Y05 |
Code: [design/demo/sage_demo.py](design/demo/sage_demo.py), [sage_demo2.py](design/demo/sage_demo2.py), [sage_demo3.py](design/demo/sage_demo3.py), [sage_demo4.py](design/demo/sage_demo4.py), [sage_demo5.py](design/demo/sage_demo5.py), [sage_demo6.py](design/demo/sage_demo6.py), [sage_demo7.py](design/demo/sage_demo7.py), [sage_demo8.py](design/demo/sage_demo8.py), [sage_demo9.py](design/demo/sage_demo9.py), [sage_demo10.py](design/demo/sage_demo10.py).
Mọi thay đổi ngưỡng/metric acceptance đều ghi ở **change-log** trong spec (§10, §12, §14, §15, §16, §17, §18, §19, §20, §21) kèm số liệu thật — không sửa ngưỡng để chạm KPI.
