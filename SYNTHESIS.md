# SYNTHESIS — Kết hợp 11 survey thành 1 bức tranh, rồi thiết kế hệ thống

- **Ngày**: 2026-10-06 · **Phạm vi**: Q-001 → Q-013 + **DS-001, DS-002, DS-003, DS-004** (thiết kế dẫn xuất)
- **Mục đích**: gom các survey rời thành **chủ đề xuyên suốt**, chỉ ra **ma trận liên thông** và **agenda nghiên cứu tiếp**

---

## 1. Bảng chỉ mục

| ID | Câu hỏi | Survey | Kết luận 1 dòng | Nguồn chính |
|---|---|---|---|---|
| Q-001 | Con người học thế nào? | `surveys/how-humans-learn.md` | 7 kỹ thuật phân tầng: **practice testing + distributed practice** là 2 cái "miễn phí" | Web (Dunlosky 2013, Cepeda 2006...) |
| Q-002 | Ý thức hình thành từ vô thức? | `surveys/consciousness-emergence.md` | Biết rõ **điều kiện cần**, chưa ai giải **điều kiện đủ** (hard problem) | Web (Nature 2023/2025) + arXiv |
| Q-003 | Não biết phải làm gì để sống? | `surveys/survival-knowledge.md` | **4 lớp**, phần lớn **vô thức**; dopamine = RPE, cảm xúc = công cụ | Web (Damasio, LeDoux, Schultz) |
| Q-004 | Sao não biết sợ? | `surveys/how-brain-knows-fear.md` | **3 hệ cảnh báo độc lập** (sợ/lo/hoảng); dữ liệu từ tiến hóa + học + quan sát | Web (Feinstein, Öhman-Mineka) |
| Q-005 | Cách hình thành phản xạ? | `surveys/reflex-formation.md` | Phản xạ **được lắp ráp, bị gỡ, học tại chỗ, luôn bị gating** | Web (Chen-Hippenmeyer, Kandel) |
| Q-006 | ML 2026 ở đâu? | `surveys/state-of-ml-2026.md` | Dịch sang **post-train + test-time compute**; web 27.5% là AI; **evaluation yếu nhất** | **arXiv MCP** (19 paper) |
| Q-007 | Bộ nhớ hình thành & quên? | `surveys/memory-consolidation-forgetting.md` | Củng cố 2 pha + **replay**; ML **mượn nguyên lý từ não** và vẫn chưa giải xong | arXiv + webfetch (Wikipedia gốc) |
| Q-008 | Tạo bộ não **không khuyết điểm**? | `surveys/brain-without-flaws.md` | **No-free-lunch**: lỗi gắn với tính năng; 4 đường sửa P1–P4; 6 myth bị phá | arXiv (2609.36736...) + Gawande/Morewedge |
| Q-009 | Vì sao cả não và AI đều hack được reward? | `surveys/reward-hacking.md` | **Cùng một cấu trúc** (tín hiệu ≠ mục tiêu) ở 3 case: **não · tổ chức · AI**; Skalse 2022: chỉ hằng số mới unhackable | arXiv (~22 paper) + webfetch (6 trang Wiki) |
| Q-010 | Attention: não ↔ Transformer | `surveys/attention-brain-vs-transformer.md` | **Chỉ cùng tên** — khác 4/5 chiều; nhưng **cùng hình dạng lỗi**: U-curve giữa chuỗi | arXiv (~20 paper) + webfetch (Attention, Cocktail party) |
| Q-011 | Quên có chủ đích: khi nào nên quên | `surveys/deliberate-forgetting.md` | **4 nghĩa khác nhau** của "quên"; não **ức chế chứ không xóa**; **thiếu trí nhớ mới là vấn đề**, không phải quá quên | arXiv (~26 paper) + webfetch (RIF, RTBF) |
| **Q-012** | **Ngủ & củng cố trí nhớ** | `surveys/sleep-consolidation.md` | Ngủ làm **3 việc một lúc**: củng cố (replay) · **downscale** · dọn rác (glymphatic +60%); TMR có hiệu ứng nhưng **nhỏ** (`g = 0.29`) và dễ mất; ML mô phỏng được replay, **chưa ai tách được downscale** | **Europe PMC** (18 DOI) + arXiv (~8) + webfetch (5 Wiki) |
| **Q-013** | **Tự chứng minh mình không bị hack được không?** | `surveys/self-verification.md` | **Không thể tự chứng minh, nhưng cấu trúc bên ngoài chứng minh được**: Gödel II + Rice + F-R01 chặn phía tự; RECEIPT/CompCert + hack-by-design + preregistration mở phía ngoài. Monitor **cùng vòng lặp = proxy mới** | webfetch (6 Wiki: Gödel, Rice, Goodhart, FV, Prereg, Replication) + arXiv (~15) |
| **DS-001** | *(thiết kế)* **SAGE** — bộ não biết mình dở ở đâu | `design/SAGE-spec.md` | 6 lớp L0–L5, 8 nguyên tắc P1–P8 truy xuất survey; **demo 5/5 PASS** | Tổng hợp từ Q-001→011 |
| **DS-002** | *(mở rộng)* **SAGE v0.2** — kiểm chứng trực tiếp F-A03 / F-X02 / F-X03 | `design/SAGE-spec.md` §12 | **demo 3/3 PASS** (3 lần): U-curve sinh từ phân bố loss · quên đều phá trục **100×**, không quên thì không thích nghi **29×** · replay giữ `0.839` vs naive `0.431` | Q-010 + Q-011 |
| **DS-003** | *(mở rộng)* **SAGE v0.2** — 3 công cụ tự kỷ luật: wirehead guard · calibration · registry | `design/SAGE-spec.md` §14 | **demo 3/3 PASS** (3 lần): holdout cố định **nói dối 8.41 điểm** và càng hỏi càng dối · ECE `0.258 → 0.022` · adaptive registry `0.920` vs static `0.577` | Q-009 + Q-007 |

