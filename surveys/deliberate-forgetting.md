# AN-011 — Quên có chủ đích: khi nào nên quên?

- **Ngày**: 2026-10-06 · **Câu hỏi**: [Q-011](../questions/Q-011.md)
- **Phương pháp**: **arXiv MCP** (7 truy vấn, ~26 paper) + **webfetch** 2 trang Wikipedia gốc (*Retrieval-induced forgetting* — Good article, *Right to be forgotten*).
- **Kết luận ở 1 dòng**: ***"Quên" là ≥4 cơ chế khác nhau, khác nhau ở cả người quyết định lẫn tiêu chí thành công*** — não **không bao giờ xóa**, nó **ức chế truy cập**; ML **xóa được nhưng không verify hết được**; luật thì **chỉ yêu cầu "ngừng tìm thấy"**, không phải xóa. ⇒ *Đoán sai về nghĩa của "quên" dẫn đến chính sách quên sai* — và hệ quả sốc nhất: **mất khả năng học không phải do quên quá nhiều, mà do thiếu trí nhớ** (replay chữa loss of plasticity).

---

## 1. Bốn nghĩa của "quên" — bảng chính

| # | Nghĩa | Ai/điều gì quyết định | Tiêu chí thành công | Đo bằng |
|---|---|---|---|---|
| **1** | **Quên để nhớ** (consolidation) | **Lịch sinh học** (ngủ, synaptic homeostasis) | tín hiệu/gọi ồn tăng | recall sau ngủ |
| **2** | **Quên chủ đích** (active/intentional) | **Có chủ đích** — có chủ thể chọn | mục tiêu cạnh tranh bị **ức chế** | RIF 13% · think/no-think |
| **3** | **Quên vì tối ưu/học** (plasticity) | **gradient + phân bố dữ liệu** | học task mới **không** mất task cũ | plasticity, forward transfer |
| **4** | **Quên vì luật** (unlearning) | **Người dùng + pháp luật** | **không suy ra được** từ model | behavioral / parametric verification |

> **Nhận định chung**: chỉ nghĩa **4** có tiêu chí thành công **đo bằng bên thứ ba**. Nghĩa 1–3 đo gián tiếp.
> → Đây là lần thứ **4** mẫu "mô tả được cơ chế nhưng thiếu con số đáng tin" lặp lại (T5 của SYNTHESIS: ý thức · benchmark · metric quên · **verification của unlearning**).

---

## 2. Nghĩa 1 & 2 — Não: **không xóa, ức chế truy cập**

### 2.1 Retrieval-induced forgetting (RIF) — số liệu thật
Experiment 1 của **Goodmon & Anderson (2011)** (Wikipedia *RIF*):

| Loại | Recall TB | So với NRp |
|---|---|---|
| **Rp+** (từng được nhắc lại) | **81%** | ↑ |
| **NRp** (không can thiệp) | 68% | baseline |
| **Rp-** (cùng nhóm với Rp+, **không** nhắc) | **55%** | ↓ **−13 điểm %** |

→ **Hiệu ứng RIF = 13%**: bản thân việc *nhắc lại* một mục **làm suy yếu** mục cạnh tranh cùng nhóm.
Đây là bằng chứng **chọn lọc**: quên sinh ra từ *chính hoạt động nhớ*.

### 2.2 Nghĩa sinh học: truy cập bị **ức chế**, không bị **xóa**
- RIF **phục hồi được** khi có điều kiện truy cập lại → nội dung còn đó, chỉ **khó gọi**.
- *Forgetting* (Wikipedia): "loss **or modification** of information **already encoded**" → **sửa đổi**, không nhất thiết là mất.
- ⇒ **Song song trực tiếp với AN-007** (quên = interference, **giữ**, không xóa) — hai survey độc lập **cùng kết luận**.

### 2.3 Consolidation = quên có **lịch**
- Synaptic consolidation (mất dần sau encoded) → ngủ là "quên được định kỳ".
- ⚠️ **Trung thực**: phần *sinh học* của AN-011 dựa trên 2 trang Wikipedia; **không** có abstract arXiv nào trong survey này xác nhận trực tiếp số liệu về think/no-think (Anderson & Green) hay dopamine-active-forgetting ở côn trùng. → **để ở mức chưa verify**, xem Khoảng trống #3.

