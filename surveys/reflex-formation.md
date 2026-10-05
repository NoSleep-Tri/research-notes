# AN-005 — Cách hình thành phản xạ (Survey)

- **Ngày**: 2026-10-06 · **Câu hỏi**: [Q-005](../questions/Q-005.md)
- **Kết luận ở 1 dòng**: *Phản xạ **không phải dây có sẵn** — nó được **lắp ráp** (development), **bị gỡ** khi vỏ não trưởng thành (Babinski/Moro), **học được ngay tại chỗ** (Aplysia, tủy sống), **được cài mới** vào tiểu não (conditioning), và mọi phản xạ đều **điều tiết theo trạng thái** — tầng "ý thức → tự động" chỉ là đoạn cuối của cùng một phổ.*

---

## 1. Khung: 5 quá trình của "hình thành phản xạ"

```
P1 · LẮP RÁP CIRCUIT (phát triển)     axon guidance + tín hiệu từ cơ quan mục tiêu
                                        → Ia afferent khớp đúng α-motor neuron
P2 · GỠ BỎ (maturation)               vỏ não lớn dần ức chế reflex bẩm sinh
                                        → Babinski mất ~12 tháng, Moro ~6 tháng
P3 · HỌC TẠI CHỖ (synapse phản xạ)    habituation / sensitization / conditioning
                                        → Aplysia (Kandel); tủy học độc lập não (RIKEN)
P4 · CÀI PHẢN XẠ MỚI (conditioning)   eyeblink → ghi vào tiểu não (interpositus)
P5 · TỰ ĐỘNG HÓA (habit)              hành vi ý thức lặp → bán phản xạ (striatum)
⊗  LỚP ĐIỀU TIẾT                     presynaptic inhibition + descending modulation
                                        → cùng 1 phản xạ, biên độ khác nhau theo trạng thái
```

---

## 2. Findings

### F-01 · Circuit phản xạ được **lắp ráp có chọn lọc** — không phải dây cắm sẵn
- **Bằng chứng**: phản xạ duỗi gân (stretch reflex) đòi hỏi **tính đặc hiệu** của nối synapse đơn突触: sợi Ia từ cơ proprioceptor nào phải khớp đúng motor neuron của **chính cơ đó** (review *Development of the monosynaptic stretch reflex circuit*, Chen & Hippenmeyer 2003). Chi tiết cơ chế: **neuregulin-1 do chính sợi afferent Ia tiết ra** → thụ thể ErbB trên cơ — cơ xương được "chỉ định" biệt hoá thành spindle *nhờ* innervation cảm giác (Wang et al. 2012, PMC3434619) — hai bên dựng nhau qua lại.
- **Ý nghĩa**: "cái gõ là búa, cái đinh là đinh" **được build**, không phải mặc định.
- **Confidence: TRUNG BÌNH-CAO** (mạnh ở model chuột/gà; wiring program đầy đủ **ở người** chưa có — xem gap G1)

### F-02 · Phản xạ bẩm sinh **hoạt động ngay** và là điều kiện sống còn
- **Bằng chứng**: suck, rooting (quay đầu tìm ti), Moro (giật mình ôm), palmar grasp (nắm chặt), stepping (bước) — có từ lõi thai/sơ sinh, theo thứ tự dự đoán được; thiếu hoặc lệch bên = dấu thần kinh bệnh lý.
- Chúng **bảo thủ tiến hóa** (có ở mọi loài có thú) — nối [AN-003](survival-knowledge.md) F-03.
- **Confidence: CAO**

### F-03 · Nhiều phản xạ **mất đi khi lớn** — "hình thành" có nghĩa cả **bị gỡ**
- **Bằng chứng**: Babinski (ngón trỏ duỗi) biến mất **~12 tháng** → thay bằng gấp lòng bàn chân (dấu Babinski **tái xuất** ở người lớn = dấu **MNN** — mất vỏ não ức chế); Moro ~**6 tháng**; palmar grasp ~1 năm; tonic neck ~6 tháng. Persist quá tuổi = cảnh báo rối loạn vận động.
- Cơ chế: **cortex trưởng thành ức chế** dần subcortical/spinal — chương trình cũ bị "uninstall" khi chương trình cao cấp online.
- **Confidence: CAO** (mốc tuổi: TB-cao, có biến thiên giữa trẻ)

