import sys, numpy as np
from PIL import Image
FR=np.array([125,116,107])
def longest(v):
    best=0;c=0
    for x in v:
        c=c+1 if x else 0
        best=max(best,c)
    return best
def lines(m,axis,minrun):
    n=m.shape[1-axis] if axis==0 else m.shape[0]
    runs=[]
    for i in range(m.shape[1] if axis==0 else m.shape[0]):
        v=m[:,i] if axis==0 else m[i,:]
        runs.append(longest(v)) 
    runs=np.array(runs); idx=np.where(runs>minrun)[0]
    g=[];
    for i in idx:
        if g and i-g[-1][1]<=2: g[-1][1]=i
        else: g.append([i,i])
    return g
for f in sys.argv[1:]:
    a=np.asarray(Image.open(f).convert('RGB')).astype(int)
    m=(np.abs(a-FR).sum(2)<45)
    h,w=m.shape
    print(f,w,h)
    print(' vlines',lines(m,0,h*0.12)); print(' hlines',lines(m,1,w*0.12))
