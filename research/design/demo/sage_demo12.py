# DS-012 — Pretrain from-scratch tren T4 (pre-register §23: commit 9314d36 + amend 70b5f83)
# Cau hoi: thu tu dan bay F-B02 (data >= kien truc > optimizer > init) co dung o regime 1 GPU khong?
# Quy tac: KHONG sua nguong K1-K6 sau khi thay so; moi thay doi ghi §23.4.
# Script nay resume duoc: cell da co results/*.json se bo qua.
import os, json, math, time, hashlib, random, traceback
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

# ---------------- Config (§23.1) ----------------
OUT = "/kaggle/working/ds012"          # results, kpi, plots (duoc luu thanh kernel output)
TMP = "/kaggle/temp/ds012"              # bin token (ephemeral — khong phai output)
for d in (OUT, f"{OUT}/results", f"{OUT}/plots", TMP):
    os.makedirs(d, exist_ok=True)

C = dict(
    N_LAYERS=6, D_MODEL=384, N_HEADS=6, N_KV=2, HEAD_DIM=64, FFN=1024,
    VOCAB=8192, SEQ=1024,
    BATCH_TOK=27648,                   # §23.4 #1: B* = 3.6e-4·D^0.931 ≈ 28k token (27 seq × 1024)
    LR=2.4e-3,                         # §23.4 #1: η* = 0.0985·N^-0.508·D^0.238 (N=14e6, D=0.3e9)
    LR_MUON=2.0e-2,                    # §23.4 #2: Muon-usage chuan (nhom AdamW giu η*)
    WARMUP=1000, TOTAL_TOK=int(3e8),   # §23.1 scale-down da ghi truoc: 0.3B token/run
    HOLDOUT_TOK=int(1e7),              # 10M token holdout cuoi, tach theo document
    CLIP=1.0,
    SEEDS=[11, 22, 33], ARMS=["A1", "A2", "A3"],
)
MAX_CELLS_THIS_SESSION = 9             # scheduling (KHONG phai nguong) — ghi §23.4 neu doi giua session
TOTAL_STEPS = C["TOTAL_TOK"] // C["BATCH_TOK"]

try:
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
except Exception:
    pass


# ---------------- Model (Qwen3-style: RMSNorm + SwiGLU + RoPE + GQA + QK-Norm) ----------------
class RMSNorm(nn.Module):
    def __init__(self, d):
        super().__init__()
        self.w = nn.Parameter(torch.ones(d))

    def forward(self, x):
        return self.w * x * torch.rsqrt(x.float().pow(2).mean(-1, keepdim=True) + 1e-6).to(x.dtype)


def rope_cache(seq, hd, device, theta=10000.0):
    inv = 1.0 / (theta ** (torch.arange(0, hd, 2, device=device).float() / hd))
    freqs = torch.outer(torch.arange(seq, device=device).float(), inv)
    return freqs.cos(), freqs.sin()


def apply_rope(x, cos, sin):  # x: (B, nh, T, hd)
    x1, x2 = x[..., 0::2], x[..., 1::2]
    cos, sin = cos[None, None, :, :], sin[None, None, :, :]
    o = torch.stack((x1 * cos - x2 * sin, x1 * sin + x2 * cos), -1).flatten(-2)
    return o.type_as(x)


class Attn(nn.Module):
    def __init__(s, d, nh, nkv, hd):
        super().__init__()
        s.nh, s.nkv, s.hd = nh, nkv, hd
        s.q = nn.Linear(d, nh * hd, bias=False)
        s.k = nn.Linear(d, nkv * hd, bias=False)
        s.v = nn.Linear(d, nkv * hd, bias=False)
        s.o = nn.Linear(nh * hd, d, bias=False)
        s.qn = nn.LayerNorm(hd, elementwise_affine=False)   # QK-Norm
        s.kn = nn.LayerNorm(hd, elementwise_affine=False)

    def forward(s, x, cos, sin):
        B, T, _ = x.shape
        q = s.qn(s.q(x).view(B, T, s.nh, s.hd)).transpose(1, 2)
        k = s.kn(s.k(x).view(B, T, s.nkv, s.hd)).transpose(1, 2)
        v = s.v(x).view(B, T, s.nkv, s.hd).transpose(1, 2)
        q, k = apply_rope(q, cos, sin), apply_rope(k, cos, sin)
        if s.nkv != s.nh:
            rep = s.nh // s.nkv
            k = k.repeat_interleave(rep, 1)
            v = v.repeat_interleave(rep, 1)
        y = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        return s.o(y.transpose(1, 2).contiguous().view(B, T, s.nh * s.hd))


