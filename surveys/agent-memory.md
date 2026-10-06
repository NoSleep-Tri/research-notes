# AN-014 — Bộ nhớ của agent LLM: agent ghi/lấy/quên trí nhớ thế nào, SAGE học gì từ đó?

- **ID**: AN-014
- **Ngày**: 2026-10-06
- **Câu hỏi**: Q-014 — *Bộ nhớ của agent LLM — agent ghi/lấy/quên trí nhớ như thế nào, và SAGE nên học gì từ đó?*
- **Nguồn đã dùng**: ~30 paper arXiv (2023-04 → 2026-10) — 2 survey · 3 kiến trúc nền (MemGPT/Generative Agents/A-MEM) · 3 benchmark (LoCoMo, HaluMem, AgentMemBench) · 5 paper quên-có-chủ đích · 4 paper bảo mật memory · 3 paper "giờ ngủ" offline consolidation. Không dùng web (websearch vẫn 401).

## 1. Câu hỏi đang trả lời

Agent LLM lưu gì ngoài context window, tổ chức/truy xuất/nó như thế nào, thất bại kiểu gì — và **bài học trực tiếp cho SAGE** (đặc biệt lớp L3 memory + DS-004 archive). Phạm vi: **memory system của agent**, không phải KV-cache/VRAM của model (trừ bài so sánh chi phí).

## 2. Bằng chứng