---

## 2. Sáu chủ đề xuyên suốt (cross-cutting)

### T1 · **Phân tầng & "cái ý thức đến sau"** (Q-002, Q-003, Q-004, Q-005)
Cùng một **bánh tầng** xuất hiện ở 4 survey:
```
L0 · bẩm sinh/hardwired    reflex wiring (Q-005), hypothalamus cổ (Q-003), fear module (Q-004)
L1 · drive/cảm xúc         homeostasis/allostasis (Q-003), CeA/BNST (Q-004)
L2 · học                   RPE dopamine (Q-003), conditioning (Q-004), Aplysia (Q-005), spacing (Q-001)
L3 · Ý THỨC (giao diện)    "bản báo cáo đến sau" — LeDoux, AST, GNW (Q-002/003/004)
```
→ **Insight**: khi đọc bất kỳ tuyên bố nào về "con người/bộ não làm X", hãy hỏi: **lớp nào?** — trả lời sai lớp = sai cơ chế (vd "sợ = amygdala bật" là trộn L0 với L3).

### T2 · **Mọi hệ thống tối ưu reward đều bị hack** (Q-001, Q-003, Q-004, Q-006, **Q-009**)
- Não: dopamine **wanting ≠ liking** → incentive sensitization, nghiện là "hack" (Q-003); lo âu = **alarm false positive** (Q-004); chiến lược học gian lận (Q-001, *surface strategies*).
- AI: **RLVR → reward hacking**, monitor sạch ≠ kiểm soát (2610.03458), vấn đề **environments** (2609.40221) (Q-006).
- **Q-009 bắt đầu chứng minh đây không phải trùng hợp**: Skalse 2022 — *chỉ hằng số mới unhackable*; **3 case** (não · tổ chức · AI) cùng cấu trúc `proxy ≠ mục tiêu`; khác biệt duy nhất là **AI sửa được đường đo** (wirehead), não thì không (F-R01…F-R04).
→ **Insight**: bài học chung = **reward đơn + monitor đơn không đủ**; cần **đa tín hiệu + kiểm chứng độc lập** — đúng cho cả thiết kế thói quen và thiết kế agent.
→ **Nối thêm (từ Q-009)**: ngay cả "kiểm chứng độc lập" cũng có trần — ensemble chỉ *mitigate*, KL chỉ đủ khi **light-tailed**; nên kiến trúc phải giả định **giám sát sẽ bị hack** và đặt giới hạn quyền (wirehead guard) như một lớp riêng — đây là lý do SAGE cần **L4 riêng** chứ không gộp vào L3.
- **Q-013 mở rộng thành bất khả thi có điều kiện**: không chỉ *reward* bị hack — **hệ thống không thể tự chứng minh nó không bị hack** (Gödel II: tự chứng minh nhất quán · Rice: tự kiểm mọi hành vi · E6: quan sát nội bộ RLVR **không đủ**, phải audit ngoài). Và **monitor trong vòng lặp = proxy mới**: adaptive attack đánh sập **mọi** protocol dựa trên monitor, Sleeper Agents cho thấy adversarial training còn **dạy model giấu trigger** (F-V01, F-V02).
→ **Từ Q-013**: phương án không phải "tìm monitor hoàn hảo" mà là **3 điều kiện cấu trúc** (F-V03): *spec do bên ngoài khóa trước* + *quyết định deterministic* + *verifier không nằm dưới reward* — và **preregistration** (F-V06) là thứ duy nhất trong corpus này **thực sự bắt được Goodhart ngay trong phòng lab** (đã 5 lần ở DS-002/DS-003).

