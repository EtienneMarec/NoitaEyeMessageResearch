"""Dictionary-guided brute force on the message OPENINGS (§47).

Assumptions (chain of §44): space model, natural pair (β, σ), read convention (symbol of rank k read at
position k), first symbol = message number read from the starting deck (its cards are in the digit
zone, §46). Under these assumptions, 15 symbols at the start of each group are enough to decrypt everything (§44).

Search: beam over the plaintext of the openings, node by node of the tree of cipher prefixes (messages
with the same cipher prefix have the same plaintext), in depth order.
  - Dictionary: only lexicon words are allowed (space = end of a complete word); score = log-probability
    of a "word unigram" model (prefix probabilities in the lexicon tree).
  - Exact constraints: each card read gets a start position y = G_t⁻¹(q_symbol); a card already placed
    forces its symbol; two cards cannot share a start; the cards of the first trigrams have their
    start in the digit zone, the others outside it.
Tracking of the truth on the testbed (rank of the true branch at each step).
Usage: python opening_search.py BEAM T [meme|autre] [tous|0,3,6] [KF = nodes imposed to the truth]"""
import sys
import time
from collections import Counter
import numpy as np
from numba import njit

N = 83


# ---------------------------------------------------------------- lexicon
def build_bigrams(tokens, child, wid, lam=0.7):
    """Bigram correction applied at the end of a word: log[(λ P(w|prev) + (1-λ) P(w)) / P(w)].
    Returns sorted keys prev*V + w and the corrections (absent pairs are worth log(1-λ))."""
    import re
    V = int(wid.max()) + 1
    uni = Counter(tokens); tot = sum(uni.values())
    big = Counter(zip(tokens, tokens[1:]))
    idx = {}
    for w in uni:
        u = 0
        for ch in w:
            u = child[u, ord(ch) - 65]
        idx[w] = int(wid[u])
    keys = []; vals = []
    for (a, b), c in big.items():
        pu = uni[b] / tot
        keys.append(idx[a] * V + idx[b]); vals.append(np.log((lam * c / uni[a] + (1 - lam) * pu) / pu))
    o = np.argsort(keys)
    return np.array(keys, np.int64)[o], np.array(vals)[o], float(np.log(1 - lam)), V


def build_lexicon(words_counts):
    """Word tree (A-Z): child[u, l], log P(l | u), log P(end | u), word identifier at terminal nodes."""
    child = [[-1] * 26]; mass = [0.0]; endm = [0.0]
    for w, c in words_counts.items():
        u = 0; mass[0] += c
        for ch in w:
            l = ord(ch) - 65
            if child[u][l] < 0:
                child[u][l] = len(child); child.append([-1] * 26); mass.append(0.0); endm.append(0.0)
            u = child[u][l]; mass[u] += c
        endm[u] += c
    child = np.array(child, np.int32); mass = np.array(mass); endm = np.array(endm)
    lpc = np.full(child.shape, -1e9)
    lpe = np.full(len(mass), -1e9)
    for u in range(len(mass)):
        for l in range(26):
            v = child[u, l]
            if v >= 0:
                lpc[u, l] = np.log(mass[v] / mass[u])
        if endm[u] > 0 and u != 0:
            lpe[u] = np.log(endm[u] / mass[u])
    wid = np.full(len(mass), -1, np.int64)
    k = 0
    for u in range(len(mass)):
        if endm[u] > 0:
            wid[u] = k; k += 1
    return child, lpc, lpe, wid


def words_from(text):
    import re
    return Counter(re.findall(r"[A-Z]+", text.upper()))


# ---------------------------------------------------------------- tree of cipher prefixes
def prefix_tree(msgs, T):
    """Nodes from position 1 on (symbol 0 = number is handled separately).
    Returns card, depth, slot (lowest message going through the node), pslot (that of the parent, -1 at the root),
    processing order, and for each message the list of its nodes."""
    index = {}; card = []; depth = []; slot = []; parent = []; paths = []
    for mi, m in enumerate(msgs):
        par = -1; path = []
        for t in range(1, min(T, len(m))):
            key = (par, m[t])
            if key not in index:
                index[key] = len(card); card.append(m[t]); depth.append(t); slot.append(mi); parent.append(par)
            par = index[key]; path.append(par)
        paths.append(path)
    pslot = [slot[p] if p >= 0 else -1 for p in parent]
    order = sorted(range(len(card)), key=lambda n: (depth[n], 0 if slot[n] != pslot[n] else 1, n))
    return (np.array(card, np.int64), np.array(depth, np.int64), np.array(slot, np.int64),
            np.array(pslot, np.int64), np.array(order, np.int64), paths)


