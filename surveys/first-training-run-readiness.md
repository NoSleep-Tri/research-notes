# AN-016 — Chuẩn bị huấn luyện thật: model base · phương pháp · compute trên Kaggle GPU

- **ID**: AN-016
- **Ngày**: 2026-10-06
- **Câu hỏi**: Q-017 — *(sinh từ Q-016 tầng-2 + chỉ thị "nghiên cứu đến đủ tài liệu rồi huấn luyện luôn")* Chuẩn bị train thật — model base / phương pháp (SFT vs GRPO) / hạng mức compute nào là đủ trên Kaggle GPU?
- **Nguồn đã dùng**: Memory-R1 full text (arXiv 2508.19828v5, gồm Appendix D Implementation Details) · arXiv 2605.30478 · 2504.20834 · 2609.00590 · 2609.39321 · 2603.19335 · 2603.28561 · TRL `GRPOConfig` (GitHub huggingface/trl main) · Kaggle accelerator quota (API) · nội bộ: AN-015, DS-009 (§20)

## 1. Câu hỏi đang trả lời

Q-016 đã kết luận 7/7 điều kiện + "chưa cần đọc thêm paper"; DS-009 (§20) đã đóng tầng-2 #1 (nhãn sạch). Câu hỏi còn lại trước khi **triển khai huấn luyện luôn** là *thông tin thực dụng*: (1) lấy method nào (SFT hay GRPO, reward gì)? (2) model base cỡ nào chạy được trên Kaggle T4 16GB? (3) compute thật cần bao nhiêu — ta có đủ? Đây là khảo sát **bounded** (2 pass), không phải mở rộng vô hạn: hết pass này mà còn thiếu gì → ghi §5, nhưng verdict "đủ/thiếu" phải trả lời được để quyết định chạy hay không.

## 2. Bằng chứng

| # | Bằng chứng | Nguồn | Loại |
|---|---|---|---|
| E1 | Memory-R1: reward = **EM (exact match)** trên output có cấu trúc {ADD/UPDATE/DELETE/NOOP}; **152 cặp** train (split 152/81/1307); **4× H100 80GB**, total batch 128, micro-batch 2/GPU, prompt 4096 / completion 2048, LR actor `1e-6`, framework **VERL**; backbone LLaMA-3.1-8B + **Qwen-2.5 {3,7,14}B**; GRPO hội tụ nhanh hơn đầu buổi, PPO ≈ GRPO cuối; Memory-SFT (BC nhãn GPT-5) F1 42.81 < GRPO 45.02; bỏ RL Memory-Manager → GRPO F1 rơi 45.0→37.5 | arXiv 2508.19828v5 §4 + Appendix D | meta (báo hệ thống, peer-adjacent) |
| E2 | GRPO + **LoRA hoạt động ở cỡ 0.6–1B**: Qwen3-0.6B và Llama3.2-1B, RLVR cải thiện pass@1 tới **+13pp**; kết quả nhạy với thiết kế reward (reward shaping sai → hành vi lệch) | arXiv 2605.30478 | observational (nghiệm thu thực nghiệm) |
| E3 | **Rủi ro thật**: trên Qwen2-1.5B + LoRA, *full-token GRPO không cải thiện hơn base*; token-selective (S-GRPO) thì 46%→70% (SVAMP) → GRPO+LoRA cần completion ngắn / credit chọn lọc | arXiv 2504.20834 | observational |
| E4 | **Cold-start barrier**: SLM "hoặc học format, hoặc học nhãn, rarely both" — direct GRPO / SFT+GRPO fail (28% / 53.5% F1, parse fail nhiều) → cần data verified / warmup có giám sát trước | arXiv 2609.00590 (CRAFT) | observational |
| E5 | GRPO trên SLM 1.5–7B: **group size** và **LoRA target modules** quyết định ổn định/hội tụ; ~80% benchmark toán cải thiện nhưng MCQ/code yếu hơn | arXiv 2609.39321 | review/nghiệm thu (systematic study, 8×A100) |
| E6 | OXRL (51 thuật toán, 0.5B–7B, ~240 runs): đòn bẩy **scale (~50pp) ≫ training paradigm (~10pp) ≫ online/offline (~9pp) ≫ loss (~1pp)**; ở 1.5B online RL (SGRPO) đứng đầu GSM8K nhưng **ranking đảo khi đổi scale**; leverage phụ thuộc task (spread 19.3pp ở GSM8K → 0.47pp ở general) | arXiv 2603.19335 | observational (đối chứng có kiểm soát) |
| E7 | TRL `GRPOConfig` mặc định: `num_generations=8` (effective batch phải chia hết G) · **`beta=0.0` → không load reference model** (tiết kiệm RAM) · `lr=1e-6` · `temperature=1.0` · `loss_type='dapo'` · `max_completion_length=512` · `epsilon=0.2` | GitHub huggingface/trl `trl/trainer/grpo_config.py` (main) | tooling (nguồn chính tắc) |
| E8 | Kaggle GPU quota: **108000s (30h)/tuần, dùng 0s**, refresh 2026-10-10; TPU 72000s. Data đã có: **1555 gold pairs** (DS-009) ≈ **10× ngưỡng 152 của Memory-R1** | Kaggle API `get_accelerator_quota` + spec §20.5 | operational |
| E9 | SFT-LoRA cải thiện rõ, GRPO thêm lợi ích nhưng **robustness thấp hơn** khi tương tác policy hỗn hợp (domain kiểm soát chặt) | arXiv 2603.28561 | observational |

