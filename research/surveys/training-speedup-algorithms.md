# AN-019 — Thuật toán tăng tốc huấn luyện: tổng hợp taxonomy + bằng chứng

- **ID**: AN-019
- **Ngày**: 2026-10-07
- **Câu hỏi**: Q-020 — [backlog](../backlog.md)
- **Nguồn đã dùng**: arXiv 2203.03466 (Tensor Programs V/μP) · arXiv 2407.17465 (u-µP) · bản repro độc lập μP (10.240 nets) · EleutherAI μP practitioner guide · arXiv 2412.19437 (DeepSeek-V3 MTP ablation) · arXiv 2404.19737 (Gloeckle et al., MTP) · arXiv 2509.02046 (Fantastic Pretraining Optimizers, ICLR 2026) · paper NeurIPS 2025 so sánh optimizer có µP-scaled WD · Keller Jordan Muon + nanoGPT speedrun · arXiv 2507.08472 (Sophia/Lion/AdamW budget) · arXiv 2404.06395 (MiniCPM/WSD) · arXiv 2404.07965 (Rho-1) · MosaicML Composer (Selective Backprop) · ACL 2024 LayerSkip · arXiv 2404.02258 (Mixture-of-Depths) · arXiv 2403.03507 (GaLore) + GALE (OpenReview) · AllenAI critical-batch-size blog + arXiv 2505.23971 · đo nội bộ v3 A1 s11
- **Prefix findings**: **F-AA01…F-AA08** — hết sạch F-A…F-Z (26/26 letter đã dùng, xác nhận bằng grep) → bắt đầu tiền tố 2 chữ "F-AA"; các survey sau tiếp tục F-AB, F-AC…

## 1. Câu hỏi đang trả lời

