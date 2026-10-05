# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy>=2.0", "matplotlib>=3.9"]
# ///
"""
DS-002 demo v4 - 3 acceptance test (D6-D8), spec SAGE sec 12. Chay tren Kaggle CPU.
  D6  U-curve lost-in-the-middle: hinh dang cong do phan bo loss, khong phai kien truc
      (F-A03, arXiv:2510.10276)
  D7  Quen deu pha kien thuc ngoai truc; directional forgetting giu duoc ca hai
      (F-X02, arXiv:2003.03523) + khong-quen-khong-chay-duoc-khi-thay-doi
  D8  Replay giu ca kien thuc lan kha nang hoc moi (F-X03, arXiv:2503.20018)
Output: stdout + out/summary.json + out/kpi.txt + 3 PNG
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

SEED = 42
rng = np.random.default_rng(SEED)
KAGGLE = Path("/kaggle/working").exists()
OUT = Path("/kaggle/working/out") if KAGGLE else Path(__file__).parent / "out2"
OUT.mkdir(parents=True, exist_ok=True)
results: dict = {}


# D6: U-curve lost-in-the-middle
L, V, P, H = 12, 6, 8, 8


def sinusoid(n_pos, dim):
    i = np.arange(n_pos, dtype=float)[:, None]
    w = 1.0 / (10000.0 ** (np.arange(dim // 2) / (dim // 2)))
    e = np.zeros((n_pos, dim))
    e[:, 0::2] = np.sin(i * w)
    e[:, 1::2] = np.cos(i * w)
    return e


def d6_model(mode, seed=7):
    r = np.random.default_rng(seed)
    D = V + P
    ep = sinusoid(L, P) if mode == "sin" else r.normal(0, 0.1, (L, P))
    return dict(
        Wk=r.normal(0, 1 / np.sqrt(D), (D, H)),
        Wv=r.normal(0, 1 / np.sqrt(D), (D, H)),
        Wq=r.normal(0, 1 / np.sqrt(P), (P, H)),
        Wo=r.normal(0, 1 / np.sqrt(H), (H, V)),
        Eb=r.normal(0, 0.05, (L,)),
        Ep=ep,
        trained=(mode != "sin"),
    )


def d6_fb(m, xs, q):
    ep = m["Ep"]
    lp = ep.shape[0]
    n = xs.shape[0]
    xe = np.eye(V)[xs]
    pe = np.broadcast_to(ep[None, :, :], (n, lp, P))
    x = np.concatenate([xe, pe], axis=2)
    qv = ep[q]
    wk, wv, wq, wo, eb = m["Wk"], m["Wv"], m["Wq"], m["Wo"], m["Eb"]
    qk = qv @ wq
    k = x @ wk
    s = (qk[:, None, :] * k).sum(-1) / np.sqrt(H) + eb[None, :]
    s -= s.max(axis=1, keepdims=True)
    a = np.exp(s)
    a /= a.sum(axis=1, keepdims=True)
    vv = x @ wv
    o = (a[:, :, None] * vv).sum(1)
    lg = o @ wo
    lg -= lg.max(axis=1, keepdims=True)
    pp = np.exp(lg)
    pp /= pp.sum(axis=1, keepdims=True)
    tgt = xs[np.arange(n), q]
    g = pp.copy()
    g[np.arange(n), tgt] -= 1.0
    dwo = o.T @ g
    do = g @ wo.T
    da = (do[:, None, :] * vv).sum(-1)
    dvv = a[:, :, None] * do[:, None, :]
    ds = a * (da - da.mean(axis=1, keepdims=True))
    dk = (qk[:, None, :] * ds[:, :, None]) / np.sqrt(H)
    dq = (ds[:, :, None] * k).sum(1) / np.sqrt(H)
    deb = ds.mean(axis=0)
    dx = dk @ wk.T + dvv @ wv.T
    grads = dict(
        Wk=np.einsum("blD,bld->Dd", x, dk),
        Wv=np.einsum("blD,bld->Dd", x, dvv),
        Wq=np.einsum("bp,bh->ph", qv, dq),
        Wo=dwo,
        Eb=deb,
    )
    if m["trained"]:
        dep = np.zeros_like(ep)
        np.add.at(dep, q, dq)
        dep += dx[:, :, V:].sum(axis=0)
        grads["Ep"] = dep
    return grads, pp


def d6_train(mode, regime, steps=3500, bs=64, lr=0.02, seed=7):
    m = d6_model(mode, seed)
    r = np.random.default_rng(seed + 11)
    keys = ["Wk", "Wv", "Wq", "Wo", "Eb"] + (["Ep"] if m["trained"] else [])
    mk = {kk: np.zeros_like(m[kk]) for kk in keys}
    vk = {kk: np.zeros_like(m[kk]) for kk in keys}
    b1, b2, eps, t = 0.9, 0.999, 1e-8, 0
    for _ in range(steps):
        if regime == "uniform":
            q = r.integers(0, L, bs)
        elif regime == "recency":
            q = np.full(bs, L - 1, int)
        else:
            q = np.where(r.random(bs) < 0.5, 0, L - 1).astype(int)
        xs = r.integers(0, V, (bs, L))
        grads, _ = d6_fb(m, xs, q)
        t += 1
        for kk in keys:
            g = grads[kk]
            mk[kk] = b1 * mk[kk] + (1 - b1) * g
            vk[kk] = b2 * vk[kk] + (1 - b2) * g * g
            mh = mk[kk] / (1 - b1 ** t)
            vh = vk[kk] / (1 - b2 ** t)
            m[kk] -= lr * mh / (np.sqrt(vh) + eps)
    return m


def d6_curve(m, n_test=400, seed=99):
    r = np.random.default_rng(seed)
    xs = r.integers(0, V, (n_test, L))
    out = []
    for p in range(L):
        _, pp = d6_fb(m, xs, np.full(n_test, p, int))
        out.append(float((pp.argmax(1) == xs[np.arange(n_test), p]).mean()))
    return out


def d6():
    arms = [("uniform", "learned"), ("recency", "learned"),
            ("uend", "learned"), ("uend", "sin")]
    curves = {}
    for reg, mode in arms:
        curves[reg + "_" + mode] = d6_curve(d6_train(mode, reg))
    mid = slice(L // 2 - 2, L // 2 + 2)

    u = curves["uniform_learned"]
    rc = curves["recency_learned"]
    ue = curves["uend_learned"]
    us = curves["uend_sin"]

    c1 = (float(np.mean(u)) >= 0.85) and ((max(u) - min(u)) <= 0.15)
    c2 = (rc[L - 1] - float(np.mean(rc[mid]))) >= 0.30
    u_gap = (ue[0] + ue[L - 1]) / 2 - float(np.mean(ue[mid]))
    c3 = u_gap >= 0.30

    fig, ax = plt.subplots(figsize=(7.5, 4.4))
    xs_pos = np.arange(L)
    for key, lab, st in [("uniform_learned", "uniform (khong U)", "-o"),
                         ("recency_learned", "recency (luon cuoi)", "-s"),
                         ("uend_learned", "U-prior + learned pos", "-^"),
                         ("uend_sin", "U-prior + sinusoid pos", "--d")]:
        ax.plot(xs_pos, curves[key], st, label=lab)
    ax.set(xlabel="vi tri trong context (0 = dau, 11 = cuoi)", ylabel="accuracy tai vi tri do",
           title="D6: hinh dang cong theo phan bo training loss, khong phai kien truc")
    ax.set_xticks(xs_pos)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "d6_u_curve.png", dpi=110)
    plt.close(fig)

    results["D6"] = dict(
        uniform_mean=round(float(np.mean(u)), 3),
        uniform_spread=round(max(u) - min(u), 3),
        recency_gap_end_minus_mid=round(rc[L - 1] - float(np.mean(rc[mid])), 3),
        uend_gap_ends_minus_mid=round(u_gap, 3),
        uend_mid=round(float(np.mean(ue[mid])), 3),
        sinusoid_mid=round(float(np.mean(us[mid])), 3),
        sinusoid_mid_gain=round(float(np.mean(us[mid]) - np.mean(ue[mid])), 3),
        curves={k: [round(v, 3) for v in vv] for k, vv in curves.items()},
        c1_uniform_flat_high=bool(c1),
        c2_recency=bool(c2),
        c3_u_curve=bool(c3),
        PASS=bool(c1 and c2 and c3),
    )


# D7: directional vs uniform forgetting (RLS)
def d7_run(arm, seed=0, sigma=0.01):
    d = 6
    r = np.random.default_rng(seed)
    theta = r.normal(0, 1, d)
    th = np.zeros(d)
    pcov = np.eye(d) * 100.0
    lam, sig2 = 0.995, sigma * sigma

    def step(x, y):
        nonlocal th, pcov
        if arm == "uniform":
            pcov /= lam
        elif arm == "variable":
            px = pcov @ x
            q = float(x @ px)
            if q > 1e-14:
                pcov += (1.0 / lam - 1.0) * np.outer(px, px) / q
        kg = (pcov @ x) / (sig2 + float(x @ pcov @ x) + 1e-18)
        th = th + kg * (y - float(x @ th))
        pcov = pcov - np.outer(kg, x @ pcov)

    def run(n, cov, rec=None, mutate=None):
        cov = np.asarray(cov, float)
        for i in range(n):
            if mutate is not None and i == 0:
                mutate()
            x = r.normal(0, 1, d) * np.sqrt(cov)
            y = float(theta @ x) + r.normal(0, sigma)
            step(x, y)
            if rec is not None:
                rec(i)

    def ms(idx):
        sl = slice(*idx)
        return float(np.mean((th[sl] - theta[sl]) ** 2))

    run(400, [1, 1, 1, 0, 0, 0])
    keep_p1 = ms((0, 3))
    run(2000, [0, 0, 0, 1, 1, 1])
    learned_new = ms((3, 6))

    p3 = []
    run(600, [0.05, 0.05, 0.05, 0, 0, 0], rec=lambda i: p3.append(ms((0, 3))))

    p4 = []
    WIN = 400

    def bump():
        theta[3:6] += 1.0

    run(500, [0, 0, 0, 1, 1, 1],
        rec=lambda i: p4.append(ms((3, 6))) if i < WIN else None,
        mutate=bump)
    return dict(p1_end_mse_dims02=keep_p1, p2_end_mse_dims35=learned_new,
                p3_mse_dims02=float(np.mean(p3)), p4_adapt_mse_dims35=float(np.mean(p4)),
                p3_series=p3[::10], p4_series=p4[::25])


def d7():
    arms = {a: d7_run(a, seed=3) for a in ("uniform", "variable", "noforgetting")}
    pv, pu, pn = arms["variable"], arms["uniform"], arms["noforgetting"]
    c1 = pu["p3_mse_dims02"] / max(pv["p3_mse_dims02"], 1e-18) >= 3.0
    c2 = pn["p4_adapt_mse_dims35"] / max(pu["p4_adapt_mse_dims35"], 1e-18) >= 2.0
    c3 = (pv["p2_end_mse_dims35"] / max(pu["p2_end_mse_dims35"], 1e-18)) <= 5.0

    fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.2))
    for a in arms:
        ax[0].plot(arms[a]["p3_series"], label=a)
    ax[0].set_yscale("log")
    ax[0].set(xlabel="buoc (P3: chi co excitation yeu o dim 0-2)", ylabel="MSE dim 0-2",
              title="D7a: quen deu pha duong ngoai truc du lieu moi")
    ax[0].legend(fontsize=8)
    ax[0].grid(alpha=0.3)
    for a in arms:
        ax[1].plot(arms[a]["p4_series"], label=a)
    ax[1].set_yscale("log")
    ax[1].set(xlabel="buoc sau khi theta[3:6] nhay +1.0 (cua so 400 buoc)", ylabel="MSE dim 3-5",
              title="D7b: khong quen = khong the thich nghi khi doi")
    ax[1].legend(fontsize=8)
    ax[1].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "d7_directional_forget.png", dpi=110)
    plt.close(fig)

    out = {}
    for a, v in arms.items():
        out[a] = {k: (float(format(x, ".3e"))) for k, x in v.items() if not k.endswith("series")}
    results["D7"] = dict(
        **out,
        ratio_uniform_over_variable_P3=round(
            pu["p3_mse_dims02"] / max(pv["p3_mse_dims02"], 1e-18), 2),
        ratio_noforget_over_uniform_P4=round(
            pn["p4_adapt_mse_dims35"] / max(pu["p4_adapt_mse_dims35"], 1e-18), 2),
        ratio_noforget_over_variable_P4=round(
            pn["p4_adapt_mse_dims35"] / max(pv["p4_adapt_mse_dims35"], 1e-18), 2),
        c1_uniform_destroys_offaxis=bool(c1),
        c2_noforget_cannot_adapt=bool(c2),
        c3_variable_learns_new_dims=bool(c3),
        PASS=bool(c1 and c2 and c3),
    )


# D8: replay giu kien thuc + kha nang hoc
NF, HID, KTRAIN = 8, 12, 5
BASE_W = None
PERMS = None


def d8_features(u, v):
    return np.stack([u, v, u * v, u * u - v * v, np.sin(3 * u), np.cos(3 * v),
                     np.abs(u) - np.abs(v), u * v * (u - v)], axis=1)


def d8_setup(n_task, min_acc=0.95, tries=25):
    """Task k = cung bo dau vao NHUNG da hoan vi cot; nhan tinh toan tren bo goc.
    -> xung dot giua cac task la co y (cung cot W1, khac thu tu) nhung van phan
    biet duoc, cho replay co the giu duoc. Moi task bat buoc hoc duoc boi net
    moi tinh truoc khi vao chuoi (harness fix DS-002 lan 2)."""
    r = np.random.default_rng(777)
    w0 = r.choice([-1.0, 1.0], NF)
    perms, accs, ntry = [], [], []
    for k in range(n_task):
        rb = np.random.default_rng(3000 + k)
        Xb = d8_features(rb.uniform(-1, 1, 900), rb.uniform(-1, 1, 900))
        yb = ((Xb @ w0) > 0).astype(int)
        best_p, best_a = None, -1.0
        for t in range(tries):
            pm = r.permutation(NF)
            net = d8_new(2)
            d8_train(net, Xb[:600, pm], yb[:600], epochs=350)
            a = d8_acc(net, Xb[600:, pm], yb[600:])
            if a > best_a:
                best_p, best_a = pm, a
            if a >= min_acc:
                break
        perms.append(best_p)
        accs.append(round(best_a, 3))
        ntry.append(t + 1)
    return w0, np.array(perms), accs, ntry


def d8_gen(k, n, r):
    u = r.uniform(-1, 1, n)
    v = r.uniform(-1, 1, n)
    X = d8_features(u, v)
    y = ((X @ BASE_W) > 0).astype(int)
    return X[:, PERMS[k]], y


def d8_new(seed=1):
    r = np.random.default_rng(seed)
    return [r.normal(0, 0.5, (NF, HID)), np.zeros(HID),
            r.normal(0, 0.5, (HID, 2)), np.zeros(2)]


def d8_fwd(net, X):
    w1, b1, w2, b2 = net
    a = np.tanh(X @ w1 + b1)
    z = a @ w2 + b2
    z -= z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True), a


def d8_train(net, X, y, epochs=500, lr=0.3, aux=None, aux_frac=0.0):
    w1, b1, w2, b2 = net
    yy = np.eye(2)[y]
    aux_y = None
    if aux is not None:
        aux_y = np.eye(2)[aux[1]]
    for _ in range(epochs):
        if aux is not None and aux_frac > 0:
            n_aux = int(round(len(y) * aux_frac / (1 - aux_frac)))
            k = np.random.randint(0, len(aux_y), n_aux)
            xb = np.vstack([X, aux[0][k]])
            yb = np.vstack([yy, aux_y[k]])
        else:
            xb, yb = X, yy
        p, a = d8_fwd(net, xb)
        g2 = (p - yb) / len(yb)
        w2 -= lr * (a.T @ g2)
        b2 -= lr * g2.sum(axis=0)
        g1 = (g2 @ w2.T) * (1 - a * a)
        w1 -= lr * (xb.T @ g1)
        b1 -= lr * g1.sum(axis=0)
    return net


def d8_acc(net, X, y):
    p, _ = d8_fwd(net, X)
    return float((p.argmax(1) == y).mean())


def d8():
    global BASE_W, PERMS
    BASE_W, PERMS, vacc, vtries = d8_setup(KTRAIN + 1)
    tr = np.random.default_rng(101)
    te = np.random.default_rng(102)
    tr_sets = [d8_gen(k, 900, tr) for k in range(KTRAIN)]
    tr_hold = d8_gen(KTRAIN, 900, tr)
    te_sets = [d8_gen(k, 400, te) for k in range(KTRAIN + 1)]
    old = list(range(KTRAIN - 1))

    arms = {}
    for arm in ("naive", "replay", "decay"):
        net = d8_new(1)
        buf = []
        for k in range(KTRAIN):
            X, y = tr_sets[k]
            aux, frac = None, 0.0
            if arm == "replay" and buf:
                aux = (np.vstack([b[0] for b in buf]), np.hstack([b[1] for b in buf]))
                frac = 0.30
            d8_train(net, X, y, aux=aux, aux_frac=frac)
            if arm == "replay":
                buf.append((X[:150].copy(), y[:150].copy()))
            if arm == "decay":
                net[0] *= 0.90
                net[2] *= 0.90
        arms[arm] = net
    arms["reset"] = d8_new(1)
    d8_train(arms["reset"], *tr_sets[KTRAIN - 1])

    def mean_old(net, ks):
        return float(np.mean([d8_acc(net, *te_sets[k]) for k in ks]))

    ret_old = {a: mean_old(n, old) for a, n in arms.items()}
    ret_all = {a: mean_old(n, list(range(KTRAIN))) for a, n in arms.items()}

    fresh = d8_new(2)
    d8_train(fresh, *tr_hold)
    acc_fresh = d8_acc(fresh, *te_sets[KTRAIN])
    plasticity = {}
    for a, n in arms.items():
        c = deepcopy(n)
        d8_train(c, *tr_hold)
        plasticity[a] = d8_acc(c, *te_sets[KTRAIN]) / max(acc_fresh, 1e-9)

    r_rp, r_na, r_dc = ret_old["replay"], ret_old["naive"], ret_old["decay"]
    c1 = r_rp >= r_na + 0.15
    c2 = r_dc <= r_rp - 0.10
    c3 = plasticity["replay"] >= 0.85

    fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.2))
    names = ["naive", "replay", "decay", "reset"]
    ax[0].bar(np.arange(4), [ret_old[a] for a in names],
              color=["#888", "#2a9d8f", "#e76f51", "#bbb"])
    ax[0].axhline(0.5, color="k", ls="--", lw=1, label="chance (=0.5)")
    ax[0].set_xticks(np.arange(4), names)
    ax[0].set(ylabel="acc TB cac task CU (0..K-2)", ylim=(0, 1.05),
              title="D8a: retention cua task cu sau 5 task")
    ax[0].legend(fontsize=8)
    ax[0].grid(alpha=0.3, axis="y")
    ax[1].bar(np.arange(3), [plasticity[a] for a in ("naive", "replay", "decay")],
              color=["#888", "#2a9d8f", "#e76f51"])
    ax[1].axhline(1.0, color="k", ls="--", lw=1, label="fresh net (=1.0)")
    ax[1].set_xticks(np.arange(3), ["naive", "replay", "decay"])
    ax[1].set(ylabel="acc / acc(fresh) tren task moi", ylim=(0, 1.15),
              title="D8b: kha nang hoc task moi so voi net moi")
    ax[1].legend(fontsize=8)
    ax[1].grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(OUT / "d8_replay_plasticity.png", dpi=110)
    plt.close(fig)

    results["D8"] = dict(
        task_verify_acc=vacc,
        task_verify_tries=vtries,
        retention_old={a: round(v, 3) for a, v in ret_old.items()},
        retention_all={a: round(v, 3) for a, v in ret_all.items()},
        plasticity_ratio={a: round(v, 3) for a, v in plasticity.items()},
        fresh_holdout_acc=round(acc_fresh, 3),
        naive_plasticity_loss_pct=round(100 * (1 - plasticity["naive"]), 1),
        c1_replay_beats_naive_retention=bool(c1),
        c2_uniform_decay_does_not_help=bool(c2),
        c3_replay_keeps_plasticity=bool(c3),
        PASS=bool(c1 and c2 and c3),
    )


if __name__ == "__main__":
    for fn in (d6, d7, d8):
        fn()
    n_pass = sum(r["PASS"] for r in results.values())
    lines = [json.dumps(results, indent=2, ensure_ascii=False),
             chr(10) + "KPI: " + str(n_pass) + "/3 module dat acceptance cua DS-002 sec 12"]
    text = chr(10).join(lines)
    print(text)
    (OUT / "summary.json").write_text(json.dumps(results, indent=2, ensure_ascii=False),
                                      encoding="utf-8")
    (OUT / "kpi.txt").write_text(text, encoding="utf-8")
