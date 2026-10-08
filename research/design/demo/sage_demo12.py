# DS-012 — Pretrain from-scratch tren T4 (pre-register §23: commit 9314d36 + amend 70b5f83)
# DS-012c §25 (pre-register §25 push TRUOC code, commit bd5dea1, 2026-10-07):
#   SCOPE = 1 MODEL (A1 x seed 11) — them checkpoint + reload-parity; K2-K6 method-effect HOAN (§24.4 #1)
# DS-012d §27 (pre-register §27 push TRUOC code, commit bfcccd6, 2026-10-07): fix#5 —
#   block grads_ok giam isfinite TREN GPU (truoc ~50 doc CPU/buoc -> 1); toan hoc y het, numerics giu nguyen.
# DS-012e §29 (pre-register §29 push TRUOC code, commits b54e87b + ce65426, 2026-10-07): profile mode —
#   env PROFILE_STEPS>0 -> 300 buoc do 4 pha wall (sync bien) + GPU-busy bang cuda events -> profile.json,
#   KHONG ckpt/eval/aggregate; mac dinh 0 = run day du binh thuong khong doi hanh vi.
# Cau hoi: thu tu dan bay F-B02 (data >= kien truc > optimizer > init) co dung o regime 1 GPU khong?
# Quy tac: KHONG sua nguong K1-K6 sau khi thay so; moi thay doi ghi §23.4.
# Script nay resume duoc: cell da co results/*.json se bo qua.
import os, json, math, time, hashlib, random, traceback, shutil
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

# ---------------- Config (§23.1) ----------------
OUT = "/kaggle/working/ds012"          # results, kpi, plots (duoc luu thanh kernel output)
TMP = f"{OUT}/data"                    # bin token nam TRONG working -> persist qua session (prep chi tra 1 lan)
for d in (OUT, f"{OUT}/results", f"{OUT}/plots", f"{OUT}/results_superseded", TMP):
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
    SEEDS=[11], ARMS=["A1"],            # §25.1(i): scope = 1 MODEL (9 cell cua §23/§24 hoãn — §24.4 #1)
)
MAX_CELLS_THIS_SESSION = 1             # §25.1(i): 1 model/session (scheduling, KHONG phai nguong)
TOTAL_STEPS = C["TOTAL_TOK"] // C["BATCH_TOK"]

# §30 (pre-reg §30 — 9b106f3, change-log §30.2): env-gated big-batch
# mac dinh = hanh vi cu y het (ACC=1, eval@100, warmup 1000, LR 2.4e-3, tong token cu)
ACC = int(os.environ.get("RUN_ACC", "1") or "1")               # so micro-batch tich luy moi buoc
EVAL_STEPS = int(os.environ.get("EVAL_STEPS", "100") or "100") # buoc eval holdout (cu: 100)
if os.environ.get("RUN_WARMUP"):
    C["WARMUP"] = int(os.environ["RUN_WARMUP"])
if os.environ.get("RUN_LR"):
    C["LR"] = float(os.environ["RUN_LR"])
if os.environ.get("RUN_TOTAL"):
    TOTAL_STEPS = int(os.environ["RUN_TOTAL"])

# §30.3a (pre-reg 1e6eacb): PROBE mode — mac dinh 0 (run day du khong doi); T0 = dau script (giam prep)
PROBE = int(os.environ.get("PROBE", "0") or "0")
T0_PROBE = time.time()
RUN_COMPILE = os.environ.get("RUN_COMPILE", "0") == "1"   # §30.6.1: lever F-X26 torch.compile (mac dinh 0 = hanh vi cu y het)
COST = int(os.environ.get("COST", "0") or "0")      # §31 COST-PROBE DS-014 (pre-reg §31 push TRUOC code 9326097)

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
        a = np.uint64(((p * 0x9E3779B97F4A7C15 + 1) & 0xFFFFFFFFFFFFFFFF) | 1)
        b = np.uint64(((p * 0xC2B2AE3D27D4EB4F + 7) & 0xFFFFFFFFFFFFFFFF) | 1)
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