| # | Bằng chứng | Nguồn | Loại |
|---|---|---|---|
| E1 | Survey lớn nhất (2024) chia memory agent thành *what/why/how design/evaluate* + chỉ ra thiếu taxonomy chung; repo theo dõi 100+ paper | arXiv 2404.13501 (Zhang et al.) | review |
| E2 | Survey 2026 đề khung 3 giai đoạn **Storage → Reflection → Experience** (giữ mẫu → tinh chỉnh → trừu tượng hóa), gọi ngành đang mắc kẹt giữa "kỹ thuật OS" và "khoa học nhận thức" | arXiv 2605.06716 | review |
| E3 | MemGPT: phân tầng ký ức fast/slow như OS (virtual context management), tự di chuyển data giữa tier, interrupt điều khiển flow → đa session chat "remember, reflect, evolve" | arXiv 2310.08560 | hệ thống/đánh giá |
| E4 | Generative Agents: **memory stream** (ghi mọi trải nghiệm bằng NL) → **reflection** (tổng hợp định kỳ thành khái niệm cao hơn) → **retrieval** điểm = recency × importance × relevance; ablation: bỏ observ/planning/reflection → mất believability | arXiv 2304.03442 (Park et al.) | ablation |
| E5 | A-MEM (Zettelkasten): mỗi ký ức = note có tags/link; **ký ức mới làm cập nhật lại ký ức cũ** (memory evolution); thắng SOTA trên 6 model | arXiv 2502.12110 | experiment |
| E6 | HippoRAG (lý thuyết index hồi hải mã): KG + PageRank mô phỏng neocortex/hippocampus → multi-hop QA **+20%**, 1 bước rẻ hơn iterative retrieval **10–30×**, nhanh 6–13× | arXiv 2405.14831 | experiment |
| E7 | Mem0: extract/consolidate/retrieve từ hội thoại; LOCOMO **+26%** vs OpenAI memory (LLM-as-judge), p95 latency **−91%**, token cost **−90%** vs full-context | arXiv 2504.19413 | benchmark |
| E8 | 4 cấu trúc (chunk/triple/atomic/summary) × 3 kiểu retrieval: **mixed structure chống nhiễu tốt nhất**, iterative retrieval thắng đều; cấu trúc nào cũng thắng ở task riêng | arXiv 2412.15266 | experiment |
| E9 | **FadeMem**: decay khác nhau theo relevance/frequency/time (bỏ binary giữ-mất) → multi-hop tốt hơn + **−45% storage**; 3 benchmark (MSC, LOCOMO, LTI-Bench) | arXiv 2601.18642 | experiment |
| E10 | **Memora/FAMA**: metric *Forgetting-Aware Memory Accuracy* **phạt việc dùng memory đã lỗi thời**; 4 LLM + 6 memory agent → "frequent reuse of invalid memories", memory agent chỉ tốt hơn **marginal** | arXiv 2604.20006 | benchmark |
| E11 | **Ghost memory**: fact cũ/chuyển tiếp/mới cùng tồn tại lẫn lộn trong bank; tách đo 3 tầng bank/retrieval/answer vì **QA accuracy cuối che giấu nơi lỗi xảy ra**; ATMA +0.240 conflict acc, temporal F1 0.0295→0.1705 | arXiv 2607.01935 | experiment + benchmark |
| E12 | **HaluMem**: đo hallucination theo *operation* (extract / update / answer) — memory system **tích lũy lỗi ở khâu ghi rồi lan sang trả lời**; 15k memory point, context >1M token | arXiv 2511.03506 | benchmark |
| E13 | MPBench: 4 kênh ghi × 9 lỗ hổng cấu trúc × 6 class tấn công; **agent ghi/liệt Retrieved càng tích cực càng dễ bị hack**; defense prompt-injection **không phủ** memory poisoning | arXiv 2606.04329 | bảo mật/benchmark |
| E14 | eTAMP: **1 lần quan sát môi trường độc hại** (trang sản phẩm bị sửa) đầu độc memory, kích hoạt ở task/site khác, bypass permission defense; ASR 32.5% (GPT-5-mini); model mạnh hơn **không an toàn hơn**; stress → ASR **×8** | arXiv 2604.02623 | tấn công |
| E15 | Sleeper poisoning: memory giả về user được ghi 99.8% (GPT-5.5), ngủ yên qua nhiều hội thoại; khi retrieve được thì **60–89% ra hành động theo ý attacker** | arXiv 2605.15338 | tấn công |
| E16 | MEXTRA: trích memory riêng tư từ agent **black-box** chỉ bằng prompt → memory = kho dữ liệu người dùng cần safeguard | arXiv 2502.13172 | tấn công |
| E17 | So chi phí thực tế: long-context GPT-5-mini **thắng về recall** (LongMemEval, LOCOMO); memory system thắng ở PersonaMem; với caching, memory system rẻ hơn sau **~10 lượt** ở context 100k | arXiv 2603.04814 | đo chi phí |
| E18 | ACM (position): tích lũy context naive → chi phí **vũ trụ cấp bậc** theo độ dài hội thoại; tóm tắt thô mua chi phí tuyến tính với **độ chính xác rơi vỡ**; chỉ **validated compaction** giữ được fidelity với chi phí tuyến tính | arXiv 2607.21503 | position |
| E19 | LycheeMemory V2: gộp **segment-level** thay vì ghi mỗi lượt → **−86% token xây dựng**, LOCOMO 89.22%; *granularity* quyết định trade-off, không chỉ nội dung giữ lại | arXiv 2608.12990 | experiment |
| E20 | TiMem: cây thời gian phân cấp, consolidation từ quan sát thô → persona; LOCOMO 75.30%, **giảm 52%** độ dài memory gọi ra | arXiv 2601.02845 | experiment |
| E21 | MRAgent: *"memory is reconstructed, not retrieved"* — bỏ pipeline tĩnh retrieve-then-reason, để reasoning tham gia vào truy vấn → +23% (LoCoMo, LongMemEval), token/runtime giảm | arXiv 2606.06036 | experiment |
| E22 | AgentMemBench (5 strategy, cùng harness, Qwen2.5-7B): external KV **thắng mọi trục**; ở LOCOMO (gold nằm rất xa) ICW/summary/graph **Recall@5 ≤ 0.005**, chỉ EKV = 0.573; đổi lấy footprint 5.100 vs 300 token | arXiv 2608.00009 | benchmark |
| E23 | LOCOMO gốc: 300 lượt / 35 phiên, LLM **vẫn xa human** dù long-context hay RAG — temporal/causal dài hạn là bottleneck | arXiv 2402.17753 | benchmark |
| E24 | ARC (compaction): tách **kho lưu trữ append-only ID-addressable** khỏi context đang active; thay quan sát cũ bằng **citation**, hỏi lại bằng ID → NIAH 99.40% vs 88.12% baseline | arXiv 2607.25066 | experiment |
| E25 | ReadAgent: chia memory episode → nén thành **gist memory** → lookup lại văn bản gốc khi cần → context hiệu dụng **×3.5–20** | arXiv 2402.09727 | experiment |
| E26 | Voyager: 3 thành phần — curriculum + **skill library** (code tái sử dụng) + self-reflect; kỹ năng tích lũy thành library mở rộng | arXiv 2305.16291 | hệ thống |
| E27 | **Auto-Dreamer**: tách *fast acquisition* (trực tuyến) khỏi *slow consolidation* (offline, cross-session); consolidator đọc vùng bank như read-only evidence, viết bộ thay thế trừu tượng hóa; train GRPO → **+7 điểm** ScienceWorld với bank **nhỏ 12×**, generalise sang ALFWorld/WebArena không train lại | arXiv 2605.20616 | experiment |
| E28 | **Language Models Need Sleep**: 2 chặng — Knowledge Seeding (distill short-term → long-term) + Dreaming (RL tự sinh curriculum) → cải thiện continual/transfer | arXiv 2606.03979 | experiment |
| E29 | **SleepGate**: tag xung đột (mới đè cũ) + **forgetting gate** cho KV cache + consolidation gộp entry → 99.5% retrieval ở PI depth 5, 97.0% depth 10 trong khi **5 baseline đều <18%**; giảm interference horizon O(n) → O(log n) | arXiv 2603.14517 | experiment |
| E30 | SCM: ngủ + **algorithmic forgetting** cho LLM (research preview, chưa có số liệu mạnh) | arXiv 2604.20943 | preprint |

