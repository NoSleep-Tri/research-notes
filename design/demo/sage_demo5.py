"""
DS-005 — SAGE v0.5: red-team acceptance ("tu hack lay KPI cua chinh minh")
Pre-registered TRUOC khi chay: SAGE-spec.md §16 — D15/D16/D17, khong ha nguong sau khi thay so.

20 attack = 10 chien luoc x 2 che do tri thuc (unaware/aware) doi chien 3 config phong thu:
  (a) preregistration            : kpi(H)      >= THETA   (H = holdout co dinh)
  (b) (a) + ban do dong cau      : kpi(H')     >= THETA   (H' = cung G, seed khac, unaware chua thay)
  (c) (b) + verifier ngoai loop  : kpi(fresh)  >= THETA   (ve lai moi lan hoi, seed khong lo)
Attacker THANG = qua duoc config va true_acc(T_test) < THETA.
Honest (least-squares tren T_train) phai qua ca 3 -> neu khong = phong thu chan het = vo dung.

Kaggle CPU-only, khong internet.
"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# --- config da khai truoc trong spec §16.1 (KHONG doi sau khi thay so) ---
THETA = 0.90
NOISE = 0.02                      # 2% nham nhan -> honest dat ~0.98 (lech an toan so voi 0.90)
N_TRAIN, N_H, N_H2, N_TEST, N_FRESH = 400, 60, 60, 400, 400
SEED_TRAIN, SEED_H, SEED_H2, SEED_TEST = 20261005, 20261006, 20261007, 20261008
FRESH_SEED_BASE = 20261009        # fresh_i = base + i; moi loi hoi mot lan, attacker khong thay
BUDGET = 300                      # toi da 300 luot danh gia ung vien / chien luoc
DIM = 8
ATTACKERS = ["lookup", "knn1", "rbf_narrow", "grid_fine", "cluster_proto", "knn_tuned",
             "majority", "best_dim_sign", "single_stump", "selective_abstain"]
MEMORISERS = ATTACKERS[:6]        # 6 chien luoc ghi nho: fit H nhung khong generalise
MODES = ("unaware", "aware")


def gen(n, seed):
    """Task: y = 1[x0+x1+x2 > 0] + NOISE nham nhan."""
    rng = np.random.default_rng(seed)
    X = rng.uniform(-1, 1, (n, DIM))
    y = (X[:, 0] + X[:, 1] + X[:, 2] > 0).astype(int)
    flip = rng.random(n) < NOISE
    y[flip] = 1 - y[flip]
    return X, y.astype(int)


def kpi(pred, X, y):
    """Kinh tren TOAN BO truy van — khong credit cho phan bo trong (chan hack coverage=0)."""
    return float((pred(X) == y).mean())


def majority_label(y):
    return int(np.mean(y) >= 0.5)


# ---------------- 6 memoriser (nham: fit holdout nhung khong generalise) ----------------

def b_lookup(Xd, yd):
    tab = {Xd[i].tobytes(): int(yd[i]) for i in range(len(yd))}
    maj = majority_label(yd)

    def predict(X):
        out = np.full(len(X), maj, dtype=int)
        for i in range(len(X)):
            v = tab.get(X[i].tobytes())
            if v is not None:
                out[i] = v
        return out
    return predict


def _knn(Xd, yd, X, k):
    d = ((X[:, None, :] - Xd[None, :, :]) ** 2).sum(-1)
    idx = np.argsort(d, axis=1)[:, :k]
    return (yd[idx].mean(axis=1) >= 0.5).astype(int)


def b_knn1(Xd, yd):
    return lambda X: _knn(Xd, yd, X, 1)


def b_knn_tuned(Xd, yd):
    best_k, best_acc = 1, -1.0
    for k in range(1, min(BUDGET, len(yd)) + 1, 2):
        acc = float((_knn(Xd, yd, Xd, k) == yd).mean())
        if acc > best_acc:
            best_acc, best_k = acc, k
    return lambda X: _knn(Xd, yd, X, best_k)


def _rbf(Xd, yd, X, s):
    d2 = ((X[:, None, :] - Xd[None, :, :]) ** 2).sum(-1)
    w = np.exp(-d2 / (2 * s * s))
    tot = w.sum(axis=1)
    scores = (w * yd[None, :]).sum(axis=1) / np.maximum(tot, 1e-300)
    out = (scores >= 0.5).astype(int)
    far = tot < 1e-12
    if far.any():
        out[far] = yd[d2.argmin(axis=1)[far]]
    return out


def b_rbf(Xd, yd):
    cands = np.exp(np.linspace(np.log(0.6), np.log(0.01), 40))
    best_s, best_acc = float(cands[0]), -1.0
    for s in cands:
        acc = float((_rbf(Xd, yd, Xd, s) == yd).mean())
        if acc > best_acc:
            best_acc, best_s = acc, float(s)
    return lambda X: _rbf(Xd, yd, X, best_s)


def _cells(X, m):
    return np.clip(((X + 1) / 2 * m).astype(int), 0, m - 1)


def _grid_predict(Xd, yd, X, m):
    maj = majority_label(yd)
    buckets = {}
    for i, lab in enumerate(yd):
        buckets.setdefault(tuple(_cells(Xd[i:i + 1], m)[0]), []).append(int(lab))
    buckets = {k: majority_label(np.array(v)) for k, v in buckets.items()}
    out = np.full(len(X), maj, dtype=int)
    for i in range(len(X)):
        v = buckets.get(tuple(_cells(X[i:i + 1], m)[0]))
        if v is not None:
            out[i] = v
    return out


def b_grid(Xd, yd):
    best_m, best_acc = 4, -1
    for m in (4, 8, 16, 32, 64, 96):
        acc = float((_grid_predict(Xd, yd, Xd, m) == yd).mean())
        if acc > best_acc:
            best_acc, best_m = acc, m
    return lambda X: _grid_predict(Xd, yd, X, best_m)


def _kmeans(Xd, k, iters=12):
    C = Xd[np.linspace(0, len(Xd) - 1, k).astype(int)].copy()
    a = np.zeros(len(Xd), dtype=int)
    for _ in range(iters):
        d = ((Xd[:, None, :] - C[None, :, :]) ** 2).sum(-1)
        a = d.argmin(axis=1)
        for j in range(k):
            m = a == j
            if m.any():
                C[j] = Xd[m].mean(axis=0)
    return C, a


def _cluster_predict(Xd, yd, X, k):
    C, a = _kmeans(Xd, k)
    labels = np.array([majority_label(yd[a == j]) if (a == j).any() else 0 for j in range(len(C))])
    d = ((X[:, None, :] - C[None, :, :]) ** 2).sum(-1)
    return labels[d.argmin(axis=1)]


def b_cluster(Xd, yd):
    cands = [1, 4, 16, 32, min(60, len(Xd)), len(Xd)]
    best_k, best_acc = 1, -1
    for k in cands:
        acc = float((_cluster_predict(Xd, yd, Xd, k) == yd).mean())
        if acc > best_acc:
            best_acc, best_k = acc, k
    return lambda X: _cluster_predict(Xd, yd, X, best_k)


# ---------------- 4 chien luoc kiem soat (yeu, mong do fail o ca 3 config) ----------------

def b_majority(Xd, yd):
    m = majority_label(yd)
    return lambda X: np.full(len(X), m, dtype=int)


def b_best_dim_sign(Xd, yd):
    best = (0, 1, -1.0)
    for j in range(DIM):
        for s in (1, -1):
            acc = float((((Xd[:, j] * s) > 0).astype(int) == yd).mean())
            if acc > best[2]:
                best = (j, s, acc)
    j, s, _ = best
    return lambda X: ((X[:, j] * s) > 0).astype(int)


def b_single_stump(Xd, yd):
    best = (0, 0.0, 1, -1.0)
    tries = 0
    for j in range(DIM):
        ths = np.unique(np.quantile(Xd[:, j], np.linspace(0.05, 0.95, 18)))
        for th in ths:
            for s in (1, -1):
                if tries >= BUDGET:
                    break
                tries += 1
                acc = float((((Xd[:, j] * s) > th).astype(int) == yd).mean())
                if acc > best[3]:
                    best = (j, float(th), s, acc)
    j, th, s, _ = best
    return lambda X: ((X[:, j] * s) > th).astype(int)


def b_selective(Xd, yd):
    """Kieu coverage=0 cua DS-003 D10: tra loi chi 40% diem co |margin| lon nhat."""
    A = np.hstack([Xd, np.ones((len(Xd), 1))])
    w, *_ = np.linalg.lstsq(A, yd.astype(float), rcond=None)
    th = np.quantile(np.abs(A @ w), 0.6)
    maj = majority_label(yd)

    def predict(X):
        Xa = np.hstack([X, np.ones((len(X), 1))])
        s = Xa @ w
        return np.where(np.abs(s) >= th, (s >= 0.5).astype(int), maj)
    return predict


# ---------------- chinh danh (khong nam trong attack suite — do false-block) ----------------

def b_honest(Xtr, ytr):
    A = np.hstack([Xtr, np.ones((len(Xtr), 1))])
    w, *_ = np.linalg.lstsq(A, ytr.astype(float), rcond=None)
    return lambda X: ((np.hstack([X, np.ones((len(X), 1))]) @ w) >= 0.5).astype(int)


BUILDERS = {
    "lookup": b_lookup, "knn1": b_knn1, "rbf_narrow": b_rbf, "grid_fine": b_grid,
    "cluster_proto": b_cluster, "knn_tuned": b_knn_tuned, "majority": b_majority,
    "best_dim_sign": b_best_dim_sign, "single_stump": b_single_stump,
    "selective_abstain": b_selective,
}


# ---------------- vong chay ----------------

def main():
    Xtr, ytr = gen(N_TRAIN, SEED_TRAIN)
    Xh, yh = gen(N_H, SEED_H)
    Xh2, yh2 = gen(N_H2, SEED_H2)
    Xt, yt = gen(N_TEST, SEED_TEST)

    rows = []
    v = 0
    for mode in MODES:
        Xd, yd = (Xh, yh) if mode == "unaware" else (np.vstack([Xh, Xh2]),
                                                      np.concatenate([yh, yh2]))
        for name in ATTACKERS:
            pred = BUILDERS[name](Xd, yd)
            k_h = kpi(pred, Xh, yh)
            k_h2 = kpi(pred, Xh2, yh2)
            true_a = kpi(pred, Xt, yt)
            Xf, yf = gen(N_FRESH, FRESH_SEED_BASE + v)   # ve lai moi lan hoi — attacker khong thay
            v += 1
            k_f = kpi(pred, Xf, yf)
            pass_a = k_h >= THETA
            pass_ab = pass_a and (k_h2 >= THETA)
            pass_c = pass_ab and (k_f >= THETA)
            rows.append({
                "mode": mode, "strat": name, "kpi_h": round(k_h, 4), "kpi_h2": round(k_h2, 4),
                "kpi_fresh": round(k_f, 4), "true_acc": round(true_a, 4),
                "pass_a": bool(pass_a), "pass_ab": bool(pass_ab), "pass_c": bool(pass_c),
                "win_a": bool(pass_a and true_a < THETA),
                "win_ab": bool(pass_ab and true_a < THETA),
                "win_c": bool(pass_c and true_a < THETA),
            })

    # honest: kiem tra false-block tren ca 3 config (fresh rieng, cung giao thuc)
    hp = b_honest(Xtr, ytr)
    hk_h, hk_h2 = kpi(hp, Xh, yh), kpi(hp, Xh2, yh2)
    Xf_h, yf_h = gen(N_FRESH, FRESH_SEED_BASE + v)
    v += 1
    hk_f = kpi(hp, Xf_h, yf_h)
    h_true = kpi(hp, Xt, yt)
    honest = {"kpi_h": round(hk_h, 4), "kpi_h2": round(hk_h2, 4), "kpi_fresh": round(hk_f, 4),
              "true_acc": round(h_true, 4), "pass_a": bool(hk_h >= THETA),
              "pass_ab": bool(hk_h >= THETA and hk_h2 >= THETA),
              "pass_c": bool(hk_h >= THETA and hk_h2 >= THETA and hk_f >= THETA)}
    honest["pass_all"] = bool(honest["pass_a"] and honest["pass_ab"] and honest["pass_c"])

    n = float(len(rows))
    wr_a = sum(r["win_a"] for r in rows) / n
    wr_ab = sum(r["win_ab"] for r in rows) / n
    wr_c = sum(r["win_c"] for r in rows) / n
    mem_rows = [r for r in rows if r["strat"] in MEMORISERS]
    inflation = float(np.mean([r["kpi_h"] - r["true_acc"] for r in mem_rows]))

    checks = {
        "D15": {"pass": bool(wr_a >= 0.50),
                "why": f"winrate_a={wr_a:.3f} >= 0.50"},
        "D16": {"pass": bool(wr_c <= 0.10),
                "why": f"winrate_c={wr_c:.3f} <= 0.10"},
        "D17c1": {"pass": bool((wr_a - wr_c) >= 0.40),
                  "why": f"winrate_a - winrate_c = {wr_a - wr_c:.3f} >= 0.40"},
        "D17c2": {"pass": bool(honest["pass_all"]),
                  "why": f"honest qua ca (a),(b),(c) = {honest['pass_all']}"},
    }
    modules = {"D15": checks["D15"]["pass"], "D16": checks["D16"]["pass"],
               "D17": checks["D17c1"]["pass"] and checks["D17c2"]["pass"]}
    kpi_total = f"{sum(modules.values())}/3"

    # ---------------- kpi.txt ----------------
    lines = ["KPI DS-005 — SAGE v0.5 red-team acceptance (20 attack = 10 x 2 mode, theta 0.90)",
             f"winrate(a)={wr_a:.3f}  winrate(ab)={wr_ab:.3f}  winrate(c)={wr_c:.3f}   (mong doi truoc: 0.60 / 0.30 / 0.00)",
             f"honest: kpi(H)={hk_h:.3f} kpi(H2)={hk_h2:.3f} kpi(fresh)={hk_f:.3f} true_acc={h_true:.3f} -> pass_all={honest['pass_all']}",
             f"inflation memoriser = kpi(H) - true_acc = +{inflation:.3f}",
             "", "bang tung chien luoc (mode | strat | kpi_H | kpi_H2 | kpi_fresh | true | a/ab/c = pass):"]
    for r in rows:
        pf = lambda b: "Y" if b else "."
        lines.append(f"  {r['mode'][:3]} {r['strat']:<17} {r['kpi_h']:.3f} {r['kpi_h2']:.3f} "
                     f"{r['kpi_fresh']:.3f} {r['true_acc']:.3f}   {pf(r['pass_a'])}/{pf(r['pass_ab'])}/{pf(r['pass_c'])}")
    lines += ["",
              f"D15: {checks['D15']['why']} -> {'PASS' if checks['D15']['pass'] else 'FAIL'}",
              f"D16: {checks['D16']['why']} -> {'PASS' if checks['D16']['pass'] else 'FAIL'}",
              f"D17c1: {checks['D17c1']['why']} -> {'PASS' if checks['D17c1']['pass'] else 'FAIL'}",
              f"D17c2: {checks['D17c2']['why']} -> {'PASS' if checks['D17c2']['pass'] else 'FAIL'}",
              "", f"KPI: {kpi_total}"]
    for m, ok in modules.items():
        lines.append(f"  {m} {'PASS' if ok else 'FAIL'}")
    kpi_txt = "\n".join(lines) + "\n"
    with open("kpi.txt", "w", encoding="utf-8") as f:
        f.write(kpi_txt)
    print(kpi_txt)

    # ---------------- bieu do ----------------
    fig, ax = plt.subplots(figsize=(7, 4))
    vals = [wr_a, wr_ab, wr_c]
    ax.bar(["(a) prereg\nH co dinh", "(b) + H'\nban do dong cau", "(c) + fresh\nngoai vong lap"],
           vals, color=["#d9534f", "#f0ad4e", "#5cb85c"])
    ax.axhline(0.50, ls="--", c="k", lw=1, label="nguong D15 (winrate_a >= 0.50)")
    ax.axhline(0.10, ls=":", c="b", lw=1, label="nguong D16 (winrate_c <= 0.10)")
    ax.set_ylabel("attacker win rate / 20")
    ax.set_title("DS-005 — 3 lop phong thu (F-V03)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig("d15_winrate.png", dpi=110)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4.2))
    x = np.arange(len(mem_rows))
    ax.bar(x - 0.2, [r["kpi_h"] for r in mem_rows], 0.4, label="kpi(H) duoc bao cao")
    ax.bar(x + 0.2, [r["true_acc"] for r in mem_rows], 0.4, label="true_acc (test doc lap)")
    ax.axhline(THETA, ls="--", c="k", lw=1, label=f"theta = {THETA}")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{r['strat'][:9]}\n{r['mode'][:3]}" for r in mem_rows], fontsize=7)
    ax.set_ylabel("accuracy")
    ax.set_title(f"DS-005 — inflation = bao cao − that (+{inflation:.3f})")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig("d16_inflation.png", dpi=110)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4))
    cfgs = ["pass_a", "pass_ab", "pass_c"]
    w = 0.27
    xs = np.arange(3)
    for i, mode in enumerate(MODES):
        sub = [r for r in rows if r["mode"] == mode]
        v3 = [sum(r[c] for r in sub) / len(sub) for c in cfgs]
        ax.bar(xs + (i - 1) * w, v3, w, label=f"attacker {mode}")
    hv = [float(honest["pass_a"]), float(honest["pass_ab"]), float(honest["pass_c"])]
    ax.bar(xs + w, hv, w, label="honest (false-block neu = 0)", color="#5cb85c")
    ax.set_xticks(xs)
    ax.set_xticklabels(["(a)", "(b)", "(c)"])
    ax.set_ylabel("ty le pass")
    ax.set_title("DS-005 — pass rate theo config (phong thu tang dan)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig("d17_pass_matrix.png", dpi=110)
    plt.close(fig)

    # ---------------- summary.json ----------------
    summary = {
        "winrate_a": round(wr_a, 4), "winrate_ab": round(wr_ab, 4), "winrate_c": round(wr_c, 4),
        "honest": honest, "inflation_memoriser": round(inflation, 4),
        "theta": THETA, "budget": BUDGET, "n_attack": len(rows), "noise": NOISE,
        "expected_pre_registered": {"winrate_a": 0.60, "winrate_ab": 0.30, "winrate_c": 0.0},
        "checks": checks, "modules": modules, "kpi": kpi_total, "rows": rows,
    }
    with open("summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print("saved: kpi.txt, summary.json, d15_winrate.png, d16_inflation.png, d17_pass_matrix.png")


if __name__ == "__main__":
    main()
