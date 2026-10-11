# DS-016 REASONING-DATA FACTORY (spec section 34) - LOCK pre-reg 324d529, change-log 34.1
# RUN_MODE=probe : run1 = QLoRA SFT (GSM8K think-mode) + probe 50 (base vs FT)
# RUN_MODE=gen   : run2 = generate N verified reasoning samples -> ds016_dataset.jsonl
# Rules: khong sua nguong/pred sau khi thay so; FAIL bao that.

import os
import sys
import json
import time
import random
import re
import subprocess

MODE = os.environ.get("RUN_MODE", "probe")
RUN_N = int(os.environ.get("RUN_N", "0"))
RUN_TOKS = float(os.environ.get("RUN_TOKS", "0"))
RUN_AVGLEN = float(os.environ.get("RUN_AVGLEN", "0"))
KERNEL_SLUG = os.environ.get("KAGGLE_KERNEL_SLUG", "ds-012-pretrain-from-scratch")

SEED_SFT = 20261011
SEED_PROBE = 20261011
SEED_GEN = 20261012
SFT_SUBSAMPLE = 4000   # 34.1 #1
SEQ_LEN = 512          # 34.1 #2
PROBE_MAX_NEW = 384    # 34.1 #2
GEN_MAX_NEW = 512      # 34.1 #2
N_PROBE = 50
B5_BUDGET_S = 7200.0
LR = 1e-4
LORA_R = 16
LORA_A = 32
MODEL_ID = "google/gemma-4-E2B-it"
OUT = "/kaggle/working/ds016"
os.makedirs(OUT, exist_ok=True)
# 34.2: allocator fix truoc khi import torch (v20 OOM - error message goi y)
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")


def log(*a):
    print("[ds016]", *a, flush=True)


def save_json(obj, name):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)


SUM = {"mode": MODE}


def write_kpi(extra=None):
    if extra:
        SUM.update(extra)
    save_json(SUM, "summary.json")
    lines = ["DS-016 reasoning-data factory (section 34) | mode=%s" % MODE]
    for k in sorted(SUM.keys()):
        v = SUM[k]
        if isinstance(v, (dict, list)):
            v = json.dumps(v, ensure_ascii=False)
        lines.append("%s = %s" % (k, v))
    with open(os.path.join(OUT, "kpi.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log("kpi-written")


log("mode", MODE, "RUN_N", RUN_N, "RUN_TOKS", RUN_TOKS, "RUN_AVGLEN", RUN_AVGLEN)
log("python", sys.version.split()[0])

# ---- env install (34.1 #4) ----
r = subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U",
                    "transformers", "peft", "accelerate", "bitsandbytes", "datasets"],
                   capture_output=True, text=True)
log("pip-rc", r.returncode, (r.stderr or "")[-300:])
r2 = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True)
with open(os.path.join(OUT, "pip_freeze.txt"), "w", encoding="utf-8") as f:
    f.write(r2.stdout)

import torch
import transformers
from transformers import (AutoModelForCausalLM, AutoProcessor, BitsAndBytesConfig,
                          TrainingArguments, Trainer, DataCollatorForSeq2Seq)
import peft
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
import datasets as hfds

SUM["versions"] = {"torch": torch.__version__, "transformers": transformers.__version__,
                   "peft": peft.__version__}
if not torch.cuda.is_available():
    write_kpi({"K-D1": "FAIL env: no cuda"})
    raise SystemExit(2)
GPU = torch.cuda.get_device_name(0)
VRAM = round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1)
log("torch", torch.__version__, "transformers", transformers.__version__,
    "peft", peft.__version__, "gpu", GPU, "vram_gb", VRAM)
SUM["gpu"] = {"name": GPU, "vram_gb": VRAM}

# =====================================================================
# Problem factory: programmatic, ground truth by construction (section 34)
# =====================================================================


