# -*- coding: utf-8 -*-
"""
DS-010 — Train smoke: SFT + GRPO cho Memory Manager (op prediction) tren Kaggle GPU.
Spec: research/design/SAGE-spec.md §21 — pre-registered TRUOC KHI file nay ton tai
  (pre-reg b00abca; change-log §21.4 #0: GRPO accum 1->2 TRUOC KHI CHAY theo hop dong E7)
Kaggle GPU + internet (tai Qwen2.5-1.5B-Instruct tu HF Hub).
Outputs: kpi.txt, summary.json, d32_acc.png, d33_reward.png, d34_f1.png, adapter_A/
"""
import gc
import json
import os
import random
import re
import subprocess
import sys
import time

# ================= config (§21.1, khong doi sau khi chay) =================
SEED = 0
Q_SEED = 20261010
MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
LORA_R, LORA_ALPHA, LORA_DROPOUT = 16, 32, 0.0
LORA_TARGETS = ["q_proj", "k_proj", "v_proj", "o_proj",
                "gate_proj", "up_proj", "down_proj"]
SFT_LR, SFT_EPOCHS = 1e-4, 2
MAX_LEN, MAX_NEW = 384, 48
GRPO_LR, GRPO_G, GRPO_COMP = 5e-6, 8, 64
GRPO_ACCUM = 2          # §21.4 #0: effective batch 8 chia het cho G=8 (hop dong E7)
STEPS_B, STEPS_C = 100, 60
R_FORMAT, R_OP = 0.3, 0.7
DELTA_BAIT = 0.15
SPLIT_SEED, TEST_FRAC = 20261010, 0.2
GEN_BS = 16
OP_VOCAB = ["ADD", "UPDATE", "DELETE", "NOOP"]
EXPECTED_TOTAL, EXPECTED_USABLE = 1579, 1555     # parity §20.5

SFT_BS = 4               # fallback OOM giam day (§21.3.6)
GRPO_BS = 4

PRED = {"test": 311, "acc_base": 0.30, "acc_A": 0.93, "acc_B": 0.55, "acc_C": 0.93,
        "Bar1": 0.797, "Bar2": 0.961, "macro_F1_A": 0.90, "reward_B_first": 0.35,
        "reward_B_last": 0.80, "train_acc_A": 0.99, "runtime_min": 90}

T_START = time.time()
FALLBACK_LOG = []
SPLIT = None


