# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy>=2.0", "matplotlib>=3.9"]
# ///
"""
DS-003 demo v1 - 3 acceptance test (D9-D11), spec SAGE sec 14 (SAGE v0.2).
  D9  Wirehead guard: verifier ngoai vong lap + lay lai mau moi lan
      (F-R01/F-R07, AN-009) — giu cong, monitor trong vong lap khong cuu duoc
  D10 Confidence calibration quyet dinh chat luong gate (F-D05)
  D11 Adaptive registry chon model theo kieu loi (L1/L2 cua SAGE)
Output: stdout + out/summary.json + out/kpi.txt + 3 PNG
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

KAGGLE = Path("/kaggle/working").exists()
OUT = Path("/kaggle/working/out") if KAGGLE else Path(__file__).parent / "out3"
OUT.mkdir(parents=True, exist_ok=True)
results: dict = {}


# --------------------------------------------------------------------------
# D9: wirehead guard — proxy trong vong lap vs ngoai vong lap
# --------------------------------------------------------------------------
DIM = 8
_A = np.zeros(DIM)
_A[0] = 2.5
_A2 = np.zeros(DIM)
_A2[1] = 2.5
ROUNDS, NPER, EXPLORE = 15, 300, 0.4
LAM = 1.5


def d9_truth(x):
    return -np.sum(x * x, axis=-1)


def d9_proxy(x):
    return -np.sum((x - _A) ** 2, axis=-1)


def d9_monitor(x):
    return -np.sum((x - _A2) ** 2, axis=-1)


def d9_field(seed):
    r = np.random.default_rng(seed)
    return (r.normal(0, 1.0, (5, DIM)), r.uniform(0, 2 * np.pi, 5), r.normal(0, 1.0, 5))


def d9_eps(x, prm):
    K, b, c = prm
    return LAM * (np.sin(x @ K.T + b) @ c)


def d9_signal(arm, x, prm, round_t):
    """Tung arm toi uu CHINH tin hieu no tin (khong cho chung duong)."""
    if arm == "proxy":
        return d9_proxy(x)
    if arm == "monitor":
        return 0.5 * (d9_proxy(x) + d9_monitor(x))
    if arm == "static":
        return d9_truth(x) + d9_eps(x, prm)
    if arm == "rotated":
        # lay lai mau moi lan: 5 lan do tuy nhien, khong co thien he thong
        return d9_truth(x) + float(np.mean([d9_eps(x, d9_field(90000 + 17 * round_t + k))
                                            for k in range(5)]))
    return d9_truth(x)  # oracle


def d9_run(arm, seed):
    r = np.random.default_rng(seed)
    prm = d9_field(1234)
    mu = np.zeros(DIM)
    sig = 1.5
    pool = []
    hist_infl = []
    for t in range(ROUNDS):
        n_exp = int(NPER * (1 - EXPLORE))
        Xe = mu + sig * r.normal(size=(n_exp, DIM))
        dirv = r.normal(size=(NPER - n_exp, DIM))
        dirv /= np.linalg.norm(dirv, axis=1, keepdims=True)
        rad = 5.0 * r.random(NPER - n_exp) ** (1.0 / DIM)
        X = np.vstack([Xe, dirv * rad[:, None]])
        pool.append(X)
        s = d9_signal(arm, X, prm, t)
        idx = np.argpartition(s, -10)[-10:]
        mu = X[idx].mean(axis=0)
        sig = max(0.15, sig * 0.92)
        if arm == "static":
            allx = np.vstack(pool)
            keep = min(len(allx), (t + 1) * NPER)
            best = allx[:keep][np.argmax(d9_signal("static", allx[:keep], prm, 0))]
            # chenh lech: holdout co dinh noi len vs do lai bang mau moi
            fresh = d9_signal("rotated", best[None, :], prm, t)[0]
            hist_infl.append(float(d9_signal("static", best[None, :], prm, 0)[0] - fresh))
    allx = np.vstack(pool)
    s = d9_signal(arm, allx, prm, ROUNDS)
    x = allx[int(np.argmax(s))]
    rep_static = float(d9_truth(x) + d9_eps(x, prm))
    rep_fresh = float(d9_signal("rotated", x[None, :], prm, 77)[0])
    return float(d9_truth(x)), rep_static, rep_fresh, hist_infl


def d9():
    arms = ["proxy", "monitor", "static", "rotated", "oracle"]
    SEEDS = 20
    acc = {a: [] for a in arms}
    infl = []
    infl_curve = []
    for sd in range(SEEDS):
        for a in arms:
            tr, rs, rf, h = d9_run(a, sd)
            acc[a].append(tr)
            if a == "static":
                infl.append(rs - rf)
                infl_curve.append(h)
    mean = {a: float(np.mean(v)) for a, v in acc.items()}
    infl_m = float(np.mean(infl))
    curve = np.mean(np.array(infl_curve, dtype=float), axis=0).tolist()

    c1 = mean["rotated"] - mean["proxy"] >= 1.0
    c2 = mean["rotated"] - mean["static"] >= 0.5
    c3 = mean["rotated"] - mean["monitor"] >= 1.0
    c4 = infl_m >= 0.5

    fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.2))
    names = ["proxy", "monitor", "static", "rotated", "oracle"]
    cols = ["#e76f51", "#e9c46a", "#8d99ae", "#2a9d8f", "#444"]
    ax[0].bar(np.arange(5), [mean[n] for n in names], color=cols)
    ax[0].axhline(0, color="k", lw=0.8)
    ax[0].set_xticks(np.arange(5), names, fontsize=8)
    ax[0].set(ylabel="truth cuoi cung (0 = tot nhat)", title="D9a: ai cung tot nhu nao khi phe duyet ung vien")
    ax[0].grid(alpha=0.3, axis="y")
    ax[1].plot(np.arange(1, ROUNDS + 1), curve, "-o", color="#e76f51")
    ax[1].axhline(0, color="k", lw=0.8)
    ax[1].set(xlabel="so lan tra cuu holdout co dinh", ylabel="inflation (so do noi len - do lai)",
              title="D9b: holdout co dinh bi toi uu qua nhieu dan theo so lan hoi")
    ax[1].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "d9_wirehead_guard.png", dpi=110)
    plt.close(fig)

    results["D9"] = dict(
        mean_truth={a: round(mean[a], 3) for a in arms},
        gap_rotated_minus_proxy=round(mean["rotated"] - mean["proxy"], 3),
        gap_rotated_minus_static=round(mean["rotated"] - mean["static"], 3),
        gap_rotated_minus_monitor=round(mean["rotated"] - mean["monitor"], 3),
        inflation_static=round(infl_m, 3),
        inflation_curve=[round(v, 3) for v in curve],
        c1_beats_proxy=bool(c1),
        c2_beats_static_holdout=bool(c2),
        c3_beats_inloop_monitor=bool(c3),
        c4_static_holdout_overfit=bool(c4),
        PASS=bool(c1 and c2 and c3 and c4),
    )


# --------------------------------------------------------------------------
# D10: confidence calibration → chat luong gate
# --------------------------------------------------------------------------
def d10_pava(y):
    vals, sizes = [], []
    for yi in y:
        v, s = float(yi), 1
        while vals and vals[-1] > v:
            pv, ps = vals.pop(), sizes.pop()
            v = (v * s + pv * ps) / (s + ps)
            s += ps
        vals.append(v)
        sizes.append(s)
    return np.repeat(vals, sizes)


def d10_ece(conf, correct, bins=10):
    edges = np.linspace(0, 1, bins + 1)
    e = 0.0
    for i in range(bins):
        m = (conf >= edges[i]) & (conf < edges[i + 1] if i < bins - 1 else conf <= 1)
        if m.sum():
            e += m.mean() * abs(float(conf[m].mean()) - float(correct[m].mean()))
    return e


def d10_gate(conf, pred, y, thr=0.95):
    acc_ok = (pred == y)
    acc = conf >= thr
    cov = float(acc.mean()) if len(acc) else 0.0
    prec = float(acc_ok[acc].mean()) if acc.sum() else 1.0
    return prec, cov, 1.0 - cov * (1.0 - prec)


def d10_violation(conf, pred, y, min_cov=0.05):
    """Muc hua hen qua muc TE NHAT o moi diem van hanh ma co ng thuc su mo
    (coverage >= 5%). Cam diem bang cach khong quyet dinh gi (coverage=0)."""
    worst = 0.0
    for t in np.arange(0.50, 1.00, 0.01):
        m = conf >= t
        cov = float(m.mean())
        if cov >= min_cov:
            prec = float((pred[m] == y[m]).mean())
            worst = max(worst, float(t) - prec)
    return worst


def d10():
    r = np.random.default_rng(11)
    n, K, T_TRUE = 6000, 10, 2.5
    q = r.dirichlet(np.full(K, 0.30), size=n)
    y = np.array([r.choice(K, p=q[i]) for i in range(n)])
    logits = T_TRUE * np.log(q) + r.normal(0, 0.15, (n, K))
    pred = logits.argmax(1)

    perm = r.permutation(n)
    ical, ite = perm[:2000], perm[2000:]

    def sm(z, T=1.0):
        e = np.exp((z - z.max(axis=1, keepdims=True)) / T)
        return e / e.sum(axis=1, keepdims=True)

    conf_raw = sm(logits[ite]).max(axis=1)
    # temperature scaling: grid search tren split calibration
    best_t, best_nll = 1.0, 1e18
    for T in np.arange(0.5, 6.01, 0.05):
        p = sm(logits[ical], T)
        nll = -np.log(np.clip(p[np.arange(len(ical)), y[ical]], 1e-12, 1)).mean()
        if nll < best_nll:
            best_t, best_nll = float(T), nll
    conf_temp = sm(logits[ite], best_t).max(axis=1)

    # isotonic (top-label) tren split calibration
    pc = sm(logits[ical]).max(axis=1)
    cc = (pred[ical] == y[ical]).astype(float)
    o = np.argsort(pc)
    iso_fit = d10_pava(cc[o])
    conf_iso = np.interp(conf_raw, pc[o], iso_fit)

    confs = {"raw": conf_raw, "temp": conf_temp, "isotonic": conf_iso}
    ece = {k: float(d10_ece(v, (pred[ite] == y[ite]).astype(float))) for k, v in confs.items()}
    # hop dong khai bao: nguong 0.95 (tham khao, metric cu) va 0.90 (cap nhat v2)
    gate = {k: d10_gate(v, pred[ite], y[ite], 0.95) for k, v in confs.items()}
    g90 = {k: d10_gate(v, pred[ite], y[ite], 0.90) for k, v in confs.items()}
    brier = {k: float(np.mean(np.sum((sm(logits[ite], t) - np.eye(K)[y[ite]]) ** 2, axis=1)))
             for k, t in [("raw", 1.0), ("temp", best_t)]}

    c1 = ece["temp"] <= 0.6 * ece["raw"]
    c2 = ece["temp"] <= 0.10
    vio = {k: d10_violation(v, pred[ite], y[ite]) for k, v in confs.items()}
    c3 = (vio["raw"] >= 0.05) and (vio["temp"] <= 0.05)

    fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.2))
    for k, col in [("raw", "#e76f51"), ("temp", "#2a9d8f")]:
        c, ok = confs[k], (pred[ite] == y[ite]).astype(float)
        xs, ys = [], []
        for i in range(10):
            m = (c >= i / 10) & (c < (i + 1) / 10 if i < 9 else c <= 1)
            if m.sum() > 0:
                xs.append(float(c[m].mean()))
                ys.append(float(ok[m].mean()))
        ax[0].plot(xs, ys, "-o", label=k, color=col)
    ax[0].plot([0, 1], [0, 1], "--", color="k", lw=1)
    ax[0].set(xlabel="confidence duoc bao", ylabel="accuracy thuc te",
              title="D10a: reliability diagram (lech = khong calibration)", xlim=(0, 1), ylim=(0, 1))
    ax[0].legend(fontsize=8)
    ax[0].grid(alpha=0.3)
    lbl = ["raw", "temp", "isotonic"]
    ax[1].bar(np.arange(3) - 0.15, [g90[k][0] for k in lbl], width=0.3,
              label="precision @ cong bo 0.90", color="#2a9d8f")
    ax[1].bar(np.arange(3) + 0.15, [g90[k][1] for k in lbl], width=0.3,
              label="coverage", color="#8d99ae")
    ax[1].axhline(0.90, color="k", ls="--", lw=1.2, label="hop dong: >= 0.90")
    ax[1].set_xticks(np.arange(3), lbl)
    ax[1].set(ylim=(0, 1.05), title="D10b: cong bo 0.90 — precision thuc te vs ti le dam lay")
    ax[1].legend(fontsize=8)
    ax[1].grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(OUT / "d10_calibration_gate.png", dpi=110)
    plt.close(fig)

    results["D10"] = dict(
        ece={k: round(v, 4) for k, v in ece.items()},
        brier={k: round(v, 4) for k, v in brier.items()},
        temperature_fitted=round(best_t, 2),
        violation_worst_overcoverage05={k: round(v, 4) for k, v in vio.items()},
        contract090_precision_reference={k: round(g90[k][0], 3) for k in lbl},
        contract090_coverage_reference={k: round(g90[k][1], 3) for k in lbl},
        gate_precision_at_095={k: round(gate[k][0], 3) for k in lbl},
        gate_coverage_at_095={k: round(gate[k][1], 3) for k in lbl},
        gating_acc_at_095_reference_only={k: round(gate[k][2], 3) for k in lbl},
        c1_ece_cut_40pct=bool(c1),
        c2_ece_below_010=bool(c2),
        c3_violation_raw_high_temp_low=bool(c3),
        PASS=bool(c1 and c2 and c3),
    )


# --------------------------------------------------------------------------
# D11: adaptive registry chon model theo kieu loi
# --------------------------------------------------------------------------
def d11_one(seed, T=3000, K=6, strong=0.97, weak=0.50, sigma=0.30, eps=0.05):
    r = np.random.default_rng(seed)
    mode = r.integers(0, K, T)
    feat = np.eye(K)[mode] + r.normal(0, sigma, (T, K))
    infer = feat.argmax(1)
    u = r.random((3, T))

    static_m = (mode == 0)
    rr_m = (mode == (np.arange(T) % K))
    oracle_m = np.ones(T, bool)

    r_static = (np.where(static_m, strong, weak) > u[0]).astype(float)
    r_rr = (np.where(rr_m, strong, weak) > u[1]).astype(float)
    r_oracle = (np.full(T, strong) > u[2]).astype(float)

    tab = np.zeros((K, K))
    cnt = np.zeros((K, K))
    rew = np.zeros(T)
    for t in range(T):
        i = infer[t]
        if r.random() < eps:
            j = int(r.integers(K))
        else:
            # optimistic init: chua thu = 1.0 > moi rate that (<=0.97) -> bat buoc thu het
            rate = np.where(cnt[i] > 0, tab[i] / np.maximum(cnt[i], 1), 1.0)
            j = int(np.argmax(rate))
        hit = (mode[t] == j)
        v = (r.random() < (strong if hit else weak))
        tab[i, j] += v
        cnt[i, j] += 1
        rew[t] = v
    a_static = float(r_static.mean())
    a_rr = float(r_rr.mean())
    a_oracle = float(r_oracle.mean())
    a_adapt = float(rew.mean())
    return (a_static, a_rr, a_adapt, a_oracle,
            {"static": r_static, "round_robin": r_rr, "adaptive": rew, "oracle": r_oracle})


def d11():
    K = 6
    STRONG = 0.97
    SEEDS, T = 10, 3000
    st, rr, ad, orc = [], [], [], []
    curves = {k: [] for k in ("static", "round_robin", "adaptive")}
    for s in range(SEEDS):
        a, b, c, d, per_round = d11_one(s, T=T, K=K, strong=STRONG)
        st.append(a)
        rr.append(b)
        ad.append(c)
        orc.append(d)
        for k in curves:
            curves[k].append(np.convolve(per_round[k], np.ones(200) / 200, mode="valid"))
    acc = {"static": float(np.mean(st)), "round_robin": float(np.mean(rr)),
           "adaptive": float(np.mean(ad)), "oracle": float(np.mean(orc))}
    oracle = acc["oracle"]
    reg = {k: float(oracle - v) for k, v in acc.items()}

    c1 = acc["adaptive"] - acc["static"] >= 0.05
    c2 = reg["adaptive"] <= 0.5 * reg["static"]
    c3 = acc["adaptive"] >= 0.9 * oracle

    fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.2))
    xs = np.arange(1, len(curves["adaptive"][0]) + 1)
    for k, col in [("static", "#e76f51"), ("round_robin", "#e9c46a"), ("adaptive", "#2a9d8f")]:
        ax[0].plot(xs, np.mean(curves[k], axis=0), color=col, label=k)
    ax[0].axhline(oracle, color="k", ls="--", lw=1, label="oracle")
    ax[0].set(xlabel="van (200 van truot)", ylabel="accuracy truot", ylim=(0.4, 1.0),
              title="D11a: hoi bang model x kieu loi (adaptive) vs co dinh")
    ax[0].legend(fontsize=8)
    ax[0].grid(alpha=0.3)
    lbl = ["static", "round_robin", "adaptive", "oracle"]
    ax[1].bar(np.arange(4), [acc[k] for k in lbl],
              color=["#e76f51", "#e9c46a", "#2a9d8f", "#444"])
    ax[1].axhline(0.9 * oracle, color="k", ls="--", lw=1, label="90% oracle (c3)")
    ax[1].set_xticks(np.arange(4), lbl, fontsize=8)
    ax[1].set(ylim=(0.4, 1.0), title="D11b: accuracy cuoi cung (TB 10 seed)")
    ax[1].legend(fontsize=8)
    ax[1].grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(OUT / "d11_registry.png", dpi=110)
    plt.close(fig)

    results["D11"] = dict(
        acc={k: round(v, 3) for k, v in acc.items()},
        regret={k: round(v, 3) for k, v in reg.items()},
        c1_beats_static=bool(c1),
        c2_regret_halved=bool(c2),
        c3_within_10pct_of_oracle=bool(c3),
        PASS=bool(c1 and c2 and c3),
    )


if __name__ == "__main__":
    for fn in (d9, d10, d11):
        fn()
    n_pass = sum(r["PASS"] for r in results.values())
    lines = [json.dumps(results, indent=2, ensure_ascii=False),
             chr(10) + "KPI: " + str(n_pass) + "/3 module dat acceptance cua DS-003 sec 14"]
    text = chr(10).join(lines)
    print(text)
    (OUT / "summary.json").write_text(json.dumps(results, indent=2, ensure_ascii=False),
                                      encoding="utf-8")
    (OUT / "kpi.txt").write_text(text, encoding="utf-8")
