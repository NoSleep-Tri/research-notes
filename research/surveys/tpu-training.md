# AN-018 — Train trên TPU: Kaggle TPU v5e-8 có giúp pretrain 12.6M nhanh hơn T4 — và nhanh hơn bao nhiêu?

- **ID**: AN-018
- **Ngày**: 2026-10-07
- **Câu hỏi**: Q-019 — *(sinh từ chỉ thị "chuyển qua nghiên cứu train trên tpu để train cho nó nhanh")* Với workload thật của dự án (GPT 12.6M, causal LM, seq 1024, batch 27×1024 token, AdamW/Muon, hiện chạy T4 ~0.427 s/step), chuyển sang Kaggle TPU v5e-8 có nhanh hơn không — và nhanh hơn bao nhiêu, tốn gì để port?
- **Nguồn đã dùng**: Kaggle quota API (2026-10-07) · kaggle.com/docs/tpu + product-announcement 607202 · Google Cloud "TPU v5e" specs · NVIDIA T4 (65 TFLOPS FP16) · HF blog `lujangusface/gpu-vs-tpu-transformer-benchmark` + `github.com/tails-mpt/gpar-workshop` (L4 vs v5e, 2026-04) · Medium "TPU 101 Part 4" (2026-04-30) · docs.pytorch.org/xla (AMP + performance) · Google Developers Blog "TorchTPU" (2026-04-07) + pytorch/xla README · nội bộ: log kernel DS-012 v3, spec §23/§24

## 1. Câu hỏi đang trả lời

DS-012 (pretrain 9 cell trên T4) **v3 bị cancel ở 0/9 cell**, full plan ước ~14h > 12h phiên Kaggle → user chỉ thị "chuyển qua nghiên cứu train trên TPU cho nó nhanh". Phạm vi: chỉ trả lời cho **workload cụ thể này** (model 12.6M, batch 27×1024 token ≈ 27 sequence, seq 1024) — **không** chấm câu chung "TPU nhanh hơn GPU", vì câu đó phụ thuộc batch / cỡ model / framework (E5).

## 2. Bằng chứng

| # | Bằng chứng | Nguồn | Loại (meta/RCT/observational/review) |
|---|---|---|---|
| E1 | Quota TPU Kaggle: **72000s (20h)/tuần, 0s đã dùng**; GPU 18349/108000s (~17% đã dùng) | Kaggle quota API `get_accelerator_quota`, 2026-10-07 | operational |
| E2 | Kaggle TPU hiện là **v5e-8** (v3-8 bị loại — announcement 607202); **20h/tuần, 9h/phiên**; PyTorch/XLA preinstalled (contrib `pytorch-xla-2-0-on-kaggle.ipynb`, runtime PJRT) | kaggle.com/docs/tpu + product-announcements | vendor docs |
| E3 | TPU v5e: **197 TFLOPS bf16/chip**, 16 GB HBM/chip, 800 GiBps, **8 chip/host** (= 1576 TFLOPS bf16 nếu dùng hết) | Google Cloud "TPU v5e" docs | vendor docs (primary) |
| E4 | T4: **65 TFLOPS FP16**, 16 GB GDDR6, ~300 GB/s → peak/chip v5e = **3.03×** T4, 8 chip = **24×** | NVIDIA T4 datasheet | vendor docs |
| E5 | Benchmark L4 vs v5e (1 encoder block, d_model 512): GPU **phẳng từ batch 16**, TPU tuyến tính; **crossover throughput ở batch 32, crossover giá ở batch 64**; seq ≥ 256 → lợi TPU; framework JAX vs PyTorch/XLA crossover ~batch 300 | HF blog `lujangusface/gpu-vs-tpu-transformer-benchmark` + `tails-mpt/gpar-workshop` (2026-04) | observational (benchmark có kiểm soát, 6 experiment) |
| E6 | Microbenchmark TPU vs T4: matmul nhỏ **N=1024 chỉ ~7% peak** (≈63 TFLOP/s), N=4096 → 777 TFLOP/s; T4 fp16 ~50 TFLOP/s @N=4096; XLA compile ~2.4s cho ví dụ đơn giản | Medium @roya90 "TPU 101 Part 4" (2026-04-30) | observational (microbench) |
| E7 | torch_xla AMP: `autocast('xla', bf16)` + optimizers `syncfree` + `xm.optimizer_step` — **không cần GradScaler** (TPU sinh bf16 native); gotchas: lazy exec → `mark_step`/`torch_xla.sync()`, recompile theo shape, `.item()` buộc sync, `clip_grad_norm_` có bẫy | docs.pytorch.org/xla (AMP + performance) | vendor docs (primary) |
| E8 | **TorchTPU** (Google blog 2026-04-07): PyTorch chạy native trên TPU (PrivateUse1, eager-first, torch.compile → XLA/StableHLO); "69% model top-4300 HF chạy out-of-box"; pytorch/xla README: sẽ **thay PyTorch/XLA khi public** | Google Developers Blog + pytorch/xla README | vendor announcement |
| E9 | **Số đo nội bộ T4**: 0.427 s/step @ 27648 tok → 65k tok/s; FLOPs/step ≈ 6ND (2.1 TFLOP) + attention (~0.1–0.3 TFLOP) ≈ 2.2–2.4 TFLOP → **~5.5 TFLOPS ≈ 8% MFU** của 65 TFLOPS peak | log kernel DS-012 v3 (10000 step / 73.1 min) + tính lại | operational |
| E10 | **Trạng thái nội bộ**: v3 `CANCEL_ACKNOWLEDGED`, `results/*.json` 404 → **0/9 cell**; `data_meta.json` + `ds012/data/*.bin` còn (prep 1230s tái dùng); DS-012b §24 đã pre-reg (`7ea467e`), code chưa viết | Kaggle API + spec §24 | operational |
| E11 | *(yếu)* Field report: "v5e-8 7× chậm hơn v3" do data-pipeline cấu hình sai; inference INT8: v5e 400 vs T4 180 tok/s (2.2×) — **inference, không phải training** | datascience.SE + deploybase.ai | observational (chất lượng thấp, chỉ tham khảo) |