# ================= 1. Data regen (copy §20, them bank_now) =================
def gen_events():
    """Stream event-log giong chinh xac sage_demo9 (seed 0, thu tu RNG khong doi).
    Tra ve list events."""
    rng = random.Random(SEED)
    events = []
    eid = 0
    truth, live, dead, created_cycle, last_honest, patient_keys = {}, set(), set(), {}, {}, {}

    def push(cycle, key, value, kind, adv=False, strategy=None, edge=False):
        nonlocal eid
        ev = {"eid": eid, "cycle": cycle, "key": key, "value": value, "kind": kind,
              "adversarial": adv, "strategy": strategy, "edge": edge}
        eid += 1
        events.append(ev)
        return ev

    plan = [(6, "tie20_aware", 20, "aware"), (6, "swarm10_aware", 10, "aware"),
            (6, "drift15_aware", 15, "aware"), (6, "spread30_aware", 30, "aware"),
            (6, "single60_aware", 60, "aware"), (6, "tie20_unaware", 20, "unaware"),
            (6, "swarm10_unaware", 10, "unaware"), (6, "spread30_unaware", 30, "unaware"),
            (5, "patient2", 30, "patient"), (6, "patient2", 30, "patient"),
            (4, "patient3", 20, "patient"), (5, "patient3", 20, "patient"),
            (6, "patient3", 20, "patient")]

    for c in range(1, 7):
        # --- new ---
        for i in range(100):
            k = "K%03d" % ((c - 1) * 100 + i)
            v = rng.uniform(0, 1)
            push(c, k, v, "new")
            truth[k] = v
            live.add(k)
            dead.discard(k)
            created_cycle[k] = c
            last_honest[k] = events[-1]["eid"]
        # --- update (chi c >= 2) ---
        if c >= 2:
            elig = [k for k in live if created_cycle[k] < c]
            for k in rng.sample(sorted(elig), min(80, len(elig))):
                nv = rng.uniform(0, 1)
                while abs(nv - truth[k]) <= 1e-12:
                    nv = rng.uniform(0, 1)
                push(c, k, nv, "update")
                truth[k] = nv
                last_honest[k] = events[-1]["eid"]
        # --- restate ---
        if live:
            for k in rng.sample(sorted(live), min(30, len(live))):
                push(c, k, truth[k], "restate")
                last_honest[k] = events[-1]["eid"]
        # --- retract ---
        if live:
            for k in rng.sample(sorted(live), min(10, len(live))):
                push(c, k, None, "retract")
                truth.pop(k, None)
                live.discard(k)
                dead.add(k)
        # --- edge quota (24/1579 -> needs_policy) ---
        for _ in range(2):                      # restate_drift
            if not live:
                break
            k = rng.choice(sorted(live))
            nv = truth[k] + 0.05
            push(c, k, nv, "restate", edge=True)
            truth[k] = nv
            last_honest[k] = events[-1]["eid"]
        for _ in range(1):                      # retract_unseen
            if not dead:
                break
            k = rng.choice(sorted(dead))
            push(c, k, None, "retract", edge=True)
        for _ in range(1):                      # poison_on_truth
            if not live:
                break
            k = rng.choice(sorted(live))
            push(c, k, truth[k], "update", adv=True, strategy="on_truth", edge=True)
        # --- attacks (cuoi chu ky) ---
        for pc, strat, n, mode in plan:
            if pc != c:
                continue
            if mode == "patient":
                if strat not in patient_keys:
                    elig = [k for k in live if created_cycle[k] < pc]
                    patient_keys[strat] = rng.sample(sorted(elig), min(n, len(elig)))
                keys = patient_keys[strat]
            else:
                keys = rng.sample(sorted(live), min(n, len(live)))
            for k in keys:
                if k not in live:
                    continue
                v = rng.uniform(0, 1) if mode == "unaware" else truth[k] + 0.15
                push(c, k, v, "update", adv=True, strategy=strat)
    return events


def label_events(events):
    """Policy §20.1 + bank_now (gia tri store TRUOC event — §21.1)."""
    state, hist, pairs = {}, {}, []
    for ev in events:
        k, v, kind, adv = ev["key"], ev["value"], ev["kind"], ev["adversarial"]
        bank = state.get(k)
        tags = []
        if adv:
            label = "NOOP"
            if k in state and v is not None and abs(v - state[k]) <= 1e-12:
                tags.append("needs_policy")
        elif kind == "new":
            if k in state:
                tags.append("needs_policy")
            label = "ADD"
            state[k] = v
        elif kind == "update":
            if k in state and abs(v - state[k]) > 1e-12:
                label = "UPDATE"
                state[k] = v
            else:
                label = "UPDATE"
                tags.append("needs_policy")
                if k in state:
                    state[k] = v
        elif kind == "restate":
            if k in state and abs(v - state[k]) <= 1e-12:
                label = "NOOP"
            elif k in state:
                label = "UPDATE"
                tags.append("needs_policy")
                state[k] = v
            else:
                label = "NOOP"
                tags.append("needs_policy")
        elif kind == "retract":
            if k in state:
                label = "DELETE"
                del state[k]
            else:
                label = "NOOP"
                tags.append("needs_policy")
        else:
            raise ValueError("unknown kind " + kind)
        pairs.append({"eid": ev["eid"], "cycle": ev["cycle"], "key": k, "kind": kind,
                      "value": v, "adversarial": adv, "strategy": ev["strategy"],
                      "gold_op": label, "needs_policy": bool(tags), "bank_now": bank,
                      "context": [{"eid": h[0], "kind": h[1], "value": h[2], "cycle": h[3]}
                                  for h in hist.get(k, [])[-5:]]})
        hist.setdefault(k, []).append((ev["eid"], kind, v, ev["cycle"]))
    return pairs


def split_rows(rows):
    """80/20 theo KEY (khong leak), seed 20261010 (§21.1)."""
    keys = sorted(set(r["key"] for r in rows))
    rng = random.Random(SPLIT_SEED)
    rng.shuffle(keys)
    n_test = int(round(len(keys) * TEST_FRAC))
    test_keys = set(keys[:n_test])
    train = [r for r in rows if r["key"] not in test_keys]
    test = [r for r in rows if r["key"] in test_keys]
    return train, test, keys, test_keys


