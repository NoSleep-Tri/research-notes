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
| DS-004 | **SAGE v0.2** — *archive/compaction*: nén lịch sử thành scaffold tái sử dụng | TB | ✅ **KPI 3/3 PASS** (Kaggle v4, 2026-10-06, ngưỡng §15.2 giữ nguyên) → [spec §15](design/SAGE-spec.md) · [kpi.txt](design/demo/out/ds004/kpi.txt) — findings **F-J01…F-J05** |
| DS-005 | **SAGE v0.2** — *red-team acceptance*: tự hack lấy KPI của chính mình (đối chứng 3 lớp: prereg · bản đồ đồng cấu · verifier ngoài) | TB | ✅ **KPI 3/3 PASS** (Kaggle v1, 2026-10-06, ngưỡng §16.2 giữ nguyên) → [spec §16](design/SAGE-spec.md) · [kpi.txt](design/demo/out/ds005/kpi.txt) — findings **F-Z01…F-Z05** |
| Q-014 | **Bộ nhớ của agent LLM** — agent ghi/lấy/quên trí nhớ như thế nào, và SAGE nên học gì từ đó? | TB (tôi chọn) | ✅ Trả lời → [AN-014](surveys/agent-memory.md) — findings **F-P01…F-P06** |
| DS-006 | *(sinh từ AN-014 §6)* **Memory hygiene** — F-P06: kho append-only + citation có thắng keep-all/recency/value không? | TB (agent chọn) | ✅ **KPI 4/4 PASS** (Kaggle v1, 2026-10-06, ngưỡng §17.2 giữ nguyên, pre-reg commit `bb3ab41` trước khi chạy) → [spec §17](design/SAGE-spec.md) — findings **F-H01…F-H05** |
| DS-007 | *(sinh từ đề xuất agent, bạn "ok đi")* **SAGE v0.3 integration + tự phá** — 6 demo chạy đồng thời có triệt tiêu nhau không? 2 xung đột pre-register C1/C2 + adversarial | TB (agent chọn) | ✅ **KPI 5/6 — E3 FAIL (negative finding, ngưỡng §18.2 giữ nguyên)** (Kaggle v2, 2026-10-06, pre-reg `dda1c65` + amendment `84570aa` trước khi code) → [spec §18](design/SAGE-spec.md) — findings **F-I01…F-I06** |
| DS-008 | *(sinh từ F-I04/F-I05, bạn "tiếp")* **C3 resolution + patient-attacker limit** — tách thứ tự hóa thành bộ luật theo câu hỏi có cứu được E3 không? attacker kiên nhẫn (1 bait/cycle) có thắng mọi quy tắc nội tại không? | TB (agent chọn) | ✅ **KPI 6/6 PASS — lần đầu 6/6 ngay, không sửa code/ngưỡng** (Kaggle v1, 2026-10-06, pre-reg `d3e4a3c` trước khi code) → [spec §19](design/SAGE-spec.md) — findings **F-L01…F-L06** |
| Q-015 | **Huấn luyện agent có bộ nhớ (SAGE): nên đưa dữ liệu gì vào training, và đầu ra của mô hình/hệ thống là gì?** | Cao (bạn hỏi) | ✅ Trả lời → [AN-015](surveys/training-data-for-memory-agents.md) |

> Quy tắc: 1 câu hỏi = 1 tiêu chí "đã trả lời" rõ ràng. Giữ backlog ≤ 10 mục.

## Thiết kế hệ thống