class MLP(nn.Module):
    def __init__(s, d, f):
        super().__init__()
        s.g = nn.Linear(d, f, bias=False)
        s.u = nn.Linear(d, f, bias=False)
        s.d = nn.Linear(f, d, bias=False)

    def forward(s, x):
        return s.d(F.silu(s.g(x)) * s.u(x))


class Block(nn.Module):
    def __init__(s, d, nh, nkv, hd, f):
        super().__init__()
        s.ln1 = RMSNorm(d)
        s.ln2 = RMSNorm(d)
        s.attn = Attn(d, nh, nkv, hd)
        s.mlp = MLP(d, f)

    def forward(s, x, cos, sin):
        x = x + s.attn(s.ln1(x), cos, sin)
        return x + s.mlp(s.ln2(x))


class GPT(nn.Module):
    def __init__(s, cfg, vocab):
        super().__init__()
        d, nh, nkv, hd, f = cfg["D_MODEL"], cfg["N_HEADS"], cfg["N_KV"], cfg["HEAD_DIM"], cfg["FFN"]
        s.emb = nn.Embedding(vocab, d)
        s.blocks = nn.ModuleList([Block(d, nh, nkv, hd, f) for _ in range(cfg["N_LAYERS"])])
        s.lnf = RMSNorm(d)
        s.head = nn.Linear(d, vocab, bias=False)
        s.head.weight = s.emb.weight                       # tied embedding
        s.apply(lambda m: nn.init.normal_(m.weight, std=0.02) if isinstance(m, (nn.Linear, nn.Embedding)) else None)

    def forward(s, idx, targets=None):
        B, T = idx.shape
        cos, sin = rope_cache(T, C["HEAD_DIM"], idx.device)
        x = s.emb(idx)
        for b in s.blocks:
            x = b(x, cos, sin)
        x = s.lnf(x)
        if targets is None:
            return s.head(x[:, [-1]])
        return F.cross_entropy(s.head(x).float().view(-1, s.head.weight.size(0)), targets.reshape(-1))


def count_params(m):
    tot = sum(p.numel() for p in m.parameters())           # tied head dem 1 lan
    non_emb = tot - m.emb.weight.numel()
    return tot, non_emb


def is_muon_param(name, p):
    return p.dim() == 2 and not name.startswith("emb") and not name.startswith("head")


# ---------------- Muon (A2) ----------------
def newtonschulz(G, steps=5):
    a, b, c = 3.4445, -4.7750, 2.0315
    X = G.float()
    X /= (X.norm() + 1e-7)
    for _ in range(steps):
        A = X @ X.T
        B = b * A + c * (A @ A)
        X = a * X + B @ X
    return X


class Muon(torch.optim.Optimizer):
    def __init__(self, params, lr):
        super().__init__(params, dict(lr=lr))

    @torch.no_grad()
    def step(self):
        for g in self.param_groups:
            for p in g["params"]:
                if p.grad is None:
                    continue
                g_ = p.grad.float()
                buf = self.state[p].get("buf")
                buf = g_ if buf is None else buf.mul_(0.95).add_(g_, alpha=1 - 0.95)
                self.state[p]["buf"] = buf
                upd = newtonschulz(buf)
                scale = max(1.0, p.size(0) / p.size(1)) ** 0.5
                p.add_(upd.type_as(p), alpha=-g["lr"] * scale)


# ---------------- Du lieu (§23.1 corpus + holdout theo document) ----------------
from tokenizers import Tokenizer, models, trainers, pre_tokenizers, decoders

_STOP = set("the of and to in a is that for it as with was on be at by this are from or an but not "
            "they have we you one all can had were her been has who will more when what about into "
            "some than its his her their there which would could other over after before these those".split())