def _restore_bins_from_output(paths, meta_p):
    # §30.5: tai bin tu OUTPUT cua phien truoc (kaggle kernels output) — 1-2' thay vi ~21' quet HF.
    # Zip output luu ds012/data/*.bin + ds012/data_meta.json + ds012/tokenizer.json (xac minh tren output v9).
    # That bai -> return None -> prepare_data chay prep day du y cu (hanh vi cu, khong bao gio chet).
    import subprocess, shutil
    stage = "/kaggle/working/_restore"
    try:
        if os.environ.get("PREP_RESTORE", "1") == "0":
            print("[data] restore disabled (PREP_RESTORE=0)", flush=True)
            return None
        shutil.rmtree(stage, ignore_errors=True)
        os.makedirs(stage, exist_ok=True)
        t0 = time.time()
        r = subprocess.run(["kaggle", "kernels", "output",
                            "tribu1/ds-012-pretrain-from-scratch", "-p", stage],
                           capture_output=True, text=True, timeout=480)
        if r.returncode != 0:
            print(f"[data] restore skip (kaggle cli rc={r.returncode}) "
                  f"stdout={r.stdout[-200:]!r} stderr={r.stderr[-200:]!r}", flush=True)
            return None
        found = {}
        for root, _d, files in os.walk(stage):
            for f in files:
                if f in ("a1.bin", "a3.bin", "hold.bin", "data_meta.json", "tokenizer.json"):
                    found[f] = os.path.join(root, f)
        # uu tien dung duong dan goc ds012/... (staging rac cung ten file -> khong chon nham)
        pref = {"a1.bin": "ds012/data/a1.bin", "a3.bin": "ds012/data/a3.bin",
                "hold.bin": "ds012/data/hold.bin", "data_meta.json": "ds012/data_meta.json",
                "tokenizer.json": "ds012/tokenizer.json"}
        for k, rel in pref.items():
            p = os.path.join(stage, rel)
            if os.path.exists(p):
                found[k] = p
        need = ("a1.bin", "a3.bin", "hold.bin", "data_meta.json")
        if not all(k in found for k in need):
            try:                                    # §30.5.3: chuan doan staging (rc=0 ma trong -> tai sao?)
                st_files, st_bytes = 0, 0
                for _root, _d, _fs in os.walk(stage):
                    for f in _fs:
                        st_files += 1
                        st_bytes += os.path.getsize(os.path.join(_root, f))
            except Exception:
                st_files, st_bytes = -1, -1
            print(f"[data] restore skip (thieu file: {sorted(set(need) - set(found))}) | "
                  f"rc={r.returncode} stdout={r.stdout[-200:]!r} stderr={r.stderr[-200:]!r} "
                  f"staging_files={st_files} staging_bytes={st_bytes} "
                  f"top={sorted(os.listdir(stage))[:8]}", flush=True)
            return None
        # verify size tuong minh voi meta TRUOC khi move (bat ca zip bi cat do chua ghi het)
        m = json.load(open(found["data_meta.json"]))
        exp1, exp3, exph = int(m["a1_tokens"]) * 2, int(m["a3_tokens"]) * 2, int(m["holdout_tokens"]) * 2
        s1 = os.path.getsize(found["a1.bin"]); s3 = os.path.getsize(found["a3.bin"])
        sh = os.path.getsize(found["hold.bin"])
        if (s1, s3, sh) != (exp1, exp3, exph) or s1 < 599_000_000:
            print(f"[data] restore skip (size/meta lech: got {s1},{s3},{sh} vs {exp1},{exp3},{exph})",
                  flush=True)
            return None
        os.makedirs(os.path.dirname(paths["a1"]), exist_ok=True)
        for k, p in paths.items():
            shutil.move(found[k + ".bin"], p)
        shutil.move(found["data_meta.json"], meta_p)
        if "tokenizer.json" in found:
            shutil.move(found["tokenizer.json"], f"{OUT}/tokenizer.json")
        shutil.rmtree(stage, ignore_errors=True)
        print(f"[data] RESTORED bin tu output phien truoc ({time.time()-t0:.0f}s) — BO QUA quet HF",
              flush=True)
        return json.load(open(meta_p))
    except Exception as e:
        print(f"[data] restore skip ({type(e).__name__}: {e})", flush=True)
        return None


def prepare_data():
    """Mot lan stream -> a1.bin (0.3B token THO, baseline), a3.bin (0.3B token SAU dedup+filter),
    hold.bin (10M token holdout — doc xuat hien SAU khi ca 2 pool day, nen khong train trung).
    Deterministic theo thu tu stream; tokenizer train tren 20M ky tu dau cua cung stream."""
    paths = {k: f"{TMP}/{k}.bin" for k in ("a1", "a3", "hold")}
    meta_p = f"{OUT}/data_meta.json"
    if all(os.path.exists(x) for x in paths.values()) and os.path.exists(meta_p):
        print("[data] reuse cached bins", flush=True)
        return json.load(open(meta_p))
    meta_r = _restore_bins_from_output(paths, meta_p)     # §30.5: prep chi chay 1 lan (fallback = quet cu)
    if meta_r is not None:
        return meta_r
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


# §29 profile: PROFILE_STEPS env (v9 launch dung preamble 1 dong set = 300); mac dinh 0 = run day du
PROFILE = int(os.environ.get("PROFILE_STEPS", "0") or "0")


