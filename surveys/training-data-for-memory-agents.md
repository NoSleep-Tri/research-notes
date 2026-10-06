# AN-015 — Dữ liệu huấn luyện & đầu ra cho agent có bộ nhớ

- **ID**: AN-015
- **Ngày**: 2026-10-06
- **Câu hỏi**: Q-015 — Nên đưa dữ liệu gì để huấn luyện (một agent/hệ kiểu SAGE), và đầu ra của nó là gì?
- **Nguồn đã dùng**: arXiv 2508.19828, 2609.34633, 2607.01224, 2607.20553, 2609.07471, 2603.29493, 2610.06401, 2610.06563, 2609.32771, 2609.23916, 2610.02593, 2605.10640, 2601.01244, 2607.04364, 2603.03818, 2609.10413, 2610.06843, 2610.05872, 2604.07894, 2610.06830 + thực nghiệm nội bộ DS-005/DS-007/DS-008

## 1. Câu hỏi đang trả lời

Hai vế: (a) **input** — dữ liệu gì đưa vào để huấn luyện một agent biết quản lý bộ nhớ (kiểu SAGE); (b) **output** — mô hình/hệ thống phải phát ra gì (định dạng gì, nhãn gì, reward gì). Phạm vi: agent có memory bank bên ngoài (memory-augmented), **không** đi từ đầu bằng pretraining scale (đã phủ một phần ở AN-006). "Huấn luyện" gồm cả parametric (fine-tune weights) lẫn non-parametric (train harness/rules bằng data) — cả hai đều có evidence.

## 2. Bằng chứng

| # | Bằng chứng | Nguồn | Loại |
|---|---|---|---|
| E1 | **Memory-R1**: RL (PPO/GRPO) cho 2 agent — Memory Manager sinh thao tác **ADD/UPDATE/DELETE/NOOP**, Answer Agent pre-select + reason; chỉ **152 QA pair** để train, thắng baseline, generalize sang LoCoMo/MSC/LongMemEval, 3B–14B | arXiv 2508.19828 (abstract đầy đủ) | preprint, empirical |
| E2 | **GenMem**: memory = **Symbolic Identifier (SID)** — tuple token rời rạc nhiều cấp, <100 ký hiệu phân bổ không gian triệu-điểm-ghi; train GRPO với **dense process + outcome rewards** 2 kênh; MemRetriever + MemEvolver | arXiv 2609.34633 (abstract đầy đủ) | preprint |
| E3 | **AutoMem**: file-system ops = memory action bậc nhất; tín hiệu train = **các quyết định memory tốt của chính agent** rút ra từ nhiều episodes; optimize riêng memory → **~2–4×** (32B cạnh tranh Claude Opus 4.5 / Gemini 3.1 Pro trên Crafter/MiniHack/NetHack) | arXiv 2607.01224 (abstract đầy đủ) | preprint |
| E4 | **CMI-Mem**: RL memory manager với **hybrid reward** = QA extrinsic + CMI intrinsic, giám sát từng operation | arXiv 2607.20553 (snippet) | preprint |
| E5 | **MEMO**: evidence extractor được train + memory manager điều kiện theo query, học từ **offline reader feedback** (kế hoạch text/visual/dual) | arXiv 2609.07471 (snippet) | preprint |
| E6 | **MemFactory**: framework thống nhất GRPO cho memory-agent (hỗ trợ Memory-R1/RMM/MemAgent), reward **đa chiều từ môi trường**; cải thiện tới **+14.8%** tương đối so với base | arXiv 2603.29493 (abstract đầy đủ) | preprint |
| E7 | **RAISED**: defense khi train gây **drift phân phối output** (model từ chối bước hợp lệ trên task benign); fix = data **tự sinh**: model tự sinh scenario tool-use, train match teacher trên cặp clean/injected cùng trajectory → giảm attack success mà giữ utility | arXiv 2610.06401 (abstract đầy đủ) | preprint |
| E8 | **HERA**: sinh data **tự động + verifiable** bằng cách mutate môi trường (feasible/infeasible pairs) + co-evolution (task mới nhắm điểm yếu cũ); abstention 61.7%→83.3%, transfer +15.3pp sang 19 model | arXiv 2610.06563 (abstract đầy đủ) | preprint |
| E9 | **CPLUS**: model đóng băng tự sinh **self-probe** + tự ghi prediction → dùng làm gradient chống quên; hiệu quả hơn replay khi dữ liệu cũ khan hiếm (5 model, 4 benchmark) | arXiv 2609.32771 (abstract đầy đủ) | preprint |
| E10 | **Time-incremental CPT**: train tiếp trên FineWeb-Edu sau cutoff — **không catastrophic forgetting**; **6B token curated ≈ 40B token thô** (chất lượng > số lượng); LoRA đủ rank ≈ full CPT; gains truyền qua SFT | arXiv 2609.23916 (abstract đầy đủ) | preprint |
| E11 | **Fisher-guided CPT selector**: chọn data theo hướng tham số → **1B token chọn ra thắng 10B token replay** (10× token-efficient) trên adaptation + forgetting (TinyLlama/Llama-3.1, medical) | arXiv 2610.02593 (abstract đầy đủ) | preprint |
| E12 | **STOC (ICML 2026)**: lý thuyết — regularization chỉ đổi **tốc độ hội tụ**, replay mới **đổi xu hướng quên**; chọn token theo attention contribution để hướng replay | arXiv 2605.10640 | accepted, peer-reviewed |
| E13 | **Racka**: mix cụ thể **44% HU / 24% EN / 21% DE / 11% code** được chọn riêng để chống catastrophic forgetting khi continual-pretrain | arXiv 2601.01244 | conf. (best paper MSZNY 2026) |
| E14 | **RL Forgets / CPO**: RL **cũng** catastrophic forgetting; KL-regularization tính trên data task hiện tại ≠ chống quên (quên = behavioral drift trên phân phối task cũ) | arXiv 2607.04364 (abstract đầy đủ) | preprint |
| E15 | **Continual VLA**: model pretrained lớn + **replay buffer nhỏ** → gần zero forgetting (đơn giản hóa được CL khi pretraining đủ lớn) | arXiv 2603.03818 (abstract đầy đủ) | preprint |
| E16 | **Fortunate Recall**: lifecycle policy **deterministic (không train)** theo ontology 10+1 loại fact → 76.9% LifecycleBench, **vượt Memory-R1 (61–70.5%)**; halve confabulation (12.0% vs 24.2%, p<0.001) | arXiv 2609.10413 (abstract đầy đủ) | preprint |
| E17 | **RV-ICL**: memory hoàn toàn **training-free** (hierarchy video ICL qua read-only tools) vẫn +3.9–8.8 điểm | arXiv 2610.06843 (snippet) | preprint |
| E18 | **Grafting**: SFT dữ liệu off-policy gây interference; học update trên **donor checkpoint** rồi ghép vào model đã post-train → Pareto thắng cả SFT lẫn on-policy self-distillation | arXiv 2610.05872 (abstract đầy đủ) | preprint |
| E19 | **TSUBASA**: ghi = dynamic memory evolution, đọc = **context distillation tự học**; nút thắt data được nêu rõ: *parametric adaptation bị chặn bởi scarcity of labeled data* | arXiv 2604.07894 (snippet) | preprint |
| E20 | **MemPilot**: policy RL chọn giữa retrieve sẵn vs curation theo query, điều khiển theo preference performance–cost–latency (multi-objective) | arXiv 2610.06830 (snippet) | preprint |
| E21 | **Nội bộ**: attack suite 12 chiến lược (DS-005) + patient attacker (DS-007/008) = **generator data tổng hợp** cho robustness; KPI F1–F6 (DS-008) là reward đã có sẵn dạng dense metric | `SAGE-spec.md` §13–§19 | experiment nội bộ (Kaggle) |