# ================= 2. Prompt (template dong bang §21.1) =================
def f6(v):
    return "none" if v is None else "%.6f" % v


def build_prompt(p):
    ctx = ["  c%d %s value=%s" % (h["cycle"], h["kind"], f6(h["value"]))
           for h in p["context"]]
    ctx_s = "\n".join(ctx) if ctx else "  (none)"
    bank = "absent" if p["bank_now"] is None else "%.6f" % p["bank_now"]
    return ("Key: %s | Cycle: %d\nBank now: %s\nContext:\n%s\n"
            "New request: kind=%s value=%s\n"
            'Decide the memory operation (choose op from ADD/UPDATE/DELETE/NOOP). '
            'Reply JSON only: {"op": "ADD"}'
            % (p["key"], p["cycle"], bank, ctx_s, p["kind"], f6(p["value"])))


def chat_render(prompt, tok):
    return tok.apply_chat_template([{"role": "user", "content": prompt}],
                                   tokenize=False, add_generation_prompt=True)


# ================= 3. Bars (content-only, dong bang §21.1) =================
def bar1(p):
    """Recency+claim, khong biet adversarial. Dung luon bank_now duoc cap (§21.1)."""
    kind, v, bank = p["kind"], p["value"], p["bank_now"]
    if kind == "new":
        return "ADD" if bank is None else "UPDATE"
    if kind == "update":
        return "UPDATE" if bank is not None else "ADD"
    if kind == "restate":
        if bank is None:
            return "ADD"
        return "NOOP" if v is not None and abs(v - bank) <= 1e-12 else "UPDATE"
    if kind == "retract":
        return "DELETE" if bank is not None else "NOOP"
    return "NOOP"


def bar2(p):
    """Bar1 + Δ=0.15 guard (chu ky poison aware/patient)."""
    op = bar1(p)
    if p["kind"] in ("update", "restate") and p["bank_now"] is not None and p["value"] is not None:
        if abs((p["value"] - p["bank_now"]) - DELTA_BAIT) <= 1e-9:
            return "NOOP"
    return op


def rule_acc(rows, fn):
    if not rows:
        return 0.0
    return sum(1 for r in rows if fn(r) == r["gold_op"]) / float(len(rows))


# ================= 4. Parse + metrics =================
OP_RE = re.compile(r'"op"\s*:\s*"?([A-Z]{4,6})"?')


def parse_op(text):
    m = OP_RE.search(text or "")
    if not m:
        return None
    op = m.group(1)
    return op if op in OP_VOCAB else None


def metrics(preds, golds):
    correct = sum(1 for p, g in zip(preds, golds) if p == g)
    parse_rate = sum(1 for p in preds if p is not None) / float(len(preds))
    tp = {c: 0 for c in OP_VOCAB}
    fp = {c: 0 for c in OP_VOCAB}
    fn = {c: 0 for c in OP_VOCAB}
    for p, g in zip(preds, golds):
        if p == g:
            tp[g] += 1
        else:
            if p is not None:
                fp[p] += 1
            fn[g] += 1
    f1s, recalls = {}, {}
    for c in OP_VOCAB:
        prec = tp[c] / float(tp[c] + fp[c]) if (tp[c] + fp[c]) else 0.0
        rec = tp[c] / float(tp[c] + fn[c]) if (tp[c] + fn[c]) else 0.0
        f1s[c] = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        recalls[c] = rec
    macro = sum(f1s[c] for c in OP_VOCAB) / len(OP_VOCAB)
    return {"acc": correct / float(len(preds)), "parse": parse_rate,
            "macro_f1": macro, "f1": f1s, "recall": recalls,
            "gold_n": {c: tp[c] + fn[c] for c in OP_VOCAB}}


def evaluate(model, tok, rows, bs=GEN_BS):
    """Greedy decode + parse. Dat padding_side=left de batched generate dung (harness)."""
    import torch
    model.eval()
    tok.padding_side = "left"
    texts = [chat_render(build_prompt(r), tok) for r in rows]
    outs = []
    for i in range(0, len(texts), bs):
        chunk = texts[i:i + bs]
        enc = tok(chunk, return_tensors="pt", padding=True, truncation=True,
                  max_length=MAX_LEN).to(model.device)
        with torch.no_grad():
            gen = model.generate(**enc, max_new_tokens=MAX_NEW, do_sample=False,
                                 pad_token_id=tok.pad_token_id)
        for j in range(gen.shape[0]):
            outs.append(tok.decode(gen[j, enc["input_ids"].shape[1]:],
                                   skip_special_tokens=True))
    preds = [parse_op(t) for t in outs]
    m = metrics(preds, [r["gold_op"] for r in rows])
    m["sample_raw"] = outs[:3]
    return m