---

## 3. Nghĩa 3 — Quên để học: hai giả thuyết **đang cạnh tranh**

### Giả thuyết A: "quên sai hướng"
**arXiv:2003.03523** (tutorial, RLS):
> *"Learning depends on the ability to acquire and assimilate new information. This ability depends — somewhat counterintuitively — on the ability to forget."*

Nhưng: RLS cổ điển dùng **uniform-direction forgetting** (quên đều mọi hướng) → **hỏng khi excitation không persistent**. Cần **variable-direction forgetting**: quên **chỉ theo hướng có dữ liệu mới**.
→ **Quên đều = phá kiến thức ngoài trục dữ liệu hiện tại.** Đây là định lượng hóa của câu *nên quên gì*.

### Giả thuyết B: "mất khả năng học là do mất *hướng cong*, không phải do quên"
- **arXiv:2312.00246** (*Directions of Curvature*): mạng mất **hướng curvature** khi train → loss of plasticity; regularizer giữ curvature thì giảm được loss of plasticity. Giải thích cũ **không đủ** cho mọi setting.
- **arXiv:2410.23495** (DASH): warm-start bằng trọng số cũ → **mất plasticity**.

### Giải pháp gây sốc: **trí nhớ chữa mất khả năng học**
**arXiv:2503.20018** (*Experience Replay Addresses Loss of Plasticity*):
> chỉ cần **thêm experience replay** (dạng **trí nhớ**) + xử lý bằng Transformer → loss of plasticity **biến mất**, **không** đổi backprop, **không** đổi activation, **không** dùng regularization.

⇒ **Nghịch lý trung tâm của Q-011**: người ta tưởng "quên không đủ" → hóa ra vấn đề là **"nhớ không đủ"**.
Quên **đơn độc** không tạo plasticity; phải đi **kèm replay**. (Cùng hướng với AFEC 2110.12187 — *active forgetting of **negative transfer***: quên **liên kết sai** giữa task, không quên task.)

---

## 4. Nghĩa 4 — Quên vì luật: xóa hay chỉ "không nhìn thấy"?

### 4.1 Machine unlearning: được chia **2 loại** + **1 lỗ hổng**
- **2405.07406** (survey): **exact unlearning** vs **approximate unlearning**; 4 scenario gồm *unlearning verification* và *privacy/security issues*.
- **2406.06186**: survey nhấn **rủi ro mới** sinh ra từ chính unlearning.
- **2506.15115** (first structured survey of **verification**): *"verification methodologies remain comparatively **underexplored and often fragmented**; existing approaches lack a unified taxonomy"* → taxonomy: **behavioral verification** vs **parametric verification**.

**LLM unlearning — lỗ hổng chứng minh được:**
- **2608.04519** (*Leak-Resistant Unlearning*): benchmark hiện tại chỉ kiểm tra **single-hop** → method **có vẻ** unlearn nhưng **multi-hop vẫn suy ra được**. Đây là bằng chứng cứng: *"xóa một điểm ≠ xóa đường suy luận"*.
- **2506.12097** (UCD) — inference-time unlearning; **2609.33639** — *trajectory* unlearning cho agent (mới, 2026-09).

### 4.2 Luật thực tế: GDPR **không** yêu cầu "quên"
Theo *Right to be forgotten* (Wikipedia):
- EU **không** có "right to be forgotten", chỉ có **"right to erasure"** — *hạn chế hơn* (Art. 17 GDPR thay cho đề xuất 2012).
- Ở search engine: **"The content remains online and is not erased"** — chỉ **delink**.
- **Google Spain v. Costeja (2014-05-13)** — phán quyết nền tảng; **CJEU 2019-09**: chỉ áp **trong EU**, không bắt buộc delink toàn cầu.
- Số liệu thật (lộ nhầm 2015): **95%** yêu cầu là người thường bảo vệ thông tin riêng tư; chỉ **5%** là tội phạm/nhân vật công chúng.
- ⚠️ Đây chính là **"che" chứ không phải "xóa"** — cùng dạng với approximate unlearning.

---

## 5. Bảng quyết định: **khi nào quên có lợi / có hại**

