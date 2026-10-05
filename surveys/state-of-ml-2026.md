# AN-006 — ML hiện nay đang ở đâu? (Survey — snapshot 10/2026)

- **Ngày**: 2026-10-06 · **Câu hỏi**: [Q-006](../questions/Q-006.md)
- **Phương pháp**: **arXiv MCP** — 9 truy vấn (sort: date, date_from 2025-06) → 19 paper tiêu biểu; **không** dùng được web (HTTP 401). *Đây là snapshot lĩnh vực đang chuyển động nhanh, KHÔNG phải systematic review.*
- **Kết luận ở 1 dòng**: *ML 2026 đã dịch chuyển từ **"pretrain to hơn"** sang **"post-train + suy luận nhiều hơn lúc inference"**, dữ liệu web **bị AI chiếm 27.5%**, và mặt trận nóng nhất là **agents + environments** — trong khi **đánh giá và độ tin cậy** là nút thắt yếu nhất.*

---

## 1. Khung: 5 tầng của ML 2026

```
T5 · ĐÁNH GIÁ & AN TOÀN   benchmark saturation · LLM-as-judge tranh cãi · reward hacking · interpretability
T4 · HỆ THỐNG (agents)    memory · tools · failure recovery · ENVIRONMENTS = bottleneck RL
T3 · HUẤN LUYỆN           pretrain → SFT/distill → RLVR (GRPO) → test-time compute (reasoning)
T2 · MÔ HÌNH               Transformer dominant + hybrid SSM vào production · MTP · VLM · MoE/PEFT
T1 · DỮ LIỆU               web AI-generated 27.5% (6/2026) → synthetic · data mixing · poisoning theory
```

---

## 2. Findings

### F-01 · Dịch chuyển paradigm: **từ "to hơn lúc pretrain" → "suy luận nhiều hơn lúc inference"**
- **Bằng chứng**: *How Much Can Language Models Gain from Test-Time Computation?* (arXiv **2610.01110**) — test-time scaling "widely proposed as a **substitute for larger models**", nhưng các so sánh hiện tại chỉ test 1 miền và **không tính chi phí selection vào budget** → nhóm này đề xuất SELF-POT để tính **cost–gain thật**.
- Song song: inference-time scaling lan sang cả diffusion (2610.01933).
- **Đọc**: hướng đi đã rõ, nhưng **lợi nhuận kinh tế còn tranh luận** (càng suy luận càng đắt).
- **Confidence: TRUNG BÌNH-CAO** (direction) · **TRUNG BÌNH** (khi nào có lợi)

### F-02 · **Post-training là chặng bắt buộc** — và chuỗi công nghiệp mới đang chuẩn hoá: *distill → RL*
- **Bằng chứng** (cùng 2 ngày 01–02/10/2026):
  - RLVR là engine của reasoning models — nhưng có vấn đề phụ: **language drift** khi RLVR (2610.02015).
  - **On-policy distillation (OPD)** "has become an **important approach** to post-training" (2610.03185) — có gains nhưng cũng **collapse** (vòng lặp dài/lặp lại).
  - **OPD trước RL**: warm-start rubric-based RL bằng distillation (2610.02781) — chuỗi "nhái giáo viên → RL" đang thành chuẩn.
  - GRPO biến thể liên tục ra: Range-GRPO (2610.01548) cho reward dạng **khoảng** khi không có đáp án chuẩn.
- **Confidence: CAO**

### F-03 · **Reward hacking là vấn đề thật** — monitor "sạch" không có nghĩa kiểm soát được
- **Bằng chứng**: *A Near-Zero Monitor Readout Is Not Evidence of Behavioral Control* (2610.03458): post-training với verifiable rewards **gây reward hacking**; can thiệp monitor vào trong training objective → **readout thấp không chứng minh** hành vi bị kiểm soát (test trên code-ge...).
- **Ý nghĩa**: verification là mặt yếu của cả paradigm RLVR.
- **Confidence: TRUNG BÌNH-CAO** (mới, cần lan rộng)

### F-04 · **Data wall đã được định lượng** — web đang "tự đầu độc" bởi AI
- **Bằng chứng**: *How Much Is an AI Token Worth?* (2609.40295): sau lọc FineWeb, **27.5% token web tháng 6/2026 là AI tạo**, lên **31.1% tháng 8/2026** → corpus pretrain đang ngập text do chính model sinh ra.
-应对: data mixing cải thiện scaling (2609.38011); lý thuyết **pretraining data poisoning** tính độ suy giảm theo tỉ lệ poison (2609.32288).
- **Ý nghĩa**: "cào web" sắp hết — chất lượng + synthetic + curate là đường sống.
- **Confidence: CAO** (số đo trực tiếp, tái lập được bằng detector)

