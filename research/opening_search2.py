"""Beam over the openings with a "word bigram conditioning the prefix" language model (§49).

Same search as opening_search.py (tree of cipher prefixes, exact constraints from re-read cards, digit
zone, out-of-dictionary words), but the score of each LETTER takes the previous word into account:
  P(prefix u | previous word p) = λ_p · Σ_{w ⊃ u} c(p, w) / c(p) + (1 − λ_p) · Σ_{w ⊃ u} P(w)
(Witten-Bell interpolation). Dictionary words are numbered in lexicographic order, where a word
precedes its extensions: the words starting with prefix u form an interval [lo_u, hi_u), and the
sums are read by binary search among the sorted successors of p (cumulative sums).
  letter u → v: log P(v | p) − log P(u | p); end of word w = u: log P(w | p) − log P(u | p).
Out-of-dictionary words: as in opening_search (penalty, character bigrams).
The dictionary is built on a large corpus (sources/texts/gutenberg, without Pride and Prejudice)."""
import re
from pathlib import Path
import numpy as np
from numba import njit
from opening_search import prefix_tree, setup, char_model, N

HERE = Path(__file__).parent


# ---------------------------------------------------------------- corpus and model
def gutenberg_books(maxbooks=10 ** 6, exclude=(1342,), folder="gutenberg"):
    """Texts of the Gutenberg books (headers and footers removed), one per book."""
    for f in sorted((HERE / "sources/texts" / folder).glob("pg*.txt"))[:maxbooks]:
        if int(f.stem[2:]) in exclude:
            continue
        t = f.read_text(encoding="utf-8", errors="ignore")
        a = t.find("*** START OF"); b = t.find("*** END OF")
        if a >= 0:
            t = t[t.find("\n", a) + 1:b if b > a else None]
        yield t


def gutenberg_text(maxbooks=10 ** 6, exclude=(1342,)):
    return "\n".join(gutenberg_books(maxbooks, exclude))


def build_lm(texts, min_count=2, char_sample=2_000_000):
    """texts: a string or a list/iterable of strings (processed one by one, for memory).
    Returns a dict of numpy arrays (dictionary tree, intervals, unigrams, CSR bigrams)."""
    from collections import Counter
    if isinstance(texts, str):
        texts = [texts]
    texts = list(texts)
    cnt = Counter(); sample = []
    for t in texts:
        toks = re.findall(r"[A-Z]+", t.upper())
        cnt.update(toks)
        if len(sample) < char_sample:
            sample.extend(toks[:char_sample - len(sample)])
    words = sorted(w for w, c in cnt.items() if c >= min_count)   # lexicographic order: a word before its extensions
    V = len(words)
    index = {w: k for k, w in enumerate(words)}
    uni = np.array([cnt[w] for w in words], float); ntok = int(sum(cnt.values())); uni /= uni.sum()
    ucum = np.concatenate([[0.0], np.cumsum(uni)])
    child = [[-1] * 26]; lo = [0]; hi = [V]; wid = [-1]
    for k, w in enumerate(words):
        u = 0
        for ch in w:
            l = ord(ch) - 65
            v = child[u][l]
            if v < 0:
                v = len(child); child[u][l] = v
                child.append([-1] * 26); lo.append(k); hi.append(k + 1); wid.append(-1)
            else:
                hi[v] = k + 1
            u = v
        wid[u] = k
    allk = []; allc = []
    for t in texts:
        ids = np.fromiter((index.get(w, -1) for w in re.findall(r"[A-Z]+", t.upper())), np.int64)
        a, b = ids[:-1], ids[1:]
        ok = (a >= 0) & (b >= 0)
        k_, c_ = np.unique(a[ok] * V + b[ok], return_counts=True)
        allk.append(k_); allc.append(c_)
    K = np.concatenate(allk); Cc = np.concatenate(allc)
    o = np.argsort(K, kind="stable"); K = K[o]; Cc = Cc[o]
    first = np.concatenate([[True], K[1:] != K[:-1]])
    keys = K[first]; bc = np.add.reduceat(Cc, np.where(first)[0])
    pa, pb = keys // V, keys % V
    bptr = np.zeros(V + 1, np.int64); np.add.at(bptr, pa + 1, 1); bptr = np.cumsum(bptr)
    bcc = np.concatenate([[0], np.cumsum(bc)]).astype(np.int64)
    cnt1 = np.zeros(V); np.add.at(cnt1, pa, bc)
    types = np.diff(bptr).astype(float)
    lam = np.where(cnt1 > 0, cnt1 / np.maximum(cnt1 + types, 1), 0.0)
    lcs, lcb, loov = char_model(sample)
    return dict(child=np.array(child, np.int32), lo=np.array(lo, np.int64), hi=np.array(hi, np.int64),
                wid=np.array(wid, np.int64), ucum=ucum, bptr=bptr, bw=pb.astype(np.int64), bcc=bcc,
                cnt1=np.maximum(cnt1, 1.0), lam=lam, lcs=lcs, lcb=lcb, loov=loov, V=V, ntok=ntok)