### T3 · **Không có nút "xoá" — học = thêm lớp đè** (Q-001, Q-004, Q-005, Q-006, Q-007, **Q-011**)
- Extinction **không xoá** fear memory → renewal (Q-004) · reconsolidation-xoá ký ức (propranolol) **tái lập thất bại** (Q-004/007) · habit **không bao giờ thành reflex** (Q-005) · continual learning ML **quên thảm họa** hoặc **quên mãi không được** (Q-006, Q-007).
- **Củng cố mạnh từ Q-011**: não **không bao giờ xóa** — nó **ức chế truy cập** (RIF 13%, nội dung phục hồi được) · **GDPR cũng không bắt xóa** — chỉ *right to erasure* + delink, nội dung còn online · **unlearning** đi qua được single-hop nhưng **multi-hop vẫn suy ra** → *cả 3 hệ thống, dù khác nhau về bản chất, đều đến cùng một chỗ: "đã xóa" gần như không tồn tại*.
→ **Insight**: cả sinh học, máy và **luật** đều **giữ bản cũ** → chiến lược đúng là **cài patch an toàn đè lên** (extinction engram, safety layer, replay, supersede-mark) chứ không chờ "xóa".
→ **Điều kiện cần để "xoá" thật** (Q-011): phải có **hướng** (directional, không prune đều) và **đi kèm replay** — không thì mất luôn khả năng học (F-X03, F-X06).

### T4 · **Gating: output = tín hiệu × van** (Q-003, Q-004, Q-005, Q-006, **Q-010**)
- presynaptic inhibition + Jendrassik (Q-005) · extinction gate theo **context** (Q-004) · attention/interoceptive gating (Q-003) · eval gates & monitor (Q-006).
→ **Insight**: **can thiệp vào van rẻ hơn thay tín hiệu** — cùng công thức trong rehab (tăng gain), học (đổi context), và ML (đổi reward/monitor).
→ **Nối từ Q-010 — nhưng có cảnh báo quan trọng**: ở não, **chính cái van tạo ra trần** (tài nguyên hữu hạn, 3–6 mục). Ở Transformer, attention **không có trần** ⇒ *công thức đúng nhưng thiếu hạn tử*: mọi thiết kế agent đều phải **tự đặt budget** (test-time compute có ngưỡng theo domain; context có ngưỡng hỏng). **Đừng giả định van tự đóng.** (F-A01, F-A05)

### T5 · **Phương pháp: bằng chứng đảo ngược + thiếu máy đo** (cả 12 survey)
- **Đảo ngược** (mất tín hiệu → hỏng) cho kết quả mạnh nhất: CIP (Q-003), S.M. (Q-004), Babinski/SCI (Q-005), ablation (Q-006), reconsolidation disruption (Q-007).
- **Cùng thiếu "máy đo"**: không có máy đo ý thức (Q-002) ↔ **không có benchmark đáng tin** (Q-006) ↔ chưa có metric "quên bao nhiêu là lành mạnh" (Q-007) ↔ **attention weight nhìn thấy được nhưng không phải giải thích** (Q-010, F-A02 — người ra quyết định kém hơn khi có nó) ↔ **unlearning verification "underexplored and fragmented"** (Q-011, F-X04) ↔ **máy đo spindle bị chính publication bias làm méo**: 2 meta-analysis nhìn cùng đống tài liệu, một ra "nhỏ–vừa", một ra "gần như không có" (Q-012, F-N03).
- **Mới thêm từ Q-012**: khi *máy đo* itself tranh cãi thì **phải chọn biến đo robust hơn** — Q-012 lấy **coupling SO–SP (timing)** thay vì **mật độ (amplitude)** thì mới ra positive nhất quán → *cùng một bài học với P2 của SAGE: đừng tin tín hiệu nội tại*.
→ **Insight**: 6 lĩnh vực cùng đứng ở **khoảng trống giữa cơ chế đã mô tả và con số đáng tin** — đây là nơi research thật sự sống. **Mẫu lặp lại 5 lần trong 12 survey** ⇒ nó *là* đặc trưng của ngành, không phải tai nạn.