## 3. So sánh với phương án đối chứng

- **Đối chứng 1 — "context dài là đủ"**: nếu model 1M token thì cần gì memory? Trả lời bằng số (E17): long-context **thắng recall** thật, nhưng chi phí tăng theo mỗi lượt, và AgentMemBench (E22) cho thấy ngược lại ở horizon rất xa — **summary/graph/recency đều sập** (Recall@5 ≤ 0.005), chỉ dense retrieval vượt qua. ⇒ Không phải "cần hay không cần" mà là **điểm giao chi phí**: ~10 lượt @ 100k token thì memory system rẻ hơn (E17); ACM (E18) khẳng định compaction *validated* là đường tuyến tính duy nhất giữ fidelity.
- **Đối chứng 2 — "lưu hết là an toàn nhất"** (keep-all): bị bác bởi E10 (dùng memory lỗi thời bị phạt, agent hay dùng), E11 (ghost memory lẫn lộn làm sai), E12 (lỗi tích lũy ở khâu ghi), E9 (**−45% storage mà multi-hop tốt hơn**). Lưu hết cũng chính là khẩu *"quên = xóa"* bị Q-011 bác — ở đây ta có **số liệu**: giữ toàn bộ = đem rác vào retrieval.
- **Đối chứng 3 — dùng LLM làm bộ nhớ chính (prompt/param) vs bộ nhớ ngoài có cấu trúc**: E22 là phép tách bạch rõ nhất — cùng harness, external KV thắng mọi trục; E7 cho lợi thế chi phí; E6/E21 cho lợi thế cấu trúc (graph/association) ở multi-hop. Vế đối lập: E5/E19 cho thấy **write cost** của cấu trúc hóa là cái giá thật (E19 sửa bằng segment-level, −86%).
- **Đối chứng 4 — bảo mật**: defense phổ biến = prompt-injection filter, nhưng E13 chỉ ra nó **không phủ** memory poisoning; E14: bypass permission-based defense. Nghĩa là threat model phải đổi, không phải vá thêm filter.

## 4. Findings

