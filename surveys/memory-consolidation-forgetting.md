# AN-007 — Bộ nhớ: hình thành, củng cố, quên (Survey)

- **Ngày**: 2026-10-06 · **Câu hỏi**: [Q-007](../questions/Q-007.md)
- **Phương pháp**: websearch **401** → thay bằng **webfetch** (2 trang Wikipedia gốc: *Memory consolidation* last-edit 30/07/2026, *Catastrophic interference* last-edit 11/08/2026 — trích được citation gốc) + **arXiv MCP** (10 truy vấn, 16 paper 2025–10/2026). Không phải systematic review.
- **Kết luận ở 1 dòng**: *Ký ức được **củng cố 2 pha** (phút–giờ ở synapse, tuần–năm từ hippocampus sang vỏ não), **ngủ và spacing là chặng làm việc thật**, **quên = interference chứ không phải xoá** — và mạng neural nhân tạo **học lại nguyên lý replay từ não** nhưng vẫn chưa giải xong bài toán liên tục.*

---

## 1. Khung: 1 vòng đời ký ức + 1 bản sao nhân tạo

```
SINH HỌC                              MÁY TÍNH (bản sao)
── encode ──► synapse đổi (phút–giờ)  train step ► weight đổi
   │  protein synthesis, late LTP        │  overlap ở hidden layer
   ▼ systems consolidation               ▼
 hippocampus ──ngủ/replay──► vỏ não      replay buffer ──► chống catastrophic
   │                                        │
   ▼ recall → RECONSOLIDATION (mở lại)     ▼
   sửa/ cập nhật / làm脆弱 ──► ổn định     continued pretraining: quên capability
   QUÊN = interference, không xoá        QUÊN = catastrophic interference (1989→2026)
```

---

## 2. Findings

### F-K01 · Củng cố có **2 pha** — và chúng khác nhau về thời gian & nơi
- **Bằng chứng** (*Memory consolidation*, Wikipedia → Dudai 2004 *Annu Rev Psychol*; Squire & Alvarez 1995):
  - **Synaptic consolidation** (phút–giờ): tín hiệu nội bào → **thay đổi biểu hiện gen + tổng hợp protein** → sửa protein synapse, tái cấu trúc; giai đoạn đầu **rất dễ bị khuỷch** (thuốc/điện chấn chặn được) — đây là cơ sở "mem fragile ngay sau học".
  - **Systems consolidation** (tuần–năm): ký ức mới **ở hippocampus**, lặp dần **cortico-cortical** → giảm phụ thuộc hippocampus (standard model, Squire & Alvarez 1995; *đối lập* Multiple Trace Theory — Nadel & Moscovitch: episodic **vẫn cần hippocampus**, chỉ semantic mới rời đi).
  - Dấu mốc: **H.M.** (Scoville & Milner 1957) — cắt hippocampus → mất ký ức gần.
- **Confidence: CAO** (tranh luận nằm ở MTT vs standard, đã nêu rõ)

### F-K02 · **Ngủ là chặng củng cố** — không phải "tắt máy"
- **Bằng chứng**: reactivation ký ức lặp trong **giấc ngủ NREM** (hippocampus ↔ neocortex) — *Sleep—A brain-state serving systems memory consolidation*, Brodt et al. **Neuron 2023**; mơ về task học → **cải thiện củng cố** (Wamsley et al. 2010, *Curr Biol*); REM liên quan procedural (McDevitt 2015) — **nhưng** MacDonald & Cote 2021 cảnh báo vẫn phức tạp.
- **Confidence: TRUNG BÌNH-CAO** (vai trò ngủ = cao · chi tiết từng pha = TB, còn tranh luận)

### F-K03 · **Spacing effect = cơ chế, không phải mẹo**
- **Bằng chứng**: giãn thời gian giữa các lần học → **cho phép chuỗi protein-synthesis chạy giữa các phiên** (mục *Spacing effect* trong consolidation) → stablize mạnh hơn; khớp với số liệu Cepeda 2006 & Dunlosky 2013 ở [AN-001](how-humans-learn.md).
- **Confidence: CAO**

### F-K04 · **Reconsolidation: ký ức mở lại khi nhớ** — cơ hội sửa, cũng là chỗ mong manh
- **Bằng chứng**: **Nader, Schafe & Le Doux (2000), *Nature*** — sợ sau khi **retrieve** cần **tổng hợp protein ở amygdala** để re-stabilize; truy cập → làm ký ức **ổn định tạm thời → mở để cập nhật**.
- **Nhưng**: *"Some studies have supported... others have failed to demonstrate disruption... remains an area of ongoing debate"* — điều kiện mở **hẹp và chưa đồng thuận** → giải thích luôn vì sao **propranolol "xoá nỗi sợ" tái lập thất bại** (xem [AN-004](how-brain-knows-fear.md) gap G5).
- **Confidence: TRUNG BÌNH**