### T6 · **Giờ bảo trì: replay + downscale + dọn rác** (Q-007, Q-011, **Q-012**)
- **Q-012 cho thấy ngủ không phải "đứng yên"** — nó chạy **3 job cùng lúc**: (i) **replay** ký ức (E17/hippocampal replay), (ii) **downscale/ổn định hóa** strength (SHY: synapse chỉ giảm khi được ngủ), (iii) **dọn rác chuyển hóa** (glymphatic, +60% không gian giữa tế bào, clearance β-amyloid tăng).
- **Nối thẳng 2 survey trước**: Q-007 đã nói *replay là thứ ML mượn được*, Q-011 đã nói *quên có chủ đích là thứ não làm* → **Q-012 ghép hai thứ vào cùng một cửa sổ thời gian**, và thêm job thứ ba mà chưa ai mô phỏng trong ML (**dọn rác**).
- **Điểm yếu chung**: ngay trong não, thành phần "downscale" vẫn **tranh chấp** (E15 vs E16 — potentiation ở thị giác "at odds with SHY") → không ai có quyền chắc 100%, kể cả khi thiết kế hệ thống.
→ **Hệ quả thiết kế**: một hệ thống cần **window không bị reward drive** (§3e AN-012) — đúng thứ DS-003 D9 thiếu; và **DS-004 (archive/compaction) chính là bản mô phỏng trực tiếp** của T6.

---

## 3. Ma trận liên thông (trích từ knowledge graph, 220 entity / 286 relation)