### F-05 · Kiến trúc **đa dạng hoá, nhưng Transformer vẫn thống trị** — hybrid là trào lưu production
- **Bằng chứng**: *Learning Rate Transfer for Hybrid Transformer-SSM Architectures* (2610.01172) — hybrid "class **adopted by several recent production language models**"; SSM/Mamba2 còn non ở distributed learning (2610.02659: "behavior... poorly understood"); linear attention còn đang sửa **bộ nhớ cố định** của nó (2610.02816).
- **Confidence: CAO** (bức tranh) / SSM thay thế Transformer → **THẤP**

### F-06 · **Agents = mặt trận nóng nhất**, và bottleneck đã rõ: **môi trường RL**
- **Bằng chứng**: cả 6 kết quả truy vấn agents đều **01–02/10/2026** — memory (Mem++ 2610.02002), **hồi phục khi fail** (Sentry 2610.02994), skill evolution cho Lean (2610.01799), benchmark sinh GPU kernel (D2K-Bench), benchmark "hiểu vai trò người dùng" (ReFract).
- **Nút thắt**: *PhantomEnvironments* (2609.40221) — train agent bằng RL bị chặn bởi **environments**: cần **reward kiểm chứng được + tương tác dài + rẻ** — human data đắt, LLM-synth environment dễ hallucinate.
- **Đọc đúng**: **nhiệt độ nghiên cứu = rất cao**; **độ tin cậy sản phẩm = chưa** (chính việc research "học từ failure" chứng minh agent còn fail nhiều).
- **Confidence: CAO** (nhiệt độ) · **TRUNG BÌNH** (mức độ ổn của sản phẩm)

### F-07 · **World models/video**: sinh đẹp nhưng **vật lý yếu**
- **Bằng chứng**: EVEWorld (2610.03374) — **"Model Laziness"**: tối ưu visual fidelity, bỏ qua physical reasoning; *Does Physics Live in the Activations?* (2610.03154) — video gen "increasingly proposed as world models" nhưng benchmark cho thấy **deficit vật lý**; World Embedding Benchmark (2610.03632, 8000 ca mô phỏng) ra đời để đo riêng.
- **Confidence: TRUNG BÌNH-CAO**

### F-08 · **Đánh giá (evaluation) là tầng yếu nhất**
- **Bằng chứng**:
  - LLM-as-a-judge cần **psychometric analysis** — đồng thuận tổng không nói human & judge cùng thấy khó ở đâu (2610.02877); judge cho ngôn ngữ ít tài nguyên còn phải **adapt** (2610.00406).
  - ScAn-Bench (2609.35707): scaling analysis — *"surprising that **no systematic study** exists"* → ngay cả **phương pháp tính scaling law** cũng chưa chuẩn hoá.
  - Robustness với prompt injection/backdoor vẫn là luận văn riêng biệt (2610.02432).
- **Confidence: TRUNG BÌNH-CAO**

### F-09 · Dùng LLM **mô phỏng con người** đang bị phát hiện là **"lép hoá" dữ liệu**
- **Bằng chứng**: Population Fidelity (2609.36253) — LLM **nén dải quan điểm** và **sai lệch theo subgroup**; Cultural Divergence (2609.29928) — **flattening & caricature** giữa các nền văn hoá; batching dùng chung context làm **méo quan hệ biến số** (2609.32546).
- **Ý nghĩa**: "LLM trả lời khảo sát thay người" — dùng được nhưng phải **đo fidelity**, không tin mặc định.
- **Confidence: TRUNG BÌNH-CAO**

### F-10 · **Efficiency là chủ đề xuyên suốt** (áp lực chi phí)
- **Bằng chứng**: survey *Efficient Task Adaptation* (2610.00928) — PEFT/prompt/embedding = **central challenge**; VLM **prune visual token** (2610.03389); cache cho diffusion world model (2610.02660); MTP head cho open models (2610.00888).
- **Confidence: CAO**

---

## 3. Myth cần loại bỏ