def get_stream():
    """Thu tungnguon theo thu tu pre-reg §23.1 (FineWeb-Edu truoc, fallback Tinystories/WikiText)."""
    from datasets import load_dataset
    tries = [
        ("HuggingFaceFW/fineweb-edu", "sample-10BT", "train"),
        ("HuggingFaceFW/fineweb", "sample-10BT", "train"),
        ("roneneldan/TinyStories", None, "train"),
        ("wikitext", "wikitext-103-raw-v1", "train"),
    ]
    last = None
    for name, cfgname, split in tries:
        try:
            kw = dict(streaming=True)
            if cfgname:
                kw["name"] = cfgname
            ds = load_dataset(name, **kw)
            it = iter(ds[split])
            next(it)  # prime (item nay bi bo — khong anh huong, stream van deterministically theo thu tu hub)

            def gen(_it=it):
                while True:
                    try:
                        yield next(_it)
                    except StopIteration:
                        return
            print(f"[data] source = {name} (cfg={cfgname})", flush=True)
            return name, gen()
        except Exception as e:
            last = e
            print(f"[data] {name} failed: {type(e).__name__}: {e}", flush=True)
    raise RuntimeError(f"all corpus sources failed: {last}")


def norm_text(t):
    t = (t or "").replace("\x00", " ")
    lines = [l.strip() for l in t.splitlines()]
    return "\n".join(l for l in lines if l)


def quality_ok(t):
    """A3 quality filter: length + alpha-ratio + langid proxy (ASCII/stopword) + repetition + digit-ratio."""
    if len(t) < 200 or len(t) > 40000:
        return False
    letters = sum(c.isalpha() for c in t)
    if letters / len(t) < 0.75:
        return False
    words = t.split()
    if len(words) < 40:
        return False
    if sum(ord(c) > 127 for c in t[:2000]) / 2000 > 0.15:
        return False
    sw = sum(1 for w in words[:200] if w.lower() in _STOP)
    if sw / max(1, min(200, len(words))) < 0.12:
        return False
    lines = [l[:80] for l in t.splitlines()[:50]]
    if len(set(lines)) < max(1, int(0.5 * len(lines))):
        return False
    if sum(c.isdigit() for c in t) / len(t) > 0.35:
        return False
    return True