### F-04 · Phản xạ **học được ngay tại synapse của chính nó** (Aplysia — Nobel 2000)
- **Bằng chứng** (Kandel, gill-withdrawal):
  - **Habituation** (lặp stimulus → phản xạ yếu đi): **homosynaptic depression** — giảm **số lượng tử (quanta)** neurotransmitter giải phóng tại synapse cảm giác→vận động (quantal analysis, PMC434028).
  - **Sensitization** (sốc mạnh → phản xạ mạnh lên): serotonin → **cAMP → PKA** → phosphorylate kênh K⁺ ( kéo dài action potential, tăng giải phóng) — **ngắn hạn** không cần gen mới.
  - **Dài hạn**: qua **CREB → tổng hợp protein + mọc synapse** → giữ **>3 tuần** (Nature 1989; Science 1987) — *ngắn hạn → dài hạn là dải liên tục, tăng luyện → tăng bền*.
- **Ý nghĩa**: "học" không cần não lớn — **ngay 1 synapse duy nhất** cũng đủ.
- **Confidence: CAO**

### F-05 · **Tủy sống học độc lập não** — không chỉ truyền
- **Bằng chứng**:
  - RIKEN (Takeoka lab, 2024): circuit tủy **adaptive motor learning** — chi "quên" cách chống lực co cứng rồi **học lại** được ngay cả khi **tách khỏi não** (*Neural circuitry in the spinal cord allows brain-independent motor learning*).
  - Chuẩn bị tủy cắt ngang (thoracic transection) vẫn biểu hiện **habituation, sensitization, conditioning kiểu Pavlovian & instrumental** (review PMC3946174; behavioral studies PMC10391333).
- **Confidence: CAO** (động vật) · **TB-CHO người** (tương ứng chức năng chưa đủ)

### F-06 · Phản xạ **mới** (conditioned) được **cài vào tiểu não**
- **Bằng chứng**: eyeblink conditioning (chuông + puff mắt) — **hồi interpositus** của tiểu não **cần thiết cho acquisition, retention và long-term retention**; **không** thay bằng hippocampus (delay paradigm); **olive dưới (inferior olive)** = đường US qua **climbing fiber**; ghi kích thích interpositus → phản xạ có điều kiện xuất hiện không cần stimulus (*Neurobiol Learn Mem* review; PMC2751661).
- ⇒ Kho "**búa mới**" được lắp vào circuit tiểu não–brainstem, tách khỏi circuit gốc.
- **Confidence: CAO**

### F-07 · Phản xạ **không cố định** — biên độ đổi theo trạng thái, và **mất tầng điều tiết → phóng đại**
- **Bằng chứng**:
  - **Gating segmental**: **presynaptic inhibition** điều trực tiếp sợi afferent — **Jendrassik maneuver** (kẹp tay, nghiến răng) **tăng** H-reflex (cơ chế: giảm presynaptic inhibition / đổi input resistance motor neuron); **motor imagery** + Jendrassik thay đổi biên H-reflex kèm gating EEG (biorXiv 2025).
  - **Mất descending modulation**: sau **chấn thương tủy** — "spinal shock" (reflex mất) → vài tuần–tháng **spasticity/hyperreflexia** (>60% ca SCI): bản chất = *loss of supraspinal modulation of stretch reflexes* + nhạy neurotransmitterdescending (PMC9144471, PMC6786768).
- ⇒ Cùng 1 arc, phản xạ **to hay nhỏ** tùy não "vặn van" tới đâu; **bỏ van → phun**.
- **Confidence: CAO**

### F-08 · Hành vi lặp → **bán phản xạ** (habit) — nhưng **không phải reflex**
- **Bằng chứng**: Graybiel — habit hình thành qua **nhiều thay đổi neural dissociable** (không phải 1 công tắc), shift từ goal-directed → **dorsolateral striatum**; tín hiệu **outcome-evaluation chuyển giai đoạn** exploration → exploitation (PMC4808096); record trực tiếp: cụm neuron firing thu gọn thành **"bốn bước" (chunk)** quanh hành vi đã thành thói quen.
- **Phân biệt**: habit vẫn cần **cue**, vẫn **override được** (goal-directed circuit còn can thiệp) — reflex thì không có "lý do", luôn chạy đủ điều kiện kích thích.
- **Confidence: TRUNG BÌNH-CAO**

---

## 3. Myth cần loại bỏ