# ================= 5. Model load / stage runner =================
def load_base(model_id):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(model_id)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    tok.padding_side = "left"       # batched generate can phai left-pad
    model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float16,
                                                 device_map="auto")
    model.eval()
    print("loaded %s on %s" % (model_id, torch.cuda.get_device_name(0)))
    return model, tok


def fresh_lora(model_id):
    from peft import LoraConfig, get_peft_model
    cfg = LoraConfig(task_type="CAUSAL_LM", r=LORA_R, lora_alpha=LORA_ALPHA,
                     lora_dropout=LORA_DROPOUT, target_modules=LORA_TARGETS)
    m, t = load_base(model_id)
    m = get_peft_model(m, cfg)
    m.print_trainable_parameters()
    return m, t


def purge():
    import torch
    gc.collect()
    torch.cuda.empty_cache()


def run_stage(label, fn, bs_names):
    """Fallback duy nhất: OOM -> giam batch mot lan (§21.3.6).
    Retry nam NGOAI except block de traceback/model ref bi giet truoc khi retry."""
    import torch
    attempts = 0
    while True:
        try:
            return fn()
        except Exception as e:
            oom = "out of memory" in str(e).lower()
            FALLBACK_LOG.append("%s: %s: %s" % (label, type(e).__name__, str(e)[:200]))
            retry = False
            if oom and attempts < 1:
                for nm in bs_names:
                    cur = globals()[nm]
                    if cur > 1:
                        globals()[nm] = max(1, cur // 2)
                        FALLBACK_LOG.append("%s: OOM -> %s %d -> %d"
                                            % (label, nm, cur, globals()[nm]))
                        retry = True
            if not retry:
                raise
            attempts += 1
        purge()


# ================= 6. SFT custom (completion-only, AMP fp16) =================
def build_sft_samples(rows, tok):
    samples = []
    for r in rows:
        user = chat_render(build_prompt(r), tok)
        comp = '{"op": "%s"}' % r["gold_op"] + tok.eos_token
        uid = tok(user, truncation=True, max_length=MAX_LEN)["input_ids"]
        cid = tok(comp, add_special_tokens=False, truncation=True,
                  max_length=MAX_LEN)["input_ids"]
        if len(uid) + len(cid) > MAX_LEN:
            uid = uid[:MAX_LEN - len(cid)]
        ids = uid + cid
        labels = [-100] * len(uid) + list(cid)
        samples.append((ids, labels))
    return samples


def run_sft(model_id):
    import torch
    from torch.cuda.amp import GradScaler, autocast
    from torch.nn.utils import clip_grad_norm_
    model, tok = fresh_lora(model_id)
    rows = SPLIT["train"]
    samples = build_sft_samples(rows, tok)
    gen = torch.Generator().manual_seed(Q_SEED)
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=SFT_LR)
    scaler = GradScaler()
    pad = tok.pad_token_id
    loss_log = []
    model.train()
    for _ep in range(SFT_EPOCHS):
        order = torch.randperm(len(samples), generator=gen).tolist()
        for i in range(0, len(order), SFT_BS):
            batch = [samples[j] for j in order[i:i + SFT_BS]]
            ml = max(len(b[0]) for b in batch)
            input_ids = torch.full((len(batch), ml), pad, dtype=torch.long)
            labels = torch.full((len(batch), ml), -100, dtype=torch.long)
            attn = torch.zeros((len(batch), ml), dtype=torch.long)
            for bi, (ids, lab) in enumerate(batch):
                input_ids[bi, :len(ids)] = torch.tensor(ids)
                labels[bi, :len(lab)] = torch.tensor(lab)
                attn[bi, :len(ids)] = 1
            dev = model.device
            input_ids, labels, attn = (x.to(dev) for x in (input_ids, labels, attn))
            with autocast():
                loss = model(input_ids=input_ids, attention_mask=attn,
                             labels=labels).loss
            scaler.scale(loss).backward()
            scaler.unscale_(opt)
            clip_grad_norm_(params, 1.0)
            scaler.step(opt)
            scaler.update()
            opt.zero_grad()
            loss_log.append(float(loss.detach().float().cpu()))
    model.save_pretrained("adapter_A")
    tok.save_pretrained("adapter_A")
    m_test = evaluate(model, tok, SPLIT["test"])
    m_train = evaluate(model, tok, rows)
    out = {"loss_first10": sum(loss_log[:10]) / min(10, len(loss_log)),
           "loss_last10": sum(loss_log[-10:]) / min(10, len(loss_log)),
           "n_steps": len(loss_log), "test": m_test, "train": m_train}
    del model, tok, opt, scaler
    purge()
    return out