@njit(cache=True)
def range_prob(p, a0, b0, ucum, bptr, bw, bcc, cnt1, lam):
    U = ucum[b0] - ucum[a0]
    if p < 0:
        return U
    a = bptr[p]; b = bptr[p + 1]
    j1 = a + np.searchsorted(bw[a:b], a0); j2 = a + np.searchsorted(bw[a:b], b0)
    return lam[p] * (bcc[j2] - bcc[j1]) / cnt1[p] + (1.0 - lam[p]) * U


@njit(cache=True)
def options2(u, sy, p, space_sym, child, lo, hi, wid, ucum, bptr, bw, bcc, cnt1, lam, lcs, lcb, loov, od, os_):
    k = 0
    if u >= 0:
        pu = range_prob(p, lo[u], hi[u], ucum, bptr, bw, bcc, cnt1, lam)
        if pu <= 0:
            return 0
        if sy == space_sym:
            if wid[u] >= 0 and u != 0:
                pw = range_prob(p, wid[u], wid[u] + 1, ucum, bptr, bw, bcc, cnt1, lam)
                if pw > 0:
                    od[k] = np.log(pw / pu); os_[k] = 0; k += 1
        else:
            v = child[u, sy]
            if v >= 0:
                pv = range_prob(p, lo[v], hi[v], ucum, bptr, bw, bcc, cnt1, lam)
                if pv > 0:
                    od[k] = np.log(pv / pu) + (np.log(1.0 - np.exp(loov)) if u == 0 else 0.0)
                    os_[k] = v; k += 1
            if u == 0:
                od[k] = loov + lcs[sy]; os_[k] = -2 - sy; k += 1
    else:
        a = -2 - u
        if sy == space_sym:
            od[k] = lcb[a, 26]; os_[k] = 0; k += 1
        else:
            od[k] = lcb[a, sy]; os_[k] = -2 - sy; k += 1
    return k


@njit(cache=True)
def beam2(card, slot, pslot, order, q, sym_of_pos, space_sym, binv, sinv, first_mask, digit_mask, B, TR, nslots,
          FORCE, child, lo, hi, wid, ucum, bptr, bw, bcc, cnt1, lam, lcs, lcb, loov):
    nN = card.shape[0]
    G0 = np.empty(N, np.int8)
    for p in range(N):
        G0[binv[p]] = p
    GI = np.zeros((B, nslots, N), np.int8); X = np.full((B, N), -1, np.int8); U = np.zeros((B, N), np.bool_)
    LX = np.zeros((B, nslots), np.int32); PW = np.full((B, nslots), -1, np.int64); nPW = np.empty_like(PW)
    SC = np.zeros(B); TXT = np.full((B, nN), -1, np.int8)
    IST = np.zeros(B, np.bool_); IST[0] = True
    nGI = np.zeros_like(GI); nX = np.empty_like(X); nU = np.empty_like(U); nLX = np.empty_like(LX)
    nSC = np.empty_like(SC); nTXT = np.empty_like(TXT); nIST = np.empty_like(IST)
    MAXC = B * 16
    cpar = np.empty(MAXC, np.int64); csym = np.empty(MAXC, np.int64); csc = np.empty(MAXC)
    cst = np.empty(MAXC, np.int64)
    od = np.empty(2); os_ = np.empty(2, np.int64)
    alive = np.zeros(nN, np.int64); trank = np.full(nN, -1, np.int64)
    nb = 1; lost = -1
    for step in range(nN):
        n = order[step]; c = card[n]; s = slot[n]; ps = pslot[n]
        nc = 0
        for b in range(nb):
            gi = G0 if ps < 0 else GI[b, ps]
            u = 0 if ps < 0 else LX[b, ps]
            pw = -1 if ps < 0 else PW[b, ps]
            if X[b, c] >= 0:
                p = -1
                for pp in range(N):
                    if gi[pp] == X[b, c]:
                        p = pp; break
                sy = sym_of_pos[p]
                if sy < 0:
                    continue
                if FORCE[n] >= 0 and sy != FORCE[n]:
                    continue
                k2 = options2(u, sy, pw, space_sym, child, lo, hi, wid, ucum, bptr, bw, bcc, cnt1, lam, lcs, lcb,
                              loov, od, os_)
                for o in range(k2):
                    if nc < MAXC:
                        cpar[nc] = b; csym[nc] = sy; csc[nc] = SC[b] + od[o]; cst[nc] = os_[o]; nc += 1
            else:
                for sy in range(27):
                    if FORCE[n] >= 0 and sy != FORCE[n]:
                        continue
                    y = gi[q[sy]]
                    if U[b, y]:
                        continue
                    if first_mask[c] != digit_mask[y]:
                        continue
                    k2 = options2(u, sy, pw, space_sym, child, lo, hi, wid, ucum, bptr, bw, bcc, cnt1, lam, lcs, lcb,
                                  loov, od, os_)
                    for o in range(k2):
                        if nc < MAXC:
                            cpar[nc] = b; csym[nc] = sy; csc[nc] = SC[b] + od[o]; cst[nc] = os_[o]; nc += 1
        alive[step] = nc
        if nc == 0:
            return SC[:0], TXT[:0], alive, trank, (step if lost < 0 else lost)
        k = min(B, nc)
        ordc = np.argsort(-csc[:nc])
        if lost < 0:
            rk = -1
            for ii in range(nc):
                j = ordc[ii]
                if IST[cpar[j]] and csym[j] == TR[n]:
                    rk = ii; break
            trank[step] = rk
            if rk < 0 or rk >= k:
                lost = step
        for i in range(k):
            j = ordc[i]; b = cpar[j]; sy = csym[j]
            nX[i] = X[b]; nU[i] = U[b]; nTXT[i] = TXT[b]; nLX[i] = LX[b]; nGI[i] = GI[b]; nPW[i] = PW[b]
            gi = G0 if ps < 0 else GI[b, ps]
            u = 0 if ps < 0 else LX[b, ps]
            p = q[sy]
            if X[b, c] < 0:
                y = gi[p]; nX[i, c] = y; nU[i, y] = True
            nTXT[i, n] = sy
            nIST[i] = IST[b] and sy == TR[n]
            nSC[i] = csc[j]
            S = sinv if sy == space_sym else binv
            for pp in range(N):
                nGI[i, s, S[pp]] = gi[pp]
            nLX[i, s] = cst[j]
            if sy == space_sym:
                nPW[i, s] = wid[u] if u >= 0 else -1
            elif ps >= 0:
                nPW[i, s] = PW[b, ps]
        nb = k
        X[:nb] = nX[:nb]; U[:nb] = nU[:nb]; TXT[:nb] = nTXT[:nb]; LX[:nb] = nLX[:nb]; GI[:nb] = nGI[:nb]
        PW[:nb] = nPW[:nb]
        SC[:nb] = nSC[:nb]; IST[:nb] = nIST[:nb]
    return SC[:nb], TXT[:nb], alive, trank, lost