| # | Myth | Thực tế | Nguồn |
|---|---|---|---|
| M1 | "Phản xạ có sẵn lúc sinh, cố định suốt đời" | Một số **mất đi** (Babinski/Moro), một số **phóng đại** sau chấn thương, biên đổi theo trạng thái | F-03, F-07 |
| M2 | "Phản xạ qua tủy nên không qua não" | Não **điều tiết liên tục** (Jendrassik, imagery); mất modulation → spasticity | F-07 |
| M3 | "Học là của não lớn; tủy chỉ là dây" | Học ngay tại **synapse phản xạ** (Aplysia) và **tủy độc lập não** (RIKEN) | F-04, F-05 |
| M4 | "Tập nhiều là thành phản xạ" | Habit ≠ reflex — habit vẫn cần cue, vẫn chặn được; ranh giới chưa đo được | F-08, G2 |
| M5 | "Trẻ sơ sinh phản xạ yếu vì chưa hoàn thiện" | Ngược lại — đủ mạnh để sống; thứ chưa có là **tầng ức chế** | F-02, F-03 |

---

## 4. Khoảng trống research

1. **Wiring program của reflex arc ở người** — gần như toàn bộ dữ liệu từ chuột/gà/zebrafish; không có map nối chi tiết ở người.
2. **Ranh giới habit ↔ reflex**: chưa có thước đo đồng thuận ("bản sao lưu bao nhiêu % là phản xạ?") — G4 cũng liên Q-001.
3. **Spinal learning → phục hồi chức năng**: RIKEN mở đường nhưng chưa có **phác đồ lâm sàng** dùng "tập cho tủy" sau chấn thương.
4. **Conditioning generalize thế nào** — reflex mới cài ở tiểu não, nhưng sao nó lan sang hành vi phức tạp?
5. **Biến thiên cá nhân**: vì sao một số trẻ reflex persist lâu hơn (di truyền? kinh nghiệm?) — dữ liệu epidemiology mỏng.

---

## 5. Hàm ý thực hành

- **Luyện để "cài"**: lặp trong **context ổn định** → habit hình thành nhanh hơn (cue mạnh); đổi context = reset (liên [AN-004](how-brain-knows-fear.md) F-08 về renewal).
- **Chặn habit bằng goal-directed**: thói quen vẫn override được → lúc đầu tư/ra quyết định lớn, **đổi bối cảnh** để phá chunk.
- **Chẩn đoán**: dấu Babinski ở người lớn = mất vỏ não ức chế → cửa sổ để phát hiện MNN.
- **Phục hồi**: spasticity sau SCI = phản xạ mất van điều tiết → điều trị nhắm **tầng điều tiết** (baclofen, luyện), không nhắm arc.
- **Yếu tố "khuếch đại" có thật**: Jendrassik = ví dụ hệ thần kinh **tự tăng gain** phản xạ khi cần — não liên tục "vặn volume" cho phản xạ.

---

## 6. Hướng kiểm chứng
Không cần GPU. Muốn minh hoạ → notebook **CPU free**: mô phỏng **reflex arc với presynaptic gating** (2 input: sensory + descending gain) + **habituation qua giảm quantal** — xem cùng 1 arc cho ra biên độ khác nhau thế nào. *Chỉ minh hoạ, không phải evidence.*

---

## 7. Nguồn

- Chen & Hippenmeyer (2003). *Development of the monosynaptic stretch reflex circuit.* Curr Opin Neurobiol · Wang et al. (2012) PMC3434619 (neuregulin-1/ErbB, spindle development).
- Kandel et al. — Aplysia: quantal analysis of habituation (PMC434028) · molecular mechanism long-term sensitization, *Nature* 1989 · long-term habituation >3 tuần, *Science*.
- Thompson & colleagues: *The role of the cerebellar interpositus nucleus in eyeblink conditioning* (PMC2751661); *Neurobiol Learn Mem* review (S0306452209000967).
- Takeoka lab / RIKEN (2024): *Neural circuitry in the spinal cord allows brain-independent motor learning* · spinal conditioning reviews PMC3946174, PMC10391333.
- Graybiel: *Habit formation* (MIT dspace, DCNS 2016) · outcome-evaluation shifts PMC4808096.
- Jendrassik & H-reflex: Exp Brain Res 1997 (s002210050643) · motor imagery gating biorXiv 2025.
- SCI spasticity: PMC9144471 · PMC6786768 · Biomedicines 2026 (MDPI).
- Newborn reflexes timeline: Queensland Health / nursing references (mốc tuổi mang tính chuẩn đoán lâm sàng).
- *arXiv không dùng cho câu này* (như Q-001/Q-004 — chủ đề não/tâm lý không có trên arXiv).