def minhash_bands(t, perms=32, cap=40):
    """Minhash (32 perm) tren word 5-gram -> 8 band hash. Chi goi khi quality_ok == True."""
    words = t.lower().split()[:2000]
    sh = []
    seen = set()
    for i in range(0, max(0, len(words) - 4), 4):
        s = " ".join(words[i:i + 5])
        if s not in seen:
            seen.add(s)
            sh.append(s)
        if len(sh) >= cap:
            break
    if not sh:
        return None
    vals = np.array([int.from_bytes(hashlib.blake2b(s.encode(), digest_size=8).digest(), "little")
                     for s in sh], dtype=np.uint64)
    out = np.full(perms, np.iinfo(np.uint64).max, dtype=np.uint64)
    for p in range(perms):
        a = np.uint64((p * 0x9E3779B97F4A7C15 + 1) | 1)
        b = np.uint64((p * 0xC2B2AE3D27D4EB4F + 7) | 1)
        out[p] = np.bitwise_and(vals * a + b, np.uint64(0xFFFFFFFFFFFFFFFF)).min()
    return [hashlib.md5(out[i * 4:(i + 1) * 4].tobytes()).hexdigest() for i in range(perms // 4)]


def train_tokenizer(sample_texts):
    tk = Tokenizer(models.BPE(unk_token=None))
    tk.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tk.decoder = decoders.ByteLevel()
    tk.train_from_iterator(
        sample_texts,
        trainers.BpeTrainer(vocab_size=C["VOCAB"], min_frequency=2, special_tokens=["<pad>"],
                            initial_alphabet=pre_tokenizers.ByteLevel.alphabet()))
    return tk


def prepare_data():
    """Mot lan stream -> a1.bin (0.3B token THO, baseline), a3.bin (0.3B token SAU dedup+filter),
    hold.bin (10M token holdout — doc xuat hien SAU khi ca 2 pool day, nen khong train trung).
    Deterministic theo thu tu stream; tokenizer train tren 20M ky tu dau cua cung stream."""
    paths = {k: f"{TMP}/{k}.bin" for k in ("a1", "a3", "hold")}
    meta_p = f"{OUT}/data_meta.json"
    if all(os.path.exists(x) for x in paths.values()) and os.path.exists(meta_p):
        print("[data] reuse cached bins", flush=True)
        return json.load(open(meta_p))
    t0 = time.time()
    src, it = get_stream()

    buf = []
    while sum(len(s) for s in buf) < 2e7:
        d = next(it)
        txt = norm_text(d.get("text", ""))
        if txt:
            buf.append(txt)
    tk = train_tokenizer(iter(buf))
    tk.save(f"{OUT}/tokenizer.json")
    del buf
    print(f"[data] tokenizer trained (vocab {C['VOCAB']}) in {time.time()-t0:.0f}s", flush=True)

    need1, need3, needh = C["TOTAL_TOK"], C["TOTAL_TOK"], C["HOLDOUT_TOK"]
    n1 = n3 = nh = 0
    d1 = d3 = dh = 0
    seen_hash, lsh_seen = set(), set()
    rejected = near_dup = exact_dup = scanned = 0
    f1 = open(paths["a1"], "wb")
    f3 = open(paths["a3"], "wb")
    fh = open(paths["hold"], "wb")
    hold_mode = False
    try:
        while True:
            if hold_mode and nh >= needh:
                break
            try:
                d = next(it)
            except StopIteration:
                print("[data] stream ended early", flush=True)
                break
            txt = norm_text(d.get("text", ""))
            if not txt:
                continue
            scanned += 1
            if not hold_mode and n1 >= need1 and n3 >= need3:
                hold_mode = True
                print(f"[data] pools full at doc {scanned} -> holdout phase ({time.time()-t0:.0f}s)", flush=True)
            ids = tk.encode(txt).ids
            if len(ids) < 8:
                continue
            if hold_mode:
                fh.write(np.asarray(ids, dtype=np.uint16).tobytes())
                nh += len(ids)
                dh += 1
                continue
            # --- A1: raw pool (khong loc) ---
            if n1 < need1:
                take = min(len(ids), need1 - n1)
                f1.write(np.asarray(ids[:take], dtype=np.uint16).tobytes())
                n1 += take
                d1 += 1
            # --- A3: dedup (exact + minhash LSH) + quality filter ---
            if n3 < need3:
                h = hashlib.md5(txt[:4000].encode("utf8", "ignore")).hexdigest()
                dup = h in seen_hash
                if not dup:
                    seen_hash.add(h)
                else:
                    exact_dup += 1
                ok = (not dup) and quality_ok(txt)
                if ok:
                    bands = minhash_bands(txt)
                    if bands is not None and (set(bands) & lsh_seen):
                        ok = False
                        near_dup += 1
                    elif bands is not None:
                        lsh_seen.update(bands)
                if ok:
                    take = min(len(ids), need3 - n3)
                    f3.write(np.asarray(ids[:take], dtype=np.uint16).tobytes())
                    n3 += take
                    d3 += 1
                else:
                    rejected += 1
            if scanned % 20000 == 0:
                print(f"[data] scanned {scanned} | a1 {n1/1e6:.1f}M | a3 {n3/1e6:.1f}M | hold {nh/1e6:.1f}M "
                      f"| rej {rejected} | {time.time()-t0:.0f}s", flush=True)
    finally:
        for f in (f1, f3, fh):
            f.close()
    meta = dict(source=src, a1_tokens=int(n1), a3_tokens=int(n3), holdout_tokens=int(nh),
                a1_docs=d1, a3_docs=d3, hold_docs=dh, rejected=rejected, exact_dup=exact_dup,
                near_dup=near_dup, scanned=scanned, prep_seconds=round(time.time() - t0, 1),
                dedup_rate=round((exact_dup + near_dup) / max(1, scanned), 4),
                reject_rate=round(rejected / max(1, scanned), 4))
    json.dump(meta, open(meta_p, "w"), indent=1)
    print(f"[data] DONE {json.dumps(meta)}", flush=True)
    return meta


# ---------------- Train ----------------
def flat_uint16(path):
    return np.memmap(path, dtype=np.uint16, mode="r")


def get_batch(flat, rng, bs, seq):
    span = bs * seq + 1
    hi = len(flat) - span
    if hi <= 0:
        raise RuntimeError(f"corpus terlalu kecil: {len(flat)} < {span}")
    o = int(rng.integers(0, hi))
    w = np.asarray(flat[o:o + span], dtype=np.int64)
    x = torch.from_numpy(w[:-1].reshape(bs, seq))
    y = torch.from_numpy(w[1:].reshape(bs, seq))
    return x.cuda(non_blocking=True), y.cuda(non_blocking=True)


@torch.no_grad()
def eval_split(flat, model, bs=27, seq=1024, cap_tokens=10_000_000):
    model.eval()
    n_batches = min((len(flat) - 1) // (bs * seq), cap_tokens // (bs * seq))
    tot, n = 0.0, 0
    span = bs * seq
    for b in range(n_batches):
        o = b * span
        w = np.asarray(flat[o:o + span + 1], dtype=np.int64)
        if len(w) < span + 1:
            break
        x = torch.from_numpy(w[:-1].reshape(bs, seq)).cuda(non_blocking=True)
        y = torch.from_numpy(w[1:].reshape(bs, seq)).cuda(non_blocking=True)
        loss = model(x, y)
        tot += loss.item() * bs
        n += bs
    model.train()
    return tot / max(1, n)


def lr_at(step, peak):
    if step < C["WARMUP"]:
        return peak * (step + 1) / C["WARMUP"]
    prog = (step - C["WARMUP"]) / max(1, TOTAL_STEPS - C["WARMUP"])
    return 0.1 * peak + 0.9 * peak * 0.5 * (1 + math.cos(math.pi * min(1.0, prog)))


def train_cell(arm, seed, flats, meta):
    res_p = f"{OUT}/results/{arm}_s{seed}.json"
    if os.path.exists(res_p):
        print(f"[skip] {arm} s{seed} done", flush=True)
        return json.load(open(res_p))
    torch.cuda.empty_cache()
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    model = GPT(C, C["VOCAB"]).cuda()
    tot, non_emb = count_params(model)
    flat = flats["a1"] if arm != "A3" else flats["a3"]

    muon = None
    if arm == "A2":
        muon_params = [p for n_, p in model.named_parameters() if is_muon_param(n_, p)]
        adam_params = [p for n_, p in model.named_parameters() if not is_muon_param(n_, p)]
        muon = Muon(muon_params, lr=C["LR_MUON"])
        # nhom Muon nam trong opt voi lr=0 -> scaler.unscale_ bao trum TAT CA gradient,
        # AdamW khong cap nhat no (lr=0: wd cung khong doi weight), chi Muon.step() cap nhat
        opt = torch.optim.AdamW([{"params": adam_params, "lr": C["LR"]},
                                 {"params": muon_params, "lr": 0.0}],
                                betas=(0.9, 0.95), weight_decay=0.1)
    else:
        opt = torch.optim.AdamW(model.parameters(), lr=C["LR"], betas=(0.9, 0.95), weight_decay=0.1)
    try:
        scaler = torch.amp.GradScaler("cuda")
    except Exception:
        scaler = torch.cuda.amp.GradScaler()
    rng = np.random.default_rng(seed)
    bs, seq = C["BATCH_TOK"] // C["SEQ"], C["SEQ"]

    hist, t0 = [], time.time()
    loss100, step, divergence = None, 0, False
    model.train()
    while step < TOTAL_STEPS:
        lr = lr_at(step, C["LR"])
        opt.param_groups[0]["lr"] = lr          # nhom AdamW (A2: group 1 = muon, lr=0, khong doi)
        if muon:
            muon.param_groups[0]["lr"] = lr / C["LR"] * C["LR_MUON"]
        x, y = get_batch(flat, rng, bs, seq)
        with torch.autocast("cuda", dtype=torch.float16):
            loss = model(x, y)
        if not torch.isfinite(loss.detach()):
            divergence = True
            print(f"[diverge] {arm} s{seed} step {step}", flush=True)
            break
        for p in model.parameters():        # zero TAT ca (Muon group nam trong opt nhung van can)
            p.grad = None
        scaler.scale(loss).backward()
        scaler.unscale_(opt)                # unscale TAT CA gradient (ca 2 group) + danh dau UNSCALED
        if any(p.grad is not None and not torch.isfinite(p.grad).all() for p in model.parameters()):
            divergence = True
            print(f"[diverge-grad] {arm} s{seed} step {step}", flush=True)
            break
        torch.nn.utils.clip_grad_norm_(model.parameters(), C["CLIP"])
        if muon:
            muon.step()
        scaler.step(opt)
        scaler.update()
        if step == 100:
            loss100 = eval_split(flats["hold"], model, bs=bs, seq=seq)
            print(f"[eval] {arm} s{seed} loss@100(hold) = {loss100:.4f}", flush=True)
        if step % 50 == 0:
            hist.append((step, float(loss.item()), round(time.time() - t0, 1)))
            if step % 1000 == 0:
                print(f"[train] {arm} s{seed} step {step}/{TOTAL_STEPS} loss {loss.item():.4f} "
                      f"{(time.time()-t0)/60:.1f}min", flush=True)
        step += 1

    val_final = eval_split(flats["hold"], model, bs=bs, seq=seq)
    wall = time.time() - t0
    res = dict(arm=arm, seed=seed, params_total=tot, params_non_emb=non_emb,
               loss_at_100=loss100, val_final=val_final, diverged=divergence,
               steps_done=step, wall_min=round(wall / 60, 1), tokens=int(step * C["BATCH_TOK"]),
               lr_peak=C["LR"], lr_muon=(C["LR_MUON"] if arm == "A2" else None),
               batch_tok=C["BATCH_TOK"], hist=hist, prep_seconds=meta.get("prep_seconds"))
    json.dump(res, open(res_p, "w"), indent=1)
    print(f"[done] {arm} s{seed}: val {val_final:.4f} (loss@100 {loss100}) wall {wall/60:.1f}min", flush=True)
    del model, opt, muon
    torch.cuda.empty_cache()
    return res


# ---------------- K1-K6 + pred-vs-obs ----------------
def aggregate(meta, results):
    import statistics as st
    by = {a: [r for r in results if r["arm"] == a] for a in C["ARMS"]}
    med = {a: (st.median([r["val_final"] for r in by[a]]) if by[a] else None) for a in C["ARMS"]}
    spread = {}
    for a, rs in by.items():
        if len(rs) >= 2:
            v = [r["val_final"] for r in rs]
            spread[a] = round((max(v) - min(v)) / max(1e-9, st.mean(v)), 4)
    sp_med = st.median(list(spread.values())) if spread else None

    ok_k1 = [r for r in results
             if (not r["diverged"]) and r["loss_at_100"] is not None
             and r["val_final"] <= 0.5 * r["loss_at_100"]]
    k1 = dict(pass_=(bool(results) and len(ok_k1) == len(results)),
              n_pass=len(ok_k1), n_total=len(results),
              details=[dict(cell=f"{r['arm']}_s{r['seed']}", loss100=r["loss_at_100"],
                            final=r["val_final"],
                            ratio=(round(r["val_final"] / r["loss_at_100"], 4)
                                   if r["loss_at_100"] else None))
                       for r in results])

    dk2 = (round(med["A1"] - med["A2"], 4) if (med["A1"] is not None and med["A2"] is not None) else None)
    dk3 = (round(med["A1"] - med["A3"], 4) if (med["A1"] is not None and med["A3"] is not None) else None)

    def verdict(d, thr):
        if d is None:
            return "MISSING"
        if sp_med is not None and sp_med >= abs(d):
            return "INCONCLUSIVE (K4)"
        return "PASS" if d >= thr else "FAIL"

    k2 = dict(delta=dk2, threshold=0.05, verdict=verdict(dk2, 0.05))
    k3 = dict(delta=dk3, threshold=0.03, verdict=verdict(dk3, 0.03))
    k4 = dict(spread_by_cell=spread, median_spread=sp_med,
              eats_k2=(sp_med is not None and dk2 is not None and sp_med >= abs(dk2)),
              eats_k3=(sp_med is not None and dk3 is not None and sp_med >= abs(dk3)),
              measured=(sp_med is not None))
    k5 = dict(n_expected=9, n_valid=len(results), pass_=(len(results) == 9),
              note=("du 9/9 cell" if len(results) == 9
                    else f"chi {len(results)}/9 — neu scale-down 2 seed/cell phai ghi §23.4 TRUOC khi chay"))
    rt = st.median([r["wall_min"] for r in results]) if results else None
    preds = [
        dict(name="K1 PASS 9/9", pred="9/9", obs=f"{k1['n_pass']}/{k1['n_total']}",
             close=(k1["n_pass"] == 9 and k1["n_total"] == 9)),
        dict(name="ΔK2 (A1−A2)", pred=0.08, obs=dk2,
             close=(dk2 is not None and abs(dk2 - 0.08) <= 0.3 * 0.08)),
        dict(name="ΔK3 (A1−A3)", pred=0.04, obs=dk3,
             close=(dk3 is not None and abs(dk3 - 0.04) <= 0.3 * 0.04)),
        dict(name="K4 median spread", pred=0.07, obs=sp_med,
             close=(sp_med is not None and abs(sp_med - 0.07) <= 0.3 * 0.07)),
        dict(name="runtime/run (min)", pred=90, obs=(round(rt, 1) if rt is not None else None),
             close=(rt is not None and abs(rt - 90) <= 0.3 * 90)),
        dict(name="A1 final val-loss", pred=2.7, obs=(round(med["A1"], 4) if med["A1"] is not None else None),
             close=(med["A1"] is not None and abs(med["A1"] - 2.7) <= 0.3 * 2.7)),
        dict(name="K3 INCONCLUSIVE (K4 nuot)", pred=True, obs=k4["eats_k3"],
             close=(k4["eats_k3"] is True)),
    ]
    k6 = dict(n_close=sum(1 for p in preds if p["close"]), n_total=len(preds), rows=preds)
    k6["pass_"] = k6["n_close"] >= 4
    return dict(K1=k1, K2=k2, K3=k3, K4=k4, K5=k5, K6=k6, medians=med, meta=meta)


def render_kpi(kpis, results):
    L = ["DS-012 KPI (pre-register §23 — nguong khong doi sau khi thay so)"]
    m = kpis["meta"]
    L.append(f"corpus: {m.get('source')} | a1 {m.get('a1_tokens',0)/1e6:.1f}M tok raw | "
             f"a3 {m.get('a3_tokens',0)/1e6:.1f}M tok loc | holdout {m.get('holdout_tokens',0)/1e6:.1f}M tok | "
             f"reject_rate {m.get('reject_rate')} | dedup_rate {m.get('dedup_rate')} | prep {m.get('prep_seconds')}s")
    if results:
        L.append(f"cells: {len(results)}/9 | model {results[0]['params_total']/1e6:.2f}M total / "
                 f"{results[0]['params_non_emb']/1e6:.2f}M non-emb | {C['BATCH_TOK']} tok/step | "
                 f"{TOTAL_STEPS} steps/run")
    k1 = kpis["K1"]
    L.append(f"K1 PASS: {k1['pass_']} ({k1['n_pass']}/{k1['n_total']} run giam >=50% vs loss@100 va khong diverge)")
    for d in k1["details"]:
        r = f" ratio {d['ratio']}" if d["ratio"] is not None else ""
        L.append(f"   {d['cell']}: loss@100 {d['loss100']} -> val {d['final']}{r}")
    L.append(f"K2 (Muon <= A1-0.05, trung vi): delta {kpis['K2']['delta']} -> {kpis['K2']['verdict']}")
    L.append(f"K3 (data filter <= A1-0.03, trung vi): delta {kpis['K3']['delta']} -> {kpis['K3']['verdict']}")
    L.append(f"K4 F-B04: spread/cell {kpis['K4']['spread_by_cell']} median {kpis['K4']['median_spread']} | "
             f"eats K2 {kpis['K4']['eats_k2']} | eats K3 {kpis['K4']['eats_k3']}")
    L.append(f"K5 artifacts: {kpis['K5']['n_valid']}/{kpis['K5']['n_expected']} -> {kpis['K5']['pass_']} "
             f"({kpis['K5']['note']})")
    L.append(f"K6 pred-vs-obs: {kpis['K6']['n_close']}/{kpis['K6']['n_total']} close (nguong >=4/7) -> {kpis['K6']['pass_']}")
    for r in kpis["K6"]["rows"]:
        L.append(f"   {r['name']}: pred {r['pred']} | obs {r['obs']} | close {r['close']}")
    L.append("medians: " + ", ".join(f"{a}={v}" for a, v in kpis["medians"].items() if v is not None))
    for r in results:
        L.append(f"   {r['arm']}_s{r['seed']}: val {r['val_final']:.4f} wall {r['wall_min']}min "
                 f"steps {r['steps_done']} div {r['diverged']}")
    npass = sum([kpis["K1"]["pass_"], kpis["K2"]["verdict"] == "PASS", kpis["K3"]["verdict"] == "PASS",
                 kpis["K4"]["measured"], kpis["K5"]["pass_"], kpis["K6"]["pass_"]])
    L.append(f"KPI {npass}/6")
    txt = "\n".join(L)
    open(f"{OUT}/kpi.txt", "w").write(txt + "\n")
    print(txt, flush=True)
    return txt


def make_plots(results, kpis):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    if results:
        plt.figure(figsize=(9, 5))
        for r in results:
            h = r["hist"]
            if h:
                plt.plot([x[0] for x in h], [x[1] for x in h], alpha=0.75, label=f"{r['arm']}-s{r['seed']}")
        plt.xlabel("step")
        plt.ylabel("train loss")
        plt.title("DS-012 loss curves (per cell)")
        plt.legend(fontsize=7, ncol=3)
        plt.tight_layout()
        plt.savefig(f"{OUT}/plots/d38_loss_curves.png", dpi=110)
        plt.close()

        data = [[r["val_final"] for r in results if r["arm"] == a] for a in C["ARMS"]]
        plt.figure(figsize=(7, 5))
        labels_ = [f"{a}\n(n={len(d)})" for a, d in zip(C["ARMS"], data)]
        try:
            plt.boxplot([d for d in data if d], tick_labels=labels_)
        except TypeError:                   # matplotlib < 3.9
            plt.boxplot([d for d in data if d], labels=labels_)
        plt.ylabel("final val-loss (holdout)")
        plt.title("DS-012 K2/K3/K4 — final val-loss by arm")
        plt.tight_layout()
        plt.savefig(f"{OUT}/plots/d39_arm_final.png", dpi=110)
        plt.close()

    rows = kpis["K6"]["rows"]
    plt.figure(figsize=(9, 5))
    xs = range(len(rows))
    plt.bar([x - 0.2 for x in xs], [1 if r["close"] else 0 for r in rows], width=0.4, label="close (1=yes)")
    plt.xticks(list(xs), [r["name"][:24] for r in rows], rotation=30, ha="right", fontsize=7)
    plt.yticks([0, 1])
    plt.title(f"DS-012 pred-vs-obs: close {kpis['K6']['n_close']}/{kpis['K6']['n_total']} (gate >=4/7)")
    plt.tight_layout()
    plt.savefig(f"{OUT}/plots/d40_pred_vs_obs.png", dpi=110)
    plt.close()


def load_results():
    out = []
    for f in sorted(os.listdir(f"{OUT}/results")):
        if f.endswith(".json"):
            out.append(json.load(open(f"{OUT}/results/{f}")))
    return out


def main():
    print(f"[env] torch {torch.__version__} | cuda {torch.cuda.is_available()} "
          f"| {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NO-GPU'}", flush=True)
    meta = prepare_data()
    flats = {k: flat_uint16(f"{TMP}/{k}.bin") for k in ("a1", "a3", "hold")}
    print(f"[shapes] a1 {len(flats['a1'])} tok | a3 {len(flats['a3'])} tok | hold {len(flats['hold'])} tok | "
          f"TOTAL_STEPS {TOTAL_STEPS}", flush=True)

    cells = [(a, s) for a in C["ARMS"] for s in C["SEEDS"]]
    done = 0
    for arm, seed in cells:
        if done >= MAX_CELLS_THIS_SESSION:
            print("[session] MAX_CELLS reached — resume o session sau (results da luu)", flush=True)
            break
        try:
            train_cell(arm, seed, flats, meta)
            done += 1
        except Exception:
            print(f"[error] {arm} s{seed}:", flush=True)
            traceback.print_exc()

    results = load_results()
    kpis = aggregate(meta, results)
    json.dump(kpis, open(f"{OUT}/summary.json", "w"), indent=1, default=str)
    render_kpi(kpis, results)
    try:
        make_plots(results, kpis)
    except Exception as e:
        print(f"[plot error] {type(e).__name__}: {e}", flush=True)
    print("[DS-012] DONE", flush=True)


if __name__ == "__main__":
    main()