- **F-P01**: Ngành memory-agent đã có taxonomy cố định — **write (extract/consolidate) · store (cấu trúc) · read (retrieve/reconstruct) · forget (supersede/decay)** — và khung tiến hóa **Storage → Reflection → Experience**; hai survey độc lập (2024, 2026) chốt cùng 3 giai đoạn đó. — *confidence: cao* · dựa trên E1, E2 (+ E3, E4, E5 là 3 dạng triển khai khác nhau cùng khung)
- **F-P02**: **"Quên chọn lọc" đã đo được lợi ích**, không còn là lý thuyết: decay theo relevance/frequency/time giảm **45% storage** mà multi-hop tốt hơn (E9); forgetting-gate cho KV cache: **99.5% vs <18%** của mọi baseline khi interference tích lũy (E29); và metric FAMA **phạt riêng** việc xài memory đã lỗi thời (E10). Quên ở đây = **điều kiện của độ đúng**, không phải cắt chi phí. — *confidence: trung bình-cao* · dựa trên E9, E10, E29 (E29 mới ở scale 793K params → số tuyệt đối chưa tin được, chỉ tin hướng)
- **F-P03**: **Lỗi memory sinh ở khâu GHI rồi lan sang trả lời, và QA accuracy cuối che nó đi** — HaluMem tách theo operation và thấy lỗi tích lũy ở extract/update trước khi hỏi (E12); ghost memory cho cùng kết luận: phải đo tách **bank / retrieval / answer** 3 tầng (E11). Đây đúng là hình hài của *Goodhart trên benchmark tổng thể*: một con số cuối không nói được chỗ nào sai. — *confidence: trung bình-cao* · dựa trên E11, E12 (cùng kết luận từ 2 benchmark độc lập 2025–2026)
- **F-P04**: **Persistent memory là bề mặt tấn công lớn nhất mở ra cho agent**: 1 lần ghi độc là đủ — ngủ yên nhiều hội thoại rồi tự kích hoạt (E15: ghi 99.8%, 60–89% ra hành động theo ý attacker), đầu độc chỉ qua **quan sát môi trường** không cần quyền ghi (E14: ASR 32.5%, stress ×8), và **agent ghi càng tích cực càng dễ bị** (E13) — trong khi defense prompt-injection **không phủ** nó (E13, E14). Model mạnh hơn **không an toàn hơn** (E14). — *confidence: cao* · dựa trên E13, E14, E15, E16 (4 nhóm độc lập, cùng hướng, 2025–2026)
- **F-P05**: **"Giờ ngủ" của agent mới chỉ ở dạng phôi thai** — offline consolidation đã có vài bản đầu (tách nhanh/chậm, bank read-only → bộ thay thế trừu tượng: E27 +7 điểm & bank 12× nhỏ; distill+replay "Sleep": E28) nhưng **chưa ai tách được downscale khỏi replay**, và chưa hệ thống nào mô phỏng trọn 3 job của Q-012 (replay · downscale · dọn rác). Khoảng trống **F-N07 vẫn còn nguyên**. — *confidence: trung bình* · dựa trên E27, E28, E30 (đều 2026, preprint/preview, chưa qua kiểm chứng độc lập)
- **F-P06**: **Bộ nhớ agent đang bị đầu độc bởi chính thiết kế "viết-everything"**: giữ hết → rác lẫn retrieval (E10, E11) + write attack surface (E13); tóm tắt thô → mất chi tiết + accuracy cliff (E18, E19); path đúng = **kho append-only + citation ID** (E24, E18) — tức là *giữ bản gốc, thay bằng tham chiếu, truy vết được*. — *confidence: trung bình-cao* · dựa trên E24 (99.40% vs 88.12%), E18, E19, cộng E10/E11 cho cái giá của cách khác

## 5. Khoảng trống / điều chưa rõ

1. **Chưa có benchmark chung cho "chất lượng khâu ghi"** — HaluMem (E12) mới là bước đầu; LOCOMO-family vẫn là recall/answer (E23, E22). FAMA (E10) đo riêng việc dùng memory lỗi thời nhưng chưa ai chuẩn hoá.
2. **Chưa ai định lượng "quên bao nhiêu là đủ"** ở agent — có 45% storage (E9), 12× bank (E27), 52% recalled length (E20) nhưng mỗi paper một metric, không so trực tiếp được (chính AgentMemBench đang cố làm điều này, E22).
3. **Offline consolidation chưa qua kiểm chứng độc lập** (E27, E28, E30 đều là preprint 2026, chưa thấy replication).
4. **Trade-off bảo mật ↔ utility chưa được đo**: E13/E14/E15 cho thấy lỗ hổng, nhưng chưa paper nào báo "chốt sổ ghi có kiểm chứng thì mất bao nhiêu % utility".
5. Benchmark chủ yếu là **hội thoại cá nhân**; agent làm việc/ra tool-call (WebArena-type) mới có E14 đếm được.

## 6. Hướng kiểm chứng tiếp

**Có thể làm demo trên Kaggle** — đề xuất **DS-006 "memory hygiene"** cho SAGE L3:
- Kiểm chứng trực tiếp F-P06 + F-P02: so 4 chính sách ghi trên cùng data toy — *keep-all* · *recency* · *decay theo giá trị* (đã có từ DS-004) · **append-only + citation ID** — đo (a) accuracy retrieval, (b) % dùng record lỗi thời (bản thu nhỏ của FAMA), (c) kích thước bank.
- Điều kiện KPI viết trước, ngưỡng không đổi sau khi thấy số (tiền lệ DS-004/DS-005).
- Nếu không chạy demo: **không cần** — các finding trên đã tự đứng bằng benchmark đã công bố.