def train_cell(arm, seed, flats, meta):
    res_p = f"{OUT}/results/{arm}_s{seed}.json"
    if os.path.exists(res_p):
        old = json.load(open(res_p))
        # Chi skip neu cell da chay DAY DU. Ket qua tu v2 (bi kill boi guard bug §23.4 #4)
        # hoac chua xong -> luu tru vao results_superseded/ va chay lai.
        if old.get("steps_done", 0) >= TOTAL_STEPS and not old.get("diverged"):
            print(f"[skip] {arm} s{seed} done", flush=True)
            return old
        arch = f"{OUT}/results_superseded/{arm}_s{seed}.json"
        shutil.move(res_p, arch)
        print(f"[rerun] {arm} s{seed}: ket qua cu (steps={old.get('steps_done')}, "
              f"diverged={old.get('diverged')}) -> luu tru {arch}", flush=True)
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
    grad_skips, nan_loss_skips, bad_streak = 0, 0, 0
    micro_nan_total = 0
    prof = PROFILE > 0
    lim = PROFILE if prof else TOTAL_STEPS
    ph_wall, iter_walls, ev_pairs = {}, [], []
    def _ph(name, wall):
        ph_wall[name] = ph_wall.get(name, 0.0) + wall
    if RUN_COMPILE:                    # §30.6.1: giong hinh mau probe V2 (K-PD4 PASS, ~38s lan dau)
        model = torch.compile(model)
        print(f"[compile] RUN_COMPILE=1 wrapped - {arm} s{seed}", flush=True)
    model.train()
    while step < lim:
        if prof:
            torch.cuda.synchronize()
            t_iter0 = t0p = time.time()
            _ev_s = torch.cuda.Event(enable_timing=True)
            _ev_s.record()
        lr = lr_at(step, C["LR"])
        opt.param_groups[0]["lr"] = lr          # nhom AdamW (A2: group 1 = muon, lr=0, khong doi)
        if muon:
            muon.param_groups[0]["lr"] = lr / C["LR"] * C["LR_MUON"]
        for p in model.parameters():        # zero TAT ca TRUOC micro-loop (§30.2; ACC=1 -> giong cu)
            p.grad = None
        loss_sum, n_fin, micro_nan = 0.0, 0, 0
        for _mi in range(ACC):              # §30: ACC=1 -> vong lap 1 lan, hanh vi cu
            x, y = get_batch(flat, rng, bs, seq)
            if prof:
                torch.cuda.synchronize(); tw1 = time.time()
                _ph("batch", tw1 - t0p); t0p = tw1
            with torch.autocast("cuda", dtype=torch.float16):
                mloss = model(x, y)
            if prof:
                torch.cuda.synchronize(); tw1 = time.time()
                _ph("forward", tw1 - t0p); t0p = tw1
            if bool(torch.isfinite(mloss.detach())):
                loss_sum += float(mloss.item()); n_fin += 1
                scaler.scale(mloss / ACC).backward()   # gradient = TRUNG BINH qua ACC micro (§30.2)
            else:
                micro_nan += 1
        micro_nan_total += micro_nan
        loss_ok = (n_fin == ACC)            # micro nao nan -> bo qua ca buoc (ngu y hanh vi loss_ok cu)
        loss_f = (loss_sum / n_fin) if n_fin else float("nan")
        if loss_ok:
            scaler.unscale_(opt)            # unscale TAT CA gradient + ghi found_inf (neu co)
            # §27 fix#5: reduce isfinite TREN GPU, doc CPU dung 1 lan/buoc (truoc do ~50 lan)
            # toan hoc y het: all(isfinite(g)) <=> sum(isfinite) == sum(numel)
            grads = [p.grad for p in model.parameters() if p.grad is not None]
            if grads:
                fin = [torch.isfinite(g).sum() for g in grads]
                grads_ok = bool(torch.stack(fin).sum().item() == sum(g.numel() for g in grads))
            else:
                grads_ok = True              # y het all([]) ban cu
        else:
            grads_ok = False                # co micro nan -> bo qua buoc, scaler khong doi scale
        if prof:
            torch.cuda.synchronize(); tw1 = time.time()
            _ph("backward", tw1 - t0p); t0p = tw1
        if loss_ok and grads_ok:
            bad_streak = 0
            torch.nn.utils.clip_grad_norm_(model.parameters(), C["CLIP"])
            if muon:
                muon.step()
            scaler.step(opt)                # khong found_inf -> cap nhat binh thuong
            scaler.update()
        elif loss_ok:
            # grad khong huu han nhung loss van tot -> overflow fp16 tai peak LR, KHONG phai
            # ket qua: scaler.step da ghi found_inf o unscale_ -> skip buoc nay + giam scale 2x
            bad_streak += 1
            grad_skips += 1
            scaler.step(opt)
            scaler.update()
            if grad_skips <= 10 or grad_skips % 50 == 0:
                print(f"[grad-skip] {arm} s{seed} step {step} (lan {grad_skips}, "
                      f"scale={scaler.get_scale():g}) — scaler skip + halve", flush=True)
        else:
            # loss khong huu han: khong backward (tranh scaler tang scale nham), weight khong doi
            bad_streak += 1
            nan_loss_skips += 1
            if nan_loss_skips <= 10 or nan_loss_skips % 50 == 0:
                print(f"[nan-skip] {arm} s{seed} step {step} (lan {nan_loss_skips}) — bo qua buoc",
                      flush=True)
        if prof:
            torch.cuda.synchronize(); tw1 = time.time()
            _ph("optim", tw1 - t0p)
            _ev_e = torch.cuda.Event(enable_timing=True)
            _ev_e.record()                  # sau khi stream da drain -> GPU window cua buoc
            ev_pairs.append((_ev_s, _ev_e))
            t0p = tw1
        if bad_streak >= 20:                # 20 buoc lien tuc khong huu han = khong phuc hoi duoc
            divergence = True
            print(f"[diverge] {arm} s{seed} step {step}: {bad_streak} buoc lien tuc khong huu han",
                  flush=True)
            break
        if not prof and step == EVAL_STEPS: # §29: profile bo eval; §30: buoc eval chuyen duoc bang EVAL_STEPS
            loss100 = eval_split(flats["hold"], model, bs=bs, seq=seq)
            print(f"[eval] {arm} s{seed} loss@{EVAL_STEPS}(hold) = {loss100:.4f}", flush=True)
        if step % 50 == 0 and loss_ok:
            hist.append((step, loss_f, round(time.time() - t0, 1)))
            if step % 1000 == 0:
                print(f"[train] {arm} s{seed} step {step}/{TOTAL_STEPS} loss {loss_f:.4f} "
                      f"{(time.time()-t0)/60:.1f}min", flush=True)
        if prof:
            iter_walls.append(time.time() - t_iter0)
        step += 1

    if prof:                              # §29: profile mode -> ghi profile.json, BO qua ckpt/eval/aggregate
        n_it = max(1, len(iter_walls))
        tot_w = sum(ph_wall.values())
        tot_i = sum(iter_walls) if iter_walls else 1e-9
        gpu_s = (sum(s.elapsed_time(e) for s, e in ev_pairs) / 1000.0) if ev_pairs else 0.0
        prof_out = {
            "mode": "ds012e_profile", "profile_steps": PROFILE, "steps_done": step,
            "n_iter": len(iter_walls),
            "s_step_iter_mean": round(tot_i / n_it, 4),
            "s_step_iter_median": (round(sorted(iter_walls)[len(iter_walls) // 2], 4)
                                   if iter_walls else None),
            "coverage": round(tot_w / tot_i, 4),
            "gpu_busy_s_total": round(gpu_s, 3),
            "gpu_busy_frac": round(gpu_s / tot_i, 4),
            "phases": {k: {"wall_mean": round(v / n_it, 4),
                           "wall_frac": (round(v / tot_w, 4) if tot_w > 0 else None)}
                       for k, v in ph_wall.items()},
            "loss_hist_last": (list(hist[-1]) if hist else None),
            "grad_skips": grad_skips, "nan_loss_skips": nan_loss_skips,
            "env": {"torch": torch.__version__,
                    "gpu": (torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)},
            "note": "5 sync/buoc (1 dau buoc + 4 bien pha); s_step instrumented KHONG doi chieu production 0.4158",
        }
        json.dump(prof_out, open(f"{OUT}/profile.json", "w"), indent=1, default=str)
        print("[profile] " + json.dumps(prof_out, indent=1, default=str), flush=True)
        del model, opt, muon
        torch.cuda.empty_cache()
        return prof_out
    val_final = eval_split(flats["hold"], model, bs=bs, seq=seq)
    # §25.1(ii): model PHAI TON TAI duoc — save + reload-parity (K2')
    ckpt_p = f"{OUT}/model_{arm}_s{seed}.pt"
    torch.save(getattr(model, "_orig_mod", model).state_dict(), ckpt_p)  # RUN_COMPILE: lay state_dict goc (eager khong doi gi)
    ckpt_bytes = os.path.getsize(ckpt_p)
    model2 = GPT(C, C["VOCAB"]).cuda()
    model2.load_state_dict(torch.load(ckpt_p, map_location="cuda"))
    val_reload = eval_split(flats["hold"], model2, bs=bs, seq=seq)
    parity = round(abs(val_reload - val_final), 5)
    print(f"[ckpt] {arm} s{seed}: {ckpt_p} ({ckpt_bytes} B) | val_reload {val_reload:.4f} | parity {parity}", flush=True)
    del model2
    wall = time.time() - t0
    res = dict(arm=arm, seed=seed, params_total=tot, params_non_emb=non_emb,
               loss_at_100=loss100, val_final=val_final, diverged=divergence,
               steps_done=step, wall_min=round(wall / 60, 1), tokens=int(step * C["BATCH_TOK"] * ACC),
               lr_peak=C["LR"], lr_muon=(C["LR_MUON"] if arm == "A2" else None),
               grad_skips=grad_skips, nan_loss_skips=nan_loss_skips,
               ckpt=ckpt_p, ckpt_bytes=ckpt_bytes, val_reload=val_reload, parity=parity,
               batch_tok=C["BATCH_TOK"], acc=ACC, micro_nan=micro_nan_total,
               hist=hist, prep_seconds=meta.get("prep_seconds"))
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

    dk2 = (round(med["A1"] - med["A2"], 4) if (med.get("A1") is not None and med.get("A2") is not None) else None)
    dk3 = (round(med["A1"] - med["A3"], 4) if (med.get("A1") is not None and med.get("A3") is not None) else None)

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
    L = ["DS-012d §27 KPI (pre-register §27 push TRUOC code bfcccd6 — fix#5: bo ~50 sync/buoc, numerics giu nguyen; baseline §25 = v7)",
         "K2-K6 (method-effect, 9-cell) HOAN theo change-log §24.4 #1 — chi thi 2026-10-07: tap trung train 1 model"]
    m = kpis["meta"]
    L.append(f"corpus: {m.get('source')} | a1 {m.get('a1_tokens',0)/1e6:.1f}M tok raw | "
             f"a3 {m.get('a3_tokens',0)/1e6:.1f}M tok loc | holdout {m.get('holdout_tokens',0)/1e6:.1f}M tok | "
             f"reject_rate {m.get('reject_rate')} | dedup_rate {m.get('dedup_rate')} | prep {m.get('prep_seconds')}s")
    if results:
        L.append(f"cells: {len(results)}/1 (scope §25 = 1 model) | model {results[0]['params_total']/1e6:.2f}M total / "
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
    # §25 K1'-K4' (nguong §25.3 — khong doi; change-log §25.5 #1)
    if results:
        r0 = results[0]
        par = r0.get("parity")
        k2p = ((r0.get("ckpt_bytes") or 0) >= 26214400) and (par is not None and abs(par) <= 0.05)
        k3p = (r0.get("wall_min") is not None and r0["wall_min"] <= 150)
        k4p = ("grad_skips" in r0) and ("nan_loss_skips" in r0)
        L.append(f"K1' (§23 K1 nguyen van): {k1['pass_']} — nguong val_final <= 0.5 x loss_at_100")
        L.append(f"K2' ckpt: {r0.get('ckpt_bytes')} B >= 25MB -> {(r0.get('ckpt_bytes') or 0) >= 26214400} | "
                 f"parity {par} <= 0.05 -> {par is not None and abs(par) <= 0.05}")
        L.append(f"K3' wall: {r0.get('wall_min')} min <= 150 -> {k3p}")
        L.append(f"K4' log du: grad_skips={r0.get('grad_skips')} nan_loss_skips={r0.get('nan_loss_skips')} "
                 f"(khong co nguong) -> {k4p}")
        L.append(f"KPI' (§25) {sum([bool(k1['pass_']), k2p, k3p, k4p])}/4")
        # §27 K-S1..K-S4 (nguong §27, khong doi sau thay so)
        hh = {int(s): t for s, _l, t in r0.get("hist", [])}
        sstep = (round((hh[10000] - hh[1000]) / 9000.0, 4) if (1000 in hh and 10000 in hh) else None)
        ks1 = (sstep is not None and sstep <= 0.28)
        ks2 = (abs(r0["val_final"] - 3.4257) <= 0.05) and bool(k1["pass_"])
        ks3 = ((r0.get("grad_skips") if r0.get("grad_skips") is not None else 999) <= 12
               and "nan_loss_skips" in r0)
        ks4 = k2p
        L.append(f"K-S1 s/step (hist 1000->10000): {sstep} <= 0.28 -> {ks1}  [baseline v7 0.4296]")
        L.append(f"K-S2 tuong duong: |val {r0['val_final']:.4f} - 3.4257| <= 0.05 -> "
                 f"{abs(r0['val_final'] - 3.4257) <= 0.05} | K1' {k1['pass_']}")
        L.append(f"K-S3 counter: grad_skips={r0.get('grad_skips')} (<=12) "
                 f"nan_loss_skips={r0.get('nan_loss_skips')} logged -> {ks3}")
        L.append(f"K-S4 artifact (giong K2'): {ks4}")
        L.append(f"KPI-S (§27) {sum([ks1, ks2, ks3, ks4])}/4")
        # §30 K-F1..K-F3 (nguong §30; chi in khi RUN_ACC > 1 — run day du khong doi)
        if ACC > 1:
            hmap = {int(s): l for s, l, _t in r0.get("hist", [])}
            kf1v = hmap.get(1000)
            kf1 = (kf1v is not None and kf1v <= 3.000)
            kf2v = r0.get("loss_at_100")    # §30.1: eval da dời sang EVAL_STEPS -> field doa la val@1000
            kf2 = (kf2v is not None and kf2v <= 3.45)
            kf3 = ((not r0.get("diverged")) and ((r0.get("grad_skips") or 0) <= 100))
            L.append(f"K-F1 train@1000 (hist): {kf1v} <= 3.000 -> {kf1}")
            L.append(f"K-F2 val@1000 (field loss_at_100): {kf2v} <= 3.45 -> {kf2}")
            L.append(f"K-F3 log: div={r0.get('diverged')} grad_skips={r0.get('grad_skips')} (<=100) "
                     f"micro_nan={r0.get('micro_nan')} -> {kf3}")
            L.append(f"KPI-F (§30) {sum([bool(kf1), bool(kf2), bool(kf3)])}/3")
    npass = sum([kpis["K1"]["pass_"], kpis["K2"]["verdict"] == "PASS", kpis["K3"]["verdict"] == "PASS",
                 kpis["K4"]["measured"], kpis["K5"]["pass_"], kpis["K6"]["pass_"]])
    L.append(f"KPI {npass}/6 (K2-K6 = method-effect 9-cell, HOAN §24.4 #1 — khong tinh acceptance DS-012c/DS-012d)")
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


# ---------------- §30.3a PROBE: 5 bien the toc do (SDPA backend / torch.compile) ----------------
def _sdpa_ctx(kind):
    # thu API moi truoc (torch >= 2.3), fallback API cu — ca 2 deu loi -> variant ghi error (K-PD3 van "reported")
    try:
        from torch.nn.attention import sdpa_kernel, SDPBackend
        b = {"efficient": [SDPBackend.EFFICIENT_ATTENTION], "math": [SDPBackend.MATH],
             "flash": [SDPBackend.FLASH_ATTENTION]}[kind]
        return sdpa_kernel(b)
    except Exception:
        kw = dict(enable_flash=False, enable_math=False, enable_mem_efficient=False)
        if kind == "efficient":
            kw["enable_mem_efficient"] = True
        elif kind == "math":
            kw["enable_math"] = True
        else:
            kw["enable_flash"] = True
        return torch.backends.cuda.sdp_kernel(**kw)


def run_probe(flats):
    import statistics as st
    from contextlib import ExitStack
    names = [v.strip() for v in os.environ.get("PROBE_VARIANTS", "V0,V1,V1b,V2,V3").split(",") if v.strip()]
    n = int(os.environ.get("PROBE_STEPS", "600") or "600")
    warm = 20                            # loai khoi do (gồm compile time cua V2/V3)
    bs, seq = C["BATCH_TOK"] // C["SEQ"], C["SEQ"]
    flat = flats["a1"]
    results = []
    for nm in names:
        entry = {"variant": nm}
        try:
            torch.manual_seed(11); np.random.seed(11)
            model = GPT(C, C["VOCAB"]).cuda()
            opt = torch.optim.AdamW(model.parameters(), lr=C["LR"], betas=(0.9, 0.95), weight_decay=0.1)
            try:
                scaler = torch.amp.GradScaler("cuda")
            except Exception:
                scaler = torch.cuda.amp.GradScaler()
            model.train()
            if nm in ("V2", "V3"):       # V2, V3 = torch.compile
                model = torch.compile(model)
            rng = np.random.default_rng(11)
            times = []
            with ExitStack() as _st:     # V1/V3 = efficient, V1b = math, V0/V2 = auto (khong ctx)
                if nm in ("V1", "V3"):
                    _st.enter_context(_sdpa_ctx("efficient"))
                elif nm == "V1b":
                    _st.enter_context(_sdpa_ctx("math"))
                for step in range(warm + n):
                    torch.cuda.synchronize(); ts = time.time()
                    for p in model.parameters():    # zero TRUOC fwd — giong production sau §30.2
                        p.grad = None
                    x, y = get_batch(flat, rng, bs, seq)
                    with torch.autocast("cuda", dtype=torch.float16):
                        loss = model(x, y)
                    ok = bool(torch.isfinite(loss.detach()))
                    gok = False
                    if ok:
                        scaler.scale(loss).backward()
                        scaler.unscale_(opt)
                        grads = [p.grad for p in model.parameters() if p.grad is not None]
                        if grads:                   # §27 grad-check: 1 CPU read/buoc — giong production
                            fin = [torch.isfinite(g).sum() for g in grads]
                            gok = bool(torch.stack(fin).sum().item() == sum(g.numel() for g in grads))
                        else:
                            gok = True
                    if ok and gok:
                        torch.nn.utils.clip_grad_norm_(model.parameters(), C["CLIP"])
                        scaler.step(opt); scaler.update()
                    elif ok:
                        scaler.step(opt); scaler.update()
                    torch.cuda.synchronize(); te = time.time()
                    if step >= warm:
                        times.append(te - ts)
            entry.update(s_step_mean=round(st.mean(times), 4),
                         s_step_median=round(st.median(times), 4), n=len(times))
        except Exception as e:
            entry["error"] = f"{type(e).__name__}: {e}"
        results.append(entry)
        print("[probe] " + json.dumps(entry), flush=True)
        try:
            del model, opt, scaler
        except Exception:
            pass
        torch.cuda.empty_cache()

    # ---- K-PD1..K-PD4 (nguong §30.3a — chon TRUOC khi do) ----
    v0 = next((r.get("s_step_mean") for r in results if r.get("variant") == "V0"), None)
    kpd1_s = (time.time() - T0_PROBE) / 60.0       # proxy session (tu T0 = dau script, gom prep); chinh thuc = log Kaggle
    kpd1 = 30.0 <= kpd1_s <= 60.0
    kpd2 = (v0 is not None and 0.35 <= v0 <= 0.50)
    kpd3 = (len(results) == len(names)
            and all(("s_step_mean" in r or "error" in r) for r in results))
    fast = [r["variant"] for r in results
            if r.get("s_step_mean") is not None and v0 is not None
            and r["s_step_mean"] <= v0 / 1.5]
    kpd4 = len(fast) > 0
    best = min([r["s_step_mean"] for r in results if r.get("s_step_mean") is not None], default=None)
    out = {"mode": "ds012f_probe", "variants": results, "probe_steps": n, "warm": warm,
           "v0": v0, "best": best, "fast_variants": fast, "kpd1_script_min": round(kpd1_s, 1),
           "kpd": {"K-PD1": bool(kpd1), "K-PD2": bool(kpd2), "K-PD3": bool(kpd3), "K-PD4": bool(kpd4)},
           "kpi_pd": f"{sum([bool(kpd1), bool(kpd2), bool(kpd3), bool(kpd4)])}/4",
           "env": {"torch": torch.__version__,
                   "gpu": (torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)}}
    json.dump(out, open(f"{OUT}/probe.json", "w"), indent=1, default=str)
    for k, v in out["kpd"].items():
        print(f"[{k}] {v}", flush=True)
    print(f"[KPI-PD] {out['kpi_pd']} | V0 {v0} | best {best} | fast {fast} "
          f"| script_wall {kpd1_s:.1f}min", flush=True)
    return out


def run_costprobe():
    # §31 COST-PROBE (DS-014) — pre-reg §31 push TRUOC code (commit 9326097, 2026-10-08).
    # 8 bien the LOCK: C0 defaultx1 · C1 reduce-overhead x1 · C2 max-autotune x1 ·
    # C3 default x2 · C4 default x4 · C5 default x8 · C6 best-mode x best-mult · C7 eager x best-mult.
    # Metric LOCK: tok_s_eff = BATCH_TOK*mult / (s_micro + s_opt/ACC), ACC = 52 (preamble RUN_ACC=52);
    # s_micro = sync-around (giong §30.3a -> so duoc V0 0.4453 / V2 0.2846), s_opt do tach x10.
    # K-CC1..K-CC4 nguong §31.2 — KHONG sua sau khi thay so. Khong cham K-F/K-S/K-P (phien timing).
    import statistics as st
    import subprocess
    import threading
    t_start = time.time()

    # --- du lieu: restore 1 lan (§30.5.3 log chuan doan) hoac synthetic (timing khong phai noi dung) ---
    paths = {k: f"{TMP}/{k}.bin" for k in ("a1", "a3", "hold")}
    meta_p = f"{OUT}/data_meta.json"
    meta_r = _restore_bins_from_output(paths, meta_p)
    if meta_r is not None:
        flat, data_kind = flat_uint16(paths["a1"]), "restored_a1"
    else:
        flat = np.random.default_rng(7).integers(0, C["VOCAB"], size=4_000_000).astype(np.uint16)
        data_kind = "synthetic_uint16_4M"
    print(f"[cost] data = {data_kind} | ACC (formula) = {ACC}", flush=True)
    bs0, seq = C["BATCH_TOK"] // C["SEQ"], C["SEQ"]

    def _mk():
        torch.manual_seed(11); np.random.seed(11)
        model = GPT(C, C["VOCAB"]).cuda()
        opt = torch.optim.AdamW(model.parameters(), lr=C["LR"], betas=(0.9, 0.95), weight_decay=0.1)
        try:
            scaler = torch.amp.GradScaler("cuda")
        except Exception:
            scaler = torch.cuda.amp.GradScaler()
        model.train()
        return model, opt, scaler

    def _micro(model, opt, scaler, rng, bs):
        for p in model.parameters():        # zero — production = 1 lan/buoc truoc micro-loop (cost ~0)
            p.grad = None
        x, y = get_batch(flat, rng, bs, seq)
        with torch.autocast("cuda", dtype=torch.float16):
            mloss = model(x, y)
        v = float(mloss.item())             # item() = sync — giong production L591
        if math.isfinite(v):
            scaler.scale(mloss).backward()
        return v

    def _opt_step(model, opt, scaler):      # production: 1 lan sau ACC micro (§27 fix#5: 1 CPU read/buoc)
        scaler.unscale_(opt)
        grads = [p.grad for p in model.parameters() if p.grad is not None]
        if grads:
            fin = [torch.isfinite(g).sum() for g in grads]
            _ = bool(torch.stack(fin).sum().item() == sum(g.numel() for g in grads))
        torch.nn.utils.clip_grad_norm_(model.parameters(), C["CLIP"])
        scaler.step(opt); scaler.update()

    def _measure(tag, mode, mult, sample_util=False):
        entry = {"variant": tag, "mode": mode, "mult": mult}
        model = opt = scaler = None
        stop_evt = None; samples = []; th = None
        try:
            torch.cuda.reset_peak_memory_stats()
            model, opt, scaler = _mk()
            entry["param_count"] = sum(p.numel() for p in model.parameters())
            if mode != "eager":
                model = torch.compile(model, mode=mode)
            rng = np.random.default_rng(11)
            bs = bs0 * mult
            for _ in range(30):             # warmup 30 (gồm compile ~40s)
                _micro(model, opt, scaler, rng, bs)
            torch.cuda.synchronize()
            if sample_util:                 # nvidia-smi sampler CHI trong cua so C0 (F-X23, 1s/mau)
                stop_evt = threading.Event()
                def _loop():
                    while not stop_evt.is_set():
                        try:
                            u = subprocess.run(
                                ["nvidia-smi", "--query-gpu=utilization.gpu",
                                 "--format=csv,noheader,nounits"],
                                capture_output=True, text=True, timeout=5)
                            samples.append(int(u.stdout.strip().splitlines()[0]))
                        except Exception:
                            pass
                        stop_evt.wait(1.0)
                th = threading.Thread(target=_loop, daemon=True); th.start()
            nmin = 100 if mult == 1 else 30
            times = []; tw0 = time.time()
            while len(times) < nmin or (len(times) < 500 and time.time() - tw0 < 20.0):
                torch.cuda.synchronize(); ts = time.time()
                _micro(model, opt, scaler, rng, bs)
                torch.cuda.synchronize()
                times.append(time.time() - ts)
            if stop_evt is not None:
                stop_evt.set()
                if th is not None:
                    th.join(timeout=7)
            opt_times = []                  # s_opt DO TACH x10 (khong dua vao s_micro)
            for _ in range(10):
                torch.cuda.synchronize(); ts = time.time()
                _opt_step(model, opt, scaler)
                torch.cuda.synchronize()
                opt_times.append(time.time() - ts)
            s_micro, s_opt = st.mean(times), st.mean(opt_times)
            tok_s = (bs0 * mult * seq) / (s_micro + s_opt / ACC)   # ACC = 52 (preamble)
            entry.update(
                s_micro_mean=round(s_micro, 4), s_micro_median=round(st.median(times), 4),
                s_opt=round(s_opt, 4), tok_s_eff=int(round(tok_s)), n=len(times),
                max_mem_gb=round(torch.cuda.max_memory_allocated() / 2**30, 2),
                gpu_util_mean=(round(sum(samples) / len(samples), 1) if samples else None),
                gpu_util_n=len(samples))
        except Exception as e:
            entry["error"] = f"{type(e).__name__}: {e}"
        print("[probe] " + json.dumps(entry), flush=True)
        try:
            del model, opt, scaler
        except Exception:
            pass
        torch.cuda.empty_cache()
        return entry

    # ---- 6 bien the core LOCK ----
    results = []
    combos = set()
    for tag, mode, mult in (("C0", "default", 1), ("C1", "reduce-overhead", 1),
                            ("C2", "max-autotune", 1), ("C3", "default", 2),
                            ("C4", "default", 4), ("C5", "default", 8)):
        results.append(_measure(tag, mode, mult, sample_util=(tag == "C0")))
        combos.add((mode, mult))
    # ---- C6/C7 theo rule LOCK (khong nhan input tu ben ngoai; loi -> loai) ----
    m_valid = [e for e in results if e.get("variant") in ("C0", "C1", "C2") and "s_micro_mean" in e]
    best_mode = min(m_valid, key=lambda e: e["s_micro_mean"])["mode"] if m_valid else "default"
    best_mult = max({e["mult"] for e in results if "s_micro_mean" in e} or {1})
    if (best_mode, best_mult) in combos:
        results.append({"variant": "C6", "mode": best_mode, "mult": best_mult,
                        "skipped": "duplicate_combo"})
        print(f"[cost] C6 skip (trung combo da do: {best_mode} x {best_mult})", flush=True)
    else:
        results.append(_measure("C6", best_mode, best_mult)); combos.add((best_mode, best_mult))
    if ("eager", best_mult) in combos:
        results.append({"variant": "C7", "mode": "eager", "mult": best_mult,
                        "skipped": "duplicate_combo"})
    else:
        results.append(_measure("C7", "eager", best_mult))

    # ---- Profiler (tra loi F-X24): 2 tag C0 + C6, key_averages cuda_time_total ----
    prof_blocks = {}
    for tag, mode, mult in (("C0", "default", 1), ("C6", best_mode, best_mult)):
        model = opt = scaler = None
        try:
            from torch.profiler import profile, ProfilerActivity
            model, opt, scaler = _mk()
            if mode != "eager":
                model = torch.compile(model, mode=mode)
            rng = np.random.default_rng(11)
            for _ in range(10):             # warm compile truoc khi profile
                _micro(model, opt, scaler, rng, bs0 * mult)
            torch.cuda.synchronize(); tw0 = time.time()
            with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as prof:
                for _ in range(5):
                    _micro(model, opt, scaler, rng, bs0 * mult)
            torch.cuda.synchronize(); wall5 = time.time() - tw0
            try:
                ka = prof.key_averages(sort_by="cuda_time_total", row_limit=12)
            except Exception:
                ka = prof.key_averages(row_limit=12)
            print(f"[prof:{tag}] wall_5steps={wall5:.3f}s\n{str(ka)[:5000]}", flush=True)
            cuda_us = 0.0
            for ev in prof.key_averages():
                t = getattr(ev, "self_cuda_time_total", None)
                if t is None:
                    t = getattr(ev, "self_device_time_total", 0) or 0
                cuda_us += t
            prof_blocks[tag] = {"wall_5s": round(wall5, 3),
                                "gpu_busy_est": round(cuda_us / 1e6 / wall5, 3)}
        except Exception as e:
            prof_blocks[tag] = {"error": f"{type(e).__name__}: {e}"}
            print(f"[prof:{tag}] error {type(e).__name__}: {e}", flush=True)
        finally:
            try:
                del model, opt, scaler
            except Exception:
                pass
            torch.cuda.empty_cache()

    # ---- K-CC1..K-CC4 + pred-vs-obs (nguong §31.2 — LOCK TRUOC code; loi/OOM = MISS) ----
    by = {e.get("variant"): e for e in results}
    def _g(tag, key):
        return by.get(tag, {}).get(key)
    wall_min = round((time.time() - t_start) / 60.0, 1)
    preds = [
        ("C0 s_micro", 0.285, 0.26, 0.31, _g("C0", "s_micro_mean")),
        ("C1 s_micro", 0.27, 0.20, 0.32, _g("C1", "s_micro_mean")),
        ("C3 tok_s_eff", 115000, 95000, 160000, _g("C3", "tok_s_eff")),
        ("C4 tok_s_eff", 130000, 100000, 190000, _g("C4", "tok_s_eff")),
        ("C5 tok_s_eff", 145000, 100000, 220000, _g("C5", "tok_s_eff")),
        ("util_c0", 70.0, 45.0, 90.0, _g("C0", "gpu_util_mean")),
        ("wall_min", 22.0, 14.0, 40.0, wall_min),
    ]
    po = {}
    for name, p, lo, hi, obs in preds:
        if obs is None:
            po[name] = {"pred": p, "band": [lo, hi], "obs": None, "close": "MISS"}
        else:
            po[name] = {"pred": p, "band": [lo, hi], "obs": round(float(obs), 4),
                        "close": bool(lo <= float(obs) <= hi)}
    n_obs = sum(1 for v in po.values() if v["obs"] is not None)
    n_close = sum(1 for v in po.values() if v["close"] is True)

    c0_tps = _g("C0", "tok_s_eff")
    levers = [e for e in results
              if e.get("tok_s_eff") is not None and c0_tps
              and e["tok_s_eff"] >= 1.30 * c0_tps]
    pc = _g("C0", "param_count") or 0
    n_entry = sum(1 for e in results
                  if "s_micro_mean" in e or "error" in e or "skipped" in e)
    kcc1 = wall_min <= 60.0
    kcc2 = (n_entry >= 6
            and all(_g(t, "s_micro_mean") is not None for t in ("C0", "C3", "C4"))
            and 12_500_000 <= pc <= 12_700_000
            and {"C0", "C6"} <= set(prof_blocks)
            and (_g("C0", "gpu_util_n") or 0) >= 1)
    kcc3 = n_obs >= 5
    kcc4 = len(levers) > 0

    out = {"mode": "ds014_cost", "data_kind": data_kind, "acc_formula": ACC,
           "variants": results, "profiler": prof_blocks, "preds": po,
           "n_obs": n_obs, "n_close": n_close, "n_pred": len(preds),
           "wall_min": wall_min, "c0_tok_s_eff": c0_tps,
           "levers_ge_1_3x": [{"variant": e["variant"], "tok_s_eff": e["tok_s_eff"],
                               "x_vs_c0": round(e["tok_s_eff"] / c0_tps, 2)}
                              for e in levers] if c0_tps else [],
           "kcc": {"K-CC1": bool(kcc1), "K-CC2": bool(kcc2),
                   "K-CC3": bool(kcc3), "K-CC4": bool(kcc4)},
           "kpi_cc": f"{sum([bool(kcc1), bool(kcc2), bool(kcc3), bool(kcc4)])}/4",
           "env": {"torch": torch.__version__,
                   "gpu": (torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)}}
    json.dump(out, open(f"{OUT}/cost.json", "w"), indent=1, default=str)
    for k, v in out["kcc"].items():
        print(f"[{k}] {v}", flush=True)
    for name, v in po.items():
        print(f"[pred] {name}: pred {v['pred']} band {v['band']} obs {v['obs']} -> {v['close']}",
              flush=True)
    print(f"[KPI-CC] {out['kpi_cc']} | C0 {c0_tps} tok/s | levers>=1.3x: "
          f"{[e['variant'] for e in levers]} | wall {wall_min}'", flush=True)
    return out


def main():
    print(f"[env] torch {torch.__version__} | cuda {torch.cuda.is_available()} "
          f"| {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NO-GPU'}", flush=True)
    if COST > 0:                      # §31 COST-PROBE (DS-014): khong prep day du, khong train/eval/ckpt
        run_costprobe()
        print("[DS-014] COST DONE", flush=True)
        return
    meta = prepare_data()
    flats = {k: flat_uint16(f"{TMP}/{k}.bin") for k in ("a1", "a3", "hold")}
    print(f"[shapes] a1 {len(flats['a1'])} tok | a3 {len(flats['a3'])} tok | hold {len(flats['hold'])} tok | "
          f"TOTAL_STEPS {TOTAL_STEPS}", flush=True)

    if PROBE > 0:                        # §30.3a: probe 5 bien the toc do -> probe.json, bo qua ckpt/eval/aggregate
        pr = run_probe(flats)
        print("[DS-012f] PROBE DONE" if pr else "[DS-012f] PROBE FAILED", flush=True)
        return

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

    if PROFILE > 0:                       # §29: profile run -> DONE chi khi co profile.json, bo aggregate
        ok_pf = os.path.exists(f"{OUT}/profile.json")
        print("[DS-012e] DONE" if ok_pf else "[DS-012e] PROFILE FAILED — khong co profile.json",
              flush=True)
        return
    results = load_results()
    kpis = aggregate(meta, results)
    json.dump(kpis, open(f"{OUT}/summary.json", "w"), indent=1, default=str)
    render_kpi(kpis, results)
    try:
        make_plots(results, kpis)
    except Exception as e:
        print(f"[plot error] {type(e).__name__}: {e}", flush=True)
    print("[DS-012f] DONE" if ACC > 1 else "[DS-012d] DONE", flush=True)


if __name__ == "__main__":
    main()