## 3. So sánh với phương án đối chứng

- **Parametric (train weights)** — Memory-R1/E1, AutoMem/E3, GenMem/E2: mạnh nhất cho "biết khi nào ghi", nhưng tốn data-compute + rủi ro drift (E7) và forgetting (E14).
- **Non-parametric (rule/harness, không train weights)** — Fortunate Recall/E16, RV-ICL/E17, Mem0/A-MEM heuristics: evidence mới nhất cho thấy **lớp luật deterministic vượt RL-trained Memory-R1** (76.9% vs 61–70.5%) và không bao giờ drift. Cái giá: thiếu linh hoạt với trường hợp ngoài ontology. Đây chính là cấu trúc SAGE đang làm (§19: bộ luật theo câu hỏi thắng attack suite).
- **SFT on-policy vs off-policy**: tư liệu "mới" thường off-policy — grafting (E18) cho thấy không cần on-policy; còn RL thuần thì bản thân nó cũng quên (E14).
- **CPT data**: chọn data theo gradient/Fisher (E11) hay replay có trọng số (E12) đều thắng đắp data thô; **chất > lượng** (E10) và mix phải chủ động thiết kế (E13).

## 4. Findings

- **F-T01**: **Dữ liệu huấn luyện gồm 3 lớp, và lớp rẻ nhất đã đủ**: (1) **QA pair + memory bank** — Memory-R1 chỉ cần **152 cặp** để học đủ 4 operation (E1); (2) **trajectory + reward** — mỗi bước ghi/đọc/trả lời được nhãn bằng reward outcome + dense process (E2, E4, E6); (3) **data tự sinh** — model tự sinh biến thể (E7), môi trường mutate ra task verifiable (E8), tự probe (E9), hoặc rút ra quyết định tốt của chính nó (E3). Không cần kho dữ liệu human-labeled lớn: nút thắt được xác nhận là label scarcity (E19). — *confidence: cao* · dựa trên E1, E3, E7, E8, E9 (abstract đầy đủ, số cụ thể)
- **F-T02**: **Đầu ra phải là "thao tác bộ nhớ có ground truth" chứ không chỉ văn bản trả lời**: contract chuẩn = operation rời rạc (**ADD/UPDATE/DELETE/NOOP**, E1) / **SID** mã hóa địa chỉ triệu-điểm-ghi bằng <100 ký hiệu (E2) / file-ops (E3), cộng với **answer cuối** (E1); reward = outcome QA kết hợp tín hiệu nội tại từng operation (E2, E4, E6). Phải tách đo 3 tầng bank/retrieval/answer thì lỗi ghi mới không bị answer che (AN-014 F-P03). — *confidence: cao* · dựa trên E1, E2, E3, E6 + AN-014
- **F-T03**: **Về data base/mix: chất lượng > số lượng, và chống quên là bài toán chọn data, không phải bài toán tăng regularization**: 6B token curated ≈ 40B thô, không thấy catastrophic forgetting khi CPT đúng recipe (E10); chọn data theo Fisher thắng replay 10× token (E11); lý thuyết + thực nghiệm ICML: replay đổi xu hướng quên, regularization chỉ đổi tốc độ (E12); mix chủ động (44/24/21/11) để giữ capability cũ (E13); RL cũng quên và KL trên task hiện tại không cứu được (E14); model pretrained lớn + replay nhỏ là đủ (E15). — *confidence: cao* · dựa trên E10–E15 (6 nguồn độc lập, nhất quán)
- **F-T04**: **Train robustness bằng data tự sinh phải kèm cặp clean/injected, nếu không sẽ mất utility**: defense kiểu train gây drift phân phối — model từ chối bước hợp lệ trên task lành (E7); cách fix đã được chứng minh = self-distillation trên cặp cùng trajectory (E7) + environment mutation verifiable (E8). Liên hệ trực tiếp: attack suite của ta (DS-005/007/008, E21) chính là generator theo tinh thần này. — *confidence: trung bình-cao* · dựa trên E7, E8, E21
- **F-T05**: **Không nhất thiết phải train weights**: lớp luật deterministic theo lifecycle ontology **vượt Memory-R1 đã train** (76.9% vs 61–70.5%, confabulation halves — E16) và training-free vẫn cạnh tranh (E17). Trade-off: rule = kiểm soát được, không drift, dễ audit; learned = tổng quát hơn ngoài ontology. — *confidence: trung bình-cao* · dựa trên E16, E17 (+ E1 để so sánh cùng benchmark)
- **F-T06**: **Khuyến nghị cho SAGE** (kết hợp evidence + 8 demo nội bộ): nếu train thật → input = (a) cặp QA+bank sinh từ stream kiểu LongMemEval/LoCoMo (E1), (b) trajectory memory-op gắn reward = **KPI F1–F6 đã có sẵn dạng dense metric** (E21), (c) attack suite làm adversarial augmentation (E21 + E7); output = JSON contract `{op, key, content, citation_id, confidence, answer}` — giữ nguyên answer + citation + confidence như KPI hiện tại, thêm field `op` có nhãn. Trường hợp không train (điều kiện Kaggle CPU hiện tại): data = stream tổng hợp + attack suite, output = bộ luật + report như DS-008. — *confidence: trung bình* · dựa trên E1, E2, E21 (kết hợp literature + thực nghiệm nội bộ, chưa chạy train thật)

