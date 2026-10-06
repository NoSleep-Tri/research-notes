# -*- coding: utf-8 -*-
"""
DS-009 — Training dataset: suy dien gold-op tu stream (SAGE)
Spec: research/design/SAGE-spec.md §20 — pre-registered TRUOC KHI file nay ton tai
  pre-reg 391d720 -> amend 22062e0 (sua phep dem update cycle 1; nguong G1-G6 khong doi)
Chay tren Kaggle (CPU, khong internet).
Outputs: kpi.txt, summary.json, d29_opdist.png, d30_fidelity.png, d31_ambiguity.png,
         train_pairs.jsonl, qa_pairs.jsonl
"""
import json
import random

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---- config (§20.1, khong doi sau khi chay) ----
SEED = 0
Q_SEED = 20261010
N_KEY = 600
CYCLES = 6
NEW_PER = 100
UPDATE_PER = 80       # chi cycle 2..6 (§20.4 amend #0)
RESTATE_PER = 30
RETRACT_PER = 10
EDGE_RD = 2           # restate_drift / cycle
EDGE_RU = 1           # retract_unseen / cycle
EDGE_PT = 1           # poison_on_truth / cycle
BAIT = 0.15
EPS = 1e-12

# (first_cycle, strategy, n, mode) — attack suite §20.1
PLAN = [
    (6, "tie20_aware", 20, "aware"),
    (6, "swarm10_aware", 10, "aware"),
    (6, "drift15_aware", 15, "aware"),
    (6, "spread30_aware", 30, "aware"),
    (6, "single60_aware", 60, "aware"),
    (6, "tie20_unaware", 20, "unaware"),
    (6, "swarm10_unaware", 10, "unaware"),
    (6, "spread30_unaware", 30, "unaware"),
    (5, "patient2", 30, "patient"),
    (6, "patient2", 30, "patient"),
    (4, "patient3", 20, "patient"),
    (5, "patient3", 20, "patient"),
    (6, "patient3", 20, "patient"),
]

PRED = {"total": 1579, "usable": 1555, "needs_rate": 0.0152, "qa": 540,
        "fidelity_naive": 0.55, "max_share": 0.386, "min_count": 60,
        "answer_acc": 1.0, "leakage": 0.0, "adv_total": 321, "atk_tagged": 1.0}


