# PLAN — Nghiên cứu & Phân tích AI (trên arXiv + Kaggle)

> Cập nhật: 2026-10-06 · `D:\Documents\1opencode`
> Công cụ: **arxiv (19)** · **kaggle (71)** · **github (46)** · **memory (9)**

---

## 1. Trọng tâm

Đây là **trạm nghiên cứu**, không phải cuộc đua leaderboard.

```
câu hỏi → thu thập (arXiv + Kaggle) → phân tích → tổng hợp báo cáo → knowledge graph
                                              ↳ chạy code (CPU/GPU) CHỈ KHI cần kiểm chứng claim
```

**Đầu ra thực sự của dự án = các bản phân tích có dẫn chứng**, kèm knowledge graph liên kết *câu hỏi ↔ paper ↔ phát hiện ↔ bằng chứng*.

**Mục tiêu 1 tháng:**
- ≥ 8 bản phân tích hoàn chỉnh (paper/survey, competition, dataset, notebook, kỹ thuật)
- ≥ 25 paper đọc + tóm tắt (mỗi paper 1 dòng take-away + độ tin cậy)
- 1 khảo sát (survey) có cấu trúc, public lên GitHub
- Knowledge graph trả lời được: *"câu hỏi này đã ai trả lời, bằng chứng ở đâu?"*

---

## 2. Vòng lặp nghiên cứu (5 bước)

### B1. Câu hỏi
Mỗi chuỗi nghiên cứu bắt đầu bằng 1 câu hỏi cụ thể, ghi vào `research/questions/`:
```
Q-001: <câu hỏi>  ·  phạm vi  ·  tiêu chí "đã trả lời"  ·  độ ưu tiên
```
→ `memory.create_entities` (loại `Question`) để truy vấn lại sau.

### B2. Thu thập — *không tốn compute*
- **arXiv**: `search_papers` / `semantic_search` → `get_abstract` → `get_paper_outline` → `read_paper_section` (đọc có chọn lọc, không đọc hết)
- **arXiv định kỳ**: `watch_topic` 2–3 chủ đề → `check_alerts` mỗi 2–3 ngày
- **Kaggle**: `search_content` (notebook + discussion + dataset + leaderboard), `search_notebooks` → `get_notebook_info` / `list_notebook_files`, `get_competition_leaderboard`, `get_dataset_files_summary`
- Ghi vào `research/inbox.md` — *chưa phân tích, chỉ đãi đầu vào*

### B3. Phân tích — **cốt lõi của dự án**
Mỗi bản phân tích theo template `analysis-template.md`:
1. **Câu hỏi** đang trả lời
2. **Bằng chứng** — trích dẫn cụ thể (paper §, notebook cell, leaderboard số liệu)
3. **So sánh** — với ít nhất 1 phương án đối chứng
4. **Phát hiện (finding)** — 1–3 ý, mỗi ý kèm `confidence: cao/trung bình/thấp`
5. **Khoảng trống / điều chưa rõ**
6. **Hướng kiểm chứng tiếp** (nếu cần → mới nghĩ tới code)

### B4. Kiểm chứng (chỉ khi cần)
Nếu 1 finding cần số liệu chứng minh → chạy tối giản trên Kaggle:
- **CPU (free)** cho EDA/tính toán nhanh — ưu tiên tuyệt đối
- **GPU** chỉ khi claim liên quan tới model thật sự cần
```
save_notebook(SaveAndRunAll) → get_notebook_session_status → download_notebook_output → cancel_notebook_session
```
Kết quả → `results.md` + quay lại B3 cập nhật confidence.

### B5. Tổng hợp & lưu trữ
- `research/notes/` — bản phân tích (markdown, dẫn chứng đầy đủ)
- `memory` — entities: `Question`, `Paper`, `Finding`, `Evidence`; relations: `answers`, `supports`, `contradicts`
- `github.push_files` — publish survey/report theo mốc

---

## 3. Cấu trúc thư mục

