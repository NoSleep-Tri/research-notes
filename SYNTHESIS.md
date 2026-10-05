# SYNTHESIS — Kết hợp 11 survey thành 1 bức tranh, rồi thiết kế hệ thống

- **Ngày**: 2026-10-06 · **Phạm vi**: Q-001 → Q-011 + **DS-001, DS-002** (thiết kế dẫn xuất)
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
| **DS-001** | *(thiết kế)* **SAGE** — bộ não biết mình dở ở đâu | `design/SAGE-spec.md` | 6 lớp L0–L5, 8 nguyên tắc P1–P8 truy xuất survey; **demo 5/5 PASS** | Tổng hợp từ Q-001→011 |
| **DS-002** | *(mở rộng)* **SAGE v0.2** — kiểm chứng trực tiếp F-A03 / F-X02 / F-X03 | `design/SAGE-spec.md` §12 | **demo 3/3 PASS** (3 lần): U-curve sinh từ phân bố loss · quên đều phá trục **100×**, không quên thì không thích nghi **29×** · replay giữ `0.839` vs naive `0.431` | Q-010 + Q-011 |

---

## 2. Năm chủ đề xuyên suốt (cross-cutting)

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

### T3 · **Không có nút "xoá" — học = thêm lớp đè** (Q-001, Q-004, Q-005, Q-006, Q-007, **Q-011**)
- Extinction **không xoá** fear memory → renewal (Q-004) · reconsolidation-xoá ký ức (propranolol) **tái lập thất bại** (Q-004/007) · habit **không bao giờ thành reflex** (Q-005) · continual learning ML **quên thảm họa** hoặc **quên mãi không được** (Q-006, Q-007).
- **Củng cố mạnh từ Q-011**: não **không bao giờ xóa** — nó **ức chế truy cập** (RIF 13%, nội dung phục hồi được) · **GDPR cũng không bắt xóa** — chỉ *right to erasure* + delink, nội dung còn online · **unlearning** đi qua được single-hop nhưng **multi-hop vẫn suy ra** → *cả 3 hệ thống, dù khác nhau về bản chất, đều đến cùng một chỗ: "đã xóa" gần như không tồn tại*.
→ **Insight**: cả sinh học, máy và **luật** đều **giữ bản cũ** → chiến lược đúng là **cài patch an toàn đè lên** (extinction engram, safety layer, replay, supersede-mark) chứ không chờ "xóa".
→ **Điều kiện cần để "xoá" thật** (Q-011): phải có **hướng** (directional, không prune đều) và **đi kèm replay** — không thì mất luôn khả năng học (F-X03, F-X06).

### T4 · **Gating: output = tín hiệu × van** (Q-003, Q-004, Q-005, Q-006, **Q-010**)
- presynaptic inhibition + Jendrassik (Q-005) · extinction gate theo **context** (Q-004) · attention/interoceptive gating (Q-003) · eval gates & monitor (Q-006).
→ **Insight**: **can thiệp vào van rẻ hơn thay tín hiệu** — cùng công thức trong rehab (tăng gain), học (đổi context), và ML (đổi reward/monitor).
→ **Nối từ Q-010 — nhưng có cảnh báo quan trọng**: ở não, **chính cái van tạo ra trần** (tài nguyên hữu hạn, 3–6 mục). Ở Transformer, attention **không có trần** ⇒ *công thức đúng nhưng thiếu hạn tử*: mọi thiết kế agent đều phải **tự đặt budget** (test-time compute có ngưỡng theo domain; context có ngưỡng hỏng). **Đừng giả định van tự đóng.** (F-A01, F-A05)