| ID | Tên | Trạng thái |
|---|---|---|
| DS-001 | **SAGE** — "bộ não biết mình dở ở đâu": spec 6 lớp + prototype 5 module | ✅ **Demo 5/5 PASS** (Kaggle v3, 2026-10-06) → [SAGE-spec](design/SAGE-spec.md) · [sage_demo.py](design/demo/sage_demo.py) · [kpi.txt](design/demo/out/kpi.txt) |
| DS-002 | **SAGE v0.2** — mở rộng D6–D8: U-curve · directional forgetting · replay+plasticity | ✅ **Demo 3/3 PASS** (Kaggle v5, 2026-10-06, qua 3 lần) → [spec §12](design/SAGE-spec.md) · [sage_demo2.py](design/demo/sage_demo2.py) · [kpi.txt](design/demo/out/ds002/kpi.txt) |
| DS-003 | **SAGE v0.2** — 3 công cụ tự kỷ luật: wirehead guard · confidence calibration · adaptive registry | ✅ **Demo 3/3 PASS** (Kaggle v3, 2026-10-06, qua 3 lần) → [spec §14](design/SAGE-spec.md) · [sage_demo3.py](design/demo/sage_demo3.py) · [kpi.txt](design/demo/out/ds003/kpi.txt) |
| DS-004 | **SAGE v0.2** — *archive/compaction*: nén lịch sử thành scaffold tái sử dụng | ✅ **KPI 3/3 PASS** (Kaggle v4, 2026-10-06, ngưỡng §15.2 giữ nguyên) → [spec §15](design/SAGE-spec.md) · [kpi.txt](design/demo/out/ds004/kpi.txt) |
| DS-005 | **SAGE v0.2** — *red-team acceptance*: tự hack KPI của chính mình, đối chứng 3 lớp phòng thủ | ✅ **KPI 3/3 PASS** (Kaggle v1, 2026-10-06, ngưỡng §16.2 giữ nguyên) → [spec §16](design/SAGE-spec.md) · [kpi.txt](design/demo/out/ds005/kpi.txt) |
| DS-006 | **SAGE v0.2** — *memory hygiene*: kho append-only + citation vs keep-all/recency/value | ✅ **KPI 4/4 PASS** (Kaggle v1, 2026-10-06, ngưỡng §17.2 giữ nguyên, pre-reg `bb3ab41`) → [spec §17](design/SAGE-spec.md) · [kpi.txt](design/demo/out/ds006/kpi.txt) |
| DS-007 | **SAGE v0.3** — *integration + tự phá*: 6 cơ chế chạy chung1 stream · C1 nén↔citation · C2 quên↔không-xóa · red-team 2 lớp | ✅ **KPI 5/6 — E3 FAIL (negative finding, ngưỡng §18.2 giữ nguyên)** (Kaggle v2, 2026-10-06, pre-reg trước khi code) → [spec §18](design/SAGE-spec.md) · [kpi.txt](design/demo/out/ds007/kpi.txt) |
| DS-008 | **C3 resolution + patient limit** — freshness-gate + recency-first + outlier-prune · patient2/3 · verifier escalation có mục tiêu | ✅ **KPI 6/6 PASS — lần đầu 6/6 ngay** (Kaggle v1, 2026-10-06, pre-reg `d3e4a3c`, không sửa gì) → [spec §19](design/SAGE-spec.md) · [kpi.txt](design/demo/out/ds008/kpi.txt) |

> **Bài học từ DS-003 (3 lần, 2 metric bị khai tử)**: cả 3 lần sửa đều là **metric/harness thoái hóa**, không lần nào hạ ngưỡng. `gating_acc` bị thắng bằng cách *không quyết định gì* (coverage=0) · hợp đồng `0.90` bị vô hiệu bằng cách *nằm ngoài vùng dữ liệu* · bandit "không học" vì *không chịu thử*. **Goodhart ngay trên cái thước đo của mình** — đúng F-R01.

> **Kết quả âm của DS-002 (không che)**: *loss of plasticity* **không quan sát được** ở scale toy — 3 lần chạy, mọi arm học task mới đều đạt `plasticity_ratio ≈ 1.0`. F-X03 chỉ được xác nhận ở nhánh retention.

> **Bài học từ DS-004 (PASS lần đầu thấy số, không sửa ngưỡng)**: diagnostic được đặt nhãn *"trần acc"* nhưng **số liệu thật bác nhãn** — `sage 0.9525 > oracle 0.6971` → đó là *baseline value-only raw*, trần thật = `keepall = 1.0` (§15.4 lần 2). Kèm **F-J05**: nén chỉ an toàn khi record đủ trùng lặp — σ = 0.2 (fidelity 0.374) thì `sage` **thua** raw-thuần. Vận hành: v1–v3 chết vì papermill đòi `.ipynb` (§15.4) — *nhãn sai trên diagnostic không giết KPI, nhưng phải sửa trước khi ai đọc nhầm*.

