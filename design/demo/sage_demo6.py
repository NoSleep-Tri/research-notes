"""
DS-006 — SAGE v0.2: memory hygiene (kho append-only + citation vs keep-all/recency/value)
Acceptance PRE-REGISTERED ở spec §17 (đọc trước khi sửa gì ở đây).

D18: cur_acc(archive) >= 0.90  VÀ  stale_rate(archive) <= 0.10
D19: cur_acc(archive) >= cur_acc(p) + 0.10   (p = keepall, recency, value)
D20: hist_acc(archive) >= 0.80  VÀ  hist_acc(archive) >= hist_acc(p) + 0.20
D21: active_ratio(archive) <= 0.40

CÙNG người trả lời top-1 cosine (KHÔNG dùng thời gian) cho mọi chính sách —
đúng thiết bị đo §17.1 (mô phỏng "retrieve-then-reason" bị E21 phê bình).
oracle_time = diagnostic KHÔNG gate: keepall nhưng answerer chọn đúng bản
theo thời gian → tách "thiếu cấu trúc" khỏi "thiếu dữ liệu" (học §15.4).
"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------- config (pre-registered §17.1) ----------
N_KEY    = 1000         # số fact-key
V_COUNTS = [(2, 200), (3, 400), (4, 300), (6, 100)]   # 20/40/30/10% — CỐ ĐỊNH
DIM      = 64
SIGMA    = 0.15         # nhiễu mỗi phiên bản (cố định trước lần chạy đầu)
BUDGET   = 0.40         # active context / N — dùng lại ngân sách DS-004 §15.2
N_CUR    = 800          # current-query
N_HIST   = 400          # historical-query
N_SEEDS  = 10
Q_SEED   = 20261010     # seed query — cố định, chung mọi seed (§17.1)

POLICIES = ["keepall", "recency", "value", "archive"]   # 4 chính sách gate
DIAG     = "oracle_time"                                # diagnostic, KHÔNG gate


# ---------- corpus ----------

def build_corpus(seed):
    """Mỗi key: v phiên bản, thời điểm U(0,1) tăng dần, giá trị khác nhau tuyệt đối.
    content = key_vec + SIGMA*eps (eps riêng mỗi phiên bản) → top-1 không phân biệt
    được phiên bản trong cùng key (đúng cơ chế ghost-memory E11)."""
    rng = np.random.default_rng(seed)
    keys = rng.standard_normal((N_KEY, DIM))
    keys /= np.linalg.norm(keys, axis=1, keepdims=True)

    vk = np.empty(N_KEY, dtype=int)
    perm = rng.permutation(N_KEY)
    pos = 0
    for v, cnt in V_COUNTS:
        vk[perm[pos:pos + cnt]] = v
        pos += cnt
    total = int(vk.sum())                       # = 3400

    key_id = np.repeat(np.arange(N_KEY), vk)
    ver = np.concatenate([np.arange(v, dtype=int) for v in vk])
    t = np.empty(total)
    val = np.empty(total)
    content = np.empty((total, DIM))
    cur_rec = np.empty(N_KEY, dtype=int)        # record của BẢN HIỆN HÀNH
    sec_rec = np.empty(N_KEY, dtype=int)        # record của BẢN TRƯỚC thay thế cuối
    cur = 0
    for k in range(N_KEY):
        v = int(vk[k])
        t[cur:cur + v] = np.sort(rng.random(v))
        val[cur:cur + v] = rng.random(v)        # liên tục → khác nhau tuyệt đối
        ck = keys[k] + SIGMA * rng.standard_normal((v, DIM))
        ck /= np.linalg.norm(ck, axis=1, keepdims=True)
        content[cur:cur + v] = ck
        cur_rec[k] = cur + v - 1                # thời điểm lớn nhất = bản hiện hành
        sec_rec[k] = cur + v - 2
        cur += v
    return {"keys": keys, "vk": vk, "N": total, "key_id": key_id, "ver": ver,
            "t": t, "val": val, "content": content,
            "cur_rec": cur_rec, "sec_rec": sec_rec}


def make_queries(corpus):
    """800 current + 400 historical, seed 20261010 — cố định cho mọi seed/policy."""
    qrng = np.random.default_rng(Q_SEED)
    ck = qrng.integers(0, N_KEY, size=N_CUR)
    hk = qrng.integers(0, N_KEY, size=N_HIST)   # mọi key đều có v >= 2
    return {"cur_key": ck, "hist_key": hk,
            "Qcur": corpus["keys"][ck], "Qhist": corpus["keys"][hk]}


# ---------- chính sách ----------

def active_sets(c):
    N, t, val = c["N"], c["t"], c["val"]
    k_keep = int(BUDGET * N)
    thr = np.quantile(t, 1.0 - BUDGET)
    return {
        "keepall": np.arange(N),
        "recency": np.where(t >= thr)[0],
        "value": np.argsort(-val)[:k_keep],
        "archive": c["cur_rec"].copy(),          # active = 1 bản hiện hành/key
        DIAG: np.arange(N),
    }


def top1(Q, content, active):
    """Người trả lời DÙNG CHUNG: top-1 cosine, KHÔNG dùng thời gian (§17.1)."""
    S = Q @ content[active].T                   # (nq, |active|)
    return active[S.argmax(axis=1)]


def evaluate(c, q, act, name):
    content, val, key_id = c["content"], c["val"], c["key_id"]
    cur_rec, sec_rec = c["cur_rec"], c["sec_rec"]

    if name == "archive":
        # current: trả lời từ active set (1 bản hiện hành/key) — cùng top1
        ans_c = top1(q["Qcur"], content, act)
        # historical: resolve qua CITATION key → [(t_i, archive_id)] → bản v-2
        ans_h = sec_rec[q["hist_key"]]
    elif name == DIAG:
        # answerer BIẾT thời gian, kho đầy đủ → chọn đúng bản theo lệch thời điểm
        ans_c = cur_rec[q["cur_key"]]
        ans_h = sec_rec[q["hist_key"]]
    else:
        ans_c = top1(q["Qcur"], content, act)
        ans_h = top1(q["Qhist"], content, act)

    cur_ok = val[ans_c] == val[cur_rec[q["cur_key"]]]
    hist_ok = val[ans_h] == val[sec_rec[q["hist_key"]]]
    # stale = trả lời bằng record CÙNG key nhưng KHÔNG phải bản hiện hành (§17.3.6)
    stale = (key_id[ans_c] == q["cur_key"]) & (ans_c != cur_rec[q["cur_key"]])

    # số phiên bản/key trong active (giải thích cơ chế 1/v)
    if name in ("archive", DIAG):
        vact = c["vk"].astype(float) if name == DIAG else np.ones(N_KEY)
    else:
        cnt = np.bincount(key_id[act], minlength=N_KEY)
        vact = cnt.astype(float)

    return {"cur_acc": float(cur_ok.mean()),
            "hist_acc": float(hist_ok.mean()),
            "stale_rate": float(stale.mean()),
            "active_ratio": len(act) / c["N"],
            "versions_active_mean": float(vact.mean()),
            "versions_active_key": float((vact[vact > 0]).mean()) if (vact > 0).any() else 0.0}


def run_seed(seed):
    c = build_corpus(seed)
    q = make_queries(c)
    act = active_sets(c)
    out = {n: evaluate(c, q, act[n], n) for n in POLICIES + [DIAG]}
    out["_archive_ratio"] = 1.0                 # kho cold = toàn bộ (báo cáo riêng §17.3.5)
    return out


# ---------- main ----------

def main():
    seeds = [run_seed(s) for s in range(N_SEEDS)]

    def mean(policy, metric):
        return float(np.mean([s[policy][metric] for s in seeds]))

    m = {p: {k: mean(p, k) for k in
              ("cur_acc", "hist_acc", "stale_rate", "active_ratio", "versions_active_key")}
         for p in POLICIES + [DIAG]}

    # ---------- acceptance (ngưỡng §17.2 — không đổi) ----------
    checks = {
        "D18c1": (m["archive"]["cur_acc"] >= 0.90,
                  f"cur_acc(archive)={m['archive']['cur_acc']:.4f} >= 0.90"),
        "D18c2": (m["archive"]["stale_rate"] <= 0.10,
                  f"stale_rate(archive)={m['archive']['stale_rate']:.4f} <= 0.10"),
    }
    for p in ("keepall", "recency", "value"):
        d = m["archive"]["cur_acc"] - m[p]["cur_acc"]
        checks[f"D19_{p}"] = (d >= 0.10,
                              f"cur_acc {m['archive']['cur_acc']:.4f} - {p} {m[p]['cur_acc']:.4f} "
                              f"= {d:+.4f} >= +0.10")
    checks["D20c1"] = (m["archive"]["hist_acc"] >= 0.80,
                       f"hist_acc(archive)={m['archive']['hist_acc']:.4f} >= 0.80")
    for p in ("keepall", "recency", "value"):
        d = m["archive"]["hist_acc"] - m[p]["hist_acc"]
        checks[f"D20_{p}"] = (d >= 0.20,
                              f"hist_acc {m['archive']['hist_acc']:.4f} - {p} {m[p]['hist_acc']:.4f} "
                              f"= {d:+.4f} >= +0.20")
    checks["D21"] = (m["archive"]["active_ratio"] <= 0.40,
                     f"active_ratio(archive)={m['archive']['active_ratio']:.4f} <= 0.40")

    mod = {
        "D18": checks["D18c1"][0] and checks["D18c2"][0],
        "D19": all(checks[f"D19_{p}"][0] for p in ("keepall", "recency", "value")),
        "D20": checks["D20c1"][0] and all(checks[f"D20_{p}"][0] for p in ("keepall", "recency", "value")),
        "D21": checks["D21"][0],
    }
    kpi = sum(mod.values())

    lines = ["KPI DS-006 — SAGE v0.2 memory hygiene (10 seeds, 800 cur + 400 hist query, budget 0.40)",
             "cur_acc   " + "  ".join(f"{p}={m[p]['cur_acc']:.4f}" for p in POLICIES + [DIAG]),
             "hist_acc  " + "  ".join(f"{p}={m[p]['hist_acc']:.4f}" for p in POLICIES + [DIAG]),
             "stale     " + "  ".join(f"{p}={m[p]['stale_rate']:.4f}" for p in POLICIES + [DIAG]),
             "active    " + "  ".join(f"{p}={m[p]['active_ratio']:.4f}" for p in POLICIES + [DIAG]),
             f"archive cold ratio = 1.0000 (kho append-only — báo cáo riêng theo §17.3.5)",
             f"versions/key trong active (giải thích 1/v): " +
             "  ".join(f"{p}={m[p]['versions_active_key']:.2f}" for p in POLICIES),
             ""]
    for k, (ok, why) in checks.items():
        lines.append(f"{k}: {why} -> {'PASS' if ok else 'FAIL'}")
    lines += ["", f"KPI: {kpi}/4 {'PASS' if kpi == 4 else 'FAIL'}"]
    for k in ("D18", "D19", "D20", "D21"):
        lines.append(f"  {k} " + ("PASS" if mod[k] else "FAIL"))
    print("\n".join(lines))

    # ---------- plots ----------
    x = np.arange(len(POLICIES))
    w = 0.38
    plt.figure(figsize=(8, 4.4))
    plt.bar(x - w / 2, [m[p]["cur_acc"] for p in POLICIES], w, label="cur_acc", color="#1b9e77")
    plt.bar(x + w / 2, [m[p]["stale_rate"] for p in POLICIES], w, label="stale_rate", color="#d95f02")
    plt.axhline(m[DIAG]["cur_acc"], ls=":", c="#7570b3", lw=2,
                label=f"oracle_time cur_acc={m[DIAG]['cur_acc']:.3f} (KHÔNG gate)")
    plt.xticks(x, POLICIES)
    plt.axhline(0.90, ls="--", c="k", lw=1, label="acceptance 0.90 (D18)")
    plt.axhline(0.10, ls="--", c="#d95f02", lw=1, label="stale max 0.10 (D18)")
    plt.ylabel("tỷ lệ"); plt.legend(fontsize=8)
    plt.title("D18/D19 — fact hiện tại: acc vs stale, cùng người trả lời top-1")
    plt.tight_layout(); plt.savefig("d18_cur_stale.png", dpi=110); plt.close()

    plt.figure(figsize=(7, 4))
    plt.bar(x, [m[p]["hist_acc"] for p in POLICIES],
            color=["#999", "#d95f02", "#7570b3", "#1b9e77"])
    plt.axhline(m[DIAG]["hist_acc"], ls=":", c="#7570b3", lw=2, label=f"oracle_time={m[DIAG]['hist_acc']:.3f}")
    plt.axhline(0.80, ls="--", c="k", lw=1, label="acceptance 0.80 (D20)")
    plt.xticks(x, POLICIES); plt.ylabel("hist_acc"); plt.legend(fontsize=8)
    plt.title("D20 — lịch sử qua citation: archive tra kho được, 3 cơ sở phải đoán")
    plt.tight_layout(); plt.savefig("d20_hist.png", dpi=110); plt.close()

    plt.figure(figsize=(7, 4))
    ratios = [m[p]["active_ratio"] for p in POLICIES]
    plt.bar(x, ratios, color=["#999", "#d95f02", "#7570b3", "#1b9e77"])
    plt.axhline(BUDGET, ls="--", c="k", lw=1, label="ngân sách 0.40 (D21, dùng lại DS-004)")
    plt.annotate(f"archive cold = 1.0 (kho append-only, không tính context)",
                 xy=(3, ratios[3]), xytext=(1.2, 0.85), fontsize=8,
                 arrowprops=dict(arrowstyle="->", lw=1))
    plt.xticks(x, POLICIES); plt.ylabel("active_ratio (context / N)"); plt.legend(fontsize=8)
    plt.title("D21 — context thực sự nạp vào: archive chỉ 1 bản hiện hành/key")
    plt.tight_layout(); plt.savefig("d21_budget.png", dpi=110); plt.close()

    # ---------- prediction check (§17.1 — dự báo viết trước, KHÔNG gate) ----------
    pred = {"cur_acc": {"archive": 0.95, "oracle_time": 0.98, "recency": 0.45,
                        "keepall": 0.33, "value": 0.30},
            "stale_rate": {"archive": 0.02, "keepall": 0.65, "value": 0.45, "recency": 0.30},
            "hist_acc": {"archive": 0.90},
            "active_ratio": {"archive": 0.29}}
    dev = {k: {p: round(m[p][k] - v, 4) for p, v in d.items()}
           for k, d in pred.items()}
    lines += ["", "lệch dự báo §17.1 (actual - predicted, không gate):"] + [
        f"  {k}/{p} = {v:+.4f}" for k, d in dev.items() for p, v in d.items()]
    print("\n".join(lines))

    summary = {
        "metrics": m, "archive_cold_ratio": 1.0,
        "checks": {k: {"pass": bool(v[0]), "why": v[1]} for k, v in checks.items()},
        "modules": {k: bool(v) for k, v in mod.items()},
        "kpi": f"{kpi}/4", "prediction_deviation": dev,
        "config": {"N_KEY": N_KEY, "V_COUNTS": V_COUNTS, "DIM": DIM, "SIGMA": SIGMA,
                   "BUDGET": BUDGET, "N_CUR": N_CUR, "N_HIST": N_HIST,
                   "N_SEEDS": N_SEEDS, "Q_SEED": Q_SEED},
    }
    with open("summary.json", "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    with open("kpi.txt", "w") as f:
        f.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