| # | Myth | Thực tế | Nguồn |
|---|---|---|---|
| M1 | "ML giờ chỉ cần model to hơn" | Compute dịch sang **post-train + inference**; data wall chặn pretrain thô | F-01, F-04 |
| M2 | "Transformer đã bị thay thế" | Hybrid Transformer-SSM mới **vào production**; SSM còn non | F-05 |
| M3 | "Benchmark cao = model giỏi" | Contamination (AI text trong web), judge chưa chuẩn, **phương pháp scaling chưa ai system study** | F-08, F-04 |
| M4 | "Monitor đọc thấp = an toàn" | Near-zero readout **không chứng minh** kiểm soát hành vi | F-03 |
| M5 | "Video gen = hiểu thế giới" | Model Laziness — đẹp về hình, **yếu vật lý** | F-07 |
| M6 | "Agents đã sẵn sàng thay người" | Chính núi paper "học từ failure/recovery" là bằng chứng chưa ổn | F-06 |

---

## 4. Khoảng trống research

1. **Planning dài hạn & reliability của agent** — fail mid-task vẫn phổ biến; chưa có giải pháp chung (Sentry chỉ là vá).
2. **Verification scaling** — reward hacking + môi trường RL (reward kiểm chứng được, rẻ, dài hạn) là bottleneck số 1.
3. **Nguồn token chất lượng thật** — web cạn, synthetic loop có **model collapse** không (đang nghiên cứu).
4. **Chi phí – chất lượng frontier** — test-time compute tăng cost; chưa có benchmark chuẩn cho **cost/quality**.
5. **Methodology lõi còn hở** — ngay scaling-analysis chưa chuẩn (ScAn-Bench); reproducibility ML lâu nay vẫn yếu.
6. **Continual/lifelong learning** — không thấy paper nào trong snapshot giải quyết cập nhật không quên.
7. **Interpretability chưa thành công cụ assure** — latent concepts có (2610.02829) nhưng chưa đưa vào quy trình kiểm định.

---

## 5. Hàm ý cho người học (áp dụng)

- **Học nền tảng trước, hype sau**: linear algebra/prob/classic ML + 1 framework → phần còn lại là **engineering hệ thống** (eval, RAG, PEFT, agents) — survey 2610.00928 xác nhận "efficient task adaptation" là central challenge thực tế.
- **Không tin benchmark trần** → tự **eval trên data của mình** (F-08); "LLM trả lời giúp" phải đo fidelity (F-09).
- **Định vị Kaggle hợp lý** (kế hoạch gốc: research, không đua leaderboard): GPU quota 30h/tuần đủ cho **PEFT/LoRA experiment nhỏ** trên model open — đúng với F-10 (efficiency).
- **Nhìn thẳng agents (F-06)**: tự động hoá được việc lặp lại, nhưng **phải có bước verify** — đúng triết lý "reliability là nút thắt" ở trên.

---

## 6. Hướng kiểm chứng

- **Notebook CPU free**: so sánh **cost–quality frontier** — 1 model nhỏ trả lời nhanh nhiều lần (best-of-n) vs 1 model lớn 1 lần, trên 20 câu; đo độ lệch so với ground truth. *Minh hoạ F-01.*
- **Có thể dùng Kaggle GPU**: LoRA fine-tune model ~1–3B để thấy F-02/F-10 (post-train + efficiency) — *experiment cá nhân, không phải evidence mới cho survey*.

---

## 7. Nguồn (19 paper qua arXiv MCP, 9 truy vấn)

**Paradigm/huấn luyện**: 2610.01110 (test-time compute & SELF-POT) · 2610.02015 (RLVR language drift) · 2610.03185 (OPD gains & collapse) · 2610.02781 (OPD→RL warm start) · 2610.02359 (multi-objective RLVR) · 2610.01548 (Range-GRPO) · 2610.03458 (reward hacking/monitor) · 2610.00888 (MTP cho open models)
**Dữ liệu/scaling**: 2609.40295 (27.5% token web = AI, 6/2026) · 2609.38011 (data mixtures) · 2609.35707 (ScAn-Bench — chưa ai system study scaling analysis) · 2609.32288 (poisoning scaling)
**Kiến trúc**: 2610.01172 (hybrid Transformer-SSM production) · 2610.02659 (Mamba2 distributed) · 2610.02816 (linear attention memory)
**Agents**: 2609.40221 (PhantomEnvironments — bottleneck RL) · 2610.02994 (Sentry failure recovery) · 2610.02002 (Mem++) · 2610.01799 (SkillEvoLean) · 2610.03226 (D2K-Bench)
**World models**: 2610.03632 (World Embedding Bench) · 2610.03374 (EVEWorld — Model Laziness) · 2610.03154 (physics in activations)
**Đánh giá/mô phỏng người**: 2610.02877 (LLM-judge psychometrics) · 2609.36253 (population fidelity) · 2609.29928 (cultural flattening) · 2609.32546 (shared-context distortion) · 2610.00928 (efficient task adaptation survey)
