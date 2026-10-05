# AN-010 — Attention: van chọn lọc của não và của Transformer

- **Ngày**: 2026-10-06 · **Câu hỏi**: [Q-010](../questions/Q-010.md)
- **Phương pháp**: **arXiv MCP** (8 truy vấn, ~20 paper) + **webfetch** 2 trang Wikipedia gốc (*Attention*, *Cocktail party effect*).
- **Kết luận ở 1 dòng**: ***Chỉ cùng tên, khác bản chất ở 4 chiều*** — nhưng **cùng hình dạng lỗi ở 2 chiều**. Não: attention là **cạnh tranh nguồn lực hữu hạn dưới một mục tiêu ngoài**; Transformer: attention là **phép tính truyền tin, không giới hạn, không có mục tiêu nào trong đó**. Não **bị** giới hạn focus (3–6 mục) và **được thưởng phạn ngoài**; Transformer **không giới hạn** nhưng **không có gì để tập trung vào**. ⇒ Bài học quan trọng nhất: **giới hạn tài nguyên là tính năng của não, không phải lỗi** — và LLM đang trả giá vì mất nó.

---

## 1. Não: attention là *cạnh tranh*, không phải *phép tính*

| Thuộc tính | Não | Nguồn |
|---|---|---|
| **Định nghĩa James 1890** | *"taking possession by the mind … of one out of what seem several simultaneously possible objects"* → **chọn 1 trong nhiều** | *Attention* |
| **Tài nguyên** | **Hữu hạn & chung một pool** (Kahneman 1973 *Attention and Effort*): 1 pool trung tâm, tổng dung lượng có trần | *Cocktail party*, *Attention* |
| **Số lượng** | **3–6 mục** trong tiêu điểm ý thức (Wundt 1890 → còn giữ sau 130 năm) | *Attention* |
| **Không gian vật lý** | **3–4 vật thể** giữ được cùng lúc (Jevons 1871, "marbles") | *Attention* |
| **Loại** | selective · sustained · divided · alternating · orienting — **nhiều hệ, không phải một** | *Attention* |
| **Kiểm soát** | **top-down** (FEF/vPFC/basal ganglia) **vs bottom-up** (V1 → superior colliculus) — **hai hệ tách biệt** | Posner & Petersen 1990 |
| **Bất đối xứng** | exogenous (tự động) **có thể bỏ qua**; endogenous (ý chí) **không** — và hiệu ứng đảo chiều sau ~300ms (inhibition of return) | Posner & Cohen 1984 |
| **Chọn lọc ở đâu?** | **Tranh luận cũ chưa chốt**: Broadbent (filter sớm) vs Treisman (attenuation) vs Deutsch-Norman (lọc 2 tầng) — bằng chứng tên riêng vẫn lọt qua mọi filter | *Cocktail party* |
| **Phát hiện ngoài ý muốn** | tên riêng, từ cấm, chữ "fire" **vẫn nhận ra** ở kênh không nghe → lọc **không** phải chặn cứng | Cherry 1953; Wood & Cowan 1995 |
| **Hệ thần kinh** | gamma 40–60Hz + **coupling tầm xa** (PF–visual cortex, *Science* 2009) | *Attention* |
| **Tự động hóa** | kỹ năng luyện >100% chính xác → chạy **không cần** attention (Morse) | Dougherty & Johnston 1996 |

**Bốn thành phần tối thiểu (Knudsen 2007)**: working memory · competitive selection · top-down sensitivity control · **salience filter**.
→ Lưu ý: **cả 4 đều là "mục tiêu + đối thủ"**. Não không có attention trung tính.

---

## 2. Transformer: attention là *phép tính*, không phải *cạnh tranh*

| Thuộc tính | Self-attention | Nguồn |
|---|---|---|
| **Bản chất** | `softmax(QKᵀ/√d)·V` — **phép truyền tin có trọng số**, chuẩn hoá hàng (softmax ⇒ tổng = 1) | định nghĩa |
| **Đơn vị** | **token** (discrete, có ranh giới rõ) — *không* có "mục" như não | — |
| **Không giới hạn** | mọi token đều nhận trọng số ≠ 0 ⇒ **không có "ẩn"**; nhưng **hiệu quả thực tế** bị giới hạn nặng | §3 |
| **Không có mục tiêu** | attention head **không biết** mình nên tìm gì; ý định đến từ loss, không từ kiến trúc | arXiv:2310.20307 |
| **Giải thích?** | **KHÔNG** — Jain & Wallace 2021: attention weight **không tương quan** gradient importance; kể cả khi tương quan, **con người không ra quyết định tốt hơn** khi có nó | 2201.11194 |
| **Vị trí** | phải **chèn tay**: RoPE/ALiBi; ngoài giới hạn train ⇒ **suy giảm** | 2405.14591, 2312.17044 |
| **Attention sink** | token (thường là BOS) **nhận attention khổng lồ dù vô nghĩa** — hiện diện **ở mọi model**, **mọi input**, **cả model nhỏ**; sinh ra **sau khi** pretraining đủ data | 2410.10781 |
| **Sinh kiến trúc** | có **secondary sink** ở lớp giữa, sống **biến thiên** theo lớp (11 họ model) | 2512.22213 |
| **Học mẫu hình** | attention pattern **xuất hiện đột ngột** trong quá trình train (first-order phase transition; linear attention → second-order rồi liên tục) | 2606.12058 |