Bạn paste 2 bảng taxonomy (bảng 1: Chinchilla · Muon · FlashAttention · speculative decode · prefill/decode · CUDA kernel · little-age-mu · nemu; bảng 2: μP · progressive training · selective backprop · low-rank gradient · Prodigy · JEPA) rồi chỉ thị **"tổng hợp lại rồi nghiên cứu thử"**. Phạm vi: chỉ thuật toán/công thức ảnh hưởng convergence · FLOPs · wall-clock · HP budget — không đụng systems (đã có fix #5 chờ riêng). Trả lời cho từng mục: (a) hợp thật với hoàn cảnh **12.6M · T4 · fp16 · SEQ 1024 · 0.427 s/step · 8% MFU · 300M token**, (b) chỉ hợp ở scale lớn, (c) N/A.

## 2. Bằng chứng

| # | Bằng chứng | Nguồn | Loại |
|---|---|---|---|
| E1 | μP: LR transfer theo width 128→8192, nhưng cần width ≥ ~256, depth ~4, batch ≥ critical; init **không** transfer theo depth | arXiv 2203.03466 | theory + experiments |
| E2 | μP nguyên bản **FAIL** transfer LR cho kiến trúc Llama-style (Lingle); μP **diverge ở FP16** (underflow); u-µP sửa: LR embedding ∝ 1/√fan-out, LayerNorm không tham số, WD riêng từng nhóm | arXiv 2407.17465 | experiments |
| E3 | Repro độc lập 10.240 nets (500→0.5B): μP transfer LR/stability thật, nhưng net μP tốt nhất thường **val loss xấu hơn** net SP tốt nhất | repro độc lập (web) | experiments |
| E4 | Guide thực hành: proxy phải train ở batch ≥ critical batch size; **re-tune khi đổi kiến trúc**; có "parameterization lottery" | EleutherAI blog | practitioner guide |
| E5 | DeepSeek-V3 MTP ablation: HumanEval 20.7→26.8 / 44.5→53.7, GSM8K +6pt, nhưng **Pile BPB 0.729→0.729 (phẳng)**, MMLU 67.5→66.6 (hạ) | arXiv 2412.19437 | ablation |
| E6 | MTP: "increasingly useful for **larger** model sizes"; 13B: +12% HumanEval, +17% MBPP — lợi ích tăng theo size, **không có evidence benefit ở <1B** | arXiv 2404.19737 (Gloeckle) | ablation |
| E7 | Fair comparison 10 optimizer, 0.1–1.2B: claim 1.4–2× → sau tuning công bằng chỉ **1.1× @1.2B**; matrix-based 1.3–1.4× ở <520M, giảm dần theo scale; **LR tuning riêng AdamW đã tới 2×** | arXiv 2509.02046 | meta-comparison |
| E8 | Muon/SOAP/Shampoo với µP + WD ∝ 1/width: **~1.4× ổn định 190M–1.4B**; bỏ scaling thì speedup biến mất | paper NeurIPS 2025 | experiments |
| E9 | Muon chỉ áp layer 2D hidden, embed/head giữ AdamW (Keller Jordan); nanoGPT speedrun giữ Muon trong mọi record | practitioner (GitHub/blog) | practitioner |
| E10 | So sánh 3 optimizer "trên ngân sách": Sophia loss thấp nhất, Lion GPU-hours nhanh nhất, **AdamW downstream tốt nhất** | arXiv 2507.08472 | experiments |
| E11 | WSD: hội tụ **đầu** nhanh hơn cosine/TCTS + hỗ trợ continual/composite finetune; paper **không** claim thắng end-to-end perplexity | arXiv 2404.06395 | experiments |
| E12 | Rho-1 Selective LM: +30% few-shot (15B OpenWebMath), MATH SOTA với **3% token** — cần reference model + bước scoring | arXiv 2404.07965 | experiments |
| E13 | Selective Backprop: bỏ backward sample loss thấp → speedup FLOPs thật (có negative result cho biến gradient-matching) | MosaicML Composer docs | practitioner docs |
| E14 | LayerSkip = **inference** speedup tới 2.16×; phần training recipe chỉ để phục vụ early-exit | ACL 2024 | experiments |
| E15 | Mixture-of-Depths: cap k token/layer qua router → FLOPs budget; cần kernel custom + lo off-policy | arXiv 2404.02258 | experiments |
| E16 | GaLore tiết **memory optimizer** (60%); GALE chỉ ra SVD trong projection **chậm** → phải thay randomized QR | arXiv 2403.03507 + GALE | experiments |
| E17 | Critical batch size ước lượng được thực nghiệm (OLMo revisited; phương pháp đơn giản mới) — CBS là knob thật nhưng phải đo | allenai blog + arXiv 2505.23971 | experiments |
| E18 | **Đo nội bộ**: 0.427 s/step, 8% MFU, ~50 sync GPU↔CPU/step từ guard `isfinite` → fix #5 ước tính **2–3×** (chưa đo) | v3 A1 s11 + root-cause analysis | internal measurement |

## 3. So sánh với phương án đối chứng

### 3.1 Bảng tổng hợp 2 taxonomy bạn paste (chấm theo hoàn cảnh mình)

Mục tiêu tối ưu của mỗi kỹ thuật khác nhau — bottleneck của mình hiện là **wall (systems overhead)**, nên cái không đụng wall vô nghĩa trước khi sửa overhead:

| Kỹ thuật | Tối ưu cái gì | Hợp mình? | Lý do (evidence) |
|---|---|---|---|
| **CUDA kernel / systems** | wall trực tiếp | ✅ **Ưu tiên 1** | E18 — 8% MFU, 50 sync/step |
| **Muon (A2 arm đã có)** | FLOPs-to-target 1.3–1.4× @<520M | ⚠️ Có, nhưng fair-tuning thu hẹp | E7, E8, E9 |
| **μP** | HP budget — transfer LR theo width | ✅ Có — **cho thí nghiệm §28 đổi width**, phải làm u-µP-style (fp16!) | E1–E4 |
| **Chinchilla ratio** | data-optimal token/param | ✅ Đã ngầm đúng: 3e8/12.6M ≈ 24 ≈ 20 | internal |
| **Selective Backprop** | FLOPs (bỏ backward loss thấp) | ⚠️ Có — nhóm data lever, **sau** systems fix | E13 |
| **Rho-1 (selective LM)** | tokens-to-target | ✅ Cùng hướng arm A3 (lọc data) — candidate chính nhóm thuật toán | E12 |
| **Critical batch (B\*)** | wall↔compute trade | ✅ Đã build in (B\*=27 theo luật batch) | E17 |
| **FlashAttention** | kernel attention | ⚠️ Minor — PyTorch SDPA đã dispatch kernel fused; SEQ 1024 không phải pain point, pain point là sync | E18 |
| **MoE** | tăng params mà FLOPs không tăng | ❌ Đối chứng nội bộ AN-017: hại ở scale này | AN-017 |
| **MTP** | sample efficiency | ❌ Không ưu tiên — benefit scale-dependent (E6), Pile flat (E5) | E5, E6 |
| **WSD schedule** | train extension/continual | ⚠️ Để dành khi muốn mở token beyond 300M | E11 |
| **MoD / token dropping** | FLOPs budget/router | ⚠️ Sau systems fix — kernel custom + rủi ro off-policy | E15 |
| **Prodigy/D-Adaptation** | HP budget (auto LR) | ⚠️ Tiện cho sweep — thay μP phần nào, theory yếu hơn | — |
| **GaLore** | memory optimizer | ❌ 12.6M/16GB — không có gì để tiết; projection còn thêm overhead | E16 |
| **PowerSGD** | comms phân tán | ❌ 1 GPU, không có mạng để nén | E16 |
| **Speculative decode / prefill-đọc** | inference | ❌ Không liên quan training | E14 (mis-aim) |
| **LayerSkip** | inference 2.16× | ❌ Không tăng tốc train | E14 |
| **Progressive context →32K** | FLOPs nếu cần ngữ cảnh dài | ❌ Không cần 32K → không có lãng phí để sửa | (bảng trước) |
| **LiGO grow 12→24 layer** | wall khi cần model to hơn giữa chừng | ⚠️ Overkill — train xong 12.6M chỉ ~90' | (bảng trước) |
| **JEPA** | paradigm representation khác | ❌ Ngoài phạm vi, không có recipe 12.6M | — |
| **little-age-mu · nemu** | không rõ | ❌ **Không tra được nguồn** — đánh dấu gap trung thực (§5) | — |

### 3.2 Đối chứng chính: systems trước hay thuật toán trước?

- **Phe systems**: bottleneck đo được (E18: 50 sync/step, 8% MFU) lớn hơn **lợi nhuận thuật toán đã chứng minh** (E7: 1.1–1.4× sau fair tuning) — sửa systems ăn 2–3× trước mặt, mọi thuật toán phía sau đều được nhân kèm.
- **Phe thuật toán (counterpoint trung thực)**: wall = (số bước) × (s/step). Fix#5 chỉ giảm s/step; Muon/Rho-1 giảm **số bước tới target** — hai đòn bẩy nhân nhau, không loại trừ nhau. Nếu chỉ làm 1, systems cho ROI chắc chắn hơn (không cần tuning, không đổi numerics).
- **Scale gap**: toàn bộ evidence (E5–E12) ở ≥300M tham số, batch lớn, bf16/H800 — mình 12.6M fp16 T4. μP còn riêng caveat FP16 (E2) → extrapolation phải đánh dấu.
- **Định nghĩa "tăng tốc" khác nhau**: memory (GaLore) · comms (PowerSGD) · inference (FlashAttn/SpecDec/LayerSkip) · HP budget (μP/Prodigy) · FLOPs-to-target (MTP/MoD/SBP) — chỉ **wall** và **FLOPs-to-target** chạm được mục tiêu của mình.

## 4. Findings (1–3 ý, kèm confidence)

- **F-AA01**: Thứ tự giữ nguyên: **systems (fix #5 → compile) đứng trên mọi thuật toán** — lợi nhuận đo được của systems (2–3× ước tính) > lợi nhuận thuật toán đã chứng minh (1.1–1.4×), và mọi thuật toán sau đó đều được nhân kèm. — *confidence: cao* · E7, E18
- **F-AA02**: **μP là công cụ methodology, không phải speedup trực tiếp** — giá trị thật: transfer LR theo width cho thí nghiệm đổi width (§28 wide-shallow), tránh confound "thua do LR sai chứ không do kiến trúc". Bắt buộc biến thể u-µP (E2: μP nguyên bản diverge FP16 — mình đang train fp16) + nhớ re-tune khi đổi depth (E1) và "transfer ≠ val loss tốt hơn" (E3). — *confidence: trung bình-cao* · E1–E4
- **F-AA03**: **MTP không nên ưu tiên ở 12.6M** — evidence tích cực đều ở scale lớn (13B: +12% HumanEval), Pile BPB phẳng, MMLU còn hạ (E5); "increasingly useful for larger sizes" nghĩa là benefit chưa được chứng minh ở size mình, trong khi extra output heads ăn capacity của model nhỏ. — *confidence: trung bình-cao (về "không ưu tiên"); thấp (về "hại")* · E5, E6
- **F-AA04**: **Matrix optimizer (arm A2) có cơ sở thật nhưng nhớ fair-tuning**: 1.3–1.4× ở <520M khi AdamW baseline cũng được tune công bằng + WD scaling ∝ 1/width; riêng LR tuning AdamW đã ăn tới 2× → nếu A2 "thắng" phải chắc baseline đã đủ tune. — *confidence: trung bình* · E7–E10
- **F-AA05**: **WSD không tăng tốc hội tụ đầu** — nó mua "train extension + continual/đổi domain" (MiniCPM không claim thắng end-to-end) → chỉ cần khi nghĩ tới việc mở token beyond 300M. — *confidence: trung bình* · E11
- **F-AA06**: **Selective data (Rho-1/SBP) là ứng viên thuật toán mạnh nhất theo đúng đòn bẩy data #1 của F-B02** — cùng phía với arm A3 (lọc data); giá trị chứng minh mạnh (3% token đạt SOTA MATH) nhưng ở corpus toán học + reference model overhead → phải pre-reg + tính toán reference forward trước khi tin. — *confidence: trung bình* · E12, E13
- **F-AA07**: **GaLore/PowerSGD = N/A** — hai thứ tiết (memory optimizer, comms) đều không phải bottleneck của mình; GALE còn chứng minh projection thêm overhead tính toán thật (E16). — *confidence: cao* · E16
- **F-AA08**: **Progressive-context · LiGO · JEPA · speculative/LayerSkip-inference = ngoài phạm vi**; **little-age-mu · nemu = không tra được nguồn** (0 kết quả xác nhận) — ghi nhận trung thực là gap, không tự nghĩ ra justification. — *confidence: cao (phân loại); không có evidence (2 mục cuối)* · E14

## 5. Khoảng trống / điều chưa rõ

- Không có evidence **12.6M · fp16 · T4** trực tiếp cho bất kỳ kỹ thuật nào — extrapolation từ ≥300M/bf16/A100 luôn kèm rủi ro (riêng μP có bằng chứng fail thật ở FP16: E2).
- "Hại ở scale nhỏ" của MTP: mình trích được nguồn scale-dependent (E6) nhưng **chưa** ai publish curve 12.6M → chỉ kết luận "không ưu tiên", chưa kết luận "tại hại".
- Gain của Muon/Rho-1 **chưa từng đo dưới hệ measurement của mình** (0.427 s/step, fix #5 chưa làm) — con số wall-clock thật chưa tồn tại.
- Critical batch size của model mình: **chưa đo** (B\*=27 chọn theo luật batch từ literature, không phải từ noise scale nội bộ).
- little-age-mu · nemu: 0 nguồn — không loại được, không xác nhận được.

## 6. Hướng kiểm chứng tiếp

1. **Sau v4**: change-log fix #5 (đọc scale-signal thay per-step `isfinite`) → chạy lại A1 → **đo** 2–3× có thật (cần cho mọi ước tính phía sau). — *cần chạy: có*
2. **§28 wide-shallow (chờ bạn duyệt)**: pre-reg kèm quyết định μP hay η*-law — nếu μP thì phải implement u-µP-style vì fp16. — *cần chạy: có (nếu chốt)*
3. **Sau khi systems fix xong**: nếu vẫn muốn thêm thuật toán → Rho-1/A3 (data selection) trước, Muon-arm A2 đã sẵn trong pre-reg DS-012. — *cần chạy: có*
4. Đo critical batch size nội bộ (gradient noise scale trên vài batch holdout) — *cần chạy: nhỏ, có thể gộp*
5. little-age-mu/nemu: hỏi lại nguồn gốc (có thể do paste lạ) trước khi tốn công. — *không cần chạy*
