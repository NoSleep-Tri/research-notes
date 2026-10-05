"""
DS-004 — SAGE v0.2: archive/compaction ("giờ bảo trì")
Acceptance PRE-REGISTERED ở spec §15 (đọc trước khi sửa gì ở đây).

D12: size_sage <= 0.40  VÀ  acc_sage >= 0.90
D13: acc_sage >= acc_recency + 0.10  VÀ  acc_sage >= acc_random + 0.10
D14: dangling_sage == 0 (mọi chu kỳ)  VÀ  acc(cuối) >= acc(đầu) - 0.05

Ngân sách 0.40 áp cho MỌI chính sách (trừ keepall). Query phân bố theo value,
age-uniform — cố định TRƯỚC khi chạy (§15.1). Lambda = 4 cố định (§15.3).
"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------- config (pre-registered §15) ----------
N0       = 3000          # corpus mục tiêu cuối
CYCLES   = 5
BUDGET   = 0.40          # size / N_total  (áp cho recency, random, sage)
LAM      = 4.0           # fidelity decay  (§15.3: không đổi sau khi thấy số)
DIM      = 8
N_TOPIC  = 12
N_QUERY  = 800
N_SEEDS  = 10
CHUNK    = 5             # số record gộp vào 1 scaffold
STUB     = 0.1           # storage của redirect stub
SC_FIX   = 1.0           # storage cố định của 1 scaffold
SC_PER   = 0.02          # storage mỗi member trong scaffold index
NOISE    = 0.06          # độ lệch nội dung trong cùng topic — CỐ ĐỊNH trước lần chạy đầu (§15.1)
SIGMAS   = [0.06, 0.20, 0.40]   # sensitivity diagnostic (KHÔNG gate KPI)

TOPIC_PROTO = None       # prototype chung cho mọi seed (nội tại của experiment)


def make_corpus(rng, n_total, start_id, noise=NOISE):
    """Sinh record: content vector quanh prototype topic, value mixture, links."""
    global TOPIC_PROTO
    if TOPIC_PROTO is None:
        TOPIC_PROTO = rng.standard_normal((N_TOPIC, DIM))
        TOPIC_PROTO /= np.linalg.norm(TOPIC_PROTO, axis=1, keepdims=True)
    topic = rng.integers(0, N_TOPIC, size=n_total)
    content = TOPIC_PROTO[topic] + noise * rng.standard_normal((n_total, DIM))
    # value: 20% cao U(0.7,1), còn lại U(0,0.5)
    hi = rng.random(n_total) < 0.20
    value = np.where(hi, rng.uniform(0.70, 1.00, n_total), rng.uniform(0.00, 0.50, n_total))
    ids = np.arange(start_id, start_id + n_total)
    # links: 30% record có 1 link tới record CÙNG topic, CŨ hơn (nếu có)
    links = [[] for _ in range(n_total)]
    for i in range(n_total):
        if rng.random() < 0.30 and i > 0:
            same = np.where(topic[:i] == topic[i])[0]
            if same.size:
                links[i] = [int(rng.choice(same))]
    return {
        "id": ids, "topic": topic, "content": content,
        "value": value, "links": links,
    }


def concat(corpus, more):
    out = {}
    for k in ("id", "topic", "value"):
        out[k] = np.concatenate([corpus[k], more[k]])
    out["content"] = np.vstack([corpus["content"], more["content"]])
    out["links"] = list(corpus["links"]) + list(more["links"])
    return out


def storage_size(rep, n_total):
    """Tổng storage của một trạng thái archive, quy về / N_total."""
    s = 0.0
    s += rep["n_raw"] * 1.0
    for m in rep["scaffold_members"].values():
        s += SC_FIX + SC_PER * max(len(m) - 1, 1)
    s += rep["n_stub"] * STUB
    return s / float(n_total)


# ---------- chính sách archive ----------

def oracle_acc(full, n_vis, queries):
    """Diagnostic KHÔNG gate: TRẦN acc đạt được với ngân sách 0.40 — query phân
    bố theo value ⇒ chi toàn bộ budget cho top-value raw là tối ưu (oracle)."""
    K = int(BUDGET * n_vis)
    top = set(int(full["id"][i]) for i in np.argsort(-full["value"][:n_vis])[:K])
    vis = [q for q in queries if q < n_vis]
    if not vis:
        return 1.0
    return sum(1.0 for q in vis if q in top) / len(vis)


def pol_keepall(corpus, n_vis):
    ids = corpus["id"][:n_vis]
    return {"raw": set(int(i) for i in ids), "member_of": {}, "fidelity": {}, "n_stub": 0}


def _flat_select(corpus, n_vis, rng, mode):
    """recency / random: chọn raw thuần, cùng ngân sách 0.40."""
    K = int(BUDGET * n_vis)
    if mode == "recency":
        sel = np.arange(n_vis - K, n_vis)          # mới nhất
    else:
        sel = rng.choice(n_vis, size=K, replace=False)  # ngẫu nhiên
    raw = set(int(corpus["id"][i]) for i in sel)
    return {"raw": raw, "member_of": {}, "fidelity": {}, "n_stub": 0}


def pol_sage(corpus, n_vis):
    """Giữ theo GIÁ TRỊ (raw) → gộp theo topic (scaffold) → evict + STUB redirect
    để link KHÔNG bao giờ gãy (D14 c1). Stub = 0.1 storage, KHÔNG truy xuất được
    nội dung (chỉ giữ liên kết) → không thể 'nén' bằng stub để qua accuracy."""
    ids = corpus["id"][:n_vis]
    val = corpus["value"][:n_vis]
    top = corpus["topic"][:n_vis]
    cont = corpus["content"][:n_vis]
    links = corpus["links"][:n_vis]
    id2i = {int(ids[i]): i for i in range(n_vis)}

    Bu = BUDGET * n_vis
    K = int(0.55 * Bu)                                  # 55% ngân sách → raw theo value
    raw_idx = set(int(x) for x in np.argsort(-val)[:K])

    # nhóm record KHÔNG raw → scaffold theo topic, chunk CHUNK (sắp value giảm dần)
    groups, gmap = [], {}
    rest = [i for i in range(n_vis) if i not in raw_idx]
    for t in range(N_TOPIC):
        mem = sorted([i for i in rest if top[i] == t], key=lambda i: -val[i])
        for s in range(0, len(mem), CHUNK):
            g = {"t": t, "idx": mem[s:s + CHUNK], "forced": False}
            if g["idx"]:
                groups.append(g)
                for i in g["idx"]:
                    gmap[int(ids[i])] = g
    groups.sort(key=lambda g: -max(val[i] for i in g["idx"]))

    used = float(K)
    cap = 0.95 * Bu                                     # chừa chỗ cho stub
    chosen = [g for g in groups if g["forced"]]
    used += sum(SC_FIX + SC_PER * max(len(g["idx"]) - 1, 1) for g in chosen)
    for g in groups:                                    # nhóm forced chưa có (đang none)
        if g["forced"] and g not in chosen:
            used += SC_FIX + SC_PER * max(len(g["idx"]) - 1, 1)
            chosen.append(g)
    for g in groups:
        if g["forced"]:
            continue
        cost = SC_FIX + SC_PER * max(len(g["idx"]) - 1, 1)
        if used + cost <= cap:
            chosen.append(g)
            used += cost

    member_of, fidelity = {}, {}
    for g in chosen:
        idxs = g["idx"]
        key = f"sc_{g['t']}_{min(idxs)}"
        cen = cont[idxs].mean(axis=0)
        dist = float(np.mean(np.sum((cont[idxs] - cen) ** 2, axis=1)))
        fidelity[key] = float(np.exp(-LAM * dist))
        for i in idxs:
            member_of[int(ids[i])] = key

    # STUB + ngân sách: loop chốt cuối — record bị bỏ khỏi scaffold phải có stub
    def _rebuild_stubs():
        retrievable = set(int(ids[i]) for i in raw_idx) | set(member_of.keys())
        s = set()
        for r in retrievable:
            idx = id2i.get(r)
            if idx is None:
                continue
            for t_id in links[idx]:
                j = int(t_id)
                if j not in retrievable:
                    s.add(j)
        return s

    def _size(stub_n):
        s = float(K)
        for g in chosen:
            s += SC_FIX + SC_PER * max(len(g["idx"]) - 1, 1)
        return (s + stub_n * STUB) / n_vis

    while True:
        stubs = _rebuild_stubs()
        if _size(len(stubs)) <= BUDGET or not any(not g["forced"] for g in chosen):
            break
        worst = min([g for g in chosen if not g["forced"]],
                    key=lambda g: min(val[i] for i in g["idx"]))
        chosen.remove(worst)
        for i in worst["idx"]:
            member_of.pop(int(ids[i]), None)
        fidelity.pop(f"sc_{worst['t']}_{min(worst['idx'])}", None)

    return {"raw": set(int(ids[i]) for i in raw_idx),
            "member_of": member_of, "fidelity": fidelity,
            "stubs": stubs, "n_stub": len(stubs)}


# ---------- đo lường ----------

def make_queries(full, rng):
    """Q truy vấn: target ~ value-weighted, age-uniform (§15.1, cố định trước)."""
    w = full["value"] / full["value"].sum()
    tgt = rng.choice(len(full["id"]), size=N_QUERY, replace=True, p=w)
    return [int(full["id"][i]) for i in tgt]


def evaluate(full, n_vis, rep, queries):
    """trả về (accuracy kỳ vọng, size, dangling)."""
    visible = set(int(full["id"][i]) for i in range(n_vis))
    raw, mem, fid = rep["raw"], rep.get("member_of", {}), rep.get("fidelity", {})
    stubs = rep.get("stubs", set())
    retrievable = raw | set(mem.keys())

    hits, scored = 0.0, 0
    for q in queries:
        if q not in visible:
            continue
        scored += 1
        if q in raw:
            hits += 1.0
        elif q in mem:
            hits += fid[mem[q]]
    acc = hits / max(scored, 1)

    # link integrity: mọi target của record TRUY XUẤT ĐƯỢC phải resolve được
    id2i = {int(full["id"][i]): i for i in range(n_vis)}
    dangling = 0
    for r in retrievable:
        i = id2i.get(r)
        if i is None:
            continue
        for t in full["links"][i]:
            t = int(t)
            if t not in retrievable and t not in stubs:
                dangling += 1

    cnt = {}
    for k in mem.values():
        cnt[k] = cnt.get(k, 0) + 1
    members = {k: [0] * c for k, c in cnt.items()}
    size = storage_size({"n_raw": len(raw), "scaffold_members": members,
                         "n_stub": rep.get("n_stub", 0)}, n_vis)
    return acc, size, dangling


# ---------- vòng chạy ----------

POLICIES = ["keepall", "recency", "random", "sage"]


def run_seed(seed):
    rng = np.random.default_rng(seed)
    full = make_corpus(rng, N0, 0)
    queries = make_queries(full, rng)          # cố định cho mọi chu kỳ (§15.1)
    out = {p: [] for p in POLICIES}
    out["oracle"] = []
    for c in range(1, CYCLES + 1):
        n_vis = int(N0 * c / CYCLES)
        reps = {
            "keepall": pol_keepall(full, n_vis),
            "recency": _flat_select(full, n_vis, rng, "recency"),
            "random": _flat_select(full, n_vis, rng, "random"),
            "sage": pol_sage(full, n_vis),
        }
        for name in POLICIES:
            out[name].append(evaluate(full, n_vis, reps[name], queries))
        out["oracle"].append((oracle_acc(full, n_vis, queries), 0.0, 0.0))
    return out


def value_deciles(full, rep, n_vis):
    """Tỷ lệ raw / scaffold / evicted theo decile của value (cuối chu kỳ 5)."""
    val = full["value"][:n_vis]
    raw, mem = rep["raw"], rep.get("member_of", {})
    ids = [int(full["id"][i]) for i in range(n_vis)]
    order = np.argsort(val)
    dec = np.array_split(order, 10)
    rows = []
    for d in dec:
        r = s = e = 0
        for i in d:
            rid = ids[int(i)]
            if rid in raw:
                r += 1
            elif rid in mem:
                s += 1
            else:
                e += 1
        n = max(len(d), 1)
        rows.append((r / n, s / n, e / n))
    return rows


def sensitivity(n_seeds=3):
    """Diagnostic KHÔNG gate KPI (§15.1): sigma tăng → fidelity scaffold giảm → acc rơi."""
    out = {}
    for sg in SIGMAS:
        vals, fids, sizes = [], None, None
        for s in range(n_seeds):
            rng = np.random.default_rng(1000 + s)      # cùng seed → cùng corpus, chỉ đổi sigma
            full = make_corpus(rng, N0, 0, noise=sg)
            queries = make_queries(full, rng)
            rep = pol_sage(full, N0)
            acc, size, _ = evaluate(full, N0, rep, queries)
            vals.append(acc)
            f = list(rep["fidelity"].values())
            fids = f if fids is None else fids + f
            sizes = size
        out[str(sg)] = {
            "acc_sage_final": round(float(np.mean(vals)), 4),
            "fidelity_mean": round(float(np.mean(fids)), 4) if fids else 0.0,
            "fidelity_min": round(float(np.min(fids)), 4) if fids else 0.0,
            "size": round(float(sizes), 4),
        }
    return out


def main():
    seeds = [run_seed(s) for s in range(N_SEEDS)]

    def series(pol, idx):        # idx 0=acc, 1=size, 2=dangling
        return np.array([[c[idx] for c in seeds[s][pol]] for s in range(N_SEEDS)])

    acc = {p: series(p, 0) for p in POLICIES}          # (seeds, cycles)
    size = {p: series(p, 1) for p in POLICIES}
    dang = {p: series(p, 2) for p in POLICIES}

    acc_mean = {p: float(acc[p].mean()) for p in POLICIES}
    acc_cycle = {p: acc[p].mean(axis=0) for p in POLICIES}
    size_final = {p: float(size[p][:, -1].mean()) for p in POLICIES}
    dang_max = {p: float(dang[p].max()) for p in POLICIES}
    acc_std = float(acc["sage"].mean(axis=1).std())
    oracle_mean = float(np.mean([[c[0] for c in seeds[s]["oracle"]] for s in range(N_SEEDS)]))

    # ---------- acceptance (ngưỡng §15.2 — không đổi) ----------
    checks = {
        "D12c1": (size_final["sage"] <= 0.40, f"size_sage(final)={size_final['sage']:.4f} <= 0.40"),
        "D12c2": (acc_mean["sage"] >= 0.90, f"acc_sage(mean)={acc_mean['sage']:.4f} >= 0.90"),
        "D13c1": (acc_mean["sage"] >= acc_mean["recency"] + 0.10,
                  f"acc_sage {acc_mean['sage']:.4f} - acc_recency {acc_mean['recency']:.4f} = "
                  f"{acc_mean['sage']-acc_mean['recency']:+.4f} >= +0.10"),
        "D13c2": (acc_mean["sage"] >= acc_mean["random"] + 0.10,
                  f"acc_sage {acc_mean['sage']:.4f} - acc_random {acc_mean['random']:.4f} = "
                  f"{acc_mean['sage']-acc_mean['random']:+.4f} >= +0.10"),
        "D14c1": (dang_max["sage"] == 0, f"dangling_sage(max qua 5 chu kỳ)={dang_max['sage']:.0f} == 0"),
        "D14c2": ((acc_cycle["sage"][-1] - acc_cycle["sage"][0]) >= -0.05,
                  f"acc(cuối)-acc(đầu)={acc_cycle['sage'][-1]-acc_cycle['sage'][0]:+.4f} >= -0.05"),
    }
    mod = {"D12": checks["D12c1"][0] and checks["D12c2"][0],
           "D13": checks["D13c1"][0] and checks["D13c2"][0],
           "D14": checks["D14c1"][0] and checks["D14c2"][0]}
    kpi = sum(mod.values())

    lines = ["KPI DS-004 — SAGE v0.2 archive/compaction (10 seeds, 5 chu kỳ, budget 0.40, lambda 4)",
             f"acc(mean) keepall={acc_mean['keepall']:.4f} recency={acc_mean['recency']:.4f} "
             f"random={acc_mean['random']:.4f} sage={acc_mean['sage']:.4f}  (acc_sage std/seed={acc_std:.4f})",
             f"size(final) keepall={size_final['keepall']:.4f} recency={size_final['recency']:.4f} "
             f"random={size_final['random']:.4f} sage={size_final['sage']:.4f}",
             f"dangling(max) recency={dang_max['recency']:.0f} random={dang_max['random']:.0f} "
             f"sage={dang_max['sage']:.0f}",
             f"ceiling (oracle: chi toan bo 0.40 cho top-value) = {oracle_mean:.4f}  <- tran acc dat duoc",
             ""]
    for k, (ok, why) in checks.items():
        lines.append(f"{k}: {why} -> {'PASS' if ok else 'FAIL'}")
    lines += ["", f"KPI: {kpi}/3 {'PASS' if kpi == 3 else 'FAIL'}",
              "  D12 " + ("PASS" if mod["D12"] else "FAIL"),
              "  D13 " + ("PASS" if mod["D13"] else "FAIL"),
              "  D14 " + ("PASS" if mod["D14"] else "FAIL")]
    print("\n".join(lines))

    # ---------- plots ----------
    plt.figure(figsize=(7, 4))
    plt.bar(POLICIES, [size_final[p] for p in POLICIES], color=["#999", "#d95f02", "#7570b3", "#1b9e77"])
    plt.axhline(0.40, ls="--", c="k", lw=1, label="budget 0.40 (§15)")
    plt.ylabel("size / N"); plt.title("D12 — Compaction: size cuối chu kỳ 5")
    plt.legend(); plt.tight_layout(); plt.savefig("d12_compaction.png", dpi=110); plt.close()

    plt.figure(figsize=(7, 4))
    for p, c in zip(POLICIES, ["#999", "#d95f02", "#7570b3", "#1b9e77"]):
        plt.plot(range(1, CYCLES + 1), acc_cycle[p], marker="o", label=p, color=c)
    plt.axhline(0.90, ls="--", c="k", lw=1, label="acceptance 0.90")
    plt.xlabel("chu kỳ"); plt.ylabel("accuracy (kỳ vọng)"); plt.legend()
    plt.title("D13 — giữ theo GIÁ TRỊ vs theo ĐỘ MỚI, qua 5 chu kỳ")
    plt.tight_layout(); plt.savefig("d13_value_vs_recency.png", dpi=110); plt.close()

    rep_final = pol_sage(make_corpus(np.random.default_rng(0), N0, 0), N0)
    dec = value_deciles(make_corpus(np.random.default_rng(0), N0, 0), rep_final, N0)
    x = np.arange(10)
    plt.figure(figsize=(7, 4))
    plt.bar(x, [d[0] for d in dec], color="#1b9e77", label="raw")
    plt.bar(x, [d[1] for d in dec], bottom=[d[0] for d in dec], color="#66c2a5", label="scaffold")
    plt.bar(x, [d[2] for d in dec], bottom=[d[0] + d[1] for d in dec], color="#dddddd", label="evicted")
    plt.xlabel("decile của value (0 = thấp nhất)"); plt.ylabel("tỷ lệ record")
    plt.title("D14 — sage giữ theo value: raw/scaffold/evicted theo decile")
    plt.legend(); plt.tight_layout(); plt.savefig("d14_retention.png", dpi=110); plt.close()

    sens = sensitivity()
    lines += ["", "sensitivity (diagnostic, không gate):"] + [
        f"  sigma={k} -> acc_sage_final={v['acc_sage_final']:.4f} "
        f"fidelity_mean={v['fidelity_mean']:.4f} size={v['size']:.4f}"
        for k, v in sens.items()]
    print("\n".join(lines))

    summary = {
        "acc_mean": acc_mean, "acc_std_sage": acc_std,
        "acc_by_cycle": {p: [round(float(v), 4) for v in acc_cycle[p]] for p in POLICIES},
        "size_final": size_final, "dangling_max": dang_max,
        "ceiling_oracle": round(oracle_mean, 4),
        "sensitivity": sens,
        "checks": {k: {"pass": bool(v[0]), "why": v[1]} for k, v in checks.items()},
        "modules": {k: bool(v) for k, v in mod.items()},
        "kpi": f"{kpi}/3",
    }
    with open("summary.json", "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    with open("kpi.txt", "w") as f:
        f.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