### F-K05 · **Quên = interference, không phải xoá** — và mạng neural nhân tạo quên *thảm họa*
- **Bằng chứng** (*Catastrophic interference*):
  - **McCloskey & Cohen 1989**: train backprop học "bài 1 cộng" → học "bài 2 cộng" → **1 trial cũng đủ làm hỏng bài 1** (kể cả 1+2 trùng lặp); đổi learning rate/hidden units/**overtraining đều không cứu được**.
  - **Ratcliff 1990**: 1 trial mới → **mất significant** trí cũ; outputs thành **hỗn hợp cũ-mới**.
  - Trái lại: **con người không catastrophic** — học tuần tự không xoá sạch cũ → đây là **stability–plasticity dilemma** cốt lõi.
  - Nguyên nhân: **trùng lặp representation ở hidden layer** (input mới **superimpose** lên weight cũ).
- **Confidence: CAO** (ở mạng; so sánh người = đặc tính quan sát, chưa có model giải thích đầy đủ)

### F-K06 · **ML học lại từ não: complementary learning systems + replay** (vòng phản hồi kín)
- **Bằng chứng** (mạch lịch sử):
  - **McClelland, McNaughton & O'Reilly 1995** (*Psychol Rev*): hippocampus **học nhanh** / neocortex **học chậm** + **interleaved replay** → đây là **nguyên tắc**, truyền thẳng vào kiến trúc mạng.
  - Pseudo-rehearsal (French 1997), self-refreshing memory (Ans & Rousset 1997), **generative replay** (Shin et al. NeurIPS 2017), **brain-inspired replay** (van de Ven 2020, *Nat Commun*).
  - **Ngủ chống quên trong mạng**: *Can sleep protect memories from catastrophic forgetting?* (González 2020, *eLife*) · **Sleep prevents catastrophic forgetting in spiking networks** (Golden 2022, *PLOS Comp Biol*) · *Sleep-like unsupervised replay reduces catastrophic forgetting* (Tadros 2022, *Nat Commun*).
- **Ý nghĩa**: **cùng nguyên lý replay** vận hành ở 2 hệ thống — bằng chứng mạnh cho "ngủ phục vụ bộ nhớ".
- **Confidence: CAO**

### F-K07 · **2026: continual learning vẫn là frontier** — đặc biệt cho LLM
- **Bằng chứng** (arXiv 2025–10/2026):
  - **Replay on Demand** (2609.40089) — continued pretraining cho LLM: **quên capability cũ** là trade-off, replay cố định thì cứng nhắc → cần curriculum **theo mode**.
  - **A Dynamical Theory of LoRA in Continual Learning** (2609.39367) — chưa ai hiểu nổi dynamics của LoRA với forgetting.
  - **Rehearsal-free CIL** (2609.39550), **server-side replay federated** (2609.38833), **width expansion** (2609.37702) — 3 hướng song song, chưa ai thắng.
  - **Ngủ vẫn được mượn**: *Sleep-Inspired Replay Prevents Catastrophic Forgetting* (2606.08447) · *Replay in the Silent Degrees of Freedom — continual learning without offline phase* (2609.31630 — **local sleep trong lúc thức**, khớp F-K02) · mô hình hippocampal replay (2608.21814).
- **Confidence: CAO** (nhiệt độ nghiên cứu) — **CHƯA** có giải pháp chuẩn cho LLM (khác: benchmark nào đo?)

### F-K08 · **Đổi phe: có khi "quên" mới là đúng** — và chống quên quá có giá
- **Bằng chứng**:
  - *What Should World Models Forget?* (2610.03713) — **challenging the convention**: "degradation trên data cũ = failure" được kế thừa từ **target bất động**; world model sống trong thế giới **đổi liên tục** → **nên stratified retention** (nhớ cái gì còn hiệu lực).
  - Ngược chiều: **catastrophic remembering** (overgeneralization) — anti-forgetting quá đà → **mất khả năng phân biệt cũ/mới** (French 1999; Sharkey & Sharkey 1995).
- **Ý nghĩa**: trade-off stability–plasticity **không có giải pháp thoát** — cả sinh học cũng **quên đủ để thích nghi, nhớ đủ để sống**.
- **Confidence: TRUNG BÌNH-CAO**

### F-K09 · **Đường thứ ba cho máy**: ký ức **ngoài** thay vì trong weight
- **Bằng chứng**: LLM agents 2026 chuyển sang **memory systems ngoài** (Mem++, Source learning — xem [AN-006](state-of-ml-2026.md) F-06) → không cần anti-forget trong tham số, chỉ cần **retrieval đúng**.
- **Confidence: TRUNG BÌNH** (đang thịnh hành, mới bắt đầu có benchmark)

---

## 3. Myth cần loại bỏ

| # | Myth | Thực tế | Nguồn |
|---|---|---|---|
| M1 | "Quên là lỗi — chống quên càng nhiều càng tốt" | **Catastrophic remembering**; world models nên quên có chọn lọc | F-K08 |
| M2 | "Ngủ là lãng phí thời gian học" | Replay/consolidation trong NREM; mơ về task cải thiện kết quả | F-K02 |
| M3 | "Nhắc lại 1 lần là nhớ mãi" | Cửa sổ reconsolidation mở rồi **dễ vỡ**; cần spacing + protein | F-K03, F-K04 |
| M4 | "Model train xong là nhớ mãi" | Catastrophic interference (1989) → continued pretraining vẫn quên (2026) | F-K05, F-K07 |
| M5 | "Đã có thuốc/nút xoá ký ức" | Reconsolidation **điều kiện hẹp**, propranolol tái lập thất bại | F-K04 |
| M6 | "Học 1 mạch 2 môn liên tiếp là ổn" | Interference (proactive/retroactive) — học trộn thắng block | F-K05 + [AN-001](how-humans-learn.md) |

---

## 4. Khoảng trống research

1. **Continual learning cho LLM**: replay tốn compute, giữ capability cũ + học mới → **chưa có chuẩn** (2609.40089 chỉ là một nhát cắt).
2. **Reconsolidation**: điều kiện mở cửa sổ **chưa đồng thuận** → chưa có "nút sửa ký ức" tin cậy được.
3. **Metric "quên bao nhiêu là đúng"** — 2610.03713 mở câu hỏi nhưng **chưa có thước đo**.
4. **Ngủ & học ở người**: REM vs NREM với procedural còn tranh luận (McDevitt vs MacDonald & Cote).
5. **Weights vs external memory**: kiến trúc nào cho agent sống lâu — chưa có lý thuyết chọn.
6. **Ebbinghaus-style measurement trên vật liệu hiện đại**: đường cong quên 1885 chưa được **re-test大规模** với nội dung số/đa phương tiện.

---

## 5. Hàm ý thực hành (nối [AN-001](how-humans-learn.md))

1. **Ngủ = làm việc học** — đừng thức đêm trước thi (F-K02).
2. **Spacing cho phép consolidation chạy** — giãn phiên ra, đừng dồn (F-K03).
3. **Interleaving chống interference** — học trộn 2 môn/nhóm đề thay vì block (F-K05, M6).
4. **Sửa trong cửa sổ reconsolidation**: recall → **cập nhật ngay** (tự sửa quan niệm sai sau khi vừa nhớ lại nó) — *cẩn thận: cơ chế còn tranh luận* (F-K04).
5. **Tự giảng lại = pseudorehearsal** — giải thích cho người khác là "replay" sinh học (F-K06).
6. **Đổi domain → cho phép quên chủ động**: khi đổi công nghệ, đừng giữ thói quen cũ **đè** lên mới — tái cấu trúc thay vì cộng dồn (F-K08).

---

## 6. Hướng kiểm chứng
- **CPU free**: notebook mô phỏng **interference + replay** — train 2 task tuần tự (quên) vs interleaved/generative replay (không quên) → **trực quan hoá F-K05/K06**.
- **Có thể làm người thật**: mini-Ebbinghaus self-experiment (flashcard, spacing 1/3/7 ngày, đo retention) — *dữ liệu cá nhân, không phải evidence khoa học*.

---

## 7. Nguồn

**Sinh học** (qua webfetch — Wikipedia trích citation gốc): Dudai 2004 *Annu Rev Psychol* · Squire & Alvarez 1995 · Nadel & Moscovitch 1997 (MTT) · Scoville & Milner 1957 (H.M.) · Brodt et al. 2023 *Neuron* (sleep) · Wamsley 2010 *Curr Biol* · **Nader, Schafe & Le Doux 2000 *Nature*** (reconsolidation) · Tronson & Taylor 2007 *Nat Rev Neurosci* · Gold 2008 (protein-synthesis evidence mixed).
**ML cổ điển**: McCloskey & Cohen 1989 · Ratcliff 1990 · French 1991/1997/1999 · Robins 1995 · **McClelland, McNaughton & O'Reilly 1995** · Ans & Rousset 1997 · Shin et al. 2017 (generative replay) · **Kirkpatrick et al. 2017 PNAS (EWC)** · Zenke 2017 (SI) · van de Ven 2020 *Nat Commun* · González 2020 *eLife* · Golden 2022 *PLOS Comp Biol* · Tadros 2022 *Nat Commun*.
**arXiv (MCP, 2025–10/2026)**: 2609.40089 (Replay on Demand) · 2609.39367 (LoRA dynamics) · 2609.39550 (rehearsal-free CIL) · 2609.38833 (federated replay) · 2609.37702 (width expansion) · 2610.03713 (What Should World Models Forget?) · 2609.31630 (local-sleep replay) · 2606.08447 (sleep-inspired replay) · 2608.21814 (hippocampal replay) · 2609.33437/2609.39405 (model merging/task vectors).