# ---------------------------------------------------------------- beam
@njit(cache=True)
def options(u, sy, space_sym, child, lpc, lpe, lcs, lcb, loov, corr, od, os_):
    """Language-model continuations for symbol sy from state u:
    u >= 0: lexicon node; u <= -2: out-of-lexicon word, previous letter -2-u. Returns their number."""
    k = 0
    if u >= 0:
        if sy == space_sym:
            if lpe[u] > -1e8:
                od[k] = lpe[u] + corr; os_[k] = 0; k += 1
        else:
            if child[u, sy] >= 0:
                od[k] = lpc[u, sy]; os_[k] = child[u, sy]; k += 1
            if u == 0:                                   # start of an out-of-lexicon word
                od[k] = loov + lcs[sy]; os_[k] = -2 - sy; k += 1
    else:
        a = -2 - u
        if sy == space_sym:
            od[k] = lcb[a, 26]; os_[k] = 0; k += 1
        else:
            od[k] = lcb[a, sy]; os_[k] = -2 - sy; k += 1
    return k


@njit(cache=True)
def beam(card, slot, pslot, order, q, sym_of_pos, space_sym, binv, sinv, first_mask, digit_mask,
         child, lpc, lpe, B, TR, nslots, wid, bkeys, bvals, bdef, V, FORCE, lcs, lcb, loov):
    nN = card.shape[0]
    G0 = np.empty(N, np.int8)                 # G⁻¹ after the number (one β step): current position -> start
    for p in range(N):
        G0[binv[p]] = p
    GI = np.zeros((B, nslots, N), np.int8); X = np.full((B, N), -1, np.int8); U = np.zeros((B, N), np.bool_)
    LX = np.zeros((B, nslots), np.int32); PW = np.full((B, nslots), -1, np.int64); nPW = np.empty_like(PW)
    SC = np.zeros(B); TXT = np.full((B, nN), -1, np.int8)
    IST = np.zeros(B, np.bool_); IST[0] = True
    nGI = np.zeros_like(GI); nX = np.empty_like(X); nU = np.empty_like(U); nLX = np.empty_like(LX)
    nSC = np.empty_like(SC); nTXT = np.empty_like(TXT); nIST = np.empty_like(IST)
    MAXC = B * 16                              # bounded buffer (memory); beyond it, candidates are ignored
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
            corr = 0.0
            if u >= 0 and lpe[u] > -1e8 and pw >= 0:
                key = pw * V + wid[u]
                j0 = np.searchsorted(bkeys, key)
                corr = bvals[j0] if (j0 < bkeys.shape[0] and bkeys[j0] == key) else bdef
            if X[b, c] >= 0:                   # card already placed: symbol forced
                p = -1
                for pp in range(N):
                    if gi[pp] == X[b, c]:
                        p = pp; break
                sy = sym_of_pos[p]
                if sy < 0:
                    continue
                if FORCE[n] >= 0 and sy != FORCE[n]:
                    continue
                k2 = options(u, sy, space_sym, child, lpc, lpe, lcs, lcb, loov, corr, od, os_)
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
                    k2 = options(u, sy, space_sym, child, lpc, lpe, lcs, lcb, loov, corr, od, os_)
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


def char_model(tokens, p_oov=0.03):
    """Character model of out-of-lexicon words: log P(1st letter), log P(letter | previous), end = index 26."""
    st = np.ones(26); bg = np.ones((26, 27))
    for w in tokens:
        st[ord(w[0]) - 65] += 1
        for a, b in zip(w, w[1:]):
            bg[ord(a) - 65, ord(b) - 65] += 1
        bg[ord(w[-1]) - 65, 26] += 1
    return np.log(st / st.sum()), np.log(bg / bg.sum(axis=1, keepdims=True)), float(np.log(p_oov))


def setup(alpha, orient):
    """Convention: symbol of rank k (in alpha) read at position k or 82 - k. Search symbols: A-Z then space."""
    pos = {ch: (k if orient == "k" else N - 1 - k) for k, ch in enumerate(alpha)}
    syms = "ABCDEFGHIJKLMNOPQRSTUVWXYZ_"
    q = np.array([pos[ch] for ch in syms], np.int64)
    sym_of_pos = np.full(N, -1, np.int64)
    for i, ch in enumerate(syms):
        sym_of_pos[pos[ch]] = i
    digit_mask = np.zeros(N, np.bool_)
    for d in "123456789":
        digit_mask[pos[d]] = True
    return syms, q, sym_of_pos, digit_mask


def run(msgs, T, alpha, orient, binv, sinv, lex, B, truth=None, subset=None, KF=0, guesses=None):
    """lex = (child, lpc, lpe, wid, bkeys, bvals, bdef, V, lcs, lcb, loov). KF: on the testbed, imposes the truth on the first KF nodes.
    guesses: {message index: text from position 1} imposed on the nodes covered."""
    child, lpc, lpe, wid, bkeys, bvals, bdef, V, lcs, lcb, loov = lex
    """subset: indices of the messages explored (the numbers of ALL messages stay constrained)."""
    syms, q, sym_of_pos, digit_mask = setup(alpha, orient)
    first_mask = np.zeros(N, np.bool_)
    for m in msgs:
        first_mask[m[0]] = True
    if subset is not None:
        msgs = [msgs[i] for i in subset]
        truth = None if truth is None else [truth[i] for i in subset]
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
    return beam(card, slot, pslot, order, q, sym_of_pos, 26, binv.astype(np.int64), sinv.astype(np.int64),
                first_mask, digit_mask, child, lpc, lpe, B, TR, len(msgs), wid, bkeys, bvals, bdef, V, FORCE, lcs, lcb, loov),         (card, order, paths, syms)