| Tình huống | Quên có **lợi** | Quên có **hại** | Metric |
|---|---|---|---|
| Đổi task/domain | ✅ cần để học được mới | ❌ quên task cũ = catastrophic | forward transfer, backward transfer |
| Xung đột phản ứng cũ-mới (extinction) | ✅ **ức chế** phản ứng cũ có lợi | ❌ **xóa thật** sẽ mất khả năng phản ứng gốc nếu ngữ cảnh quay lại | context-dependent recall |
| Dữ liệu tích luỹ nhiễu (interference) | ✅ quên *theo hướng* dữ liệu mới | ❌ quên **đều** = phá kiến thức ngoài trục | 2003.03523: variable vs uniform |
| Luật buộc (GDPR) | ✅ bắt buộc | ❌ xóa quá mức → mất audit trail | verification: behavioral vs parametric |
| Cần giữ khả năng học dài hạn | ❌ quên **đơn độc** không đủ | ✅ cần **replay** đi kèm | 2503.20018 |
| Ký ức cạnh tranh (RIF) | ⚠️ trung tính với mục tiêu | ❌ tự nhiên gây **−13%** recall mục cạnh tranh | Goodmon & Anderson 2011 |

> **Điểm chốt**: *"nên quên"* **không** phụ thuộc vào lượng quên, mà vào **hướng của quên** (A) và **có replay đi kèm không** (B).

---

## 6. Myth cần loại bỏ

| # | Myth | Thực tệ | Nguồn |
|---|---|---|---|
| M1 | "Quên = xóa vĩnh viễn" | Não **ức chế truy cập**, nội dung **phục hồi được**; "forgetting" là loss **or modification** | RIF; *Forgetting* |
| M2 | "GDPR buộc AI phải quên" | GDPR là **right to erasure**, và search chỉ **delink** — nội dung **còn online** | *Right to be forgotten* |
| M3 | "Unlearn xong là không suy ra được" | Benchmark single-hop **bỏ sót** leak qua multi-hop; verification *"underexplored and fragmented"* | 2608.04519; 2506.15115 |
| M4 | "Càng quên nhiều càng học tốt" | Quên **đều** phá kiến thức ngoài trục dữ liệu; cần **directional** | 2003.03523 |
| M5 | "Mất khả năng học = quên quá nhiều" | Replay (**trí nhớ**) chữa loss of plasticity, không đổi gì khác; mất **curvature directions** mới là cơ chế | 2503.20018; 2312.00246 |
| M6 | "Quên chủ đích = chủ động dọn ký ức" | RIF là **tác dụng phụ** của việc nhắc lại — không có chủ thể nào "quyết định" | Goodmon & Anderson 2011 |
| M7 | "Đo mức quên là chuyện đã xong" | Verification **chưa có taxonomy chung**; nghĩa 1–3 đo gián tiếp | 2506.15115; §1 |

---

## 7. Khoảng trống research

1. **Không có metric "quên bao nhiêu là lành mạnh"** — AN-007 đã nêu, nay **mở rộng**: cũng không có ngưỡng nào cho "quên chủ đích là đủ". Không ai định nghĩa *đủ quên*.
2. **Không có framework chọn forget-policy theo domain** — mình quyết định quên gì, dùng tiêu chí nào? Nghĩa 4 có luật; nghĩa 1–3 thì **không ai có thẩm quyền**. → *Câu hỏi trung tâm cho thiết kế agent.*
3. **Chưa verify sinh học của think/no-think & dopamine-active-forgetting** trong survey này (chỉ có Wikipedia RIF là Good article). Cần arXiv/PMC gốc.
4. **RIF chưa kiểm trên skill/kỹ năng** — mọi số liệu RIF là **recall từ vựng tình huống**; không ai chứng minh RIF với **kỹ năng vận động/hành vi**.
5. **Hai giả thuyết loss of plasticity chưa đối chiếu trực tiếp**: *curvature loss* (2312.00246) vs *replay cứu được* (2503.20018). Lưu ý **confound**: paper replay dùng **Transformer** — không rõ cứu nhờ replay hay nhờ kiến trúc.
6. **Multi-hop unlearning chưa có phương pháp nào vượt qua** — 2608.04519 chỉ mới chỉ ra lỗ hổng, chưa có fix.
7. **Luật vs unlearning chưa tương đương** — không có precedent nào yêu cầu mô hình **vượt ngưỡng verification**; delink search engine ≠ không suy ra được từ weight.
8. **Nonhuman RIF** — chưa rõ có tồn tại ở động vật (Wikipedia trích dữ liệu ở người + onsets ở khỉ chưa đọc). Cần kiểm.