---

## 3. Chỗ **cùng hình dạng lỗi** — cả hai đều "quên giữa chuỗi"

| Hiện tượng | Não | Transformer |
|---|---|---|
| **Serial position: đầu & cuối mạnh hơn, giữa yếu** | **primacy + recency effect** — chuẩn của trí nhớ tự do (Murdock 1962) | **lost-in-the-middle**: hiệu năng giảm rõ khi thông tin ở *giữa* context dài (2307.03172) |
| **Cơ chế?** | **chưa rõ** | **không phải "mất thông tin"** — U-curve **tự xuất hiện** khi train trên 2 paradigm nhớ (dài hạn vs ngắn hạn); **primacy là hệ quả** của uniform-loss, recency là chủ đích | 
| **Source** | *Attention*, *Cocktail party* (serial position chưa trích ở đây — đánh dấu chưa verify) | 2510.10276 — chứng minh bằng **train từ đầu trên GPT-2/Llama** |

⇒ **Đây là cái rẻ nhất và mạnh nhất**: cùng một đường cong U ở hai hệ thống, nhưng **hai cơ chế khác nhau**. Não: giả định "thông tin đầu/cuối là quan trọng hơn" là **sinh học**; LLM: U-curve là **học được từ phân bố loss** ⇒ **có thể sửa bằng dữ liệu, không phải bằng kiến trúc**.

---

## 4. Bảng so sánh 8 chiều

| # | Chiều | Não | Transformer | Cùng hay khác? |
|---|---|---|---|---|
| 1 | **Đơn vị** | mục vật thể / đặc tính / đối tượng (mờ, biên không rõ) | **token** rời rạc, biên rõ | ❌ khác hẳn |
| 2 | **Tài nguyên** | **hữu hạn**, 1 pool chung, 3–6 mục | **vô hạn về lý thuyết**, chỉ giới hạn *hiệu quả* | ❌ khác hẳn |
| 3 | **Mục tiêu** | **có sẵn** (drive, phần thưởng, nhiệm vụ) — top-down | **không có** — attention chỉ phản ứng Q/K | ❌ khác hẳn |
| 4 | **Đối thủ** | có **cạnh tranh thật** (lateral inhibition, top-2 quyết định) | **softmax đã chuẩn hoá** — không cạnh tranh, chỉ chia sẻ | ❌ khác hẳn |
| 5 | **Thứ tự (position)** | **sinh học** (retinotopy, đồng tâm) — không cần học | **phải chèn** (RoPE), ngoài range thì hỏng | ⚠️ cùng *vấn đề* (giữa chuỗi yếu), khác *nguyên nhân* |
| 6 | **Lọc ngoài ý muốn** | **có** — tên riêng lọt qua mọi filter | **không có khái niệm** "lọc ngoài ý muốn" | ❌ chỉ có một bên |
| 7 | **Hình dạng lỗi** | U-curve (primacy/recency) | U-curve (lost-in-middle) | ✅ **cùng** |
| 8 | **Đo được?** | khó (cần EEG/fMRI, gián tiếp) | attention weight **dễ lấy** nhưng **không phải giải thích** | ✅ cùng *bẫy đo lười* |

---

## 5. Cùng tên / khác cơ chế và ngược lại

**Cùng tên, khác bản chất (nguy hiểm nhất khi mượn):**
- "Attention" ở Transformer là **một phép toán**. Ở não là **một cuộc cạnh tranh giữa các ứng viên, dưới tài nguyên hữu hạn, có mục tiêu, có đối thủ**. → Câu *"attention với 32 head giống não"* là **sai ở 4/5 điểm**.
- "Context" ở Transformer = chuỗi token. Ở não = **ý thức hiện tại + working memory** — nhỏ hơn nhiều, và **bị ghi đè liên tục**, không phải băng video.