def wordy_plaintexts(T_en, seed, L=110):
    """Testbed of "whole words" with the structure of the eyes' openings: group A (3 messages) shares ~24 characters;
    groups B and C (6 messages) share a short first word, C (3 messages) shares ~20 more characters.
    Each piece starts and ends at a word boundary; numbers 1 to 9 first."""
    import random
    rnd = random.Random(seed)

    def phrase(n):
        while True:
            i = T_en.find("_", rnd.randrange(1000, len(T_en) - 5000)) + 1
            j = T_en.rfind("_", i, i + n + 1)
            if j > i:
                return T_en[i:j]

    def short_word():
        while True:
            w = phrase(6).split("_")[0]
            if 2 <= len(w) <= 4:
                return w
    A = phrase(24); BC = short_word(); C = BC + "_" + phrase(15)
    msgs = [A + "_" + phrase(L) for _ in range(3)] + [BC + "_" + phrase(L) for _ in range(3)] +            [C + "_" + phrase(L) for _ in range(3)]
    return [str(k + 1) + m for k, m in enumerate(msgs)]


def texts_of(TXT, paths, syms, msgs):
    out = []
    for mi, path in enumerate(paths):
        out.append("".join(syms[TXT[n]] if TXT[n] >= 0 else "?" for n in path))
    return out


if __name__ == "__main__":
    import testbed_spaces as tbs
    from explore import xgak_encrypt
    from keyed_deck_attack import tables
    from known_q_local_filter import ALPHAS
    names, BS, INV = tables()
    B = int(sys.argv[1]) if len(sys.argv) > 1 else 20000
    T = int(sys.argv[2]) if len(sys.argv) > 2 else 16
    lexsrc = sys.argv[3] if len(sys.argv) > 3 else "meme"
    subset = None if (len(sys.argv) <= 4 or sys.argv[4] == "tous") else [int(v) for v in sys.argv[4].split(",")]
    KF = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    rng = np.random.default_rng(7)
    alpha = ALPHAS["AZ19_"]; orient = "k"
    T_en = tbs.english_with_spaces()
    pl = wordy_plaintexts(T_en, 3)
    import re
    if lexsrc == "meme":
        t = T_en.replace("_", " ")
    else:
        from pathlib import Path
        t = " ".join(Path(f).read_text(encoding="utf-8", errors="ignore") for f in
                     ("sources/texts/kalevala_en_crawford.txt", "sources/texts/hermetic_museum_vol1_waite1893.txt",
                      "sources/texts/turba_philosophorum_waite1896.txt"))
    tokens = re.findall(r"[A-Z]+", t.upper())
    wc = Counter(tokens)
    child, lpc, lpe, wid = build_lexicon(wc)
    bkeys, bvals, bdef, V = build_bigrams(tokens, child, wid)
    lex = (child, lpc, lpe, wid, bkeys, bvals, bdef, V) + char_model(tokens)
    print(f"lexicon: {len(wc)} words ({lexsrc})", flush=True)
    q = np.array([alpha.index(ch) for ch in tbs.ALPHA_S], np.int64)
    for bname, sname in (("outshuffle", "milk"), ("rot24", "deal3fwd_inv")):
        D0 = rng.permutation(N)
        S = np.array([BS[sname] if ch == "_" else BS[bname] for ch in tbs.ALPHA_S], np.int64)
        msgs = [D0[np.array(xgak_encrypt(np.array([tbs.ALPHA_S.index(ch) for ch in m], np.int64), q, S))].tolist() for m in pl]
        t0 = time.time()
        (SC, TXT, alive, trank, lost), (card, order, paths, syms) = run(msgs, T, alpha, orient, INV[bname], INV[sname],
                                                                       lex, B, truth=pl, subset=subset, KF=KF)
        nst = len(card)
        print(f"β={bname} σ={sname}, T={T}, beam {B}, {KF} guessed nodes: {nst} nodes, {time.time() - t0:.0f} s; "
              f"true branch {'kept to the end' if lost < 0 else f'lost at step {lost} (rank {trank[lost]})'}", flush=True)
        print("   live candidates per step (max): " + str(int(alive.max())) + "; ranks of the truth: "
              + str(trank[:max(lost, 0) + 1].tolist() if lost >= 0 else trank.tolist()), flush=True)
        if len(SC):
            best = int(np.argmax(SC))
            dec = texts_of(TXT[best], paths, syms, msgs)
            for mi in (0, 3, 6):
                print(f"   {mi} found: {dec[mi]}\n   {mi} true : {pl[mi][1:T]}", flush=True)