## 3. So sánh với phương án đối chứng

- **(a) Port sang TPU v5e-8 (1 chip)**: peak 3.03× T4 (E3/E4) **nhưng** — (i) E5: với batch ~27 sequence (dưới ngưỡng crossover throughput 32), GPU có thể **không thua**; benchmark của E5 là encoder block khác bài toán của mình → không map 1-1; (ii) E6: model nhỏ (d_model 384) → matmul nhỏ, utilization TPU thấp; (iii) **amortize compile**: run §24 chỉ ~93s train (217 bước × 0.427s) — XLA compile model thật (E6 đo 2.4s cho case đơn giản, real case có thể hàng chục–hàng trăm giây, và **compile lại mỗi phiên Kaggle mới**) sẽ **nuốt sạch lợi thế** cho run ngắn; TPU chỉ có ý nghĩa với run dài (§23 ~78 phút T4: compile 1–3 phút vẫn amortize được). Kỳ vọng trung thực: **0.7×–3×, chưa đo được → không dự báo cứng**.
- **(b) Ở lại T4, giảm overhead**: E9 cho bottleneck là **~92% không phải compute** (8% MFU) → giảm sync/`.item()`/kernel-launch, hoặc `torch.compile` trên T4, là đối chứng **rẻ hơn nhiều**: giữ nguyên numerics + pre-reg hiện có, không đổi hardware. Nếu overhead-fix trên T4 đạt 2× thì port TPU phải **vượt cả mức đó** mới đáng.
- **(c) TPU 8-chip data parallel**: 8× peak (E3) **nhưng** field report `xmp.spawn` multi-process lỗi init trên Kaggle ("Expected 8 worker addresses, got 1") → rủi ro infra chưa tự kiểm chứng; không phải bước đầu tiên.
- **(d) Chờ TorchTPU native** (E8): được thiết kế để code PyTorch chạy ít đổi → port rẻ hơn torch_xla; **nhưng** chưa rõ đã public / có trên Kaggle chưa (10/2026) → không khả dụng cho run sắp tới, không được tính vào kế hoạch.

## 4. Findings (kèm confidence)