# ================= 7. GRPO arm =================
def run_grpo_arm(name, model, tok, steps):
    from datasets import Dataset
    from trl import GRPOConfig, GRPOTrainer
    log = []

    def reward_fn(prompts, completions, gold=None, **kw):
        rs, ps = [], []
        golds = gold if gold is not None else kw.get("gold")
        for c, g in zip(completions, golds):
            op = parse_op(c)
            fmt = 1.0 if op is not None else 0.0
            ok = 1.0 if op == g else 0.0
            rs.append(R_FORMAT * fmt + R_OP * ok)
            ps.append(fmt)
        log.append({"step": len(log),
                    "mean": sum(rs) / float(len(rs)),
                    "parse": sum(ps) / float(len(ps))})
        return rs

    rows = [{"prompt": chat_render(build_prompt(r), tok), "gold": r["gold_op"]}
            for r in SPLIT["train"]]
    ds = Dataset.from_list(rows)
    want = {"output_dir": "out_grpo_" + name, "num_generations": GRPO_G,
            "beta": 0.0, "learning_rate": GRPO_LR, "temperature": 1.0,
            "max_completion_length": GRPO_COMP,
            "per_device_train_batch_size": GRPO_BS,
            "gradient_accumulation_steps": GRPO_ACCUM,   # §21.4 #0
            "max_steps": steps, "logging_steps": 5, "report_to": "none",
            "save_strategy": "no", "seed": Q_SEED,
            "gradient_checkpointing": True,
            "gradient_checkpointing_kwargs": {"use_reentrant": False},
            "fp16": True, "loss_type": "grpo", "remove_unused_columns": False}
    fields = GRPOConfig.__dataclass_fields__
    critical = ["num_generations", "beta", "learning_rate", "temperature",
                "max_completion_length", "per_device_train_batch_size",
                "max_steps", "output_dir"]
    missing = [k for k in critical if k not in fields]
    if missing:
        raise RuntimeError("GRPOConfig thieu field critical: %s (TRL lech version)"
                           % missing)
    kwargs = {k: v for k, v in want.items() if k in fields}
    dropped = [k for k in want if k not in kwargs]
    if dropped:
        FALLBACK_LOG.append("%s GRPOConfig dropped optional: %s" % (name, dropped))
    args = GRPOConfig(**kwargs)
    trainer = GRPOTrainer(model=model, reward_funcs=reward_fn, args=args,
                          train_dataset=ds, processing_class=tok)
    trainer.train()
    del trainer, args, ds
    m = evaluate(model, tok, SPLIT["test"])
    return {"log": log, "test": m}


