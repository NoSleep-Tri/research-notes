# AN-017 — Tạo model AI từ đầu: kiến trúc · dữ liệu · huấn luyện · tinh chỉnh, và với 1 GPU thì tạo được gì

- **ID**: AN-017
- **Ngày**: 2026-10-06
- **Câu hỏi**: Q-018 — *(sinh từ chỉ thị "tiếp tục nghiên cứu tạo model ai")* Tạo model AI từ đầu — kiến trúc / dữ liệu / huấn luyện / tinh chỉnh: công thức nào đã kiểm chứng, và với compute 1 GPU (Kaggle T4) thì tạo được model gì thật sự?
- **Nguồn đã dùng**: arXiv 2608.27370 (Puro-2B) · 2609.25081 (ufakzeka-1) · 2609.14715 (JugnuLM-53M/110M) · 2609.27581 (Step Law <59M) · 2605.07783 (Chain-based Distillation) · 2604.16380 (Data Mixing survey) · 2406.17557 (FineWeb) · 2203.15556 (Chinchilla) · 2501.00656 (OLMo 2) · 2512.13961 (OLMo 3) · 2401.02385 (TinyLlama) · 2608.25990 (SAMuon/Muon) · nội bộ: AN-016 (F-W05), DS-010, Kaggle quota

## 1. Câu hỏi đang trả lời

"Tạo model AI" có 4 khâu: **(1) kiến trúc · (2) dữ liệu · (3) huấn luyện · (4) tinh chỉnh (post-training)**. Câu hỏi thực dụng: công thức nào đã được **bằng chứng kiểm chứng** (không phải marketing), chi phí thật là bao nhiêu, và **ranh giới cứng** của 1 GPU T4 16GB + 30h/tuần là gì — tức là "tạo model" ở đây nên hiểu là *pretrain from scratch*, *fine-tune model có sẵn*, hay *distill*?

## 2. Bằng chứng