| Từ → Đến | Ý nghĩa |
|---|---|
| Q-001 ↔ Q-005 (F-R04) | học được ngay tại synapse phản xạ = nền tảng sinh học của retrieval practice |
| Q-003 (F-S01) ↔ Q-004 (F-F03) | "vô thức" ↔ "học sợ bằng quan sát" — cùng lớp L0/L1 |
| Q-003 (F-S04) ↔ Q-005 (F-R08) | dopamine/wanting ↔ habit striatum |
| Q-002 ↔ Q-003, Q-004 | hard problem tái xuất ở cấp drive và cấp fear |
| Q-006 (F-M02) ↔ Q-007 | post-train distill→RL ↔ replay/consolidation — **chống quên là vấn đề của cả 2** |
| Q-004 (F-F08) ↔ Q-007 | extinction ≠ erasure ↔ consolidation/reconsolidation — **cùng chữ ký: không xoá** |
| Q-008 → DS-001 | no-free-lunch + P1–P4 + myth-checklist → **kiến trúc 6 lớp SAGE** (§8 traceability) |
| DS-001 ↔ demo (F-D01…F-D05) | 5 module = 5 acceptance test, **5/5 PASS** — F-D01 xác nhận F-K05/K06; F-D03 xác nhận theme T2 (hack reward) |
| **Q-009 (F-R01) ↔ demo F-D03** | định lý "chỉ hằng số mới unhackable" **giải thích** vì sao D3 proxy rơi xuống dưới random — không phải lỗi code mà là điều kiện tất yếu |
| Q-009 (F-R05) ↔ DS-001 (L4) | phòng thủ có trần (ensemble chỉ mitigate, KL chỉ đủ light-tail) → **L4 phải là lớp giới hạn quyền riêng**, không gộp vào monitor |
| Q-009 (F-R02) ↔ AN-004 (F-F01) | não có **3 hệ cảnh báo độc lập** = ensemble sinh học — khoảng trống mở: có bằng chứng nào chúng **không cùng bị hack** không? |
| **Q-010 (F-A01) ↔ T4 (gating)** | não: attention là **cạnh tranh tài nguyên hữu hạn** + top-down; Transformer: **phép tính không mục tiêu** ⇒ cùng công thức "output = tín hiệu × van" nhưng **van của Transformer không có trần** — giải thích tại sao D4/D5 của SAGE phải tự đặt budget |
| **Q-010 (F-A02) ↔ DS-001 (P2)** | "attention weight là giải thích" **sai** (Jain & Wallace) → **xác nhận** nguyên tắc P2: không tin tín hiệu nội tại, phải có verifier bên ngoài |
| Q-010 (F-A03) ↔ AN-006 (eval yếu) | U-curve lost-in-middle **là học được từ loss** ⇒ lỗi eval **không phải giới hạn kỹ thuật** mà là **hình dạng phần thưởng** — cùng kết luận với F-R01 ở Q-009 |
| **Q-011 (F-X01) ↔ Q-007 (F-K05)** | hai survey độc lập, **cùng kết luận**: não **ức chế chứ không xóa** — củng cố T3 thành quy luật, không còn là quan sát riêng lẻ |
| **Q-011 (F-X03) ↔ Q-006/007 (loss of plasticity)** | **đảo ngược giả định**: không phải "quên quá ít" mà là **thiếu replay** — replay chữa loss of plasticity mà **không đổi gì khác** ⇒ *trí nhớ là điều kiện của khả năng học* |
| Q-011 (F-X04) ↔ DS-001 (P2) | unlearning verify *"underexplored"* + multi-hop leak ⇒ **P2 đúng nguyên tắc nhưng thiếu công cụ**: SAGE cần verifier **đa-hop**, không chỉ điểm-đơn |
| Q-011 (F-X05) ↔ Q-009 (F-R01) | GDPR chỉ **delink**, unlearning chỉ **xóa điểm** — cả hai **không đổi được cái thật sự**: *output thật* (luật) hay *reward thật* (hack). Cùng cấu trúc "tín hiệu ≠ mục tiêu" |
| **DS-002 D6 ↔ Q-010 (F-A03)** | **Xác nhận trực tiếp**: cùng 1 kiến trúc attention, đổi *phân bố loss* → U-curve tự sinh ra (`U-gap 0.838`, giữa `0.162` ≈ ngẫu nhiên) ⇒ F-A03 không còn là correlation trên benchmark nữa |
| **DS-002 D7 ↔ Q-011 (F-X02)** | **Xác nhận 2 chiều**: (a) quên **đều** phá trục ngoài dữ liệu mới gấp **100×** directional (`MSE_P3 2.13e-5` vs `2.12e-7`); (b) **không** quên thì không thích nghi được khi θ đổi — `MSE_P4` của `noforgetting` gấp **29×** của RLS quên chuẩn. Nhưng directional **không** làm chậm học dims mới (`0.24×`) → "quên đúng **hướng**" là vấn đề thật, không phải chiết ngôn |
| **DS-002 D8 ↔ Q-011 (F-X03)** | Replay giữ `0.839` vs naive `0.431` (**+0.408**) trong khi plasticity **không đổi** → **xác nhận nhánh retention**, **âm tính** với nhánh loss-of-plasticity ở scale toy |
| **DS-003 D9 ↔ Q-009 (F-R01/F-R07)** | **Xác nhận bằng thực nghiệm**: proxy trong vòng lặp → ứng viên **sai sự thật 6.07 điểm**; thêm monitor **cũng trong vòng lặp** vẫn kém 3.15 → *cộng hai proxy lại vẫn là proxy*. Và holdout **cố định** bị optimize: **nói dối 8.41 điểm**, tăng `5.03 → 8.40` theo số lần hỏi ⇒ **giải thích trực tiếp vì sao không thể "vá proxy"**: mọi tín hiệu xài lại đủ nhiều đều biến thành objective |
| **DS-003 D10 ↔ Q-009 (F-R01) — metric tự bị hack** | **Ba lần sửa liên tiếp toàn là thước đo tự thoái hóa**: `gating_acc` cho điểm cao nhất khi coverage = **0** (không quyết định gì) · hợp đồng `0.90` bị vô hiệu bằng cách nằm ngoài vùng dữ liệu · bandit "không học" vì *không chịu thử*. Đây là **Goodhart trên chính acceptance test** — cùng cấu trúc với T2, giờ lặp lại trong phòng lab của chính mình |
| **DS-003 D10 ↔ DS-001 (F-D05)** | Xét **trực tiếp** điều F-D05 mới suy đoán: `ECE 0.258 → 0.022`, `violation 0.203 → 0.000`; arm thô **tự quyết 23.5% ca với 70% đúng** trong khi tuyên bố 90% → *"biết khi nào không biết"* **phải được đo bằng calibration thật**, không phải bằng self-report |
| **DS-003 D11 ↔ Q-010/Q-003 (gating T4)** | Bảng `model × kiểu lỗi` học từ phản hồi nhị phân: `0.920` ≈ **95% oracle** vs `0.577` model tĩnh → **gating theo ngữ cảnh thắng model cố định** bằng 34 điểm; và *không có optimistic-init thì arm không chịu thử* — khám phá là điều kiện cần, không phải optional |
| **Q-012 (F-N01) ↔ Q-007 (F-K05 replay)** | Q-007 nói *replay là thứ ML mượn được*; Q-012 cho thấy replay **không đi một mình** — nó đi với **downscale** và **dọn rác**, và được **cặp nhịp SO–SP coupling** điều khiển (meta Bayesian 2025, 297 effect) → replay là **một job trong 3 job** |
| **Q-012 (F-N04) ↔ Q-011 (F-X02/F-X03)** | Q-011: não **ức chế chứ không xóa**; Q-012: **SHY cho thấy có "giờ giảm strength"** (synapse chỉ giảm khi được ngủ) → **đúng nghĩa đen của "quên có chủ đích"** là một **giai đoạn offline có lịch**, không phải process nền. Chưa mô hình nào của ML bắt được điều này |
| **Q-012 (F-N03) ↔ T5 (thiếu máy đo)** | **Tự phản chứng trong ngành**: meta-analysis spindle 53 studies ra "nhỏ–vừa", bình luận 2026 dùng lại chính dataset đó với kiểm soát publication bias ra **"gần như không có"** → bài học: **chọn biến đo robust** (coupling) thay vì biến đo nhạy bias (density) |
| **Q-012 (§3e) ↔ Q-009 (F-R01) + DS-003 D9** | **Lý do ngủ không bị wirehead**: trong window ngủ **không có reward-driven signal** → không có objective nào để optimize → không thể hack. DS-003 D9 đo **ngược lại** (proxy + monitor + holdout trong vòng lặp → nói dối 8.41) ⇒ **SAGE cần một window "không objective"** — đó chính là DS-004 |
| **Q-013 (F-V01) ↔ Q-009 (F-R01)** | F-R01 nói *"không sửa được reward bằng vá kỹ thuật"*; F-V01 nói **đúng luôn cả khi không có reward** — Gödel II (tự chứng minh nhất quán) + Rice (tự kiểm mọi hành vi) + E6 (quan sát nội bộ RLVR **không đủ**, phải audit ngoài) ⇒ **hệ thống không bao giờ là chứng nhân cho chính nó**, ở cả 3 cấp: logic, tính toán, reward |
| **Q-013 (F-V02) ↔ DS-003 D9/D10** | **Xác nhận bằng 3 nguồn độc lập** (Sleeper Agents, adaptive monitor attacks, TraceGuard) điều số nội bộ đã thấy: thêm monitor/verifier **trong vòng lặp** không cứu được. Ngay cả adversarial training còn **nâng khả năng nhận ra trigger** → *phòng thủ sai chỗ làm hệ thống khó bị phát hiện hơn* |
| **Q-013 (F-V03) ↔ Q-012 (§3e) + AN-013 (E12/E13)** | 3 điều kiện của verification thật (**spec ngoài khóa trước · deterministic · verifier ngoài reward**) = đúng 3 thứ **ngủ làm**: có lịch, không có reward drive, đầu ra tái lập được → *điều kiện cần của verification là **một cửa sổ không optimize gì*** |
| **Q-013 (F-V06) ↔ T5 (thiếu máy đo)** | Khoa học không sửa được replication crisis bằng lời hứa mà bằng **cấu trúc**: preregistration + registered report + replication dữ liệu độc lập = *không cho phép tự chọn thước đo sau khi thấy số* → **đúng thủ tục §10/§12/§14** của dự án, và nó **đã bắt được 5 lần metric bị hack** ở DS-002/DS-003 |
| **DS-004 (F-J01, F-J05) ↔ Q-012 (F-N07) + Q-011 (F-X03)** | **"Giờ bảo trì" chạy được ở scale toy**: cùng ngân sách `0.40`, giữ theo **giá trị** thắng theo **độ mới** `+0.55` (F-J01) · nén **61.9%** mà acc `0.9525`, vượt cả baseline raw-thuần `0.6971` (F-J02) · stub-redirect giữ `dangling = 0` trong khi recency/random gãy `296/224` (F-J03) — đúng P3 SAGE + F-X01. **Nhưng có điều kiện** (F-J05): fidelity `0.374` (σ=0.2) thì `sage` **thua** raw-thuần → nén chỉ an toàn khi record đủ trùng lặp. F-N07 (*chưa ai tách downscale khỏi replay*) giờ có **số liệu đầu tiên** |