**Cùng cơ chế, khác tên:**
- **Sparsity + chọn lọc** — não: lateral inhibition + top-2 winner-take-all; Transformer: attention softmax tạo trọng số thưa. Khác cách hiện thực, cùng chức năng **lọc nhiễu**.
- **Vòng lặp đóng vòng** — não: FEF ↔ sensory cortex (tăng gain vùng đang để ý); Transformer: **residual + layer norm** — tăng gain token đã "được chú ý". Cùng nguyên lý, một bên là sinh học, một bên là hệ số scale.
- **Inhibition of return** (Posner 1984) ≈ **recency bias** trong chuỗi context. Cùng chữ ký: *đã dùng rồi thì giảm ưu tiên*.

**Chỉ một bên có:**
- ✅ **Không đối xứng bất biến** — não: không thể bỏ qua exogenous cue; LLM: hoàn toàn đối xứng với token.
- ✅ **Attention sink / no-op token** — Transformer **tự sinh** token lỗ hổng để đổ attention (2410.10781); não **không** có token nào để "đổ".
- ✅ **Attention tốn tài nguyên thật** — não: 20W, ngủ bắt buộc, gián đoạn = tổn thất; Transformer: gần như miễn phí ⇒ **không có cơ chế buộc phải nghỉ**.

---

## 6. Bốn lỗi chung (có bằng chứng)

| # | Lỗi | Não | Transformer | Bằng chứng |
|---|---|---|---|---|
| A1 | **Bỏ sót phần giữa chuỗi** | U-curve serial position | lost-in-the-middle | 2307.03172; 2510.10276 |
| A2 | **Lọc sai → mất thông tin quan trọng** | bỏ tên riêng (tưởng chỉ nghe 1 kênh nhưng vẫn nhận) | bỏ constraint ở giữa prompt | *Cocktail party*; 2502.12352/2507.18742 (spec self-correction) |
| A3 | **Không có ý thức giới hạn của mình** | không biết mình đang bỏ sót (inattentional blindness) | attention weight cho cảm giác "đã xét hết" nhưng thực tế chưa | AN-008 D7; AN-002 (ý thức đến sau) |
| A4 | **Càng dài càng tệ** | working memory 3–4 mục, task-switching tốn 1–2s | context dài → **catastrophic degradation** ở ngưỡng | Kahneman 1973; 2601.15300, 2606.29718 (context rot) |

---

## 7. Bảng "mượn được / không mượn được" → cho thiết kế agent

| Nguyên lý não | Mượn được? | Bằng chứng | Hàm động cho agent |
|---|---|---|---|
| **Giới hạn focus là feature** | ⚠️ chỉ gián tiếp | test-time compute **có trần**: CoT dài hơn **giảm** hiệu năng ở một số domain | 2502.18080 → **giới hạn budget theo domain**, đừng scale mù |
| **Working memory nhỏ, có cửa sổ trượt** | ✅ | đây chính là RAG / context window management | thiết kế scaffold (SAGE L1/L2) |
| **Ưu tiên = top-down từ nhiệm vụ** | ⚠️ chưa có cơ chế | LLM head không biết mục tiêu | **prompt/plan làm top-down** — không có nó thì chỉ bottom-up |
| **Attention sink như van xả áp lực** | 🟡 chưa hiểu | sink sinh ra ở mọi model, chưa rõ chức năng | **chưa nên mượn** — xem khoảng trống #3 |
| **Inhibition of return** | 🟡 | recency bias của LLM là hiện tượng **cùng dạng** nhưng **khác cơ chế** | đừng gọi là "giống não" |
| **Đa kênh độc lập (cocktail party)** | ❌ sai bản chất | não tách **stream âm thanh**; LLM chỉ có 1 dòng token | phải **xây** multi-stream, không phải bật lên |
| **Attention = không phải giải thích** | ✅ **rất quan trọng** | Jain & Wallace 2021 | **không** dùng saliency map làm cơ sở quyết định → đúng P2 của SAGE (external verification) |
| **Suy hao khi dùng nhiều** | ⚠️ | não: 20W + ngủ; LLM: latency không tự làm nghỉ | cần **nghỉ có chủ đích** cho agent dài hạn |

---

## 8. Myth cần loại bỏ

| # | Myth | Thực tệ | Nguồn |
|---|---|---|---|
| M1 | "Attention 32 head ≈ attention của não" | Khác ở **4/5** chiều: đơn vị, tài nguyên, mục tiêu, đối thủ | §4 |
| M2 | "Attention weight là giải thích" | **Không tương quan** gradient importance; **và** khi có nó người dùng **ra quyết định kém hơn** | 2201.11194 (Jain & Wallace) |
| M3 | "Lỗi lost-in-the-middle là do giới hạn cửa sổ" | **Không** — U-curve tự xuất hiện khi train trên paradigm nhớ; **primacy là hệ quả**, recency là chủ đích | 2510.10276 |
| M4 | "Cứ cho context dài hơn là tốt hơn" | có **ngưỡng** hỏng; CoT dài có thí giảm hiệu năng | 2601.15300; 2502.18080 |
| M5 | "Attention sinh ra là do mô hình tự chọn" | **sinh ra** sau pretraining đủ data; ở **mọi model kể cả nhỏ** | 2410.10781 |
| M6 | "Não cũng bị bottleneck context y hệt" | Não có bottleneck **sinh học** (năng lượng); LLM bị bottleneck **thuật toán** (softmax, position) — **hỏng chỗ khác nhau** | §4 |