| # | Bằng chứng | Nguồn | Loại |
|---|---|---|---|
| E1 | **Puro-2B**: pretrain from-scratch model ~2B, tới **1.4T token, FP8, trên RTX 5090 (consumer)**; best < **$6.9K** ≈ Qwen2.5-1.5B; fitted **Puro Cost Scaling Law**: ~$4.4K là đủ chạm Qwen2-1.5B. Đối chiếu: Llama-3.2-3B tốn >$1.5M, reproduce SmolLM3-3B >$700K → chi phí giảm ~2 magnitudes nhờ: hardware + FP8 + hyperball + curriculum model averaging + data recipe | arXiv 2608.27370 | observational (báo hệ thống, có cost ledger) |
| E2 | **ufakzeka-1**: 151M (byte-tokenizer Thổ Nhĩ Kỳ), **13.5B token, tổng $286**, 3-stage pretrain + instruction-tune; 3 phát hiện chuyển được: (i) safety gate "đã fix" bằng data viết từ chính câu hỏi nó đọc **64/64, số thật 34/64** (contamination); (ii) **variance giữa các seed ≈ spread giữa mọi recipe thử được** → so sánh 1 seed ở cỡ này vô nghĩa; (iii) data rounds chỉ chữa được thứ **vốn thiếu trong data** — identity-tracking dài context + multi-turn arithmetic không dịch chuyển → **giới hạn cỡ model, không phải gap data** | arXiv 2609.25081 | observational (report + ledger mở) |
| E3 | **JugnuLM**: giữ nguyên recipe (Qwen3-style decoder: GQA + RoPE + SwiGLU + RMSNorm + QK-Norm + z-loss, data FineWeb-Edu), chỉ đổi hình học 53.5M → 109.7M (sâu & mỏng 23×576): BLiMP 78.1→81.3, WikiText-2 bpb 2.04→1.95 với **ít token hơn** (8B vs 12B) → gain do **năng lực/độ sâu, không do data**. Thang ablation: **value residuals + Muon giữ** (ARC-Easy 52.5→56.1 tích lũy); **data blend đa dạng KHÔNG giữ** (bị kẹt vào đúng bộ lọc giáo dục FineWeb-Edu) và **distillation từ 1.7B chỉ chạm đỉnh ARC nếu đổi lấy perplexity** → cả hai là **negative trung thực** | arXiv 2609.14715 | observational (controlled scaling + ablation, 935 run class) |
| E4 | **Step Law dưới 59M**: 935 runs, nanoGPT/TinyStories; chấp nhận H2 — **dạng power law giữ, hệ số đổi**: `η*(N,D) = 0.0985 N^-0.508 D^0.238` (R²=0.834), `B*(D) = 3.6e-4 D^0.931` (R²=0.950) → hyperparameter cho regime 1-GPU **đã có công thức hiệu chuẩn riêng**, không được xin từ công thức 59M–1B | arXiv 2609.27581 | observational (thiết kế lưới + hiệu chuẩn lại) |
| E5 | **Chain-based Distillation**: SLM 138M khởi tạo bằng nội suy tham số qua chuỗi anchor (định kỳ distill từ teacher) → **vượt model train from-scratch trên cùng 10B token** cho task, **không cần recovery pre-training**; cross-architecture/cross-vocab qua "bridge distillation"; tiết kiệm phải gọi teacher lặp cho mọi cỡ | arXiv 2605.07783 | observational |
| E6 | **Data mixing là bài toán bilevel trên simplex**: static (rule-based / learning-based) vs dynamic (adaptive / externally guided); trộn domain quyết định downstream dưới ngân sách cố định — "decisive impact" | arXiv 2604.16380 | review (survey hệ thống) |
| E7 | **FineWeb**: 15T token từ 96 snapshot Common Crawl, **ablate từng quyết định thiết kế** (dedup, filter); **FineWeb-Edu** (1.3T, lọc theo giáo dục) cho MMLU/ARC **tăng mạnh** → lọc + dedup là đòn bẩy hạng nhất; mớ test-mining/contamination thành практи chuẩn | arXiv 2406.17557 | observational (ablative dataset report) |
| E8 | **Chinchilla**: 400 model 70M–16B, 5–500B token → compute-optimal = **N và D nhân đôi cùng lúc**; model lớn khi đó bị undertrained. Nhưng E1/E3 cho thấy under tight budget hiện đại lại **overtrain model nhỏ** (TinyLlama: 1.1B × 1T token × 3 epoch) → luật kinh tế, không phải mâu thuẫn: chọn N theo budget rồi train D tối ưu theo E4 | arXiv 2203.15556 | observational (meta-scale study) |
| E9 | **OLMo 2**: recipe mở trọn vẹn (data, code, log, checkpoint); **curriculum giai đoạn cuối** (Dolmino Mix 1124 đưa vào **annealing**) cải thiện downstream rõ rệt; OLMo 3 (7B/32B) phát hành **toàn bộ vòng đời** → kiến thức recipe đã mở, không còn bí mật nhà lab | arXiv 2501.00656, 2512.13961 | observational (open lifecycle) |
| E10 | **Muon vs Adam**: profile phổ giải thích Muon > Adam > SGD (volatile head ở Edge-of-Stability cần step nhỏ, bulk chịu được step lớn); JugnuLM **giữ Muon** ở bước R2 (E3) → optimizer thật sự là đòn bẩy nhỏ nhưng thật, nhất quán ở 2 nguồn độc lập | arXiv 2608.25990 + E3 | observational (mechanism + ablation) |
| E11 | **Điểm chuẩn nội bộ**: Kaggle T4 16GB, quota **30h/tuần**; DS-010 đã chứng minh **1.5B LoRA SFT chạy 15 phút, acc 0.99**; AN-016 F-W05: pipeline method+reward+data đủ 8/8 | Kaggle API + spec §21, AN-016 | operational |
| E12 | **Công thức tham chiếu nhỏ**: TinyLlama 1.1B × 1T token × 3 epoch trên Lit-GPT/FlashAttention — "mượn" arch + tokenizer Llama 2, tái lập bằng hạ tầng mở | arXiv 2401.02385 | observational |

## 3. So sánh với phương án đối chứng

- **(a) Fine-tune model có sẵn (SFT/LoRA/GRPO)** → **đã làm**: DS-010/DS-011 chứng minh 1.5B + LoRA trên T4 là *vùng đã chinh phục* (E11). Đây là đường **mặc định** khi nhu cầu = 1 task cụ thể.
- **(b) Pretrain from-scratch** → chỉ **hợp lý ở cỡ 10–100M + vài B token** trên T4 (E3: 53–110M ăn 8–12B token; E4 cho công thức LR/batch đúng regime; E1: 1.4T token của Puro là **không với tới** T4 — 30h/tuần × T4 ≈ đơn vị GPU-hours không đủ 2 magnitudes). Sản phẩm của (b) ở scale này = **model nền cho nghiên cứu/giải thích/teaching**, không phải model cạnh tranh leaderboard (E2 tự nói: "capability là những gì model cỡ này đáng lẽ có").
- **(c) Distill/khởi tạo từ teacher** → E5 chứng minh 138M init từ chuỗi distill **vượt from-scratch** cùng data; E3 cảnh báo distill thuần đổi lấy perplexity. → (c) thắng (b) ở hầu hết mọi mục đích **trừ** khi muốn hoàn toàn không phụ thuộc teacher.
- **(d) Chờ compute lớn hơn** → phản chứng bằng E1/E2: chi phí đã rơi xuống $6.9K (1.5B) và $286 (151M) — rào cản giờ là **biết recipe + làm data sạch**, không phải tiền (E9: recipe mở).

## 4. Findings