---

## 4. Agenda nghiên cứu tiếp

| # | Câu hỏi (bridge) | Nối | Trạng thái |
|---|---|---|---|
| Q-007 | Bộ nhớ hình thành & quên — Ebbinghaus → continual learning | Q-001/004/005/006 | ✅ **xong (2026-10-06)** |
| Q-008 | Tạo bộ não **không khuyết điểm** — làm được tới đâu? | Q-001→007 (tổng hợp) | ✅ **xong (2026-10-06)** |
| Q-009 | Vì sao cả não và AI đều **hack được reward**? | Q-003/004/006 | ✅ **xong (2026-10-06)** — 3 case chung 1 cấu trúc |
| Q-010 | **Attention** — van chọn lọc của não và của Transformer | Q-002/003/006 | ✅ **xong (2026-10-06)** — khác 4/5 chiều, cùng 2 chiều lỗi |
| Q-011 | **Quên có chủ đích**: khi nào nên quên (đổi tech stack, đổi domain)? | Q-001/007 | ✅ **xong (2026-10-06)** — 4 nghĩa; quên phụ thuộc *hướng* + *replay*, không phải lượng |
| **Q-012** | **Ngủ & củng cố trí nhớ** — ngủ làm gì với ký ức, ML mô phỏng được gì? | Q-007, Q-011, Q-006 | ✅ **xong (2026-10-06)** — 3 job/giờ ngủ; TMR `g = 0.29`; khoảng trống: chưa ai tách **downscale** khỏi replay |
| **DS-001** | **Thiết kế SAGE** — biến 5 chủ đề T1–T5 thành kiến trúc + prototype | T1→T5, Q-008 | ✅ **xong (2026-10-06)** — demo **5/5 PASS** trên Kaggle |
| **DS-002** | **Mở rộng demo** — kiểm chứng trực tiếp 3 finding của Q-010/Q-011 | Q-010 (F-A03), Q-011 (F-X02, F-X03) | ✅ **xong (2026-10-06)** — demo **3/3 PASS** (3 lần, change-log §12) |
| **DS-003** | **Mở rộng demo** — 3 công cụ tự kỷ luật của SAGE v0.2 (roadmap §11) | Q-009 (F-R01/F-R07), DS-001 (F-D05) | ✅ **xong (2026-10-06)** — demo **3/3 PASS** (3 lần, change-log §14) |
| **Q-013** | **Một hệ thống tự chứng minh mình không bị hack được không?** | Q-009 (F-R01), Q-012 (§3e), DS-003 (F-G01) | ✅ **xong (2026-10-06)** — *không thể tự chứng minh, cấu trúc bên ngoài thì được*; prefix **F-V** |
| **DS-004** | **Archive/compaction** — "giờ bảo trì" của SAGE (nén lịch sử thành scaffold) | Q-012 (T6, F-N07), Q-011 (F-X03) | ✅ **xong (2026-10-06)** — demo **3/3 PASS** (Kaggle v4, ngưỡng §15.2 giữ nguyên · change-log §15.4); prefix **F-J** |
| **DS-005** | **Red-team acceptance** — tự hack lấy KPI của chính mình, đối chứng 3 lớp phòng thủ | Q-013 (F-V03, §6), DS-003 (D9) | ⬜ **đề xuất từ AN-013 §6**, chờ duyệt chạy |