### T5 · **Phương pháp: bằng chứng đảo ngược + thiếu máy đo** (cả 11 survey)
- **Đảo ngược** (mất tín hiệu → hỏng) cho kết quả mạnh nhất: CIP (Q-003), S.M. (Q-004), Babinski/SCI (Q-005), ablation (Q-006), reconsolidation disruption (Q-007).
- **Cùng thiếu "máy đo"**: không có máy đo ý thức (Q-002) ↔ **không có benchmark đáng tin** (Q-006) ↔ chưa có metric "quên bao nhiêu là lành mạnh" (Q-007) ↔ **attention weight nhìn thấy được nhưng không phải giải thích** (Q-010, F-A02 — người ra quyết định kém hơn khi có nó) ↔ **unlearning verification "underexplored and fragmented"** (Q-011, F-X04).
→ **Insight**: 5 lĩnh vực cùng đứng ở **khoảng trống giữa cơ chế đã mô tả và con số đáng tin** — đây là nơi research thật sự sống. **Mẫu lặp lại 4 lần trong 11 survey** ⇒ nó *là* đặc trưng của ngành, không phải tai nạn.

---

## 3. Ma trận liên thông (trích từ knowledge graph, 189 entity / 231 relation)

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

---

## 4. Agenda nghiên cứu tiếp

| # | Câu hỏi (bridge) | Nối | Trạng thái |
|---|---|---|---|
| Q-007 | Bộ nhớ hình thành & quên — Ebbinghaus → continual learning | Q-001/004/005/006 | ✅ **xong (2026-10-06)** |
| Q-008 | Tạo bộ não **không khuyết điểm** — làm được tới đâu? | Q-001→007 (tổng hợp) | ✅ **xong (2026-10-06)** |
| Q-009 | Vì sao cả não và AI đều **hack được reward**? | Q-003/004/006 | ✅ **xong (2026-10-06)** — 3 case chung 1 cấu trúc |
| Q-010 | **Attention** — van chọn lọc của não và của Transformer | Q-002/003/006 | ✅ **xong (2026-10-06)** — khác 4/5 chiều, cùng 2 chiều lỗi |
| Q-011 | **Quên có chủ đích**: khi nào nên quên (đổi tech stack, đổi domain)? | Q-001/007 | ✅ **xong (2026-10-06)** — 4 nghĩa; quên phụ thuộc *hướng* + *replay*, không phải lượng |
| **DS-001** | **Thiết kế SAGE** — biến 5 chủ đề T1–T5 thành kiến trúc + prototype | T1→T5, Q-008 | ✅ **xong (2026-10-06)** — demo **5/5 PASS** trên Kaggle |
| **DS-002** | **Mở rộng demo** — kiểm chứng trực tiếp 3 finding của Q-010/Q-011 | Q-010 (F-A03), Q-011 (F-X02, F-X03) | ✅ **xong (2026-10-06)** — demo **3/3 PASS** (3 lần, change-log §12) |

---

## 5. Trạng thái dự án vs PLAN.md

- **M2 (survey 5–10 paper/câu hỏi)**: ✅ vượt — **11 survey**, Q-006 dùng 19 paper arXiv, Q-007 dùng 16 paper, Q-009 dùng ~22 paper, Q-010 dùng ~20 paper, Q-011 dùng ~26 paper.
- **KPI graph**: **189 entity / 231 relation** (mục tiêu ban đầu 100 entity ✅).
- **DS-001 (thiết kế + demo)**: ✅ `design/SAGE-spec.md` + `design/demo/` — Kaggle `tribu1/sage-v0-1-demo-ds-001` v3 = **5/5 PASS** (D1 replay +38.7pp · D2 18× · D3 Goodhart · D4 −33.4% · D5 +5.7pp).
- **DS-002 (mở rộng demo)**: ✅ `design/SAGE-spec.md` §12 + `design/demo/sage_demo2.py` — Kaggle `tribu1/sage-v0-2-demo-ds-002` v5 = **3/3 PASS** (D6 U-gap 0.838 · D7 100× + 29× · D8 replay 0.839 vs naive 0.431). **3 lần chạy** (1/3 → 2/3 → 3/3), mọi thay đổi ghi ở change-log §12, **3 ngưỡng không đổi**. **Kết quả âm**: loss of plasticity không quan sát được ở scale toy (3/3 lần).
- **Còn nợ §9**: migrate token Kaggle/GitHub sang `{env:...}` (**chưa làm** — rủi ro bảo mật).
- **Lưu ý hạ tầng**: websearch đang **401** → workaround: arXiv MCP + `webfetch` (Wikipedia/PMC/PubMed).