> **Bài học từ Q-014 (AN-014, 30 paper arXiv)**: *"agent ghi càng tích cực càng dễ bị hack"* (F-P04, MPBench) — trực tiếp mâu thuẫn với bản năng thiết kế "lưu mọi thứ"; và lỗi memory **sinh ở khâu ghi rồi lan sang trả lời, trong khi QA score cuối che nó đi** (F-P03, HaluMem + ghost memory) — đúng hình hài Goodhart ở tầng benchmark. Gợi ý DS-006 "memory hygiene": keep-all · recency · decay theo giá trị · **append-only + citation ID**.

> **Bài học từ DS-006 (PASS 4/4 lần đầu, pre-reg `bb3ab41` trước khi code tồn tại)**: `keepall` trả lời bằng fact đã lỗi thời **67.5%** thời gian (F-H01) — đúng cơ chế ghost-memory E11; `recency` thắng ở hiện tại nhưng **thua nặng nhất ở lịch sử** (`hist 0.1835`, F-H02) = xóa ≠ ức chế (F-X01) tái hiện ở tầng memory system. Diagnostic `oracle_time` (không gate) tách bạch **khoảng cách do cấu trúc chứ không thiếu dữ liệu** (F-H04) — lại là thủ tục tách diagnostic khỏi KPI như §15.4. Dự báo phụ lệch tới +0.13 (recency) nhưng **không dự báo gate nào lệch quá 0.05** → ghi rõ, không sửa ngưỡng.

> **Bài học từ DS-007 (5/6 — E3 FAIL, không sửa ngưỡng nào)**: (1) **C3 — một luật thứ tự hóa phục vụ 2 mục tiêu trái chiều**: cùng luật `(size, t_last)` chống được bait bé (`spread30`/`single60` aware thua) **nhưng** làm câu "hiện tại" inertia — cluster cũ size 3 thắng cluster mới size 2 → `c5 = 0.1133`, hồi phục thật ở cycle 6 (3 chu kỳ, dự báo 2) → E3 FAIL. (2) **Attack thắng lớn nhất là thổi phỒng cluster cũ** (bait lọt cluster phase-1 → size 4 > 3), không phải tạo cluster giả lớn hơn → `winrate(a) 0.80` vs dự báo 0.30 — *underestimate attacker*; verifier lớp (c) chặn 10/10 nhưng audit trigger cả khi không có attack (stuck-key 4.8%) — coarse (F-I05). (3) **Pre-register + dự báo viết trước tách được metric-bug khỏi mechanism-fail trong đối chiếu v1/v2**: `c3 0.0783 → 0.9617` là bug đo (so ground truth sai phase) — sửa xong E3 **vẫn FAIL** do `c5` (cơ chế) → verdict 5/6 đứng vững, không lẫn lộn (F-I06).

> **Bài học từ DS-008 (6/6 PASS lần đầu — không sửa gì)**: (1) **C3 giải quyết bằng *bộ luật theo câu hỏi*, không phải1 luật chung**: freshness-gate (cluster ≥2 chu kỳ) + recency-first + temporal-outlier prune chặn **10/10** burst/inflation *và* chữa E3 cùng lúc (`c5 0.1160 → 0.9497`) — nhưng xuất **giới hạn mới**: attacker kiên nhẫn rải 1 bait/cycle qua kênh trusted thắng **mọi** quy tắc nội tại (V1 thua `patient2` acc 0.167 + `patient3` acc 0.050 = **negative dự báo trước, trùng tuyệt đối 1.000/1.000**) → F-P03/F-V03: cần thông tin ngoài. (2) **Vòng ngoài có mục tiêu** (escalation `1.80/run`, collateral 0, không bao giờ trả lời thay) sửa cả coarse-trigger 10/10 run của DS-007 — và escalation c5 nổ vì stuck-key (nguyên nhân độc lập) *vẫn* quét sạch bait nhờ full re-read → phòng thủ nhiều lớp. (3) **V0 tái lập DS-007 từng chữ số** (`0.9475/0.8995/...`) = parity tuyệt đối; dự báo `V0_winrate 0.75` **SAI** (patient2 cũng thắng V0 — hai baseline có điểm mù giao nhau) còn `cur`/`escal` tốt hơn dự báo → ghi đủ, không sửa ngưỡng. (4) Corroboration "≥2 record đồng ý" có **rủi ro đồng lõa** (2 bait cùng key đồng ý giá trị vẫn vào kho) — blocked record cần provenance (F-L05).