## 5. Khoảng trống / điều chưa rõ

- Chưa có "ImageNet của memory-training" — MemFactory (E6) mô tả ngành còn *fragmented và task-specific*; chưa rõ bộ data chuẩn nào để so sánh chéo.
- Số liệu Memory-R1/Fortunate Recall lấy từ abstract, chưa đọc full paper → chưa chắc reproductions/benchmark protocol.
- E4, E5, E17, E19, E20 mới ở mức snippet → confidence giảm một bậc cho các claims phụ thuộc riêng chúng.
- Chưa chứng minh được: data tổng hợp từ attack suite có chuyển hóa thành robustness thật khi train (chỉ có proxy là bộ luật thắng attack — DS-007/008).

## 6. Hướng kiểm chứng tiếp

**Có cần chạy Kaggle?** Có, tùy chọn — **DS-009 (candidate)**: sinh bộ dataset huấn luyện cho SAGE từ stream + attack suite: output `train_pairs.jsonl` (mỗi dòng = `{context, memory_bank, question, gold_op, gold_answer, citation}`) kèm thống kê (số cặp/op, tỷ lệ, độ lệch), KPI: ≥N cặp, phân bố op không lệch quá X%, gold lấy từ ground-truth stream (không hallucinate). Chạy CPU nhẹ, artifact về `out/ds009/`. Việc **train model thật** nằm ngoài điều kiện máy (cần GPU) → để separate, không nhận trong milestone hiện tại.
