"""EXACT constraint-programming attack (OR-Tools CP-SAT) on the reinsertion table.

Model (§8/§13): sorted deck at the start of each message, first symbol outside the deck; at each letter,
the card at position q is read, removed, then reinserted at index F[q]; then a known base shuffle β
(or none). Unknowns: F[0..82]. The positions of all cards at each step follow from them.
Constraint: each read position belongs to the set R of read positions (booleans inR).
Objective: minimise |R|. The solver learns from conflicts (a wrong destination that later leads to a read
outside R) instead of enumerating like the beam.
"""
import sys
import time
import numpy as np
from ortools.sat.python import cp_model

N = 83


def build(msgs, L, beta=None, forbid_self=True, dest_not_read=False, pairs=None):
    md = cp_model.CpModel()
    F = [md.NewIntVar(0, N - 1, f"F{q}") for q in range(N)]
    if forbid_self:
        for q in range(N):
            md.Add(F[q] != q)
    inR = [md.NewBoolVar(f"R{q}") for q in range(N)]
    binv = None
    if beta is not None:
        binv = [0] * N
        for i, b in enumerate(beta):
            binv[int(b)] = i
    qvars = []
    for mi, msg in enumerate(msgs):
        P = [md.NewConstant(x) for x in range(N)]      # position of each card (sorted deck)
        const = [x for x in range(N)]                     # known value if constant, else None
        for t in range(1, min(L, len(msg))):
            c = msg[t]
            q = P[c]
            qvars.append((mi, t, q))
            md.AddElement(q, inR, 1)
            mt = md.NewIntVar(0, N - 1, f"m{mi}_{t}")
            md.AddElement(q, F, mt)
            nxt = [None] * N
            for x in range(N):
                if x == c:
                    nxt[x] = mt
                    continue
                p = P[x]
                v = md.NewIntVar(0, N - 1, "")
                lt = md.NewBoolVar(""); le = md.NewBoolVar(""); ge = md.NewBoolVar("")
                md.Add(q < p).OnlyEnforceIf(lt); md.Add(q > p).OnlyEnforceIf(lt.Not())
                md.Add(p <= mt).OnlyEnforceIf(le); md.Add(p > mt).OnlyEnforceIf(le.Not())
                md.Add(mt <= p).OnlyEnforceIf(ge); md.Add(mt > p).OnlyEnforceIf(ge.Not())
                b1 = md.NewBoolVar(""); b2 = md.NewBoolVar("")
                md.AddBoolAnd([lt, le]).OnlyEnforceIf(b1); md.AddBoolOr([lt.Not(), le.Not()]).OnlyEnforceIf(b1.Not())
                md.AddBoolAnd([lt.Not(), ge]).OnlyEnforceIf(b2); md.AddBoolOr([lt, ge.Not()]).OnlyEnforceIf(b2.Not())
                md.Add(v == p - 1).OnlyEnforceIf(b1)
                md.Add(v == p + 1).OnlyEnforceIf(b2)
                md.Add(v == p).OnlyEnforceIf([b1.Not(), b2.Not()])
                nxt[x] = v
            if binv is not None:
                P2 = []
                for x in range(N):
                    w = md.NewIntVar(0, N - 1, "")
                    md.AddElement(nxt[x], binv, w)
                    P2.append(w)
                P = P2
            else:
                P = nxt
            md.AddAllDifferent(P)
    if pairs:
        # shared text blocks: two linked positions (msg, t) must read the same position
        qd = {(mi, t): q for mi, t, q in qvars}
        for (a, i), (b, j) in pairs:
            if (a, i) in qd and (b, j) in qd:
                md.Add(qd[(a, i)] == qd[(b, j)])
    if dest_not_read:
        # a destination is never a read position: inR[q] => inR[F[q]] false
        for q in range(N):
            z = md.NewIntVar(0, 1, "")
            md.AddElement(F[q], inR, z)
            md.Add(z == 0).OnlyEnforceIf(inR[q])
    md.Minimize(sum(inR))
    return md, F, inR, qvars


def solve(msgs, L, beta=None, seconds=300, workers=16, verbose=True, **kw):
    md, F, inR, qvars = build(msgs, L, beta, **kw)
    sv = cp_model.CpSolver()
    sv.parameters.max_time_in_seconds = seconds
    sv.parameters.num_workers = workers
    t = time.time()
    st = sv.Solve(md)
    res = {"status": sv.StatusName(st), "time": time.time() - t}
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        res["F"] = np.array([sv.Value(v) for v in F])
        res["R"] = [q for q in range(N) if sv.Value(inR[q])]
        res["obj"] = sv.ObjectiveValue(); res["bound"] = sv.BestObjectiveBound()
        res["q"] = [(mi, t, sv.Value(q)) for mi, t, q in qvars]
    return res