def gen_events():
    """Stream event-log. Tra ve (events, truth_final, qa, live_final).
    Thu tu trong chu ky: new -> update -> restate -> retract -> edge -> attacks."""
    rng = random.Random(SEED)
    events = []
    eid = 0
    truth = {}            # key -> value (oracle, luc tao ra su kien)
    live = set()
    dead = set()
    created_cycle = {}
    last_honest = {}      # key -> eid cua su kien trung thuc cuoi (citation)
    patient_keys = {}

    def push(cycle, key, value, kind, adv=False, strategy=None, edge=False):
        nonlocal eid
        ev = {"eid": eid, "cycle": cycle, "key": key, "value": value,
              "kind": kind, "adversarial": adv, "strategy": strategy,
              "edge": edge}
        eid += 1
        events.append(ev)
        return ev

    for c in range(1, CYCLES + 1):
        # --- new ---
        new_keys = []
        for i in range(NEW_PER):
            k = "K%03d" % ((c - 1) * NEW_PER + i)
            v = rng.uniform(0, 1)
            push(c, k, v, "new")
            truth[k] = v
            live.add(k)
            dead.discard(k)
            created_cycle[k] = c
            last_honest[k] = events[-1]["eid"]
            new_keys.append(k)
        # --- update (chi c >= 2; key da tao >= 1 chu ky) ---
        if c >= 2:
            elig = [k for k in live if created_cycle[k] < c]
            for k in rng.sample(sorted(elig), min(UPDATE_PER, len(elig))):
                nv = rng.uniform(0, 1)
                while abs(nv - truth[k]) <= EPS:
                    nv = rng.uniform(0, 1)
                push(c, k, nv, "update")
                truth[k] = nv
                last_honest[k] = events[-1]["eid"]
        # --- restate (value = current dung bang) ---
        if live:
            for k in rng.sample(sorted(live), min(RESTATE_PER, len(live))):
                push(c, k, truth[k], "restate")
                last_honest[k] = events[-1]["eid"]
        # --- retract (key dang song -> oracle xoa) ---
        if live:
            for k in rng.sample(sorted(live), min(RETRACT_PER, len(live))):
                push(c, k, None, "retract")
                truth.pop(k, None)
                live.discard(k)
                dead.add(k)
        # --- edge quota ---
        for _ in range(EDGE_RD):        # restate_drift: claim restate, value lech
            if not live:
                break
            k = rng.choice(sorted(live))
            nv = truth[k] + 0.05
            push(c, k, nv, "restate", edge=True)
            truth[k] = nv               # oracle recency: cap nhat
            last_honest[k] = events[-1]["eid"]
        for _ in range(EDGE_RU):        # retract_unseen: key da chet
            if not dead:
                break
            k = rng.choice(sorted(dead))
            push(c, k, None, "retract", edge=True)
        for _ in range(EDGE_PT):        # poison_on_truth: adversarial, dung truth
            if not live:
                break
            k = rng.choice(sorted(live))
            push(c, k, truth[k], "update", adv=True, strategy="on_truth", edge=True)
        # --- attacks (cuoi chu ky, tren key da ton tai) ---
        for pc, strat, n, mode in PLAN:
            if pc != c:
                continue
            if mode == "patient":
                if strat not in patient_keys:
                    elig = [k for k in live if created_cycle[k] < pc]
                    patient_keys[strat] = rng.sample(
                        sorted(elig), min(n, len(elig)))
                keys = patient_keys[strat]
            else:
                keys = rng.sample(sorted(live), min(n, len(live)))
            for k in keys:
                if k not in live:
                    continue            # key da chet: bo qua (van dam bao key ton tai)
                v = rng.uniform(0, 1) if mode == "unaware" else truth[k] + BAIT
                push(c, k, v, "update", adv=True, strategy=strat)

    # --- QA pairs: moi key song cuoi ---
    qa = []
    for k in sorted(live):
        qa.append({"question": "Gia tri hien tai cua key %s?" % k,
                   "gold_answer": truth[k],
                   "citation": last_honest.get(k)})
    return events, truth, qa, live


def label_events(events):
    """Policy §20.1: recency-wins, poison -> NOOP (world-truth),
    declared != computed -> tag needs_policy (canonical de replay tiep)."""
    state = {}
    hist = {}
    pairs = []
    for ev in events:
        k, v, kind, adv = ev["key"], ev["value"], ev["kind"], ev["adversarial"]
        tags = []
        if adv:
            label = "NOOP"
            if k in state and v is not None and abs(v - state[k]) <= EPS:
                tags.append("needs_policy")     # poison_on_truth: store-only khong phan biet
        elif kind == "new":
            if k in state:
                tags.append("needs_policy")     # khong xay ra trong gen
            label = "ADD"
            state[k] = v
        elif kind == "update":
            if k in state and abs(v - state[k]) > EPS:
                label = "UPDATE"
                state[k] = v
            else:                               # update len gia tri khong doi / key chua thay
                label = "UPDATE"
                tags.append("needs_policy")
                if k in state:
                    state[k] = v
        elif kind == "restate":
            if k in state and abs(v - state[k]) <= EPS:
                label = "NOOP"
            elif k in state:                    # restate_drift -> canonical UPDATE
                label = "UPDATE"
                tags.append("needs_policy")
                state[k] = v
            else:                               # restate cua key chua thay
                label = "NOOP"
                tags.append("needs_policy")
        elif kind == "retract":
            if k in state:
                label = "DELETE"
                del state[k]
            else:                               # retract_unseen -> canonical NOOP
                label = "NOOP"
                tags.append("needs_policy")
        else:
            raise ValueError("unknown kind " + kind)
        ctx = [{"eid": h[0], "kind": h[1], "value": h[2], "cycle": h[3]}
               for h in hist.get(k, [])[-5:]]
        pairs.append({"eid": ev["eid"], "cycle": ev["cycle"], "key": k,
                      "kind": kind, "value": v, "adversarial": adv,
                      "strategy": ev["strategy"], "gold_op": label,
                      "needs_policy": bool(tags), "context": ctx})
        hist.setdefault(k, []).append((ev["eid"], kind, v, ev["cycle"]))
    return pairs, state