## 3. So sánh với phương án đối chứng

- **(a) Đọc thêm nữa** (PPO-vs-GRPO sâu hơn, DPO/SimPO, reward model học được…) → **không cần**: E6 nói thẳng loss/algorithm là leverage ~1pp, ranking đảo theo scale; E1 đã có sẵn reward EM + cấu trúc output; đọc thêm chỉ mua ~1pp trong khi rủi ro lớn nhất (E3/E4) đã có playbook.
- **(b) Chờ compute lớn hơn** (giống 4×H100 của E1) → **không cần cho smoke**: ta không nhân rộng 8B full-FT; mục tiêu là *tín hiệu học được + so bar* với 1.5B LoRA trên T4 (E2 chứng minh 0.6–1B chạy được). Gap E1 vs T4 phải **ghi thành thật** (F-W02), không che.
- **(c) Train Answer Agent trước** → **sai thứ tự**: E1 (ablation) cho thấy Memory-Manager contributes lớn và data DS-009 chính là nhãn op; Memory-R1 cũng tách 2 agent riêng (Limitations: "train riêng để ổn định dưới sparse reward"). → DS-010 = **chỉ Memory Manager (op)**.
- **(d) Direct GRPO-from-base** → **không** làm arm duy nhất: E4 (cold-start) + E3 (GRPO+LoRA có thể không hơn base) → cần arm **SFT trước** để tách "học được format/nhãn" khỏi "RL thêm được gì".

## 4. Findings

- **F-W01 — Method chốt được**: structured-op output + reward EM/rule-based + GRPO là recipe đã kiểm chứng ở 3B–14B (E1) **và** ở 0.6–1B với LoRA (E2); tooling defaults biết trước (E7). *confidence: cao* · E1, E2, E7
- **F-W02 — Gap compute ghi thành thật**: E1 dùng 4×H100 80GB full-FT, batch 128, prompt 4096; Kaggle có T4 16GB → bắt buộc **LoRA + ≤1.5B + prompt ngắn** (context DS-009 ~vài trăm token). Smoke này **không** tái lập E1 ở scale của họ — chỉ kiểm chứng pipeline + tín hiệu học. *confidence: cao* · E1, E8
- **F-W03 — Hai failure mode đã biết + playbook**: (i) full-token GRPO+LoRA có thể **không hơn base** (E3) → completion ngắn (JSON ~20 token, vừa max_completion) + arm SFT-warmup; (ii) cold-start "format *hoặc* nhãn" (E4) → SFT arm tách riêng, GRPO arm chạy tiếp từ SFT. *confidence: cao-trung bình* · E3, E4, E5
- **F-W04 — Chọn algorithm không phải đòn bẩy chính**: leverage scale ≫ paradigm ≫ loss (E6), ranking đảo theo scale → DS-010 chạy **cả 2 arm (SFT, SFT→GRPO)** và báo cáo, không "phán" method war; đòn bẩy thật = data + scale (đã có: 1555 cặp gold, 10× E1). *confidence: cao* · E6, E5, E9
- **F-W05 — Verdict: ĐỦ tài liệu để triển khai** — 8/8 mảnh ghép (method · reward · data · model family Qwen2.5 cùng dòng E1 · evidence scale 0.6–1B · tooling defaults · quota 30h · failure playbook); thiếu duy nhất = **runtime state của Kaggle kernel** (TRL version, HF hub truy cập được không) — cái này **không phải thiếu literature**, là pre-run smoke mà chính DS-010 sẽ trả lời. *confidence: cao* · E1–E8

## 5. Khoảng trống / điều chưa rõ

- Version TRL/transformers/peft trong image Kaggle + HF hub có truy cập được với `enableInternet:true` → chỉ pre-run smoke mới biết (E7 là config của `main`, không phải version cài sẵn).
- GRPO có **thêm được gì** trên nền SFT ở cỡ 1.5B cho task 4-class này (E2/E3 mâu thuẫn nhẹ theo domain) → **chính DS-010 T4/T5 trả lời**.
- Task Answer (hồi quy giá trị + chống poison khi trả lời) chưa đưa vào scope — cần qa_pairs 540 + design reward khác (DS-011).
- E5/E6 dùng A100/H100 — group size optimum của T4 không suy ra thẳng từ đó; pre-reg sẽ set G=8 (mặc định E7) và ghi nếu đổi.

## 6. Hướng kiểm chứng tiếp

**Có — chạy ngay DS-010** (pre-register §21 *trước khi code*): Kaggle GPU, Qwen2.5-1.5B-Instruct + LoRA, split theo key (chống leakage), **2 arm**: (A) SFT trên gold op · (B) GRPO tiếp từ A (reward = 0.3 format + 0.7 op-EM, G=8, beta=0, completion ngắn); **bars pre-registered**: recency-content (dự báo ≈0.797) và recency+Δ-guard (dự báo ≈0.961); fallback duy nhất cho phép: OOM → 0.5B (ghi change-log, ngưỡng giữ nguyên).