```
D:\Documents\1opencode\
├── opencode.json            # 4 MCP (KHÔNG commit token)
├── PLAN.md                  # tài liệu này
├── memory.jsonl             # knowledge graph
└── research\
    ├── inbox.md             # đãi đầu vào (chưa phân tích)
    ├── backlog.md           # câu hỏi chờ xử lý
    ├── questions\Q-00x.md   # câu hỏi + tiêu chí trả lời
    ├── notes\               # BẢN PHÂN TÍCH (đầu ra chính)
    │   ├── 2026-10-06_<ten>.md
    │   └── ...
    ├── surveys\<ten>\       # khảo sát tổng hợp nhiều nguồn
    ├── templates\
    │   ├── analysis-template.md
    │   └── paper-note-template.md
    └── evidence\            # output tải về: csv/log làm bằng chứng
```

---

## 4. Nhịp làm việc (mỗi phiên 45–90')

| Lúc nào | Việc | Công cụ |
|---|---|---|
| **Mỗi phiên** | 1 câu hỏi → thu thập → **hoàn thành 1 bản phân tích** → ghi memory | arxiv · kaggle · memory |
| **Mỗi 2–3 ngày** | `check_alerts`, dọn `inbox.md` → `notes/`, trả lời/backlog question | arxiv · memory |
| **Cuối tuần** | 1 digest tổng hợp (đã phân tích gì, phát hiện gì, câu hỏi nào đóng) → commit | memory · github |

---

## 5. Mốc (bản turbo — theo ngày)