def run2(msgs, T, alpha, orient, binv, sinv, lm, B, truth=None, KF=0, guesses=None):
    syms, q, sym_of_pos, digit_mask = setup(alpha, orient)
    first_mask = np.zeros(N, np.bool_)
    for m in msgs:
        first_mask[m[0]] = True
    card, depth, slot, pslot, order, paths = prefix_tree(msgs, T)
    TR = np.full(len(card), -1, np.int64)
    if truth is not None:
        for mi, path in enumerate(paths):
            for t, n in enumerate(path, start=1):
                TR[n] = syms.index(truth[mi][t]) if truth[mi][t] in syms else -2
    FORCE = np.full(len(card), -1, np.int64)
    for st in range(min(KF, len(order))):
        FORCE[order[st]] = TR[order[st]]
    for mi, g in (guesses or {}).items():
        for t, n in enumerate(paths[mi][:len(g)]):
            sy = syms.index(g[t])
            if FORCE[n] >= 0 and FORCE[n] != sy:
                raise ValueError(f"incompatible guesses at node {n} (message {mi}, position {t + 1})")
            FORCE[n] = sy
    L = lm
    return beam2(card, slot, pslot, order, q, sym_of_pos, 26, binv.astype(np.int64), sinv.astype(np.int64),
                 first_mask, digit_mask, B, TR, len(msgs), FORCE, L["child"], L["lo"], L["hi"], L["wid"], L["ucum"],
                 L["bptr"], L["bw"], L["bcc"], L["cnt1"], L["lam"], L["lcs"], L["lcb"], L["loov"]), \
        (card, order, paths, syms)


def bits_per_char(lm, text):
    """Cross-entropy (bits per character, space included) of the model on a text, out-of-dictionary words counted
    by the character model. Measures the strength of the language model."""
    toks = re.findall(r"[A-Z]+", text.upper())
    child = lm["child"]; wid = lm["wid"]
    tot = 0.0; nch = 0; prev = -1
    od = np.empty(2); os_ = np.empty(2, np.int64)
    for w in toks:
        u = 0; lp = 0.0; oov = False
        for ch in w:
            sy = ord(ch) - 65
            k = options2(u, sy, prev, 26, child, lm["lo"], lm["hi"], wid, lm["ucum"], lm["bptr"], lm["bw"],
                         lm["bcc"], lm["cnt1"], lm["lam"], lm["lcs"], lm["lcb"], lm["loov"], od, os_)
            # dictionary path if possible, otherwise out of dictionary
            j = 0 if (k > 0 and os_[0] >= 0 and not oov) else (k - 1)
            if j < 0:
                lp = None; break
            if os_[j] < 0:
                oov = True
            lp += od[j]; u = os_[j]
        if lp is None:
            continue
        k = options2(u, 26, prev, 26, child, lm["lo"], lm["hi"], wid, lm["ucum"], lm["bptr"], lm["bw"], lm["bcc"],
                     lm["cnt1"], lm["lam"], lm["lcs"], lm["lcb"], lm["loov"], od, os_)
        if k == 0:
            continue
        lp += od[0]
        tot += lp; nch += len(w) + 1
        prev = wid[u] if u >= 0 else -1
    return -tot / nch / np.log(2)
