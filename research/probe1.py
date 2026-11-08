from stats import load_eyes
names, M = load_eyes()
N = dict(zip(names, M))
P = 83
# main isomorph family (Lymm G/H), length 24
fam = [("W1",34),("W1",64),("E2",39),("E2",74)]
L = 24
segs = [N[n][i:i+L] for n,i in fam]
for s in segs: print(" ".join(f"{v:02d}" for v in s))
from itertools import combinations
def affine_fit(a, b):
    sols=[]
    for m in range(1,P):
        k=(b[0]-m*a[0])%P
        if all((m*x+k)%P==y for x,y in zip(a,b)): sols.append((m,k))
    return sols
for (i,a),(j,b) in combinations(enumerate(segs),2):
    add = {(y-x)%P for x,y in zip(a,b)}
    mul = {(y*pow(x,-1,P))%P for x,y in zip(a,b) if x}
    print(fam[i],fam[j],"add-consts",len(add),"mul-consts",len(mul),"affine",affine_fit(a,b))
# partial pi between the pairs, and commutation test
def pmap(a,b):
    d={}
    for x,y in zip(a,b):
        if d.get(x,y)!=y: return None
        d[x]=y
    return d
maps={(i,j):pmap(segs[i],segs[j]) for i in range(4) for j in range(4) if i!=j}
print("all correspondences are partial bijections:", all(v is not None for v in maps.values()))