def build_oracle(events):
    """Doc lap: recency-wins tren event trung thuc (adversarial khong doi)."""
    o = {}
    for ev in events:
        if ev["adversarial"]:
            continue
        k, kind, v = ev["key"], ev["kind"], ev["value"]
        if kind in ("new", "update", "restate"):
            o[k] = v
        elif kind == "retract":
            o.pop(k, None)
    return o


def naive_replay(events):
    """Baseline: moi event -> ADD keep-first, khong bao gio xoa."""
    store = {}
    for ev in events:
        if ev["value"] is None:
            continue
        k = ev["key"]
        if k not in store:
            store[k] = ev["value"]
    return store


def fidelity(replay, oracle):
    if not oracle:
        return 0.0
    ok = 0
    for k, v in oracle.items():
        if k in replay and abs(replay[k] - v) <= EPS:
            ok += 1
    return ok / float(len(oracle))


def main():
    events, truth_gen, qa, live = gen_events()
    random.Random(Q_SEED).shuffle(qa)   # Q_SEED dung cho thu tu xuat QA
    pairs, state_policy = label_events(events)
    oracle = build_oracle(events)
    naive = naive_replay(events)

    total = len(events)
    usable = [p for p in pairs if not p["needs_policy"]]
    needs = [p for p in pairs if p["needs_policy"]]
    edge_evs = [ev for ev in events if ev["edge"]]
    pair_by_eid = {p["eid"]: p for p in pairs}

    needs_rate = len(needs) / float(total)
    edge_detected = sum(1 for ev in edge_evs
                        if pair_by_eid[ev["eid"]]["needs_policy"])
    tagged_rate = (edge_detected / float(len(edge_evs))) if edge_evs else 0.0

    fid_policy = fidelity(state_policy, oracle)
    fid_naive = fidelity(naive, oracle)

    ops = {}
    for p in usable:
        ops[p["gold_op"]] = ops.get(p["gold_op"], 0) + 1
    n_ops = len(ops)
    max_share = (max(ops.values()) / float(len(usable))) if usable else 0.0
    min_count = min(ops.values()) if ops else 0

    # answer acc: gold QA vs state_policy (duong code doc lap voi oracle/gen truth)
    acc_ok = 0
    leak = 0
    for q in qa:
        # key lay tu question ("... key Kxxx?")
        kname = q["question"].split("key ")[-1].rstrip("?")
        if kname in state_policy and abs(q["gold_answer"] - state_policy[kname]) <= EPS:
            acc_ok += 1
        s = str(q["gold_answer"])
        if s in q["question"] or ("%.6f" % q["gold_answer"]) in q["question"]:
            leak += 1
    answer_acc = acc_ok / float(len(qa)) if qa else 0.0
    leakage = leak / float(len(qa)) if qa else 0.0

    adv_evs = [ev for ev in events if ev["adversarial"]]
    atk_suite = [ev for ev in adv_evs if ev["strategy"] != "on_truth"]
    atk_tagged = (sum(1 for ev in adv_evs if ev["strategy"]) /
                  float(len(adv_evs))) if adv_evs else 0.0
    poison_noop = (sum(1 for ev in adv_evs
                       if pair_by_eid[ev["eid"]]["gold_op"] == "NOOP") /
                   float(len(adv_evs))) if adv_evs else 0.0

    checks = {
        "G1": (len(usable) >= 800 and len(qa) >= 500),
        "G2": (needs_rate <= 0.10 and abs(tagged_rate - 1.0) <= EPS),
        "G3": (fid_policy >= 0.995 and fid_naive <= 0.65),
        "G4": (n_ops == 4 and max_share <= 0.80 and min_count >= 20),
        "G5": (answer_acc >= 0.99 and leakage <= 0.01),
        "G6": (atk_tagged >= 0.95 and abs(poison_noop - 1.0) <= EPS),
    }
    kpi = sum(1 for v in checks.values() if v)
    kpi_pass = kpi == len(checks)

    edge_breakdown = {}
    for ev in edge_evs:
        if ev["strategy"]:
            lbl = ev["strategy"]
        elif ev["kind"] == "restate":
            lbl = "restate_drift"
        else:
            lbl = "retract_unseen"
        edge_breakdown[lbl] = edge_breakdown.get(lbl, 0) + 1
    atk_by = {}
    for ev in adv_evs:
        atk_by[ev["strategy"]] = atk_by.get(ev["strategy"], 0) + 1

    obs = {"total": total, "usable": len(usable), "needs_rate": needs_rate,
           "qa": len(qa), "fidelity_naive": fid_naive,
           "max_share": max_share, "min_count": min_count,
           "answer_acc": answer_acc, "leakage": leakage,
           "adv_total": len(adv_evs), "atk_tagged": atk_tagged}

    lines = []
    lines.append("G1 scale (usable>=800 & qa>=500): usable=%d qa=%d -> %s"
                 % (len(usable), len(qa), "PASS" if checks["G1"] else "FAIL"))
    lines.append("G2 coverage (needs_rate<=0.10 & edge tagged=1.00): "
                 "needs_rate=%.4f edge_tagged=%.4f (%d/%d) -> %s"
                 % (needs_rate, tagged_rate, edge_detected, len(edge_evs),
                    "PASS" if checks["G2"] else "FAIL"))
    lines.append("G3 round-trip (policy>=0.995 & naive<=0.65): "
                 "fidelity_policy=%.4f fidelity_naive=%.4f -> %s"
                 % (fid_policy, fid_naive, "PASS" if checks["G3"] else "FAIL"))
    lines.append("G4 distribution (n=4 & max<=0.80 & min>=20): "
                 "n_ops=%d max_share=%.4f min_count=%d -> %s"
                 % (n_ops, max_share, min_count, "PASS" if checks["G4"] else "FAIL"))
    lines.append("G5 answer (acc>=0.99 & leak<=0.01): answer_acc=%.4f "
                 "leakage=%.4f -> %s"
                 % (answer_acc, leakage, "PASS" if checks["G5"] else "FAIL"))
    lines.append("G6 provenance (tagged>=0.95 & noop=1.00): "
                 "attack_tagged=%.4f poison_noop=%.4f -> %s"
                 % (atk_tagged, poison_noop, "PASS" if checks["G6"] else "FAIL"))
    lines.append("")
    lines.append("KPI: %d/%d %s" % (kpi, len(checks),
                                    "PASS" if kpi_pass else "SEE §20.5"))
    lines.append("events=%d usable=%d needs_policy=%d qa=%d | ops: ADD=%d "
                 "UPDATE=%d NOOP=%d DELETE=%d"
                 % (total, len(usable), len(needs), len(qa),
                    ops.get("ADD", 0), ops.get("UPDATE", 0),
                    ops.get("NOOP", 0), ops.get("DELETE", 0)))
    lines.append("attacks: suite=%d on_truth=%d adv_total=%d | by=%s"
                 % (len(atk_suite), atk_by.get("on_truth", 0), len(adv_evs),
                    sorted(atk_by.items())))
    lines.append("edge breakdown: %s | oracle_keys=%d live_final=%d "
                 "naive_store=%d"
                 % (sorted(edge_breakdown.items()), len(oracle), len(live),
                    len(naive)))
    lines.append("predicted vs observed (non-gating): " + ", ".join(
        "%s %.3f/%.3f" % (k, PRED[k], obs[k]) for k in PRED))
    kpi_txt = "\n".join(lines) + "\n"
    print(kpi_txt)

    summary = {"config": {"SEED": SEED, "Q_SEED": Q_SEED, "N_KEY": N_KEY,
                          "CYCLES": CYCLES, "NEW_PER": NEW_PER,
                          "UPDATE_PER": UPDATE_PER, "RESTATE_PER": RESTATE_PER,
                          "RETRACT_PER": RETRACT_PER, "EDGE": [EDGE_RD, EDGE_RU,
                          EDGE_PT], "BAIT": BAIT},
               "counts": {"events": total, "usable": len(usable),
                          "needs_policy": len(needs), "qa": len(qa),
                          "adv": len(adv_evs), "atk_suite": len(atk_suite)},
               "ops": ops, "edge": edge_breakdown, "attacks": atk_by,
               "fidelity": {"policy": fid_policy, "naive": fid_naive},
               "coverage": {"needs_rate": needs_rate,
                            "edge_tagged": tagged_rate},
               "answer": {"acc": answer_acc, "leakage": leakage},
               "pred_vs_obs": {k: {"pred": PRED[k], "obs": obs[k]}
                               for k in PRED},
               "kpi": "%d/%d" % (kpi, len(checks)),
               "checks": {k: bool(v) for k, v in checks.items()}}
    with open("summary.json", "w") as f:
        json.dump(summary, f, indent=1)
    with open("kpi.txt", "w") as f:
        f.write(kpi_txt)
    with open("train_pairs.jsonl", "w") as f:
        for p in usable:
            f.write(json.dumps(p) + "\n")
    with open("qa_pairs.jsonl", "w") as f:
        for q in qa:
            f.write(json.dumps(q) + "\n")

    # ---------- plots ----------
    fig, ax = plt.subplots(figsize=(7, 4))
    names = ["ADD", "UPDATE", "NOOP", "DELETE"]
    vals = [ops.get(n, 0) for n in names]
    bars = ax.bar(names, vals, color=["#4C78A8", "#F58518", "#54A24B", "#E45756"])
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 8, str(v),
                ha="center", fontsize=9)
    ax.set_title("DS-009 gold-op distribution (usable pairs=%d)" % len(usable))
    ax.set_ylabel("count")
    fig.tight_layout()
    fig.savefig("d29_opdist.png", dpi=110)

    fig, ax = plt.subplots(figsize=(7, 3.2))
    ax.barh(["policy", "naive (ADD keep-first)"], [fid_policy, fid_naive],
            color=["#4C78A8", "#B8B8B8"])
    ax.axvline(0.995, color="green", ls="--", lw=0.9, label="threshold 0.995")
    ax.axvline(0.65, color="red", ls=":", lw=0.9, label="naive ceiling 0.65")
    ax.set_xlim(0, 1.08)
    ax.set_xlabel("round-trip fidelity vs oracle store")
    ax.set_title("G3: replay gold-op reconstructs oracle (policy) — naive does not")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig("d30_fidelity.png", dpi=110)

    fig, ax = plt.subplots(figsize=(7, 3.6))
    ek = sorted(edge_breakdown.items(), key=lambda x: -x[1])
    ax.bar([k for k, _ in ek], [v for _, v in ek],
           color=["#E45756", "#F58518", "#B279A2"][:len(ek)])
    ax.set_ylabel("count")
    ax.set_title("G2: needs_policy events = %d/%d (%.4f), all tagged"
                 % (len(needs), total, needs_rate))
    fig.tight_layout()
    fig.savefig("d31_ambiguity.png", dpi=110)

    print("wrote kpi.txt summary.json d29_opdist.png d30_fidelity.png "
          "d31_ambiguity.png train_pairs.jsonl qa_pairs.jsonl")


if __name__ == "__main__":
    main()