def _k_eq(rng):
    x = rng.randint(-20, 30)
    a = rng.randint(2, 9)
    b = rng.randint(-30, 30)
    c = a * x + b
    return ("Solve for x: %d*x + %d = %d. What is x?" % (a, b, c), x)


def _k_percent(rng):
    while True:
        P = rng.choice([40, 60, 80, 100, 120, 150, 200, 240, 300, 400])
        d = rng.choice([10, 20, 25, 40, 50])
        r = rng.choice([5, 10, 20, 25, 40, 50])
        num = P * (100 - d) * (100 + r)
        if num % 10000 == 0:
            return ("A phone costs %d dollars. During a sale its price drops by %d percent. "
                    "After the sale the price rises by %d percent. What is the final price "
                    "in dollars?" % (P, d, r), num // 10000)


def _k_seq(rng):
    a1 = rng.randint(1, 20)
    d = rng.randint(2, 15)
    n = rng.randint(5, 30)
    return ("An arithmetic sequence starts at %d with common difference %d. "
            "What is the %d-th term?" % (a1, d, n), a1 + (n - 1) * d)


def _k_work(rng):
    pairs = [(m, n) for m in range(12, 61) for n in range(m + 1, 61)
             if (m * n) % (m + n) == 0]
    m, n = rng.choice(pairs)
    return ("Person A finishes a job in %d minutes and person B in %d minutes. "
            "Working together, how many minutes do they need? The answer is an integer."
            % (m, n), (m * n) // (m + n))


def _k_rect(rng):
    while True:
        l = rng.randint(6, 30)
        w = rng.randint(6, 30)
        k = rng.randint(1, 5)
        if w - k >= 2:
            return ("A rectangle has length %d and width %d. The length increases by %d "
                    "and the width decreases by %d. What is the new area?"
                    % (l, w, k, k), (l + k) * (w - k))


def _k_chain(rng):
    while True:
        n = rng.randint(5, 40)
        v = n
        ops = []
        ok = True
        for _ in range(4):
            t = rng.choice(["mul", "add", "sub"])
            if t == "mul":
                m = rng.randint(2, 4)
                v *= m
                ops.append("multiply by %d" % m)
            elif t == "add":
                m = rng.randint(3, 20)
                v += m
                ops.append("add %d" % m)
            else:
                if v - 12 < 0:
                    ok = False
                    break
                m = rng.randint(3, 12)
                v -= m
                ops.append("subtract %d" % m)
        if not ok:
            continue
        for dv in [2, 3, 4, 5]:
            if v % dv == 0 and v // dv >= 3:
                v //= dv
                ops.append("divide by %d" % dv)
                break
        tail = (" Then %s." % ops[4]) if len(ops) > 4 else ""
        return ("Start with the number %d. %s. Then %s. Then %s. Then %s.%s "
                "What number do you end with?" % (n, ops[0], ops[1], ops[2], ops[3], tail), v)


def _k_shop(rng):
    n1 = rng.randint(2, 9)
    p1 = rng.randint(3, 15)
    n2 = rng.randint(2, 9)
    p2 = rng.randint(2, 12)
    M = ((n1 * p1 + n2 * p2) // 10 + 1) * 10
    return ("You buy %d notebooks at %d dollars each and %d pens at %d dollars each. "
            "You pay with a %d dollar bill. How much change do you get in dollars?"
            % (n1, p1, n2, p2, M), M - (n1 * p1 + n2 * p2))


def _k_mix(rng):
    while True:
        L = rng.choice([10, 20, 30, 40, 50, 60, 80, 100])
        p = rng.choice([10, 20, 25, 40, 50])
        if (L * p) % 100 == 0:
            return ("A %d liter solution is %d percent acid. How many liters of acid "
                    "does it contain?" % (L, p), (L * p) // 100)


KINDS = [_k_eq, _k_percent, _k_seq, _k_work, _k_rect, _k_chain, _k_shop, _k_mix]


def make_problems(seed, n):
    rng = random.Random(seed)
    out = []
    for i in range(n):
        fn = KINDS[rng.randrange(len(KINDS))]
        text, ans = fn(rng)
        out.append({"id": i, "problem": text, "answer": str(int(ans))})
    return out


BOX_RE = re.compile(r"boxed\{\s*(-?\d+)\s*\}")
NUM_RE = re.compile(r"-?\d+")


def extract_answer(gen_text):
    seg = gen_text.rsplit("<|think|>", 1)[-1] if "<|think|>" in gen_text else gen_text
    ms = BOX_RE.findall(seg)
    if ms:
        return ms[-1]
    ns = NUM_RE.findall(seg)
    return ns[-1] if ns else None


INSTR = ("Solve the math problem. First think step by step: write all reasoning between "
         "<|think|> and <|think|>. Then write the final integer answer exactly as boxed{answer}.")


def render_user(problem):
    return INSTR + "\n\nProblem: " + problem


# =====================================================================
# Model load + LoRA (34.1 #4: fallback chain, ENV-FAIL khong fallback model)
# =====================================================================
from transformers import AutoModelForImageTextToText


def load_base():
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                             bnb_4bit_compute_dtype=torch.float16,
                             bnb_4bit_use_double_quant=True)
    try:
        m = AutoModelForCausalLM.from_pretrained(
            MODEL_ID, quantization_config=bnb, torch_dtype=torch.float16,
            device_map="auto")
        log("load-ok", "AutoModelForCausalLM")
        return m
    except Exception as e1:
        log("causal-lm-fail", repr(e1)[:400])
        try:
            m = AutoModelForImageTextToText.from_pretrained(
                MODEL_ID, quantization_config=bnb, torch_dtype=torch.float16,
                device_map="auto")
            log("load-ok", "AutoModelForImageTextToText (text-only)")
            return m
        except Exception as e2:
            log("ENV-FAIL model-load", repr(e2)[:400])
            write_kpi({"K-D1": "FAIL env: model load", "e_causal": repr(e1)[-300:],
                       "e_itt": repr(e2)[-300:]})
            raise SystemExit(2)


def wrap_lora(model):
    # 34.2 diag: find giant fp16 tensors + kbit flags (v20 OOM root cause)
    sized = [(n, int(p.numel()), str(p.dtype), p.__class__.__name__)
             for n, p in model.named_parameters()
             if p.dtype in (torch.float16, torch.bfloat16)]
    sized.sort(key=lambda x: -x[1])
    log("fp16-top", sized[:8])
    log("kbit-flags is4", getattr(model, "is_loaded_in_4bit", None),
        "is8", getattr(model, "is_loaded_in_8bit", None))
    # offload unused multimodal towers (text-only run) if present
    for attr in ("vision_tower", "audio_tower", "vision_model", "audio_model",
                 "multi_modal_projector", "mm_projector"):
        sub = getattr(model, attr, None)
        if sub is not None:
            try:
                sub.to("cpu")
                log("offload-cpu", attr)
            except Exception as e:
                log("offload-fail", attr, repr(e)[:120])
    torch.cuda.empty_cache()
    lin_full = [(n, mod) for n, mod in model.named_modules()
                if isinstance(mod, torch.nn.Linear)]
    pref = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    # 34.3: restrict to language_model full paths - Gemma4ClippableLinear (nn.Module wrapper,
    # khong phai nn.Linear) nam trong VISION/AUDIO tower, peft khong wrap duoc; text-only run
    lang_targets = sorted({n for n, m in lin_full
                           if n.rsplit(".", 1)[-1] in pref and "language_model" in n})
    if lang_targets:
        targets = lang_targets
        log("lora-targets mode full-path-language_model n", len(targets), targets[:4])
    else:
        targets = sorted({n for n, m in lin_full
                          if n.rsplit(".", 1)[-1] in pref
                          and not any(k in n.lower()
                                      for k in ("vision", "audio", "tower"))})
        log("lora-targets mode leaf-sans-towers n", len(targets), targets[:6])
    if not targets:
        write_kpi({"K-D1": "FAIL env: no lora targets"})
        raise SystemExit(2)
    # 34.2: manual QLoRA recipe - KHONG goi peft.prepare_model_for_kbit_training
    # (v20 OOM: no cast fp16 param 2.35B -> fp32)
    cfg = LoraConfig(r=LORA_R, lora_alpha=LORA_A, lora_dropout=0.0,
                     target_modules=targets, task_type="CAUSAL_LM")
    model = get_peft_model(model, cfg)
    model.print_trainable_parameters()
    try:
        model.enable_input_require_grads()
        log("input-require-grads ok")
    except Exception:
        emb = model.get_input_embeddings()

        def _make_grad(module, inp, out):
            if torch.is_tensor(out):
                out.requires_grad_(True)

        emb.register_forward_hook(_make_grad)
        log("input-require-grads fallback-hook")
    try:
        model.gradient_checkpointing_enable(
            gradient_checkpointing_kwargs={"use_reentrant": False})
        log("grad-ckpt ok reentrant=False")
    except TypeError:
        model.gradient_checkpointing_enable()
        log("grad-ckpt ok default-kwargs")
    model.config.use_cache = False
    torch.cuda.empty_cache()
    log("vram-after-wrap", round(torch.cuda.memory_allocated() / 1e9, 2), "GiB")
    return model


# =====================================================================
# SFT data (GSM8K train -> think-mode), Trainer
# =====================================================================
def build_sft(tokenizer):
    ds = hfds.load_dataset("openai/gsm8k", "main")
    rows = list(ds["train"])
    rng = random.Random(SEED_SFT)
    rng.shuffle(rows)
    rows = rows[:SFT_SUBSAMPLE]
    kept = 0
    skipped = 0
    out = []
    for row in rows:
        parts = row["answer"].split("####")
        gold_m = NUM_RE.search(parts[-1].strip().replace(",", ""))
        if not gold_m:
            skipped += 1
            continue
        gold = gold_m.group(0)
        reasoning = parts[0].strip()
        asst = "<|think|>%s<|think|>boxed{%s}" % (reasoning, gold)
        prompt = tokenizer.apply_chat_template(
            [{"role": "user", "content": render_user(row["question"])}],
            tokenize=False, add_generation_prompt=True)
        p_ids = tokenizer(prompt, add_special_tokens=False)["input_ids"]
        a_ids = tokenizer(asst, add_special_tokens=False)["input_ids"]
        a_ids = a_ids + [tokenizer.eos_token_id]
        ids = p_ids + a_ids
        if len(ids) > SEQ_LEN or len(a_ids) < 4:
            skipped += 1
            continue
        out.append({"input_ids": ids, "labels": [-100] * len(p_ids) + list(a_ids)})
        kept += 1
    log("sft-kept", kept, "skipped", skipped)
    return out, kept, skipped


def run_sft(model, tokenizer):
    kept_rows, kept, skipped = build_sft(tokenizer)
    if kept < 100:
        write_kpi({"K-D1": "FAIL sft-data", "kept": kept})
        raise SystemExit(2)
    hds = hfds.Dataset.from_list(kept_rows)
    targs = TrainingArguments(
        output_dir=OUT + "/ckpt", num_train_epochs=1,
        per_device_train_batch_size=2, gradient_accumulation_steps=4,
        learning_rate=LR, lr_scheduler_type="cosine", warmup_ratio=0.03,
        logging_steps=10, save_strategy="no", report_to=[], fp16=True,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        seed=SEED_SFT, remove_unused_columns=False)
    coll = DataCollatorForSeq2Seq(tokenizer, padding=True,
                                  label_pad_token_id=-100, return_tensors="pt")
    try:
        tr = Trainer(model=model, args=targs, train_dataset=hds,
                     data_collator=coll, processing_class=tokenizer)
    except TypeError:
        tr = Trainer(model=model, args=targs, train_dataset=hds,
                     data_collator=coll, tokenizer=tokenizer)
    t0 = time.time()
    tr.train()
    wall = time.time() - t0
    hist = []
    for h in tr.state.log_history:
        if "loss" in h:
            hist.append({"step": int(h.get("step", 0)), "loss": float(h["loss"])})
    return wall, hist, kept, skipped


# =====================================================================
# Generation + verify
# =====================================================================
def gen_and_verify(model, tokenizer, problems, sampling, max_new):
    outs = []
    t0 = time.time()
    ntok = 0
    for p in problems:
        prompt = tokenizer.apply_chat_template(
            [{"role": "user", "content": render_user(p["problem"])}],
            tokenize=False, add_generation_prompt=True)
        ids = tokenizer(prompt, return_tensors="pt").to(model.device)
        kw = {"max_new_tokens": max_new, "do_sample": sampling,
              "pad_token_id": tokenizer.eos_token_id}
        if sampling:
            kw["temperature"] = 0.7
            kw["top_p"] = 0.95
        with torch.no_grad():
            out = model.generate(**ids, **kw)
        gen_ids = out[0][ids["input_ids"].shape[1]:]
        txt = tokenizer.decode(gen_ids, skip_special_tokens=False)
        ntok += int(gen_ids.shape[0])
        pred = extract_answer(txt)
        outs.append({"id": p["id"], "problem": p["problem"], "gold": p["answer"],
                     "pred": pred, "ok": bool(pred == p["answer"]),
                     "raw": txt[:4000]})
    wall = time.time() - t0
    return outs, ntok, wall


def try_plots(hist, pb, pf):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        if hist:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.plot([h["step"] for h in hist], [h["loss"] for h in hist], marker=".")
            ax.set_title("DS-016 SFT loss (GSM8K think-mode, 1 epoch)")
            ax.set_xlabel("step")
            ax.set_ylabel("loss")
            fig.tight_layout()
            fig.savefig(OUT + "/d01_loss.png", dpi=110)
            plt.close(fig)
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(["base", "finetuned"], [pb, pf], color=["gray", "steelblue"])
        ax.axhline(pb + 0.05, color="red", ls="--", lw=1, label="K-D2 gate (+0.05)")
        ax.set_ylim(0, 1)
        ax.set_title("DS-016 probe verify-pass (50 problems, greedy)")
        ax.legend()
        fig.tight_layout()
        fig.savefig(OUT + "/d02_probe.png", dpi=110)
        plt.close(fig)
        log("plots-ok")
    except Exception as e:
        log("plots-fail", repr(e)[:300])


def try_plots_dataset(n_total, n_ver, lengths):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(["generated", "verified"], [n_total, n_ver], color=["gray", "seagreen"])
        ax.set_title("DS-016 dataset gen: verified rate")
        fig.tight_layout()
        fig.savefig(OUT + "/d03_dataset.png", dpi=110)
        plt.close(fig)
        if lengths:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.hist(lengths, bins=20, color="seagreen")
            ax.set_title("DS-016 gen length distribution (tokens)")
            fig.tight_layout()
            fig.savefig(OUT + "/d04_lengths.png", dpi=110)
            plt.close(fig)
        log("plots-ok")
    except Exception as e:
        log("plots-fail", repr(e)[:300])


# =====================================================================
# MODE: probe (run 1)
# =====================================================================
if MODE == "probe":
    model = load_base()
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    tokenizer = processor.tokenizer
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    log("tokenizer", tokenizer.__class__.__name__, "vocab", len(tokenizer))

    model = wrap_lora(model)
    wall_sft, hist, kept, skipped = run_sft(model, tokenizer)
    log("sft-done wall_min", round(wall_sft / 60.0, 1),
        "loss_first", hist[0]["loss"] if hist else None,
        "loss_last", hist[-1]["loss"] if hist else None)
    model.save_adapter(OUT + "/adapter", "ds016")
    log("adapter-saved")
    model.config.use_cache = True

    probe = make_problems(SEED_PROBE, N_PROBE)
    save_json({"probe_problems": probe}, "probe_problems.json")

    with torch.no_grad():
        with model.disable_adapter():
            base_out, base_tok, base_wall = gen_and_verify(
                model, tokenizer, probe, False, PROBE_MAX_NEW)
    ft_out, ft_tok, ft_wall = gen_and_verify(model, tokenizer, probe, False, PROBE_MAX_NEW)

    pb = sum(o["ok"] for o in base_out) / float(len(base_out))
    pf = sum(o["ok"] for o in ft_out) / float(len(ft_out))
    tok_s = ft_tok / ft_wall if ft_wall > 0 else 0.0
    avg_len = ft_tok / float(len(probe))
    log("probe", "pass_base", round(pb, 4), "pass_ft", round(pf, 4),
        "tok_s", round(tok_s, 2), "avg_len", round(avg_len, 1),
        "base_wall_min", round(base_wall / 60.0, 1), "ft_wall_min", round(ft_wall / 60.0, 1))

    save_json({"base": base_out, "ft": ft_out}, "probe_details.json")
    loss_ok = bool(hist and hist[-1]["loss"] < hist[0]["loss"])
    k_d1 = "PASS" if loss_ok else "FAIL"
    k_d2 = "PASS" if pf >= pb + 0.05 else "FAIL"
    preds = {
        "pred1_verify_pass_base_0.35_[0.15,0.60]": {"obs": round(pb, 4),
         "grade": "CLOSE" if 0.15 <= pb <= 0.60 else "MISS"},
        "pred2_verify_pass_FT_0.60_[0.35,0.85]": {"obs": round(pf, 4),
         "grade": "CLOSE" if 0.35 <= pf <= 0.85 else "MISS"},
        "pred3_toks_25_[12,45]": {"obs": round(tok_s, 2),
         "grade": "CLOSE" if 12 <= tok_s <= 45 else "MISS"},
        "pred4_sft_wall_45min_[30,80]": {"obs": round(wall_sft / 60.0, 1),
         "grade": "CLOSE" if 30 <= wall_sft / 60.0 <= 80 else "MISS"},
    }
    mem = round(torch.cuda.max_memory_allocated() / 1e9, 2)
    SUM["sft"] = {"kept": kept, "skipped": skipped, "wall_min": round(wall_sft / 60.0, 1),
                  "loss_first": hist[0]["loss"] if hist else None,
                  "loss_last": hist[-1]["loss"] if hist else None,
                  "hist": hist}
    SUM["probe"] = {"n": N_PROBE, "pass_base": round(pb, 4), "pass_ft": round(pf, 4),
                    "tok_s": round(tok_s, 2), "avg_len": round(avg_len, 1),
                    "base_wall_min": round(base_wall / 60.0, 1),
                    "ft_wall_min": round(ft_wall / 60.0, 1)}
    SUM["preds_vs_obs"] = preds
    SUM["vram_peak_gb"] = mem
    write_kpi({"K-D1": k_d1, "K-D2": k_d2})
    try_plots(hist, pb, pf)
    log("RUN1-DONE K-D1", k_d1, "K-D2", k_d2)

# =====================================================================
# MODE: gen (run 2)
# =====================================================================
elif MODE == "gen":
    if RUN_N <= 0:
        write_kpi({"K-D4": "FAIL env: RUN_N missing"})
        raise SystemExit(2)
    dst = "/tmp/kout"
    rr = subprocess.run([sys.executable, "-m", "kaggle", "kernels", "output",
                         KERNEL_SLUG, "-p", dst, "--force"],
                        capture_output=True, text=True)
    log("kernels-output-rc", rr.returncode, (rr.stderr or "")[-200:])
    ad = os.path.join(dst, "ds016", "adapter")
    if not os.path.isdir(ad):
        write_kpi({"K-D4": "FAIL env: adapter not found after kernels output"})
        raise SystemExit(2)
    log("adapter-found", ad, "bytes", sum(
        os.path.getsize(os.path.join(dp, fn))
        for dp, _, fns in os.walk(ad) for fn in fns))

    model = load_base()
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    tokenizer = processor.tokenizer
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = peft.PeftModel.from_pretrained(model, ad, adapter_name="ds016")
    model.eval()
    model.config.use_cache = True

    # audit: N-rule (34.1 #5)
    n_expected = 0
    if RUN_TOKS > 0 and RUN_AVGLEN > 0:
        n_expected = 50 * int(B5_BUDGET_S * RUN_TOKS / (50.0 * RUN_AVGLEN))
        n_expected = max(300, min(1200, n_expected))
        if n_expected != RUN_N:
            log("RULE-MISMATCH expected", n_expected, "got", RUN_N)
        else:
            log("rule-ok N", RUN_N)

    probs = make_problems(SEED_GEN, RUN_N)
    outs, ntok, wall = gen_and_verify(model, tokenizer, probs, True, GEN_MAX_NEW)
    verified = [o for o in outs if o["ok"]]
    seen = set()
    uniq = []
    for o in verified:
        if o["problem"] not in seen:
            seen.add(o["problem"])
            uniq.append(o)
    with open(OUT + "/ds016_dataset.jsonl", "w", encoding="utf-8") as f:
        for o in uniq:
            f.write(json.dumps({"problem": o["problem"],
                                "solution_think": o["raw"],
                                "final_answer": o["gold"],
                                "ground_truth": o["gold"],
                                "generator": MODEL_ID,
                                "verified": True}, ensure_ascii=False) + "\n")
    # K-D3: verify lai 100% tren file export
    n_lines = 0
    n_recheck = 0
    with open(OUT + "/ds016_dataset.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            n_lines += 1
            if extract_answer(row["solution_think"]) == row["final_answer"]:
                n_recheck += 1
    pass_rate = len(verified) / float(len(outs))
    unique_frac = (len(set(o["problem"] for o in verified)) /
                   float(len(verified))) if verified else 0.0
    lens = [len(o["raw"].split()) for o in uniq]
    log("gen", "n_gen", len(outs), "verified", len(verified), "uniq", len(uniq),
        "pass_rate", round(pass_rate, 4), "wall_h", round(wall / 3600.0, 2),
        "recheck", "%d/%d" % (n_recheck, n_lines))

    k_d3 = "PASS" if (len(uniq) >= 300 and n_recheck == n_lines and n_lines > 0
                      and unique_frac >= 0.99) else "FAIL"
    k_d4 = "PASS" if wall <= B5_BUDGET_S * 1.2 else "FAIL"
    SUM["dataset"] = {"run_n": RUN_N, "n_expected_rule": n_expected,
                      "n_generated": len(outs), "n_verified": len(verified),
                      "n_export": n_lines, "pass_rate": round(pass_rate, 4),
                      "unique_frac": round(unique_frac, 4),
                      "recheck_ok": "%d/%d" % (n_recheck, n_lines),
                      "wall_min": round(wall / 60.0, 1),
                      "tok_s": round(ntok / wall, 2) if wall > 0 else 0.0,
                      "avg_words": round(sum(lens) / float(len(lens)), 1) if lens else 0.0}
    write_kpi({"K-D3": k_d3, "K-D4": k_d4})
    try_plots_dataset(len(outs), len(uniq), lens)
    log("RUN2-DONE K-D3", k_d3, "K-D4", k_d4)

else:
    write_kpi({"env": "FAIL: unknown RUN_MODE " + MODE})
    raise SystemExit(2)