| Mốc | Thời gian | Tiêu chí hoàn thành |
|---|---|---|
| **M0 — Nền tảng** | **Ngày 1** | Scaffold thư mục + 2 template (`analysis`, `paper-note`). Test pipeline Kaggle bằng **1 notebook CPU free** để chắc phần kiểm chứng chạy được. |
| **M1 — Phân tích đầu tiên** | **Ngày 2–3** | 2–3 bản phân tích hoàn chỉnh (gợi ý: 1 competition + 1 notebook top + 1 paper), mỗi bản có ≥1 finding + confidence. |
| **M2 — Survey nhỏ** | **Ngày 4–7** | Trả lời 1 câu hỏi bằng 5–10 paper: `search_papers` → đọc section → 1 `surveys/<ten>.md` có so sánh + khoảng trống. |
| **M3 — Chuỗi tự động** | **Tuần 2** | 2–3 `watch_topic` chạy đều; knowledge graph đủ liên kết Q ↔ Paper ↔ Finding ↔ Evidence; digest cuối tuần đầu tiên. |
| **M4 — Tổng hợp** | **Tuần 3–4** | 1 survey public trên GitHub (README + notes), ≥ 8 phân tích, mọi finding có confidence + nguồn. — ✅ **xong sớm (2026-10-06)**: [`NoSleep-Tri/research-notes`](https://github.com/NoSleep-Tri/research-notes) public với **19 survey** (AN-001 → AN-019, trả lời Q-001 → Q-020) + SYNTHESIS + **spec 11 demo có KPI (DS-001→DS-011) + DS-012/DS-012b/DS-012c pre-reg (DS-012c v4 4/4 PASS raw → v5 rerun)** |

---

## 6. Chỉ số theo dõi (KPI)

- **Sản lượng**: ≥ 1 bản phân tích/phiên · ≥ 5 paper tóm tắt/tuần
- **Chất lượng**: 100% finding có **dẫn chứng + confidence** (không cảm tính)
- **Độ sâu**: mỗi survey có ≥ 1 **khoảng trống research** được chỉ ra
- **Đóng question**: ≥ 30% câu hỏi trong `backlog` được trả lời/thu hẹp mỗi tuần
- **Kiến thức**: entity/relations mới trong `memory.jsonl` mỗi phiên
- **Compute**: số run GPU/tuần chỉ phản ánh việc *thực sự cần kiểm chứng* (gần 0 cũng được)
- **Thiết kế**: mỗi design doc có **acceptance test chạy được** — hiện **DS-001 5/5** · **DS-002 3/3** · **DS-003 3/3** · **DS-004 3/3** · **DS-005 3/3** · **DS-006 4/4** · **DS-007 5/6** (E3 FAIL = negative finding giữ nguyên, không sửa ngưỡng) · **DS-008 6/6** (lần đầu 6/6 ngay, không sửa gì) · **DS-009 6/6** (training dataset, lần đầu ngay, dự báo 10/11 khớp) · **DS-010 5/6** (train smoke **SFT+GRPO trên Kaggle GPU T4** — lần train đầu tiên; **T5 FAIL giữ thật**, T3/T4 PASS sau fix bug OP_RE ghi change-log trước-run, ngưỡng không đổi; acc_SFT 0.9900 vượt Bar2) · **DS-011 5/6** (Answer Agent robustness — **experiment cuối**; A_mixed chống đầu độc `ASR 0.0000` giữ utility (F-T04 ✓), **T5 FAIL giữ thật** = F-L02 bị bác một phần do Δ=+0.15 fingerprint, kênh-lie `ASR 0.7500` marker crowd-out; v1/v2 infra-fail pre-run ghi change-log, ngưỡng không đổi) — pre-register ngưỡng trước khi chạy

---

## 7. Rủi ro & phòng ngừa

| Rủi ro | Phòng ngừa |
|---|---|
| **Ngập trong info** (đọc mãi không ra sản phẩm) | 1 phiên = 1 bản phân tích hoàn chỉnh. `inbox.md` chỉ là chờ phân tích, tối đa 10 mục tồn |
| Finding cảm tính, không có nguồn | Template ép: dẫn chứng + confidence. Thiếu nguồn = không phải finding |
| Đọc tràn lan, mất trọng tâm | Mỗi chuỗi bắt buộc 1 `Question` có tiêu chí "đã trả lời" |
| Token lộ trong `opencode.json` | Chuyển sang `{env:KAGGLE_TOKEN}` / `{env:GITHUB_TOKEN}` |
| Quota GPU phung phí | CPU free cho mọi kiểm chứng nhanh; GPU chỉ khi claim bắt buộc |

---

## 8. Bộ tool theo giai đoạn

| Giai đoạn | Server | Tool tiêu biểu |
|---|---|---|
| B1 Câu hỏi | `memory` | `create_entities`, `create_relations` |
| B2 Thu thập | `arxiv` | `search_papers`, `semantic_search`, `get_abstract`, `get_paper_outline`, `read_paper_section`, `watch_topic`, `check_alerts` |
| | `kaggle` | `search_content`, `search_notebooks`, `get_notebook_info`, `list_notebook_files`, `get_competition_leaderboard`, `get_dataset_files_summary`, `get_forum_topic` |
| B3 Phân tích | (mình + template) | `analysis-template.md` |
| B4 Kiểm chứng | `kaggle` | `save_notebook`, `get_notebook_session_status`, `download_notebook_output`, `cancel_notebook_session`, `get_accelerator_quota` |
| B5 Tổng hợp | `memory` · `github` | `search_nodes` → `push_files`, `create_or_update_file` |

---

## 9. Việc cần làm ngay (Ngày 1)

- [x] Scaffold `research/` (questions, notes, surveys, templates, evidence) + `inbox.md`, `backlog.md`
- [x] Viết `analysis-template.md` + `paper-note-template.md`
- [x] **Test pipeline kiểm chứng**: 1 notebook CPU free trên Kaggle (save → poll → download output) — ✅ đã chạy thật với DS-001 demo (v1→v3, download PNG + kpi.txt về local)
- [x] Chọn 1 câu hỏi đầu tiên (Q-001) → `memory.create_entities`
- [ ] Chuyển 2 token sang biến môi trường — **tạm ngưng theo yêu cầu người dùng**: không được mở `opencode.json` nữa (tránh lộ token); migrate sẽ do người dùng tự làm
- [x] **Push research/ lên GitHub** (2026-10-06): repo công khai [`NoSleep-Tri/research-notes`](https://github.com/NoSleep-Tri/research-notes) — 30 file: README (chỉ mục) + SYNTHESIS + backlog + inbox + 11 `questions/` + 11 `surveys/` + `design/SAGE-spec.md` + 2 code demo + 4 file KPI/summary. *Không có git CLI trên máy* → dùng GitHub MCP `push_files`, đọc file bằng `fetch("file:///...")` bên trong Code Mode để **nội dung không đi qua context**