- **F-B01 — "Tạo model AI" đã là bài toán công thức mở, và chi phí thật đã giảm ~2 magnitudes**: từ >$1.5M (Llama-3.2-3B) xuống **$6.9K cho class 1.5B** (Puro-2B, RTX 5090, FP8) và **$286 cho 151M** (ufakzeka-1); cả hai đều phát hành data recipe + code + ledger. *confidence: cao* · E1, E2, E9
- **F-B02 — Thứ tự đòn bẩy khi tạo model đã có bằng chứng**: **data (lọc/dedup + curriculum annealing) ≥ kiến trúc-giản-thoát chuẩn (Qwen3-style) > optimizer (Muon) > init (distill chain)**; và 2 "honest negative" phải nhớ: blend đa dạng **không** thắng bộ lọc giáo dục có chủ đích (E3), distill đổi lấy perplexity (E3). Data mixing là bài toán bilevel có taxonomy riêng (E6). *confidence: cao-trung bình* · E3, E6, E7, E9, E10, E12
- **F-B03 — Ranh giới cứng của 1 GPU T4**: pretrain from-scratch hợp lý = **model 10–100M, ngân sách token ~1–12B**, LR/batch theo công thức Step Law hiệu chuẩn riêng cho N<59M (E4); **không** tái lập được 1.4T-token của Puro (E1). Nếu nhu cầu > 100M hay > 1 task → dùng (a) hoặc (c). *confidence: cao* · E1, E3, E4, E11
- **F-B04 — Ở cỡ nhỏ, seed variance ≈ recipe spread**: ufakzeka-1 đo được spread seed bằng spread mọi recipe thử (E2) → **mọi** đánh giá recipe ở scale nhỏ phải multi-seed (≥3) hoặc thừa nhận không phân biệt được; điều này trực tiếp ràng buộc cách pre-reg demo (xem §6). *confidence: cao* · E2, đối chiếu E3 (cũng 1 seed/cell — giới hạn của chính paper trung thực)
- **F-B05 — Cổng đánh giá phải decontaminate, gate "fix bằng data sinh từ câu hỏi của nó" đọc 64/64 vs số thật 34/64**: bài học của E2 tái khớp chính kết quả DS-003 (holdout cố định nói dối 8.41 điểm) và DS-005 (verifier ngoài mới chặn 20/20) → eval khi "tạo model" viết tay + held-out + invariant script chạy trước mỗi build. *confidence: cao* · E2, đối chiếu nội bộ §14/§16

## 5. Khoảng trống / điều chưa rõ

- **Puro dùng FP8 trên RTX 5090** — T4 (Turing) **không có FP8**; delta throughput thật giữa bf16-T4 và fp8-5090 trong bài không tách rời được hardware vs precision → ước lượng thời gian pretrain trên T4 vẫn là **suy đoán** cho tới khi chạy thử.
- **Corpus thật cho model nhỏ**: E7/E3 đều dùng FineWeb-Edu (tiếng Anh, TB lọc); **tiếng Việt/tiếng ta** chưa có study tương đương trong bộ nguồn này → chất lượng data domain-specific ở budget nhỏ chưa rõ.
- **Post-training cho model tự tạo** (instruction-tune + RLVR) ở cỡ <300M: E2 chỉ làm instruction-tune dữ liệu mở, không có RLVR; AN-016/DS-010 đã biết RLVR ở 0.6–1.5B nhưng là **trên model có sẵn** → ô giao chưa ai đi.
- E3/E4 đều **1 seed/cell** → chính các paper đo được significance còn yếu (E2 nói đúng: 1 seed không phân biệt recipe).

## 6. Hướng kiểm chứng tiếp

**Có — pre-register DS-012 "pretrain from-scratch trên T4"** (§23, viết trước khi code): nanoGPT-style decoder ~10–30M, tokenizer BPE nhỏ, corpus 1–2B token (FineWeb-Edu slice + slice tiếng Việt nếu tải được), **đúng thang ablation đã kiểm chứng của E3** để trả lời thay cho marketing:

- **A1 (baseline, "công thức chuẩn")**: Qwen3-style blocks + AdamW + LR/batch theo **E4** (Step Law <59M) — bar: val-loss giảm theo power law, không diverge.
- **A2 (optimizer)**: A1 + **Muon** — dự báo: hội tụ nhanh hơn ở token budget cố định (E10/E3-R2).
- **A3 (data)**: A1 + **lọc duplicate/filter** kiểu FineWeb mini — dự báo: cải thiện val-loss + downstream proxy (E7), và **negative đã biết**: "blend đa dạng" không thắng filter (E3-R3).
- **Multi-seed ≥3/cell** (F-B04) + eval held-out + decontaminate (F-B05) — **ngưỡng viết trước, không sửa sau khi thấy số**; nếu seed spread > effect → ghi **negative finding**, không phán method war.
- Fallback duy nhất cho phép (ghi change-log): OOM → giảm model/token giữ nguyên ngưỡng.

Không cần dùng lại 1.4T token (F-B03) — mục tiêu là **kiểm chứng thứ tự đòn bẩy F-B02 ở đúng regime 1 GPU**, không phải đua leaderboard.