---

## 9. Khoảng trống research

1. **Attention sink là gì?** — token lỗ hổng dùng để *đổ* attention; 2410.10781 mô tả **khi nào** sinh ra nhưng **không** trả lời **tại sao cần**; 2512.22213 tách secondary sink ở lớp giữa. **Câu hỏi mở lớn nhất của Q-010.**
2. **Serial position ở người — chưa verify trong survey này** (Murdock 1962, Shapiro 1997 "own-name attentional blink"): cần lấy nguồn gốc thay vì suông. *Chỉ giữ ở mức giả thuyết.*
3. **Không có thí nghiệm nào đo "top-down attention" trong LLM** — người ta dùng prompt như top-down, nhưng chưa có paper tách được ảnh hưởng của "mục tiêu" khỏi "prompt dài hơn".
4. **So sánh định lượng U-curve hai hệ** — có U-curve cả hai, nhưng **chưa có** nghiên cứu nào đặt chúng **cùng trục số** (vị trí/độ dài chuẩn hoá, độ mờ đường cong). Đây là khoảng trống *đo lường* — cùng dạng với F-C01 (không có máy đo ý thức) và "không có benchmark đáng tin" của AN-006.
5. **Giới hạn ngưỡng context** — 2601.15300 nói có "critical threshold" nhưng **ngưỡng có phụ thuộc vào task không?** Chưa rõ. Nếu có → phải thiết kế budget **theo nhiệm vụ**, không phải theo model.
6. **Không biết có tương đương não của "inhibition of return"** không — recency bias ở LLM có phải hiện tượng học được từ dữ liệu, hay hệ quả của **causal mask**? Chưa tách được → **đây là lý do M5/M6 ở §8 chưa đóng**.
7. **Test-time compute vs attention**: latent reasoning (2502.05171, không cần token) cho thấy **tư duy không cần ngôn ngữ** — nhưng **không ai** so sánh trực tiếp với System 2 của não (cũng không cần ngôn ngữ). Khoảng trống liên ngành.

---

## 10. Hướng kiểm chứng tiếp

- **Chạy được trên Kaggle (CPU)**: **đo đường cong U** — mô phỏng "lost-in-the-middle" bằng một model nhỏ (char-level) với thông tin đặt ở các vị trí khác nhau, rồi đo accuracy theo vị trí. Kiểm chứng **trực tiếp** 2510.10276 bằng code nhỏ. Đây là acceptance test D6 tiềm năng cho **DS-002**.
- **Cần LLM lớn / người**: phần so sánh định lượng với não; serial position ở người.
- **Không cần gì** cho phần lý thuyết.

## 11. Nguồn

- **arXiv (MCP, abstract trực tiếp)**: 2201.11194 (Jain & Wallace — attention ≠ explanation) · 2307.03172 (lost-in-the-middle gốc) · **2510.10276 (U-curve là học được từ loss)** · 2410.10781 (attention sink phổ quát) · 2512.22213 (secondary sink) · 2606.12058 (phase transition copy head) · 2601.15300 (ngưỡng context) · 2606.29718 (context rot) · 2502.18080 (thinking-optimal scaling — CoT dài có thể giảm hiệu năng) · 2502.05171 (latent reasoning) · 2405.14591 & 2312.17044 (RoPE / length generalization) · 2507.19595 & 2608.15459 (survey efficient attention) · 2310.20307 (causal interpretation) · 2407.07011 & 2209.11895 (induction heads).
- **webfetch — Wikipedia gốc**: *Attention* (James 1890, Wundt 3–6 mục, Jevons 1871 3–4 marbles, Kahneman 1973 pool, Knudsen 2007 4 thành phần, Posner & Petersen 1990 top-down/bottom-up, inhibition of return, gamma 40–60Hz, Morse automaticity, Maslach 1998) · *Cocktail party effect* (Cherry 1953, Broadbent filter, Treisman attenuation, Deutsch-Norman 2 tầng, Kahneman capacity, Moray 1959, Wood & Cowan 1995 tên riêng, Bee & Micheyl 2008 động vật).
- **Nội bộ**: AN-002 (ý thức đến sau → loại bỏ A3) · AN-004 (3 hệ cảnh báo, top-down) · AN-006 (evaluation yếu → khoảng trống #4) · AN-008 §D7 (không có root access) · DS-001 P2 (external verification → dùng M2 làm cơ sở).