---

## 8. Áp dụng: chính sách quên cho **dự án này**

| Case | Nghĩa dùng | Chính sách |
|---|---|---|
| **`research/` corpus & inbox** | **4 (luật)** — nhưng **không** xóa | Giữ nguyên raw source (**audit trail**); chỉ **delink** = đánh dấu *đã xử lý* → giống RTBF, **không** xóa. *(Nếu xóa raw thì không còn truy vết để kiểm chứng finding.)* |
| **Context window / SYNTHESIS** | **3 (replay)** | Mỗi N câu hỏi → **tổng kết lại** (replay) → chính `SYNTHESIS.md`. Bằng chứng 2503.20018: replay là thứ giữ ability học → **đừng bao giờ cắt replay để tiết kiệm context**. |
| **SAGE (DS-001)** | **1 + 3** | Prune theo **hướng** (variable-direction, 2003.03523) + **replay buffer** ở L1/L2; **không** prune đều. Thêm acceptance test cho v0.2: *prune đều → mất task cũ, prune có replay → không mất*. |
| **Knowledge graph** | **2 (ức chế, không xóa)** | Khi một finding bị phản bác → **không xóa entity** (giữ truy vết như AN-009 change-log), mà **đánh dấu superseded** + thêm relation `supersedes`. |

---

## 9. Hướng kiểm chứng tiếp

- **Chạy được trên Kaggle (CPU)**: mô phỏng **replay vs prune** — train tuần tự 2 task, so 3 điều kiện: (a) quên đều, (b) prune theo hướng, (c) prune + replay. Kiểm chứng **trực tiếp** 2503.20018 + 2003.03523 ở scale nhỏ. → **DS-002 acceptance test D7**.
- **Cần người / LLM lớn**: RIF trên skill (khoảng trống #4); multi-hop unlearning.
- **Không cần gì** cho phần lý thuyết & luật.

## 10. Nguồn

- **arXiv (MCP, abstract trực tiếp)**: 2209.02299 & 2405.07406 (survey machine unlearning) · 2406.06186 (unlearning + rủi ro mới) · 2404.01206 (short survey ML + LLM) · **2506.15115 (verification: underexplored/fragmented, taxonomy behavioral vs parametric)** · **2608.04519 (multi-hop leak)** · 2506.12097 (UCD) · 2609.33639 (trajectory unlearning cho agent) · 2502.12520 (SafeEraser) · **2003.03523 (quên đều sai hướng — RLS tutorial)** · 2110.12187 (AFEC — active forgetting of negative transfer) · 2111.10831 (Learning by Active Forgetting) · 2307.01163 & 2410.16168 (active forgetting cho pretraining language plasticity) · 2402.01348 (CORE cognitive replay) · **2312.00246 (mất curvature directions)** · **2503.20018 (replay chữa loss of plasticity)** · 2410.23495 (DASH) · 1902.03187 (controlled forgetting / dopaminergic) · 1703.07655 (ASP — adaptive synaptic plasticity).
- **webfetch — Wikipedia gốc**: *Retrieval-induced forgetting* (Good article; Goodmon & Anderson 2011 Exp.1: Rp+ 81% / NRp 68% / Rp− 55% → RIF 13%) · *Right to be forgotten* (GDPR Art.17 = right to erasure, content remains online, Google Spain v. Costeja 2014, CJEU 2019, 95%/5%).
- **Nội bộ**: AN-007 (quên = interference, giữ → M1) · AN-009 (F-R01: tín hiệu ≠ mục tiêu → số 4 cùng cấu trúc) · AN-010 (F-A01: van không có trần → chính sách quên cũng cần trần) · DS-001 (P2: không tin tín hiệu nội tại → verification của unlearning).