- **F-Q01 — Rào cản truy cập TPU = 0, nhưng quota đổi hình: "30h/tuần + 12h/phiên GPU" → "20h/tuần + 9h/phiên TPU"**: TPU 20h/tuần còn **trọn 0s dùng**; 9h/phiên ngắn hơn 12h → kể cả nhanh hơn, §23 full (~14h trên T4) vẫn cần **≥1.6× speedup** mới vừa 1 phiên TPU — "nhanh hơn" tự nó không đủ, phải nhanh đủ để lọt session cap. — *confidence: cao* · E1, E2, E9
- **F-Q02 — "24× peak" KHÔNG phải speedup: với batch 27 sequence, evidence crossover nói TPU có thể không nhanh hơn, và run ngắn bị nuốt bởi compile** — E5: TPU chỉ vượt rõ ở batch ≥32 (throughput) / ≥64 (giá), model nhỏ utilization thấp (E6: matmul N=1024 ~7% peak), trong khi bottleneck T4 thật đang là overhead (E9, 8% MFU) — thứ XLA sửa được **nhưng** eager CUDA sửa cũng được (phương án (b)). Suy đoán duy nhất đứng đắn: **0.7×–3×, phải đo bằng smoke benchmark**; mọi con số >3× trong tài liệu là peak/spec, không phải đo workload này. — *confidence: trung bình* · E3, E5, E6, E9
- **F-Q03 — Port TPU đổi numerics + đổi runtime semantics → bắt buộc pre-reg mới TRƯỚC khi chạy, không phải "chạy lại code trên hardware khác"**: TPU không có fp16 GradScaler (bf16 native: `autocast` + `syncfree` + `xm.optimizer_step`, E7) → **fix #4 của §23.4 (GradScaler skip + halve scale) vô nghĩa trên TPU**; và XLA lazy exec (`mark_step`, recompile theo shape, `.item()` sync) ≠ eager CUDA → mọi ngưỡng K1–K6/loss-parity so với số T4 là không hợp lệ nếu không ghi change-log trước. — *confidence: cao* · E7, đối chiếu §23.4 #4
- **F-Q04 — Đối chứng rẻ nhất chưa thử: đo + giảm overhead ngay trên T4, vì 92% thời gian hiện tại không phải compute** — 0.427 s/step mà chỉ ~5.5 TFLOPS (E9) nghĩa là phần lớn thời gian là Python/kernel-launch/sync/eval-side work; port TPU thắng **chỉ nếu** graph-compile của XLA vượt được cả mức tối ưu đó. Đây là lý do smoke benchmark TPU phải **đối chiếu với cùng số T4 đã đo**, không so với peak spec. — *confidence: trung bình* · E9, E7, đối chiếu E5

## 5. Khoảng trống / điều chưa rõ

- **Chưa ai benchmark đúng workload này** (causal LM 12.6M, seq 1024, batch 27, có Muon/clip/eval) trên v5e-8 → mọi con số speedup trong note này là phỏng đoán có căn cứ, không phải đo.
- E5 dùng encoder block, units batch khác (samples, seq khác) → crossover 32/64 không map trực tiếp; claim "BF16 hurt TPU" của E5 mâu thuẫn chuẩn ngành (bf16 là precision mặc định của TPU) → **khả năng benchmark có config sai** → confidence của chính E5 nên đọc giảm một bậc.
- **TorchTPU (E8) đã public / có trên Kaggle chưa** — không kiểm chứng được từ đây → loại khỏi kế hoạch tới.
- **Bottleneck T4 chưa profile**: 8% MFU đến từ đâu (dataloader? kernel launch? eval?) chưa tách được từ log → §6.
- `quota_refresh_time: 2026-01-10T00:00:00Z` đọc theo YYYY-MM-DD là ngày đã lùi (format lạ) → **không dựa vào giá trị này** để tính thời điểm reset quota; chỉ tin `time_used = 0s`.
- Multi-chip `xmp.spawn` 8-worker trên Kaggle v5e-8: chỉ có field report lỗi init, chưa tự chạy xác nhận.

## 6. Hướng kiểm chứng tiếp

**Có — cần 1 smoke benchmark pre-registered (đề xuất DS-013, ghi §26 vào spec TRƯỚC KHI code — §25 đã dành cho DS-012c, đổi số 2026-10-07)**, đối chiếu đúng số T4 đã đo:

- **Câu hỏi**: với đúng config §24 (217 bước, 27×1024 tok, model 12.6M), TPU v5e-8 **1 chip** (bf16) có `median s/step ≤ 0.285s` (**≥1.5× T4**) sau khi tính cả XLA compile **không**?
- **KPI viết trước (đề xuất)**: **K-T1** 3/3 lần chạy không crash / không recompile giữa chừng · **K-T2** median s/step (100 bước steady, trừ compile) ≤ 0.285 → chọn TPU cho run tới; nếu > 0.285 → **ở lại T4 + ghi negative finding** (không hạ ngưỡng) · **K-T3** loss không NaN/Inf qua 217 bước bf16.
- **Thừa nhận đã thấy số khi chọn ngưỡng**: đã thấy T4 `0.427 s/step` (E9) + toàn bộ E1–E11; **chưa thấy bất kỳ số nào chạy trên TPU** (E1: quota `time_used = 0s` = chưa từng chạy) → ngưỡng 1.5× chọn trước khi có số TPU.
- **Phương án không cần TPU**: chạy luôn **DS-012b §24 trên T4** (đã pre-reg `7ea467e`, ~25 phút, không đổi numerics, không cần port) — trả lời câu hỏi khoa học đã đăng ký ngay; TPU chỉ đáng đầu tư nếu smoke PASS **và** mục tiêu là thang lớn hơn (§23 full, 14h T4 → ~7h TPU ở 2×).