# ================= 8. main =================
def main():
    global SPLIT
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA khong san sang — kernel phai enable GPU (§21)")
    print("GPU: %s" % torch.cuda.get_device_name(0))

    # trl/peft moi nhat (internet ON theo §21.1)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q",
                           "--upgrade", "trl", "peft", "accelerate"])
    # peft moi bat torchao >= 0.16 khi dispatch LoRA, image Kaggle chi co 0.10 ->
    # ImportError o get_peft_model (§21.4 #1). torchao la optional dep, ta khong dung:
    # go bo -> is_torchao_available() = False (find_spec None) -> dispatcher skip sach.
    subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", "-q",
                           "torchao"])

    # --- data regen + parity (§21.1) ---
    events = gen_events()
    pairs = label_events(events)
    usable = [p for p in pairs if not p["needs_policy"]]
    parity_ok = (len(pairs) == EXPECTED_TOTAL and len(usable) == EXPECTED_USABLE)
    train_rows, test_rows, all_keys, test_keys = split_rows(usable)
    leak = len(set(r["key"] for r in train_rows) & test_keys)
    SPLIT = {"train": train_rows, "test": test_rows}
    print("data: total=%d usable=%d train=%d test=%d keys=%d leak=%d parity=%s"
          % (len(pairs), len(usable), len(train_rows), len(test_rows),
             len(all_keys), leak, parity_ok))

    bar1_test = rule_acc(test_rows, bar1)
    bar2_test = rule_acc(test_rows, bar2)
    print("bars: Bar1=%.4f Bar2=%.4f (test n=%d)" % (bar1_test, bar2_test,
                                                     len(test_rows)))

    results, curves = {}, {}

    # --- stage BASE ---
    def stage_base():
        m, t = load_base(MODEL_ID)
        res = evaluate(m, t, test_rows)
        del m, t
        purge()
        return res
    results["base"] = run_stage("base", stage_base, [])
    print("base acc=%.4f parse=%.4f" % (results["base"]["acc"],
                                        results["base"]["parse"]))

    # --- stage A: SFT ---
    a = run_stage("A-SFT", lambda: run_sft(MODEL_ID), ["SFT_BS"])
    results["A"], results["A_train"] = a["test"], a["train"]
    a_loss = {"first10": a["loss_first10"], "last10": a["loss_last10"],
              "steps": a["n_steps"]}
    print("A: acc=%.4f macroF1=%.4f train_acc=%.4f loss %.4f->%.4f"
          % (a["test"]["acc"], a["test"]["macro_f1"], a["train"]["acc"],
             a["loss_first10"], a["loss_last10"]))
    del a
    purge()

    # --- stage B: GRPO from base ---
    def stage_b():
        mb, tb = fresh_lora(MODEL_ID)
        r = run_grpo_arm("B", mb, tb, STEPS_B)
        del mb, tb
        purge()
        return r
    b = run_stage("B-GRPO", stage_b, ["GRPO_BS"])
    results["B"], curves["B"] = b["test"], b["log"]
    print("B: acc=%.4f reward n=%d" % (b["test"]["acc"], len(b["log"])))
    del b
    purge()

    # --- stage C: SFT -> GRPO ---
    def stage_c():
        from peft import PeftModel
        bc, tc = load_base(MODEL_ID)
        mc = PeftModel.from_pretrained(bc, "adapter_A", is_trainable=True)
        r = run_grpo_arm("C", mc, tc, STEPS_C)
        del mc, bc, tc
        purge()
        return r
    c = run_stage("C-GRPO", stage_c, ["GRPO_BS"])
    results["C"], curves["C"] = c["test"], c["log"]
    print("C: acc=%.4f reward n=%d" % (c["test"]["acc"], len(c["log"])))
    del c
    purge()

    # ---------- T1..T6 (nguong §21.2 — khong doi sau khi thay so) ----------
    def fmean(log, sl):
        seg = log[sl] if len(log) >= 10 else log
        if not seg:
            return 0.0
        return sum(x["mean"] for x in seg) / float(len(seg))

    b_first = fmean(curves["B"], slice(0, 10))
    b_last = fmean(curves["B"], slice(-10, None))
    parse_end = curves["B"][-1]["parse"] if curves["B"] else 0.0
    gap = results["A"]["acc"] - results["A_train"]["acc"]
    delta = results["A"]["acc"] - results["base"]["acc"]

    checks, d = {}, {}
    checks["T2"] = t2 = delta >= 0.10
    d["T2"] = ("T2 SFT learns (accA >= base+0.10): base=%.4f accA=%.4f "
               "delta=%.4f -> %s" % (results["base"]["acc"], results["A"]["acc"],
                                     delta, "PASS" if t2 else "FAIL"))
    checks["T3"] = t3 = results["A"]["acc"] >= 0.85
    d["T3"] = ("T3 beats rules bar (accA>=0.85): accA=%.4f Bar1=%.4f Bar2=%.4f "
               "-> %s" % (results["A"]["acc"], bar1_test, bar2_test,
                          "PASS" if t3 else "FAIL"))
    checks["T4"] = t4 = results["A"]["macro_f1"] >= 0.85
    d["T4"] = ("T4 macro-F1 (>=0.85): f1A=%.4f | report accB=%.4f accC=%.4f "
               "accA/Bar2=%.4f/%.4f f1(base,B,C)=%.3f/%.3f/%.3f recallA=%s -> %s"
               % (results["A"]["macro_f1"], results["B"]["acc"],
                  results["C"]["acc"], results["A"]["acc"], bar2_test,
                  results["base"]["macro_f1"], results["B"]["macro_f1"],
                  results["C"]["macro_f1"],
                  {k2: round(results["A"]["recall"][k2], 3) for k2 in OP_VOCAB},
                  "PASS" if t4 else "FAIL"))
    checks["T5"] = t5 = (b_last >= b_first + 0.10) and (parse_end >= 0.90)
    d["T5"] = ("T5 GRPO cold-start B (reward+0.10, parse>=0.90): first=%.4f "
               "last=%.4f delta=%.4f parse_end=%.4f -> %s"
               % (b_first, b_last, b_last - b_first, parse_end,
                  "PASS" if t5 else "FAIL"))
    checks["T6"] = t6 = (leak == 0 and parity_ok and gap >= -0.10)
    d["T6"] = ("T6 leak/parity/overfit (leak=0, 1579/1555, gap>=-0.10): leak=%d "
               "parity=%s trainA=%.4f testA=%.4f gap=%.4f -> %s"
               % (leak, parity_ok, results["A_train"]["acc"],
                  results["A"]["acc"], gap, "PASS" if t6 else "FAIL"))

    # ---------- charts ----------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7.5, 4))
    names = ["base", "A(SFT)", "B(GRPO)", "C(SFT+GRPO)", "Bar1", "Bar2"]
    vals = [results["base"]["acc"], results["A"]["acc"], results["B"]["acc"],
            results["C"]["acc"], bar1_test, bar2_test]
    cols = ["#9c9c9c", "#4C78A8", "#F58518", "#54A24B", "#B8B8B8", "#E45756"]
    bars = ax.bar(names, vals, color=cols)
    for b_, v in zip(bars, vals):
        ax.text(b_.get_x() + b_.get_width() / 2, v + 0.015, "%.3f" % v,
                ha="center", fontsize=8)
    ax.axhline(0.85, color="green", ls="--", lw=0.9, label="T3 gate 0.85")
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("test op accuracy (key-split)")
    ax.set_title("DS-010: trained arms vs rules bars (test n=%d)" % len(test_rows))
    ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig("d32_acc.png", dpi=110)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    for nm, color in (("B", "#F58518"), ("C", "#54A24B")):
        ys = [x["mean"] for x in curves[nm]]
        ax.plot(range(len(ys)), ys, label=nm + " mean reward", color=color, lw=1.2)
    ax.axhline(1.0, color="grey", ls=":", lw=0.8)
    ax.set_xlabel("GRPO step (1 reward log per optimizer step)")
    ax.set_ylabel("reward (0.3 format + 0.7 op-EM)")
    ax.set_title("GRPO reward curves — B from base (cold-start), C from SFT")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig("d33_reward.png", dpi=110)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    names4 = ["base", "A", "B", "C"]
    f1s = [results[k]["macro_f1"] for k in names4]
    bars = ax.bar(names4, f1s, color=["#9c9c9c", "#4C78A8", "#F58518", "#54A24B"])
    for b_, v in zip(bars, f1s):
        ax.text(b_.get_x() + b_.get_width() / 2, v + 0.01, "%.3f" % v,
                ha="center", fontsize=8)
    ax.axhline(0.85, color="green", ls="--", lw=0.9, label="T4 gate 0.85")
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("macro-F1 (4 classes)")
    ax.set_title("DS-010: macro-F1 per arm — recall A: " +
                 " ".join("%s %.2f" % (c, results["A"]["recall"][c])
                          for c in OP_VOCAB))
    ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig("d34_f1.png", dpi=110)
    plt.close(fig)

    # T1 — 5 artifacts da ghi o buoc nay; kpi/summary ghi sau do (neu loi ghi = crash hien hinh)
    required = ["d32_acc.png", "d33_reward.png", "d34_f1.png",
                "adapter_A/adapter_config.json", "adapter_A/adapter_model.safetensors"]
    have = [f for f in required if os.path.exists(f)]
    checks["T1"] = t1 = len(have) == len(required)
    d["T1"] = ("T1 pipeline (3 PNG + adapter_A, kpi/summary written last): "
               "have=%d/5 missing=%s -> %s"
               % (len(have), [f for f in required if f not in have],
                  "PASS" if t1 else "FAIL"))

    kpi = sum(1 for v in checks.values() if v)
    kpi_pass = kpi == 6
    runtime = (time.time() - T_START) / 60.0
    lines = [d["T%d" % i] for i in range(1, 7)]
    lines.append("")
    lines.append("KPI: %d/6 %s" % (kpi, "PASS" if kpi_pass else "SEE §21.5"))
    lines.append("data: total=%d usable=%d train=%d test=%d keys=%d | bars "
                 "Bar1=%.4f Bar2=%.4f | ops test gold=%s"
                 % (len(pairs), len(usable), len(train_rows), len(test_rows),
                    len(all_keys), bar1_test, bar2_test,
                    results["A"]["gold_n"] if "gold_n" in results["A"] else "?"))
    lines.append("SFT: steps=%d loss %.4f->%.4f | GRPO: B=%d C=%d reward-log "
                 "entries | bs sft=%d grpo=%d accum=%d G=%d loss_type=grpo"
                 % (a_loss["steps"], a_loss["first10"], a_loss["last10"],
                    len(curves["B"]), len(curves["C"]), SFT_BS, GRPO_BS,
                    GRPO_ACCUM, GRPO_G))
    pvo = [("test", len(test_rows)), ("acc_base", results["base"]["acc"]),
           ("acc_A", results["A"]["acc"]), ("acc_B", results["B"]["acc"]),
           ("acc_C", results["C"]["acc"]), ("Bar1", bar1_test),
           ("Bar2", bar2_test), ("macro_F1_A", results["A"]["macro_f1"]),
           ("reward_B_first", b_first), ("reward_B_last", b_last),
           ("train_acc_A", results["A_train"]["acc"]), ("runtime_min", runtime)]
    lines.append("predicted vs observed (non-gating): " + ", ".join(
        "%s %.3f/%.3f" % (k, PRED[k], v) for k, v in pvo))
    lines.append("fallback/OOM log: %s" % (FALLBACK_LOG or "none"))
    lines.append("note: seed %d/%d dat, nhung train/GPU khong deterministic — ket qua la 1 lan chay."
                 % (SEED, Q_SEED))
    kpi_txt = "\n".join(lines) + "\n"
    print(kpi_txt)

    raw_samples = {k: results[k].get("sample_raw", [])[:2]
                   for k in ("base", "A", "B", "C")}
    summary = {
        "config": {"MODEL_ID": MODEL_ID, "LORA": [LORA_R, LORA_ALPHA],
                   "SFT": [SFT_LR, SFT_EPOCHS, SFT_BS], "MAX_LEN": MAX_LEN,
                   "GRPO": [GRPO_LR, GRPO_G, GRPO_COMP, GRPO_BS, GRPO_ACCUM,
                            STEPS_B, STEPS_C, "grpo"],
                   "reward": [R_FORMAT, R_OP],
                   "seed": [SEED, Q_SEED, SPLIT_SEED]},
        "data": {"total": len(pairs), "usable": len(usable),
                 "train": len(train_rows), "test": len(test_rows),
                 "keys": len(all_keys), "leak": leak, "parity_ok": parity_ok},
        "bars": {"Bar1": bar1_test, "Bar2": bar2_test},
        "results": {k: {"acc": v["acc"], "macro_f1": v["macro_f1"],
                        "parse": v["parse"], "recall": v["recall"],
                        "f1": v.get("f1")}
                    for k, v in results.items()},
        "grpo": {"B_first10": b_first, "B_last10": b_last,
                 "parse_end": parse_end, "B_log": len(curves["B"]),
                 "C_log": len(curves["C"])},
        "sft_loss": a_loss,
        "pred_vs_obs": {k: {"pred": PRED[k], "obs": v} for k, v in pvo},
        "raw_samples": raw_samples,
        "fallback_log": FALLBACK_LOG,
        "kpi": "%d/6" % kpi, "checks": checks,
        "runtime_min": runtime,
    }
    with open("summary.json", "w") as f:
        json.dump(summary, f, indent=1)
    with open("kpi.txt", "w") as f:
        f.write(kpi_txt)
    print("wrote kpi.txt summary.json d32_acc.png d33_reward.png d34_f1.png "
          "adapter_A/")


if __name__ == "__main__":
    main()