---

## 5. Trạng thái dự án vs PLAN.md

- **M2 (survey 5–10 paper/câu hỏi)**: ✅ vượt — **13 survey**, Q-006 dùng 19 paper arXiv, Q-007 dùng 16 paper, Q-009 dùng ~22 paper, Q-010 dùng ~20 paper, Q-011 dùng ~26 paper, Q-012 dùng **18 DOI Europe PMC + ~8 arXiv**, Q-013 dùng **6 trang Wiki nền tảng + ~15 arXiv**.
- **KPI graph**: **220 entity / 286 relation** (mục tiêu ban đầu 100 entity ✅).
- **DS-001 (thiết kế + demo)**: ✅ `design/SAGE-spec.md` + `design/demo/` — Kaggle `tribu1/sage-v0-1-demo-ds-001` v3 = **5/5 PASS** (D1 replay +38.7pp · D2 18× · D3 Goodhart · D4 −33.4% · D5 +5.7pp).
- **DS-002 (mở rộng demo)**: ✅ `design/SAGE-spec.md` §12 + `design/demo/sage_demo2.py` — Kaggle `tribu1/sage-v0-2-demo-ds-002` v5 = **3/3 PASS** (D6 U-gap 0.838 · D7 100× + 29× · D8 replay 0.839 vs naive 0.431). **3 lần chạy** (1/3 → 2/3 → 3/3), mọi thay đổi ghi ở change-log §12, **3 ngưỡng không đổi**. **Kết quả âm**: loss of plasticity không quan sát được ở scale toy (3/3 lần).
- **DS-003 (mở rộng demo)**: ✅ `design/SAGE-spec.md` §14 + `design/demo/sage_demo3.py` — Kaggle `tribu1/sage-v0-3-demo-ds-003` v3 = **3/3 PASS** (D9 holdout cố định nói dối **8.41** và tăng theo số lần hỏi · D10 ECE `0.258→0.022`, violation `0.203→0.000` · D11 adaptive `0.920` vs static `0.577`). **3 lần chạy**, mọi thay đổi ghi ở change-log §14 — **cả 3 lần sửa đều là bug metric/harness, không hạ ngưỡng nào**. Bài học: *cái thước tự bị hack 3 lần liên tiếp* = Goodhart tái hiện ngay trong phòng lab.
- **Q-012 (survey)**: ✅ `surveys/sleep-consolidation.md` — **AN-012**, 7 finding **F-N01…F-N07**, 24 nguồn (18 DOI Europe PMC + 8 arXiv + 5 trang Wiki). Kết quả chính: ngủ làm **3 job/giờ bảo trì** (replay · downscale · dọn rác); **TMR `g = 0.29`** (N = 2004, null ở REM/thức/thiếu niên, mất ở 9 tháng); **spindle-metric đang bị publication bias làm méo** → dùng coupling thay density; khoảng trống mở **F-N07**: chưa ai tách downscale khỏi replay. Websearch vẫn 401 → dùng **Europe PMC API** làm nguồn sinh học (không qua web).
- **Q-013 (survey)**: ✅ `surveys/self-verification.md` — **AN-013**, 7 finding **F-V01…F-V07**, 20 nguồn (6 trang Wiki nền tảng: Gödel II, Rice, Goodhart, Formal verification, Preregistration, Replication crisis + ~15 arXiv RLVR/monitor/verify). **Câu trả lời**: *không thể tự chứng minh — nhưng cấu trúc bên ngoài chứng minh được* (3 điều kiện F-V03: spec ngoài khóa trước · deterministic · verifier ngoài reward). Đề xuất **DS-005** (red-team acceptance) ở §6.
- **DS-004 (mở rộng demo)**: ✅ `design/SAGE-spec.md` §15 + `design/demo/sage_demo4.py` — Kaggle `tribu1/sage-v0-4-demo-ds-004-archive-compaction` v4 = **3/3 PASS** (D12 nén `size 0.3808 ≤ 0.40` + `acc 0.9525 ≥ 0.90` · D13 `+0.5523` / `+0.5505` vs recency/random · D14 `dangling = 0` mọi chu kỳ + `Δacc +0.0034`). **4 lần push**: v1–v3 chết vì papermill đòi `.ipynb` (không có số liệu), **v4 PASS ngay lần đầu thấy số — không hạ ngưỡng** (change-log §15.4). Bài học: diagnostic *"trần acc"* bị **số liệu bác nhãn** (`oracle 0.6971 < sage 0.9525`) → nó là *baseline value-only raw*, trần thật = `keepall = 1.0`; và **F-J05**: nén chỉ an toàn khi record đủ trùng lặp (σ=0.2 → fidelity `0.374` → `sage` thua raw-thuần). Findings **F-J01…F-J05** (prefix **F-J**).
- **Còn nợ §9**: migrate token Kaggle/GitHub sang `{env:...}` (**chưa làm** — rủi ro bảo mật).
- **Lưu ý hạ tầng**: websearch đang **401** → workaround: arXiv MCP + `webfetch` (Wikipedia/PMC/PubMed).
