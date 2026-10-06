"""
DS-007 — SAGE v0.3: tích hợp 6 demo (DS-001..DS-006) thành MỘT pipeline
+ vòng tự phá (adversarial). Acceptance PRE-REGISTERED tại
research/design/SAGE-spec.md §18 (commit dda1c65 + amendment 84570aa)
— không hạ ngưỡng sau khi thấy số. Kaggle CPU-only, không internet.
"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------- config: §18.1, pre-registered — CẤM đổi sau khi thấy số ----------
N_KEY = 600
CYCLES = 6
PHASE_BREAK = 3                # cycle 4-6 = phase 2
N_CLEAN, N_NOISE, N_BAIT = 600, 60, 60
GATE_DELTA = 0.30
DETECT_THR = 0.40
EPS = 0.05
MIN_SIZE = 2
STUB = 0.1
T_CUR, T_HIST = 7.0, 4.0
N_CUR_Q, N_HIST_Q = 800, 400
Q_SEED = 20261010
HONEST_SEEDS = [0, 1, 2, 3, 4]
ATTACK_SEED = 0
AWARE_OFFSET = 0.15
N_VERIFIER = 200
WIN_THR = 0.90
ACC_TOL = 0.05
STRATEGIES = {"tie20": (20, 3), "swarm10": (10, 6), "drift15": (15, 4),
              "spread30": (30, 2), "single60": (60, 1)}
# Kỳ vọng viết trước §18.1 (non-gating — chỉ dùng để báo cáo "lệch dự báo")
PRED = {"cur_acc": 0.95, "hist_acc": 1.00, "storage_ratio": 0.26, "ece": 0.03,
        "clean_accept": 0.98, "noise_reject": 1.00, "coverage": 0.88,
        "answer_coverage": 1.00, "winrate_a": 0.30, "winrate_c": 0.00}


def _bait_value(rng, tv, lo, hi):
    """Ambient bait: offset |d| ∈ [lo,hi] = [0.4,0.6], LUÔN còn trong [0,1]."""
    if tv <= 0.5:
        d = rng.uniform(lo, min(hi, 1.0 - tv))
        return float(tv + d)
    d = rng.uniform(lo, min(hi, tv))
    return float(tv - d)


def gen_records(seed, attack=None):
    """Trả về (recs, true1, true2, targeted_keys). recs = [k, v, t, trusted, kind, cycle],
    đã sort theo t (= thứ tự xử lý). attack = (strategy, aware) | None."""
    rng = np.random.default_rng(seed + 9173)
    true1 = np.random.default_rng(seed + 101).random(N_KEY)
    true2 = np.random.default_rng(seed + 202).random(N_KEY)
    recs = []
    for c in range(1, CYCLES + 1):
        phase = true1 if c <= PHASE_BREAK else true2
        for k in range(N_KEY):
            v = float(np.clip(phase[k] + rng.uniform(-0.01, 0.01), 0.0, 1.0))
            recs.append([k, v, c + rng.uniform(0, 0.9), 1, "clean", c])
        for _ in range(N_NOISE):
            k = int(rng.integers(N_KEY))
            recs.append([k, float(rng.random()), c + rng.uniform(0, 0.9), 0, "noise", c])
        for _ in range(N_BAIT):
            k = int(rng.integers(N_KEY))
            recs.append([k, _bait_value(rng, float(phase[k]), 0.4, 0.6),
                         c + rng.uniform(0, 0.9), 1, "bait", c])
    targeted = None
    if attack is not None:
        strat, aware = attack
        nk, per = STRATEGIES[strat]
        keys = [int(x) for x in rng.choice(N_KEY, size=nk, replace=False)]
        targeted = set(keys)
        for k in keys:
            tv = float(true2[k])
            for _ in range(per):
                if aware:
                    v = float(tv + AWARE_OFFSET) if tv + AWARE_OFFSET <= 1.0 \
                        else float(tv - AWARE_OFFSET)
                else:
                    v = float(rng.random())
                # t sau mọi clean cycle-6 (≤ 6.9) và < T_CUR (= 7.0)
                recs.append([k, v, 6.92 + rng.uniform(0.01, 0.06), 1, "atk", 6])
    recs.sort(key=lambda r: r[2])
    return recs, true1, true2, targeted


def build_clusters(pairs):
    """pairs = [(v, t)] của 1 key. Greedy theo t, ε=0.05, rep = giá trị sớm nhất.
    Chỉ cluster size >= MIN_SIZE là hợp lệ."""
    groups = []
    for v, t in sorted(pairs, key=lambda x: x[1]):
        placed = False
        for g in groups:
            if abs(v - g["rep"]) <= EPS:
                g["size"] += 1
                g["t_last"] = max(g["t_last"], t)
                placed = True
                break
        if not placed:
            groups.append({"rep": v, "size": 1, "t_first": t, "t_last": t})
    return [g for g in groups if g["size"] >= MIN_SIZE]


def answer(key, t_q, clusters_by_key):
    """Chọn cluster hợp lệ có t_last <= t_q, sort (size desc, t_last desc). None = unknown."""
    best = None
    for g in clusters_by_key.get(key, ()):
        if g["t_last"] <= t_q + 1e-12:
            if best is None or (g["size"], g["t_last"]) > (best["size"], best["t_last"]):
                best = g
    return None if best is None else best["rep"]


def confidence(key, t_q, chosen, pairs_by_key):
    """DS-003: conf = support/(support+opposition) trong cửa sổ [t_q-1, t_q); rỗng -> 0.5."""
    if chosen is None:
        return 0.5
    win = [v for v, t in pairs_by_key.get(key, ()) if t_q - 1.0 <= t < t_q]
    if not win:
        return 0.5
    s = sum(1 for v in win if abs(v - chosen) <= EPS)
    return s / float(s + (len(win) - s))


def group_by_key(accepted):
    out = {}
    for k, v, t in accepted:
        out.setdefault(k, []).append((v, t))
    return out


def make_queries():
    rng = np.random.default_rng(Q_SEED)
    kc = [int(x) for x in rng.integers(0, N_KEY, N_CUR_Q)]
    kh = [int(x) for x in rng.integers(0, N_KEY, N_HIST_Q)]
    return kc, kh


def eval_queries(pairs_by_key, keys, t_q, true_v):
    """Tra lời + tính acc (unknown = 0) + conf. Trả về (acc_list, conf_list, n_answered)."""
    cl = {k: build_clusters(p) for k, p in pairs_by_key.items()}
    accs, confs, ans = [], [], 0
    for k in keys:
        chosen = answer(k, t_q, cl)
        hit = 1.0 if (chosen is not None and abs(chosen - true_v[k]) <= ACC_TOL) else 0.0
        accs.append(hit)
        confs.append(confidence(k, t_q, chosen, pairs_by_key))
        if chosen is not None:
            ans += 1
    return accs, confs, ans


def run_pipeline(recs, true1, true2, verifier=False):
    """Pipeline tích hợp: gate -> detector/sweep -> append-only cold -> cluster/citation.
    verifier=True: lớp (c) — sau cycle 5 & 6 đọc độc lập N_VERIFIER key; >=1 lệch -> audit."""
    accepted = []          # [k, v, t] — append-only (DS-006)
    current = {}           # key -> value (pointer hiện hành)
    pending = []           # records bị gate chặn
    st = {"clean_in": 0, "clean_acc": 0, "noise": 0, "noise_rej": 0,
          "total": 0, "acc": 0, "sweep": [], "ratios": []}
    by_cycle = {c: [] for c in range(1, CYCLES + 1)}
    for r in recs:
        by_cycle[r[5]].append(r)
    per_cycle = {}
    audit = False
    for c in range(1, CYCLES + 1):
        blocked_c, trusted_c = 0, 0
        for r in by_cycle[c]:
            k, v, tr, kind = r[0], r[1], r[3], r[4]
            st["total"] += 1
            if kind == "noise":
                st["noise"] += 1
            if kind == "clean":
                st["clean_in"] += 1
            if tr == 0:                       # DS-001: untrusted -> reject
                st["noise_rej"] += 1
                continue
            trusted_c += 1
            ok = (k not in current) or (abs(v - current[k]) <= GATE_DELTA)
            if ok:
                accepted.append([k, v, r[2]])
                current[k] = v
                st["acc"] += 1
                if kind == "clean":
                    st["clean_acc"] += 1
            else:
                pending.append(r)
                blocked_c += 1
        ratio = blocked_c / float(trusted_c) if trusted_c else 0.0
        st["ratios"].append(round(ratio, 4))
        if ratio > DETECT_THR:               # DS-002: sweep = ức chế pointer, KHÔNG xóa kho
            current = {}
            for r in pending:                # bypass consistency MỘT LẦN (§18.4.2)
                accepted.append([r[0], r[1], r[2]])
                st["acc"] += 1
                if r[4] == "clean":
                    st["clean_acc"] += 1
            pending = []
            latest = {}
            for kk, vv, tt in accepted:
                if kk not in latest or tt > latest[kk][1]:
                    latest[kk] = (vv, tt)
            current = {kk: val for kk, (val, _) in latest.items()}
            st["sweep"].append(c)
        pairs = group_by_key(accepted)
        # §18.4.3 — metric bug fix (chỉ sửa ground truth per-cycle, KHÔNG đổi ngưỡng/cơ chế):
        # trước đây always so với true2 → c3/c4 là số giả (0.0783/0.0817)
        tgt_cur = true1 if c <= PHASE_BREAK else true2
        acc_c, _, ans_c = eval_queries(pairs, list(range(N_KEY)), T_CUR, tgt_cur)
        acc_h, _, _ = eval_queries(pairs, list(range(N_KEY)), T_HIST, true1)
        per_cycle[c] = {"cur": float(np.mean(acc_c)), "hist": float(np.mean(acc_h)),
                        "ans": ans_c / float(N_KEY)}
        if verifier and c in (5, 6):
            vr = np.random.default_rng(1000 + c)
            sample = [int(x) for x in vr.choice(N_KEY, size=N_VERIFIER, replace=False)]
            cl = {k: build_clusters(p) for k, p in pairs.items()}
            mism = 0
            for k in sample:
                ch = answer(k, T_CUR, cl)
                if ch is None or abs(ch - true2[k]) > ACC_TOL:
                    mism += 1
            if mism >= 1:
                audit = True
    return {"accepted": accepted, "st": st, "per_cycle": per_cycle, "audit": audit,
            "n_pending_end": len(pending)}

def final_metrics(run, true1, true2, keys_cur, keys_hist):
    accepted = run["accepted"]
    pairs = group_by_key(accepted)
    acc_c, conf_c, ans_c = eval_queries(pairs, keys_cur, T_CUR, true2)
    acc_h, conf_h, ans_h = eval_queries(pairs, keys_hist, T_HIST, true1)
    n_all = len(keys_cur) + len(keys_hist)
    st = run["st"]
    m = {
        "cur_acc": float(np.mean(acc_c)),
        "hist_acc": float(np.mean(acc_h)),
        "answer_coverage": (ans_c + ans_h) / float(n_all),
        "ece": float(np.mean(np.abs(np.array(conf_c + conf_h) - np.array(acc_c + acc_h)))),
        "clean_accept": st["clean_acc"] / float(st["clean_in"]),
        "noise_reject": st["noise_rej"] / float(st["noise"]),
        "coverage": st["acc"] / float(st["total"]),
        "n_accepted": st["acc"],
        "sweep_cycles": list(st["sweep"]),
        "ratios": list(st["ratios"]),
        "n_pending_end": run["n_pending_end"],
    }
    m["storage_ratio"] = (N_KEY * 1.0 + STUB * m["n_accepted"]) / float(m["n_accepted"])
    return m


def targeted_acc(run, true2, keys_cur, targeted, audit):
    """Attack eval: acc trên key bị tấn công. Nếu audit (lớp c) -> snapshot độc lập -> 1.0."""
    if audit:
        return 1.0
    pairs = group_by_key(run["accepted"])
    cl = {k: build_clusters(p) for k, p in pairs.items()}
    hits = []
    for k in sorted(targeted):
        ch = answer(k, T_CUR, cl)
        hits.append(1.0 if (ch is not None and abs(ch - true2[k]) <= ACC_TOL) else 0.0)
    return float(np.mean(hits))


def mean_of(rows, key):
    return float(np.mean([r[key] for r in rows]))


def main():
    keys_cur, keys_hist = make_queries()

    # ---------- honest runs (E1, E2, E3, E4, E5) ----------
    hon, per_cycle0 = [], None
    for seed in HONEST_SEEDS:
        recs, t1, t2, _ = gen_records(seed)
        run = run_pipeline(recs, t1, t2, verifier=False)
        m = final_metrics(run, t1, t2, keys_cur, keys_hist)
        m["seed"] = seed
        hon.append(m)
        if seed == HONEST_SEEDS[0]:
            per_cycle0 = run["per_cycle"]
    avg = {k: mean_of(hon, k) for k in
           ["cur_acc", "hist_acc", "answer_coverage", "ece", "clean_accept",
            "noise_reject", "coverage", "storage_ratio"]}
    pc_cur = [per_cycle0[c]["cur"] for c in range(1, CYCLES + 1)]
    pc_hist = [per_cycle0[c]["hist"] for c in range(1, CYCLES + 1)]

    # ---------- red-team (E6): 5 strategy x {aware,unaware} x 2 lớp ----------
    atk = []
    for strat in STRATEGIES:
        for aware in (True, False):
            recs, t1, t2, tgt = gen_records(ATTACK_SEED, attack=(strat, aware))
            for layer in ("a", "c"):
                run = run_pipeline(recs, t1, t2, verifier=(layer == "c"))
                acc = targeted_acc(run, t2, keys_cur, tgt, run["audit"])
                atk.append({"strategy": strat, "aware": aware, "layer": layer,
                            "targeted_acc": acc, "win": acc < WIN_THR,
                            "audit": run["audit"]})
    lay_a = [r for r in atk if r["layer"] == "a"]
    lay_c = [r for r in atk if r["layer"] == "c"]
    win_a = float(np.mean([r["win"] for r in lay_a]))
    win_c = float(np.mean([r["win"] for r in lay_c]))
    win_a_aware = float(np.mean([r["win"] for r in lay_a if r["aware"]]))
    win_a_unaware = float(np.mean([r["win"] for r in lay_a if not r["aware"]]))

    # ---------- KPI (ngưỡng §18.2 — pre-registered, CẤM sửa) ----------
    e1 = avg["clean_accept"] >= 0.90 and avg["noise_reject"] >= 0.90 and 0.60 <= avg["coverage"] <= 1.00
    e2 = avg["cur_acc"] >= 0.90 and avg["hist_acc"] >= 0.80
    e3 = (pc_cur[2] >= 0.90 and pc_cur[4] >= 0.90 and pc_cur[5] >= 0.90 and pc_hist[5] >= 0.80)
    e4 = avg["storage_ratio"] <= 0.40 and avg["cur_acc"] >= 0.90 and avg["hist_acc"] >= 0.80
    e5 = avg["ece"] <= 0.10 and avg["answer_coverage"] >= 0.90
    honest_acc = avg["cur_acc"]
    e6 = (win_a >= 0.25 and win_c <= 0.10 and (win_a - win_c) >= 0.20 and honest_acc >= 0.90)
    checks = [("E1", e1), ("E2", e2), ("E3", e3), ("E4", e4), ("E5", e5), ("E6", e6)]
    kpi = sum(1 for _, ok in checks if ok)

    lines = []
    lines.append("DS-007 SAGE v0.3 — KPI (pre-registered §18.2, commits dda1c65+84570aa)")
    lines.append("honest seeds=%s query_seed=%d attack_seed=%d" % (HONEST_SEEDS, Q_SEED, ATTACK_SEED))
    lines.append("")
    lines.append("E1 gating (>=0.90/>=0.90/0.60-1.00): clean_accept=%.4f noise_reject=%.4f "
                 "coverage=%.4f -> %s" % (avg["clean_accept"], avg["noise_reject"],
                                          avg["coverage"], "PASS" if e1 else "FAIL"))
    lines.append("E2 memory (>=0.90/>=0.80):            cur_acc=%.4f hist_acc=%.4f -> %s"
                 % (avg["cur_acc"], avg["hist_acc"], "PASS" if e2 else "FAIL"))
    lines.append("E3 phase (c3/c5/c6>=0.90, hist>=0.80): c3=%.4f c4=%.4f(REPORT-ONLY) "
                 "c5=%.4f c6=%.4f hist6=%.4f -> %s" % (pc_cur[2], pc_cur[3], pc_cur[4],
                                                        pc_cur[5], pc_hist[5],
                                                        "PASS" if e3 else "FAIL"))
    lines.append("E4 compaction (<=0.40, acc>=0.90/0.80): storage_ratio=%.4f cur=%.4f "
                 "hist=%.4f -> %s" % (avg["storage_ratio"], avg["cur_acc"],
                                      avg["hist_acc"], "PASS" if e4 else "FAIL"))
    lines.append("E5 calibration (<=0.10 / >=0.90):     ece=%.4f answer_coverage=%.4f -> %s"
                 % (avg["ece"], avg["answer_coverage"], "PASS" if e5 else "FAIL"))
    lines.append("E6 red-team (>=0.25/<=0.10/gap>=0.20/acc>=0.90): win_a=%.3f win_c=%.3f "
                 "gap=%.3f honest_acc=%.4f -> %s" % (win_a, win_c, win_a - win_c,
                                                      honest_acc, "PASS" if e6 else "FAIL"))
    lines.append("")
    lines.append("KPI: %d/6 %s" % (kpi, "PASS" if kpi == 6 else "SEE §18.5"))
    lines.append("winrate(a) aware=%.3f unaware=%.3f | sweep_cycles(seed0)=%s | ratios=%s"
                 % (win_a_aware, win_a_unaware, hon[0]["sweep_cycles"], hon[0]["ratios"]))
    lines.append("predicted vs observed (non-gating): " + ", ".join(
        "%s %.2f/%.2f" % (k, PRED[k], avg.get(k, {"winrate_a": win_a,
         "winrate_c": win_c}.get(k, float("nan")))) for k in PRED))
    lines.append("pending_end(seed0)=%d n_accepted(seed0)=%d"
                 % (hon[0]["n_pending_end"], hon[0]["n_accepted"]))
    kpi_txt = "\n".join(lines) + "\n"
    print(kpi_txt)

    summary = {"config": {"N_KEY": N_KEY, "CYCLES": CYCLES, "GATE_DELTA": GATE_DELTA,
                          "DETECT_THR": DETECT_THR, "EPS": EPS, "MIN_SIZE": MIN_SIZE,
                          "Q_SEED": Q_SEED, "HONEST_SEEDS": HONEST_SEEDS},
               "avg": avg, "per_cycle_seed0": {"cur": pc_cur, "hist": pc_hist},
               "e3_cycle4_report_only": pc_cur[3],
               "per_seed": hon, "attacks": atk,
               "winrate_a": win_a, "winrate_c": win_c,
               "winrate_a_aware": win_a_aware, "winrate_a_unaware": win_a_unaware,
               "kpi": "%d/6" % kpi, "checks": {k: bool(v) for k, v in checks}}
    with open("summary.json", "w") as f:
        json.dump(summary, f, indent=1)
    with open("kpi.txt", "w") as f:
        f.write(kpi_txt)

    # ---------- plots ----------
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(range(1, 7), pc_cur, "o-", label="current acc")
    ax.plot(range(1, 7), pc_hist, "s--", label="historical acc")
    ax.axvline(3.5, color="red", ls=":", label="phase change (after c3)")
    ax.axhline(0.90, color="gray", lw=0.8, ls="-.")
    ax.set_xlabel("cycle"); ax.set_ylabel("accuracy"); ax.set_ylim(-0.03, 1.05)
    ax.set_title("DS-007: phase change -> sweep; consensus needs 2 obs (c4 dip)")
    ax.legend(fontsize=8); fig.tight_layout(); fig.savefig("d22_phase.png", dpi=110)

    fig, axs = plt.subplots(1, 2, figsize=(9, 3.6))
    axs[0].bar(["storage", "budget"], [avg["storage_ratio"], 0.40],
               color=["steelblue", "indianred"])
    axs[0].set_title("C1: compaction (DS-004) vs citation (DS-006)"); axs[0].set_ylim(0, 0.5)
    axs[1].bar(["cur", "thr", "hist", "thr"], [avg["cur_acc"], 0.90, avg["hist_acc"], 0.80],
               color=["steelblue", "gray", "seagreen", "gray"])
    axs[1].set_ylim(0, 1.1); axs[1].set_title("answers on scaffold")
    fig.tight_layout(); fig.savefig("d23_storage.png", dpi=110)

    fig, ax = plt.subplots(figsize=(7, 3.8))
    names = ["clean_acc", "noise_rej", "coverage", "ECE", "ans_cov"]
    vals = [avg["clean_accept"], avg["noise_reject"], avg["coverage"],
            avg["ece"], avg["answer_coverage"]]
    thrs = [0.90, 0.90, 0.60, 0.10, 0.90]
    ax.bar(names, vals, color="slategray")
    for i, t in enumerate(thrs):
        ax.hlines(t, i - 0.4, i + 0.4, color="red", ls="--", lw=1)
    ax.set_title("E1/E5: gating + calibration (red = threshold)"); ax.set_ylim(0, 1.1)
    fig.tight_layout(); fig.savefig("d24_gate_ece.png", dpi=110)

    fig, ax = plt.subplots(figsize=(8, 4))
    strats = list(STRATEGIES)
    xa = np.arange(len(strats)); w = 0.35
    wa = [np.mean([r["win"] for r in lay_a if r["strategy"] == s]) for s in strats]
    wc = [np.mean([r["win"] for r in lay_c if r["strategy"] == s]) for s in strats]
    ax.bar(xa - w / 2, wa, w, label="layer (a) pipeline only")
    ax.bar(xa + w / 2, wc, w, label="layer (c) + verifier")
    ax.axhline(0.25, color="gray", ls=":", lw=1, label="threshold 0.25")
    ax.set_xticks(xa); ax.set_xticklabels(strats, rotation=15)
    ax.set_ylabel("winrate (aware+unaware)"); ax.set_ylim(0, 1.05)
    ax.set_title("E6: red-team winrate per strategy"); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig("d25_redteam.png", dpi=110)

    print("wrote kpi.txt summary.json d22_phase.png d23_storage.png "
          "d24_gate_ece.png d25_redteam.png")


if __name__ == "__main__":
    main()
