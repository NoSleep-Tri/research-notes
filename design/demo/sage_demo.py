# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy>=2.0", "matplotlib>=3.9"]
# ///
"""
SAGE v0.1 demo — 5 acceptance test của spec DS-001 §10.
Chạy trên Kaggle CPU (máy local không dùng).
Output: stdout + out/kpi.txt + out/summary.json + 5 PNG trong out/
  D1  học tuần tự → quên; replay vs grow (P3, F-K05)
  D2  ghi có cổng vs FIFO cùng capacity (P4)
  D3  proxy sai → Goodhart; holdout bắt được (P2, F-M04)
  D4  phòng thủ 2 tầng nhanh/chậm (Q-004)
  D5  scaffold gate theo confidence (P6, F-B02)
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

SEED = 42
rng = np.random.default_rng(SEED)
KAGGLE = Path("/kaggle/working").exists()
OUT = Path("/kaggle/working/out") if KAGGLE else Path(__file__).parent / "out"
OUT.mkdir(parents=True, exist_ok=True)
results: dict = {}


# ───────────────────────────────── D1: quên / replay / grow
def make_region(n, region, variant, r):
    """Region -1 = task A (XOR). Region +1 = task B ('threshold' hoặc 'conflict')."""
    u = r.uniform(-1, 1, n)
    v = r.uniform(-1, 1, n)
    X = np.zeros((n, 4))
    X[:, 0], X[:, 1], X[:, 2] = u, v, float(region)
    if region < 0:
        y = (u * v > 0).astype(int)
    elif variant == "threshold":
        y = (u > 0.3).astype(int)
    else:
        y = (u * v < 0).astype(int)
    return X, y


def fwd(net, X):
    W1, b1, W2, b2 = net
    a1 = np.tanh(X @ W1 + b1)
    z2 = a1 @ W2 + b2
    z2 -= z2.max(axis=1, keepdims=True)
    e = np.exp(z2)
    return e / e.sum(axis=1, keepdims=True), a1


def train(net, X, y, epochs=800, lr=0.3, aux=None, aux_frac=0.0, log=None, log_eval=None):
    W1, b1, W2, b2 = net
    Y = np.eye(2)[y]
    for ep in range(epochs):
        if aux is not None and aux_frac > 0:
            n_aux = int(round(len(y) * aux_frac / (1 - aux_frac)))
            Xa, Ya = aux
            k = rng.integers(0, len(Ya), n_aux)
            Xb = np.vstack([X, Xa[k]])
            Yb = np.vstack([Y, Ya[k]])
        else:
            Xb, Yb = X, Y
        p, a1 = fwd(net, Xb)
        g2 = (p - Yb) / len(Yb)
        W2 -= lr * (a1.T @ g2)
        b2 -= lr * g2.sum(axis=0)
        g1 = (g2 @ W2.T) * (1 - a1 * a1)
        W1 -= lr * (Xb.T @ g1)
        b1 -= lr * g1.sum(axis=0)
        if log is not None and ep % 20 == 0:
            ex, ey = log_eval if log_eval is not None else (X, y)
            log.append(acc(net, ex, ey))
    return net


def acc(net, X, y):
    p, _ = fwd(net, X)
    return float((p.argmax(1) == y).mean())


def new_net(h=5, seed=0):
    r = np.random.default_rng(seed)
    return [r.normal(0, 0.5, (4, h)), np.zeros(h), r.normal(0, 0.5, (h, 2)), np.zeros(2)]


def d1():
    XA, yA = make_region(1200, -1, "threshold", rng)
    XB1, yB1 = make_region(1200, +1, "threshold", rng)
    XB2, yB2 = make_region(1200, +1, "conflict", rng)
    XAt, yAt = make_region(600, -1, "threshold", rng)
    XB1t, yB1t = make_region(600, +1, "threshold", rng)
    XB2t, yB2t = make_region(600, +1, "conflict", rng)
    YAh = np.eye(2)[yA]

    HS = [4, 6, 8]
    per_h, curves = {}, {}
    for h in HS:
        row = {}
        for tag, Xb, yb, Xbt, ybt in [("B1_threshold", XB1, yB1, XB1t, yB1t),
                                      ("B2_conflict", XB2, yB2, XB2t, yB2t)]:
            net = new_net(h, 1)
            train(net, XA, yA)
            curve = [acc(net, XAt, yAt)]
            train(net, Xb, yb, log=curve, log_eval=(XAt, yAt))
            naive_A, naive_B = acc(net, XAt, yAt), acc(net, Xbt, ybt)

            net = new_net(h, 1)
            train(net, XA, yA)
            crep = [acc(net, XAt, yAt)]
            train(net, Xb, yb, aux=(XA, YAh), aux_frac=0.25, log=crep, log_eval=(XAt, yAt))
            rp_A, rp_B = acc(net, XAt, yAt), acc(net, Xbt, ybt)

            row[tag] = dict(naive_A=round(naive_A, 3), naive_B=round(naive_B, 3),
                            replay_A=round(rp_A, 3), replay_B=round(rp_B, 3),
                            naive_forget_pp=round((curve[0] - naive_A) * 100, 1),
                            replay_forget_pp=round((crep[0] - rp_A) * 100, 1))
            if h == 6:
                curves[tag] = (curve, crep)
        nA, nB = new_net(h, 1), new_net(h, 2)
        train(nA, XA, yA)
        grow_a0 = acc(nA, XAt, yAt)          # đo trước khi "học task B" (net B riêng)
        train(nB, XB1, yB1)
        grow_a1 = acc(nA, XAt, yAt)          # đo lại — net A không bị đụng tới
        row["grow"] = dict(A=round(grow_a1, 3), B=round(acc(nB, XB1t, yB1t), 3),
                           forget_pp=round((grow_a0 - grow_a1) * 100, 4))
        per_h[str(h)] = row

    gains = [per_h[str(h)]["B1_threshold"]["replay_A"] - per_h[str(h)]["B1_threshold"]["naive_A"]
             for h in HS]
    med_gain = float(np.median(gains))
    # "0% quên" = drop trước/sau giai đoạn học task B của net grow (metric tương đối, không absolute)
    grow_zero = all(abs(per_h[str(h)]["grow"]["forget_pp"]) < 0.01 for h in HS)
    grow_abs_ok = all(per_h[str(h)]["grow"]["A"] >= 0.98 for h in HS)
    ok = med_gain >= 0.20 and grow_zero and grow_abs_ok

    fig, ax = plt.subplots(1, 3, figsize=(13, 3.8))
    for i, tag in enumerate(["B1_threshold", "B2_conflict"]):
        if tag in curves:
            cr, cp = curves[tag]
            ax[0].plot(cr, label=f"naive ({tag.split('_')[0]})")
            ax[0].plot(cp, label=f"replay ({tag.split('_')[0]})")
    ax[0].set(xlabel="epoch (đang học task B)", ylabel="acc task A",
              title="D1: acc task A khi học task B (h=6)")
    ax[0].legend(fontsize=8); ax[0].grid(alpha=.3)
    x = np.arange(len(HS))
    nA = [per_h[str(h)]["B1_threshold"]["naive_A"] for h in HS]
    rA = [per_h[str(h)]["B1_threshold"]["replay_A"] for h in HS]
    gA = [per_h[str(h)]["grow"]["A"] for h in HS]
    ax[1].bar(x - .25, nA, .25, label="naive")
    ax[1].bar(x, rA, .25, label="replay 25%")
    ax[1].bar(x + .25, gA, .25, label="grow")
    ax[1].set_xticks(x, [f"h={h}" for h in HS]); ax[1].set_ylim(0, 1.05)
    ax[1].set_title("acc task A cuối (B1)"); ax[1].legend(fontsize=8); ax[1].grid(alpha=.3, axis="y")
    nB = [per_h[str(h)]["B1_threshold"]["naive_B"] for h in HS]
    rB = [per_h[str(h)]["B1_threshold"]["replay_B"] for h in HS]
    ax[2].bar(x - .15, nB, .3, label="naive")
    ax[2].bar(x + .15, rB, .3, label="replay")
    ax[2].set_xticks(x, [f"h={h}" for h in HS]); ax[2].set_ylim(0, 1.05)
    ax[2].set_title("acc task B cuối (B1)"); ax[2].legend(fontsize=8); ax[2].grid(alpha=.3, axis="y")
    fig.tight_layout(); fig.savefig(OUT / "d1_forgetting.png", dpi=110); plt.close(fig)

    results["D1"] = dict(per_h=per_h, median_gain_replay_minus_naive_taskA=round(med_gain, 3),
                         grow_zero_forgetting=bool(grow_zero), grow_abs_ge_98=bool(grow_abs_ok),
                         PASS=bool(ok))


# ───────────────────────────────── D2: ghi có cổng
def d2():
    N, K, W_STAKES = 3000, 200, 5.0
    critical = rng.random(N) < 0.05
    surprise = rng.exponential(1.0, N)
    score = surprise + W_STAKES * critical

    fifo: list[int] = []
    for i in range(N):
        fifo.append(i)
        if len(fifo) > K:
            fifo.pop(0)
    fifo = set(fifo)

    buf: dict[int, float] = {}
    THETA = 1.0
    for i in range(N):
        if score[i] < THETA:
            continue
        buf[i] = score[i]
        if len(buf) > K:
            del buf[min(buf, key=buf.get)]
    gated = set(buf)

    def recall(mask, kept):
        idx = np.where(mask)[0]
        return float(np.mean([i in kept for i in idx]))

    fifo_c, fifo_b = recall(critical, fifo), recall(~critical, fifo)
    gat_c, gat_b = recall(critical, gated), recall(~critical, gated)

    fig, ax = plt.subplots(figsize=(6.5, 4))
    x = np.arange(2)
    ax.bar(x - .18, [fifo_c, fifo_b], .36, label="FIFO (lưu hết)")
    ax.bar(x + .18, [gat_c, gat_b], .36, label="gated (surprise+stakes)")
    ax.set_xticks(x, ["recall QUAN TRỌNG", "recall nhảm"])
    ax.set(ylabel="recall", title=f"D2: cùng bộ nhớ K={K}, N={N}")
    ax.legend(); ax.grid(alpha=.3, axis="y")
    fig.tight_layout(); fig.savefig(OUT / "d2_gating.png", dpi=110); plt.close(fig)

    results["D2"] = dict(fifo_critical=round(fifo_c, 3), fifo_boring=round(fifo_b, 3),
                         gated_critical=round(gat_c, 3), gated_boring=round(gat_b, 3),
                         PASS=bool(gat_c >= 2 * fifo_c))


# ───────────────────────────────── D3: proxy sai → Goodhart
def d3():
    d, T = 10, 150
    xs = np.zeros((T, d))
    xs[:, 0] = -0.8                       # truth = -||x - xs||², đỉnh ở x0 = -0.8
    w3 = rng.normal(0, 1.5, (T, d)); b3 = rng.uniform(0, 6.3, T)
    w4 = rng.normal(0, 1.5, (T, d)); b4 = rng.uniform(0, 6.3, T)
    Ms = [1, 10, 100, 1000]
    tr, pr, vr = {m: [] for m in Ms}, {m: [] for m in Ms}, {m: [] for m in Ms}
    rb = []
    for t in range(T):
        pool = rng.uniform(-1, 1, (1000, d))
        f = -((pool - xs[t]) ** 2).sum(1)                       # truth
        g = 3 * pool[:, 0]                                      # proxy misspecified
        h = (f + 0.5 * np.sin(pool @ w3[t] + b3[t])
             + 0.3 * np.sin(pool @ w4[t] + b4[t]))              # holdout chính xác hơn
        rb.append(float(f.mean()))                             # baseline = chọn 1 bừa E[f]
        for M in Ms:
            idx = np.argsort(-g[:M])
            tr[M].append(float(f[idx[0]]))
            pr[M].append(float(g[idx[0]]))
            top = idx[:min(10, M)]
            vr[M].append(float(f[top[int(np.argmax(h[top]))]]))

    ms = np.array(Ms, float)
    T_, P_, V_ = ([np.mean(tr[m]) for m in Ms], [np.mean(pr[m]) for m in Ms],
                  [np.mean(vr[m]) for m in Ms])
    base_f = np.mean(rb)

    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot(ms, P_, "o-", label="proxy (người tối ưu THẤY)")
    ax.plot(ms, T_, "o-", label="truth (điểm THẬT)")
    ax.plot(ms, V_, "s--", label="truth + holdout verifier")
    ax.axhline(base_f, color="gray", ls=":", label="chọn bừa ngẫu nhiên E[f]")
    ax.set_xscale("log")
    ax.set(xlabel="số ứng viên thử M", ylabel="điểm TB",
           title="D3: Goodhart — optimize proxy, truth đi xuống")
    ax.legend(); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(OUT / "d3_goodhart.png", dpi=110); plt.close(fig)

    ok = (P_[-1] > P_[0] + 1) and (T_[-1] < T_[0] - 1) and (V_[-1] > T_[-1] + 0.5) \
        and (T_[-1] < base_f - 1)          # optimize tệ hơn cả bắn tỉa mù
    results["D3"] = dict(proxy_M1=round(P_[0], 2), proxy_M1000=round(P_[-1], 2),
                         truth_M1=round(T_[0], 2), truth_M1000=round(T_[-1], 2),
                         verifier_M1000=round(V_[-1], 2), random_baseline=round(base_f, 2),
                         PASS=bool(ok))


# ───────────────────────────────── D4: phòng thủ 2 tầng
def d4():
    N = 40000
    threat = rng.random(N) < 0.1
    e1 = rng.normal(np.where(threat, 1.5, 0.0), 1)     # tín hiệu nhanh (nhiễu)
    e2 = rng.normal(np.where(threat, 2.5, 0.0), 1)     # xác nhận chậm (rõ hơn)
    C_FP, C_FN, C_TEST = 10.0, 50.0, 2.0
    n_th = int(threat.sum())

    ts = np.linspace(-3, 4, 300)
    one = []
    for t in ts:
        ev = e1 > t
        cost = (C_FP * ((~threat) & ev).sum() + C_FN * (threat & ~ev).sum()) / N
        recall = 1 - (threat & ~ev).sum() / n_th
        one.append((cost, recall))
    one = np.array(one)

    t1s, t2s = np.linspace(-2.5, 3, 50), np.linspace(-2, 4, 60)
    two = np.zeros((len(t1s), len(t2s), 2))
    for i, a in enumerate(t1s):
        al = e1 > a
        for j, b in enumerate(t2s):
            ev = al & (e2 > b)
            cost = (C_FP * ((~threat) & ev).sum() + C_FN * (threat & ~ev).sum()
                    + C_TEST * al.sum()) / N
            recall = 1 - (threat & ~ev).sum() / n_th
            two[i, j] = (cost, recall)

    targets = np.linspace(0.80, 0.99, 20)
    c1s, c2s = [], []
    for R in targets:
        m1, m2 = one[:, 1] >= R, two[:, :, 1] >= R
        c1s.append(one[m1, 0].min() if m1.any() else np.nan)
        c2s.append(two[:, :, 0][m2].min() if m2.any() else np.nan)

    m1, m2 = one[:, 1] >= 0.95, two[:, :, 1] >= 0.95
    c1 = float(one[m1, 0].min()); c2 = float(two[:, :, 0][m2].min())

    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot(targets, c1s, label="1 tầng (quyết ngay)")
    ax.plot(targets, c2s, label="2 tầng (nhanh → chậm)")
    ax.axvline(0.95, color="k", ls=":", alpha=.5)
    ax.set(xlabel="recall (chặn được đe dọa)", ylabel="cost TB / kịch bản",
           title="D4: cùng recall → 2 tầng rẻ hơn")
    ax.legend(); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(OUT / "d4_twotier.png", dpi=110); plt.close(fig)

    results["D4"] = dict(cost_1tier_at_recall95=round(c1, 2), cost_2tier_at_recall95=round(c2, 2),
                         saving_pct=round(100 * (1 - c2 / c1), 1), PASS=bool(c2 < c1 * 0.9))


# ───────────────────────────────── D5: scaffold gate
def d5():
    N = 20000
    c = 0.40 + 0.60 * rng.beta(2, 2, N)                 # confidence (calibrated)
    correct_int = rng.random(N) < c                      # P(đúng | confidence) = confidence
    tool = rng.random(N) < 0.95                          # scaffold: 95%, cost 1
    shuffled = rng.permutation(correct_int)              # lệch calibration

    def frontier(ok, conf):
        order = np.argsort(conf)            # hỏi item TỰ THẤP confidence trước
        costs, accs = [], []
        for k in np.linspace(0, N, 101).astype(int):
            ask = np.zeros(N, bool)
            ask[order[:k]] = True
            costs.append(ask.mean())
            accs.append(np.where(ask, tool, ok).mean())
        return np.array(costs), np.array(accs)

    ca, aa = frontier(correct_int, c)
    cs, ash = frontier(shuffled, c)

    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot(ca, aa, "o-", label="gate theo confidence (calibrated)")
    ax.plot(cs, ash, "s--", label="gate (confidence lệch)")
    ax.scatter([0], [correct_int.mean()], color="r", zorder=5, label="không hỏi")
    ax.scatter([1], [tool.mean()], color="g", zorder=5, label="hỏi mọi thứ")
    ax.set(xlabel="tỷ lệ hỏi scaffold (cost)", ylabel="accuracy",
           title="D5: accuracy/cost frontier của scaffold")
    ax.legend(loc="lower right"); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(OUT / "d5_scaffold.png", dpi=110); plt.close(fig)

    i50 = int(np.searchsorted(ca, 0.50))
    acc50 = float(aa[i50])
    base = float(correct_int.mean())
    ask_all = float(tool.mean())
    linear50 = 0.5 * base + 0.5 * ask_all
    sh50 = float(ash[int(np.searchsorted(cs, 0.50))])
    ok = (acc50 >= 0.88) and (acc50 - linear50 >= 0.05) and (abs(sh50 - linear50) <= 0.015)
    results["D5"] = dict(internal_only=round(base, 3), ask_all=round(ask_all, 3),
                         gate_calibrated_at_50pct=round(acc50, 3),
                         naive_mix_at_50pct=round(linear50, 3),
                         gate_shuffled_at_50pct=round(sh50, 3),
                         PASS=bool(ok))


# ───────────────────────────────── main
if __name__ == "__main__":
    for fn in (d1, d2, d3, d4, d5):
        fn()
    n_pass = sum(r["PASS"] for r in results.values())
    lines = [json.dumps(results, indent=2, ensure_ascii=False),
             f"\nKPI: {n_pass}/5 module đạt acceptance của DS-001 §10"]
    text = "\n".join(lines)
    print(text)
    (OUT / "summary.json").write_text(json.dumps(results, indent=2, ensure_ascii=False),
                                      encoding="utf-8")
    (OUT / "kpi.txt").write_text(text, encoding="utf-8")
