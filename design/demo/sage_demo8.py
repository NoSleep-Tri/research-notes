"""
DS-008 — SAGE: C3 resolution (tach thu tu hoa) + patient-attacker limit.
Acceptance PRE-REGISTERED tai research/design/SAGE-spec.md §19
(commit d3e4a3c) — khong ha nguong sau khi thay so.
3 bien the tren CUNG stream: V0 = baseline DS-007 · V1 = pending-corroboration
+ freshness-gate + recency-first + temporal-outlier prune · V2 = V1 + verifier
xoay vong 50 key/cycle + escalation (chi prune record lech, KHONG tra loi thay).
Kaggle CPU-only, khong internet.
"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------- config: §19.1, pre-registered — CAM doi sau khi thay so ----------
N_KEY = 600
CYCLES = 6
PHASE_BREAK = 3                # cycle 4-6 = phase 2
N_CLEAN, N_NOISE, N_BAIT = 600, 60, 60
GATE_DELTA = 0.30
DETECT_THR = 0.40
EPS = 0.05
MIN_SIZE = 2
FRESH_CYCLES = 2               # freshness-gate: cluster phai phu >= 2 chu ky
PRUNE_DEV = 1.5                # temporal-outlier: |t - median_t| > 1.5 -> loai
STUB = 0.1
T_CUR, T_HIST = 7.0, 4.0
N_CUR_Q, N_HIST_Q = 800, 400
Q_SEED = 20261010
HONEST_SEEDS = [0, 1, 2, 3, 4]
ATTACK_SEED = 0
AWARE_OFFSET = 0.15
N_VERIFIER = 50                # audit xoay vong 50 key/cycle (§19.1)
VERIFIER_CYCLES = (4, 5, 6)
WIN_THR = 0.90
ACC_TOL = 0.05
VARIANTS = ("V0", "V1", "V2")
STRATEGIES = {"tie20": (20, 3), "swarm10": (10, 6), "drift15": (15, 4),
              "spread30": (30, 2), "single60": (60, 1)}
# patient*: 1 bait/cycle qua kenh trusted, rai dung nhip quan sat
# patient2 = 30 key x (cycle 5,6) = 60 · patient3 = 20 key x (cycle 4,5,6) = 60
PATIENT = {"patient2": (30, (5, 6)), "patient3": (20, (4, 5, 6))}
# Du bao truoc khi chay (non-gating — chi de bao "lech du bao", §19.5)
PRED = {"V0_winrate": 0.75, "V1_winrate": 0.17, "V2_patient": 0.00,
        "V1_cur": 0.95, "V1_c3": 0.98, "V1_c5": 0.95, "V1_c6": 0.99,
        "V1_hist": 0.90, "V1_storage": 0.26, "V1_ece": 0.04,
        "V2_escal_avg": 1.92}


def _bait_value(rng, tv, lo, hi):
    """Ambient bait: offset |d| in [lo,hi] = [0.4,0.6], LUON con trong [0,1]."""
    if tv <= 0.5:
        d = rng.uniform(lo, min(hi, 1.0 - tv))
        return float(tv + d)
    d = rng.uniform(lo, min(hi, tv))
    return float(tv - d)


def gen_records(seed, attack=None):
    """Tra ve (recs, true1, true2, targeted_keys). recs = [k, v, t, trusted, kind, cycle],
    da sort theo t (= thu tu xu ly). attack = (strategy, aware) | None.
    patient2/patient3: 1 bait/cycle rai dung nhip — dong thoi la KEEPER ghi truoc §19."""
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
        if strat in STRATEGIES:
            nk, per = STRATEGIES[strat]
            keys = [int(x) for x in rng.choice(N_KEY, size=nk, replace=False)]
            for k in keys:
                tv = float(true2[k])
                for _ in range(per):
                    if aware:
                        v = float(tv + AWARE_OFFSET) if tv + AWARE_OFFSET <= 1.0 \
                            else float(tv - AWARE_OFFSET)
                    else:
                        v = float(rng.random())
                    # t sau moi clean cycle-6 (<= 6.9) va < T_CUR (= 7.0)
                    recs.append([k, v, 6.92 + rng.uniform(0.01, 0.06), 1, "atk", 6])
        else:
            nk, bcycles = PATIENT[strat]
            keys = [int(x) for x in rng.choice(N_KEY, size=nk, replace=False)]
            for k in keys:
                tv = float(true2[k])
                for c in bcycles:
                    if aware:
                        v = float(tv + AWARE_OFFSET) if tv + AWARE_OFFSET <= 1.0 \
                            else float(tv - AWARE_OFFSET)
                    else:
                        v = float(rng.random())
                    # t sau moi clean cung cycle, truoc clean cycle sau
                    recs.append([k, v, c + 0.95 + rng.uniform(0, 0.03), 1, "atk", c])
        targeted = set(keys)
    recs.sort(key=lambda r: r[2])
    return recs, true1, true2, targeted

def build_clusters(pairs, variant):
    """pairs = [(v, t)] cua 1 key. Greedy theo t, eps=0.05.
    V0 (DS-007): rep = gia tri som nhat, chi can size >= MIN_SIZE.
    V1/V2: + temporal-outlier prune (|t - median_t| > PRUNE_DEV -> loai),
    value = median cua phan con lai, eligible = phu >= FRESH_CYCLES chu ky."""
    groups = []
    for v, t in sorted(pairs, key=lambda x: x[1]):
        placed = False
        for g in groups:
            if abs(v - g["rep"]) <= EPS:
                g["size"] += 1
                g["vals"].append(v)
                g["ts"].append(t)
                g["t_last"] = max(g["t_last"], t)
                placed = True
                break
        if not placed:
            groups.append({"rep": v, "size": 1, "vals": [v], "ts": [t],
                           "t_first": t, "t_last": t})
    out = []
    for g in groups:
        if g["size"] < MIN_SIZE:
            continue
        if variant == "V0":
            g["value"] = g["rep"]                # som nhat = DS-007
            g["cycles"] = len({int(t) for t in g["ts"]})
            g["eligible"] = True
        else:
            med_t = float(np.median(g["ts"]))
            keep = [(v, t) for v, t in zip(g["vals"], g["ts"])
                    if abs(t - med_t) <= PRUNE_DEV]
            if len(keep) < MIN_SIZE:
                continue                         # prune lam nho cluster -> loai
            g["size"] = len(keep)
            g["value"] = float(np.median([v for v, _ in keep]))
            g["t_first"] = min(t for _, t in keep)
            g["t_last"] = max(t for _, t in keep)
            g["cycles"] = len({int(t) for _, t in keep})
            g["eligible"] = g["cycles"] >= FRESH_CYCLES
        del g["vals"], g["ts"]
        out.append(g)
    return out


def answer(key, t_q, clusters_by_key, variant):
    """Chon cluster eligible co t_last <= t_q.
    V0: sort (size desc, t_last desc) — DS-007.
    V1/V2: sort (t_last desc, size desc) — recency-first ca cur va hist (§19.1)."""
    best = None
    for g in clusters_by_key.get(key, ()):
        if not g["eligible"]:
            continue
        if g["t_last"] <= t_q + 1e-12:
            rank = (g["size"], g["t_last"]) if variant == "V0" \
                else (g["t_last"], g["size"])
            if best is None or rank > best[0]:
                best = (rank, g)
    return None if best is None else best[1]["value"]


def confidence(key, t_q, chosen, pairs_by_key):
    """DS-003: conf = support/(support+opposition) trong cua so [t_q-1, t_q); rong -> 0.5."""
    if chosen is None:
        return 0.5
    win = [v for v, t in pairs_by_key.get(key, ()) if t_q - 1.0 <= t < t_q]
    if not win:
        return 0.5
    s = sum(1 for v in win if abs(v - chosen) <= EPS)
    return s / float(s + (len(win) - s))


def group_by_key(accepted, quarantined=None):
    out = {}
    for a in accepted:
        if quarantined and a[5] in quarantined:
            continue                              # ức chế (F-X01): loai khoi clustering
        out.setdefault(a[0], []).append((a[1], a[2]))
    return out


def make_queries():
    rng = np.random.default_rng(Q_SEED)
    kc = [int(x) for x in rng.integers(0, N_KEY, N_CUR_Q)]
    kh = [int(x) for x in rng.integers(0, N_KEY, N_HIST_Q)]
    return kc, kh


def eval_queries(pairs_by_key, keys, t_q, true_v, variant):
    """Tra loi + tinh acc (unknown = 0) + conf. Tra ve (acc_list, conf_list, n_answered)."""
    cl = {k: build_clusters(p, variant) for k, p in pairs_by_key.items()}
    accs, confs, ans = [], [], 0
    for k in keys:
        chosen = answer(k, t_q, cl, variant)
        hit = 1.0 if (chosen is not None and abs(chosen - true_v[k]) <= ACC_TOL) else 0.0
        accs.append(hit)
        confs.append(confidence(k, t_q, chosen, pairs_by_key))
        if chosen is not None:
            ans += 1
    return accs, confs, ans

def run_pipeline(recs, true1, true2, variant):
    """Pipeline: gate -> (V1/V2: pending-corroboration) -> detector/sweep ->
    append-only cold -> cluster/citation. V2: verifier sau cycle 4,5,6.
    Eval per-cycle truoc verifier (audit doc answer TRUOC khi phan dinh — §19.1)."""
    use_corrob = variant in ("V1", "V2")
    accepted = []            # [k, v, t, cycle, kind, rid] — append-only (DS-006)
    quarantined = set()      # rid bi ức chế — van nam trong kho, khong xoa
    escalations = []         # cac cycle goi leo thang (V2)
    collateral = 0           # record TRUNG THUC bi quarantine (F5: phai = 0)
    rid = 0
    current = {}             # key -> value (pointer hien hanh)
    current_t = {}           # key -> t cua record dang tro
    pending = []             # records bi gate chan
    st = {"clean_in": 0, "clean_acc": 0, "noise": 0, "noise_rej": 0,
          "total": 0, "acc": 0, "sweep": [], "ratios": []}
    by_cycle = {c: [] for c in range(1, CYCLES + 1)}
    for r in recs:
        by_cycle[r[5]].append(r)
    per_cycle = {}
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
                accepted.append([k, v, r[2], c, kind, rid])
                rid += 1
                current[k] = v
                current_t[k] = r[2]
                st["acc"] += 1
                if kind == "clean":
                    st["clean_acc"] += 1
            else:
                pending.append(r)
                blocked_c += 1
        promoted_this = 0
        if use_corrob:
            # --- pending-corroboration (§19.1): >=2 record bi chan cung key
            # dong y (|dv| <= EPS) -> thua ca. Chi ban le thi khong co ban doi.
            by_k = {}
            for i, r in enumerate(pending):
                by_k.setdefault(r[0], []).append(i)
            prom = set()
            for _k, idxs in by_k.items():
                gs = []                        # [[rep_v, [i,...]], ...] theo gia tri
                for i in idxs:
                    v = pending[i][1]
                    hit = None
                    for g in gs:
                        if abs(v - g[0]) <= EPS:
                            hit = g
                            break
                    if hit is None:
                        gs.append([v, [i]])
                    else:
                        hit[1].append(i)
                for g in gs:
                    if len(g[1]) >= 2:
                        prom.update(g[1])
            new_pending = []
            for i, r in enumerate(pending):
                if i in prom:
                    accepted.append([r[0], r[1], r[2], r[5], r[4], rid])
                    rid += 1
                    if r[2] > current_t.get(r[0], -1.0):
                        current[r[0]] = r[1]
                        current_t[r[0]] = r[2]
                    st["acc"] += 1
                    if r[4] == "clean":
                        st["clean_acc"] += 1
                    if r[5] == c:
                        promoted_this += 1
                else:
                    new_pending.append(r)
            pending = new_pending
        # detector: ty le bi chan TRUOC/SU corroboration cua chinh cycle nay
        blocked_after = blocked_c - promoted_this
        ratio = blocked_after / float(trusted_c) if trusted_c else 0.0
        st["ratios"].append(round(ratio, 4))
        if ratio > DETECT_THR:               # DS-002: sweep = ức chế pointer, KHONG xoa kho
            current, current_t = {}, {}
            for r in pending:                # bypass consistency MOT LAN (§18.4.2)
                accepted.append([r[0], r[1], r[2], r[5], r[4], rid])
                rid += 1
                st["acc"] += 1
                if r[4] == "clean":
                    st["clean_acc"] += 1
            pending = []
            latest = {}
            for a in accepted:
                kk, vv, tt = a[0], a[1], a[2]
                if kk not in latest or tt > latest[kk][1]:
                    latest[kk] = (vv, tt)
            for kk, (val, tt) in latest.items():
                current[kk] = val
                current_t[kk] = tt
            st["sweep"].append(c)
        pairs = group_by_key(accepted, quarantined)
        tgt_cur = true1 if c <= PHASE_BREAK else true2
        acc_c, _, ans_c = eval_queries(pairs, list(range(N_KEY)), T_CUR, tgt_cur, variant)
        acc_h, _, _ = eval_queries(pairs, list(range(N_KEY)), T_HIST, true1, variant)
        per_cycle[c] = {"cur": float(np.mean(acc_c)), "hist": float(np.mean(acc_h)),
                        "ans": ans_c / float(N_KEY)}
        if variant == "V2" and c in VERIFIER_CYCLES:
            # --- verifier co muc tieu (§19.1): doc doc lap 50 key, chi tinh key
            # DA tra loi (unknown != lech). >=1 lech -> leo thang doc toan bo
            # -> quarantine record lech ground-truth theo phase — KHONG tra loi thay.
            vr = np.random.default_rng(7000 + c)
            sample = [int(x) for x in vr.choice(N_KEY, size=N_VERIFIER, replace=False)]
            cl = {k: build_clusters(p, variant) for k, p in pairs.items()}
            mism = 0
            for k in sample:
                ch = answer(k, T_CUR, cl, variant)
                if ch is None:
                    continue
                if abs(ch - tgt_cur[k]) > ACC_TOL:
                    mism += 1
            if mism >= 1:
                escalations.append(c)
                for a in accepted:
                    if a[5] in quarantined:
                        continue
                    tgt_r = true1 if a[3] <= PHASE_BREAK else true2
                    if abs(a[1] - tgt_r[a[0]]) > ACC_TOL:
                        quarantined.add(a[5])
                        if a[4] == "clean":
                            collateral += 1
    return {"accepted": accepted, "quarantined": quarantined, "st": st,
            "per_cycle": per_cycle, "escalations": escalations,
            "collateral": collateral, "variant": variant,
            "n_pending_end": len(pending)}


def final_metrics(run, true1, true2, keys_cur, keys_hist):
    accepted = run["accepted"]
    variant = run["variant"]
    pairs = group_by_key(accepted, run["quarantined"])
    acc_c, conf_c, ans_c = eval_queries(pairs, keys_cur, T_CUR, true2, variant)
    acc_h, conf_h, ans_h = eval_queries(pairs, keys_hist, T_HIST, true1, variant)
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
        "n_quarantined": len(run["quarantined"]),
        "escalations": len(run["escalations"]),
        "escalation_cycles": list(run["escalations"]),
        "collateral": run["collateral"],
    }
    m["storage_ratio"] = (N_KEY * 1.0 + STUB * m["n_accepted"]) / float(m["n_accepted"])
    return m


def targeted_acc(run, true2, targeted):
    """Attack eval: acc tren key bi tan cong — LUON tinh tu ky nuc con lai
    (khong snapshot oracle nhu DS-007; §19.3.4 cam escalation tra loi thay)."""
    pairs = group_by_key(run["accepted"], run["quarantined"])
    cl = {k: build_clusters(p, run["variant"]) for k, p in pairs.items()}
    hits = []
    for k in sorted(targeted):
        ch = answer(k, T_CUR, cl, run["variant"])
        hits.append(1.0 if (ch is not None and abs(ch - true2[k]) <= ACC_TOL) else 0.0)
    return float(np.mean(hits))


def mean_of(rows, key):
    return float(np.mean([r[key] for r in rows]))

def main():
    keys_cur, keys_hist = make_queries()

    # ---------- honest runs (F1, F5, F6) — 5 seeds x 3 bien the cung stream ----------
    hon = {v: [] for v in VARIANTS}
    pc_by_seed = {v: {} for v in VARIANTS}
    for seed in HONEST_SEEDS:
        recs, t1, t2, _ = gen_records(seed)
        for v in VARIANTS:
            run = run_pipeline(recs, t1, t2, v)
            m = final_metrics(run, t1, t2, keys_cur, keys_hist)
            m["seed"] = seed
            hon[v].append(m)
            pc_by_seed[v][seed] = run["per_cycle"]
    avg = {v: {k: mean_of(hon[v], k) for k in
               ["cur_acc", "hist_acc", "answer_coverage", "ece", "clean_accept",
                "noise_reject", "coverage", "storage_ratio", "n_accepted",
                "escalations", "collateral"]} for v in VARIANTS}
    # per-cycle TB qua 5 seed (§19.2 F1 dung so trung binh, khong dung seed0 don)
    pc_avg = {v: [float(np.mean([pc_by_seed[v][s][c]["cur"] for s in HONEST_SEEDS]))
                  for c in range(1, CYCLES + 1)] for v in VARIANTS}
    pch_avg = {v: [float(np.mean([pc_by_seed[v][s][c]["hist"] for s in HONEST_SEEDS]))
                   for c in range(1, CYCLES + 1)] for v in VARIANTS}

    # ---------- red-team (F2/F3/F4): 12 attack x 3 bien the ----------
    atk = []
    aids = []
    for s in STRATEGIES:
        for aware in (True, False):
            aid = "%s_%s" % (s, "a" if aware else "u")
            aids.append(aid)
            recs, t1, t2, tgt = gen_records(ATTACK_SEED, attack=(s, aware))
            for v in VARIANTS:
                run = run_pipeline(recs, t1, t2, v)
                acc = targeted_acc(run, t2, tgt)
                atk.append({"aid": aid, "strategy": s, "aware": aware, "variant": v,
                            "targeted_acc": acc, "win": acc < WIN_THR,
                            "escalations": len(run["escalations"])})
    for pname in PATIENT:
        aids.append(pname)
        recs, t1, t2, tgt = gen_records(ATTACK_SEED, attack=(pname, True))
        for v in VARIANTS:
            run = run_pipeline(recs, t1, t2, v)
            acc = targeted_acc(run, t2, tgt)
            atk.append({"aid": pname, "strategy": pname, "aware": True, "variant": v,
                        "targeted_acc": acc, "win": acc < WIN_THR,
                        "escalations": len(run["escalations"])})

    def wr(variant, names):
        rows = [r for r in atk if r["variant"] == variant and r["aid"] in names]
        return float(np.mean([r["win"] for r in rows]))

    def acc_of(variant, name):
        return [r for r in atk if r["variant"] == variant and r["aid"] == name][0]

    f2_names = ["tie20_a", "swarm10_a", "drift15_a"]
    f3_names = ["spread30_a", "single60_a", "tie20_u", "swarm10_u", "drift15_u"]
    f4_names = ["patient2", "patient3"]
    wr0, wr1 = wr("V0", aids), wr("V1", aids)
    wr2_patient = wr("V2", f4_names)
    wr1_patient = wr("V1", f4_names)

    # ---------- KPI (nguong §19.2 — pre-registered, CAM sua) ----------
    v1, v0, v2 = avg["V1"], avg["V0"], avg["V2"]
    f1 = (pc_avg["V1"][2] >= 0.90 and pc_avg["V1"][4] >= 0.90
          and pc_avg["V1"][5] >= 0.90 and pch_avg["V1"][5] >= 0.80)
    f2 = wr("V1", f2_names) <= 0.10
    f3 = wr("V1", f3_names) <= 0.10
    f4a = wr1_patient >= 0.50
    f4b = wr2_patient <= 0.10
    esc_avg_v2 = avg["V2"]["escalations"]
    coll_total = int(sum(r["collateral"] for r in hon["V2"]))
    f5 = (esc_avg_v2 <= 2.0 and coll_total == 0
          and v2["cur_acc"] >= v1["cur_acc"] - 0.01)
    f6 = (v1["storage_ratio"] <= 0.40 and v1["ece"] <= 0.10
          and v1["answer_coverage"] >= 0.90 and v1["cur_acc"] >= 0.90
          and v1["hist_acc"] >= 0.80)
    # F4 = F4a AND F4b (§19.2: 6 module, F4 la 1 hang voi 2 dieu kien)
    checks = [("F1", f1), ("F2", f2), ("F3", f3),
              ("F4", f4a and f4b), ("F5", f5), ("F6", f6)]
    kpi = sum(1 for _, ok in checks if ok)
    kpi_pass = kpi == len(checks)

    lines = []
    lines.append("DS-008 SAGE — KPI (pre-registered §19.2, commit d3e4a3c)")
    lines.append("variants=V0/V1/V2 same stream | honest seeds=%s query=%d attack=%d"
                 % (HONEST_SEEDS, Q_SEED, ATTACK_SEED))
    lines.append("")
    lines.append("F1 adaptation (c3/c5/c6>=0.90, hist>=0.80): c3=%.4f c4=%.4f(REPORT) "
                 "c5=%.4f c6=%.4f hist6=%.4f -> %s" % (pc_avg["V1"][2], pc_avg["V1"][3],
                                                        pc_avg["V1"][4], pc_avg["V1"][5],
                                                        pch_avg["V1"][5],
                                                        "PASS" if f1 else "FAIL"))
    lines.append("F2 burst killed (<=0.10): tie20_a/swarm10_a/drift15_a winrate="
                 "%.3f -> %s" % (wr("V1", f2_names), "PASS" if f2 else "FAIL"))
    lines.append("F3 inflation+single killed (<=0.10): spread30_a/single60_a/3xunaware "
                 "winrate=%.3f -> %s" % (wr("V1", f3_names), "PASS" if f3 else "FAIL"))
    lines.append("F4a patient limit NEGATIVE (>=0.50): winrate(V1,patient)=%.3f "
                 "(pred 1.00) -> %s" % (wr1_patient, "PASS" if f4a else "FAIL"))
    lines.append("F4b external repair (<=0.10): winrate(V2,patient)=%.3f (pred ~0) -> %s"
                 % (wr2_patient, "PASS" if f4b else "FAIL"))
    lines.append("F5 targeted escalation (avg<=2, collateral=0, cur(V2)>=cur(V1)-0.01): "
                 "escal_avg=%.2f collateral=%d curV2=%.4f curV1=%.4f -> %s"
                 % (esc_avg_v2, coll_total, v2["cur_acc"], v1["cur_acc"],
                    "PASS" if f5 else "FAIL"))
    lines.append("F6 no-regression (storage<=0.40, ece<=0.10, cov>=0.90, cur>=0.90, "
                 "hist>=0.80): storage=%.4f ece=%.4f answer_cov=%.4f cur=%.4f "
                 "hist=%.4f -> %s" % (v1["storage_ratio"], v1["ece"],
                                      v1["answer_coverage"], v1["cur_acc"],
                                      v1["hist_acc"], "PASS" if f6 else "FAIL"))
    lines.append("")
    lines.append("KPI: %d/%d %s" % (kpi, len(checks),
                                    "PASS" if kpi_pass else "SEE §19.5"))
    lines.append("winrate all12: V0=%.3f V1=%.3f | V2 patient=%.3f | V0 cur=%.4f "
                 "(DS-007 ref 0.9475)" % (wr0, wr1, wr2_patient, v0["cur_acc"]))
    lines.append("V1 per-cycle cur=%s" % [round(x, 4) for x in pc_avg["V1"]])
    lines.append("V0 per-cycle cur=%s (diagnostic)" % [round(x, 4) for x in pc_avg["V0"]])
    lines.append("V2 escalation_cycles per seed=%s | quarantined(seed0)=%d "
                 "pending_end=%d" % ([hon["V2"][i]["escalation_cycles"]
                                      for i in range(len(HONEST_SEEDS))],
                                     hon["V2"][0]["n_quarantined"],
                                     hon["V2"][0]["n_pending_end"]))
    obs = {"V0_winrate": wr0, "V1_winrate": wr1, "V2_patient": wr2_patient,
           "V1_cur": v1["cur_acc"], "V1_c3": pc_avg["V1"][2],
           "V1_c5": pc_avg["V1"][4], "V1_c6": pc_avg["V1"][5],
           "V1_hist": v1["hist_acc"], "V1_storage": v1["storage_ratio"],
           "V1_ece": v1["ece"], "V2_escal_avg": esc_avg_v2}
    lines.append("predicted vs observed (non-gating): " + ", ".join(
        "%s %.2f/%.2f" % (k, PRED[k], obs[k]) for k in PRED))
    lines.append("patient detail: " + " | ".join(
        "%s %s acc=%.3f win=%s esc=%d" % (r["variant"], r["aid"], r["targeted_acc"],
                                          r["win"], r["escalations"])
        for r in atk if r["aid"] in f4_names))
    kpi_txt = "\n".join(lines) + "\n"
    print(kpi_txt)

    summary = {"config": {"N_KEY": N_KEY, "CYCLES": CYCLES, "GATE_DELTA": GATE_DELTA,
                          "DETECT_THR": DETECT_THR, "EPS": EPS,
                          "FRESH_CYCLES": FRESH_CYCLES, "PRUNE_DEV": PRUNE_DEV,
                          "N_VERIFIER": N_VERIFIER, "Q_SEED": Q_SEED,
                          "HONEST_SEEDS": HONEST_SEEDS},
               "avg": avg, "per_cycle_avg": pc_avg, "per_cycle_hist_avg": pch_avg,
               "per_seed": hon, "attacks": atk,
               "winrate": {"V0": wr0, "V1": wr1, "V2_patient": wr2_patient,
                           "V1_patient": wr1_patient},
               "escalation_total_V2": int(sum(r["escalations"] for r in hon["V2"])),
               "collateral_total_V2": coll_total,
               "pred_vs_obs": {k: {"pred": PRED[k], "obs": obs[k]} for k in PRED},
               "kpi": "%d/%d" % (kpi, len(checks)),
               "checks": {k: bool(v) for k, v in checks}}
    with open("summary.json", "w") as f:
        json.dump(summary, f, indent=1)
    with open("kpi.txt", "w") as f:
        f.write(kpi_txt)

    # ---------- plots ----------
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(range(1, 7), pc_avg["V1"], "o-", label="V1 cur (fix)")
    ax.plot(range(1, 7), pc_avg["V0"], "s--", label="V0 cur (DS-007 baseline)")
    ax.plot(range(1, 7), pch_avg["V1"], "^:", label="V1 hist")
    ax.axvline(3.5, color="red", ls=":", label="phase change (after c3)")
    ax.axhline(0.90, color="gray", lw=0.8, ls="-.")
    ax.set_xlabel("cycle"); ax.set_ylabel("accuracy"); ax.set_ylim(-0.03, 1.05)
    ax.set_title("DS-008: freshness-gate + recency-first -> recovery at c5 (F1)")
    ax.legend(fontsize=8); fig.tight_layout(); fig.savefig("d26_phase.png", dpi=110)

    fig, ax = plt.subplots(figsize=(9.5, 4))
    xa = np.arange(len(aids)); w = 0.27
    for i, v in enumerate(VARIANTS):
        vals = [1.0 if acc_of(v, a)["win"] else 0.0 for a in aids]
        ax.bar(xa + (i - 1) * w, vals, w, label=v)
    ax.axhline(0.10, color="red", ls="--", lw=1, label="thr 0.10")
    ax.set_xticks(xa); ax.set_xticklabels(aids, rotation=45, ha="right", fontsize=7)
    ax.set_ylabel("win (1=attack thang)"); ax.set_ylim(0, 1.08)
    ax.set_title("DS-008: 12 attacks x 3 variants (patient2/3 = predicted V1 loses)")
    ax.legend(fontsize=8, ncol=4); fig.tight_layout()
    fig.savefig("d27_winrate.png", dpi=110)

    fig, axs = plt.subplots(1, 2, figsize=(9.5, 3.8))
    esc = [hon["V2"][i]["escalations"] for i in range(len(HONEST_SEEDS))]
    axs[0].bar(["s%d" % s for s in HONEST_SEEDS], esc, color="slategray")
    axs[0].axhline(2.0, color="red", ls="--", lw=1, label="thr 2")
    axs[0].set_title("F5: honest escalations/run (DS-007: audit 10/10 runs)")
    axs[0].set_ylim(0, 3); axs[0].legend(fontsize=8)
    pats = [wr("V0", f4_names), wr1_patient, wr2_patient]
    axs[1].bar(["V0", "V1", "V2"], pats, color=["steelblue", "indianred", "seagreen"])
    axs[1].axhline(0.10, color="red", ls="--", lw=1, label="thr 0.10 (V2)")
    axs[1].axhline(0.50, color="gray", ls=":", lw=1, label="thr 0.50 (V1 NEG)")
    axs[1].set_title("F4: patient winrate (V1 predicted LOSE)")
    axs[1].set_ylim(0, 1.08); axs[1].legend(fontsize=8)
    fig.tight_layout(); fig.savefig("d28_escalation.png", dpi=110)

    print("wrote kpi.txt summary.json d26_phase.png d27_winrate.png "
          "d28_escalation.png")


if __name__ == "__main__":
    main()
