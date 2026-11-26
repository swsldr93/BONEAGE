import json,struct,numpy as np,sys,re
import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); from glb import load,acc,CT,NC
CT[5122]=np.int16
SKIP=re.compile(r'(Index|Middle|Ring|Pinky|Thumb)[1-4]$|_End$')
LOCO={'walk','run','very low crouch sneaking forward'}
def slim(fi,fo,step=1):
    j,bn=load(fi); N=j['nodes']
    hips=[i for i,n in enumerate(N) if n.get('name','').endswith('Hips')][0]
    rest=N[hips].get('translation',[0,0,0])
    out=bytearray(); views=[]; accs=[]
    def add_bytes(b,align=4):
        while len(out)%align: out.append(0)
        o=len(out); out.extend(b); views.append({'buffer':0,'byteOffset':o,'byteLength':len(b)}); return len(views)-1
    def add_acc(i,data=None):
        a=dict(j['accessors'][i]); arr=acc(j,bn,i) if data is None else data
        arr=np.ascontiguousarray(arr.astype(CT[a['componentType']]))
        a['bufferView']=add_bytes(arr.tobytes()); a.pop('byteOffset',None); a['count']=int(arr.shape[0])
        if 'min' in a and a['componentType']==5126: a['min']=[float(x) for x in arr.min(0)]; a['max']=[float(x) for x in arr.max(0)]
        accs.append(a); return len(accs)-1
    memo={}
    def A(i):
        if i not in memo: memo[i]=add_acc(i)
        return memo[i]
    for m in j['meshes']:
        for p in m['primitives']:
            p['attributes']={k:A(v) for k,v in p['attributes'].items()}
            if 'indices' in p: p['indices']=A(p['indices'])
    for s in j.get('skins',[]):
        if 'inverseBindMatrices' in s: s['inverseBindMatrices']=A(s['inverseBindMatrices'])
    for im in j.get('images',[]):
        bv=j['bufferViews'][im['bufferView']]; o=bv.get('byteOffset',0); raw=bytes(bn[o:o+bv['byteLength']])
        import io; from PIL import Image; I=Image.open(io.BytesIO(raw)).convert('RGB'); ob=io.BytesIO(); I.save(ob,'JPEG',quality=78); im['mimeType']='image/jpeg'; im['bufferView']=add_bytes(ob.getvalue())
    tmemo={}
    for an in j['animations']:
        ch2=[]; sm2=[]
        for ch in an['channels']:
            nd=ch['target']['node']; nmn=N[nd].get('name','')
            if SKIP.search(nmn): continue
            if ch['target']['path']=='scale' or (ch['target']['path']=='translation' and nd!=hips): continue   # bones keep their lengths: only the hips move
            sm=an['samplers'][ch['sampler']]; ti=acc(j,bn,sm['input']); v=acc(j,bn,sm['output']).copy()
            if nd==hips and ch['target']['path']=='translation' and an['name'] in LOCO: v[:,0]=rest[0]; v[:,2]=rest[2]   # in place: the game moves them
            if an['name']=='idle': keep=int((ti<=6.0).sum()); ti=ti[:keep]; v=v[:keep]   # six seconds of standing about is plenty: it loops
            if step>1: idx=list(range(0,len(ti),step)); idx[-1:]=[len(ti)-1] if idx[-1]!=len(ti)-1 else idx[-1:]; 
            else: idx=list(range(len(ti)))
            if step>1 and idx[-1]!=len(ti)-1: idx.append(len(ti)-1)
            tib=ti[idx].astype(np.float32).tobytes()
            if tib in tmemo: ia=tmemo[tib]
            else: ia=add_acc(sm['input'],ti[idx]); tmemo[tib]=ia
            if ch['target']['path']=='rotation':
                q=np.round(np.clip(v[idx],-1,1)*32767).astype(np.int16); a=dict(j['accessors'][sm['output']]); a['componentType']=5122; a['normalized']=True; a.pop('min',None); a.pop('max',None); a['bufferView']=add_bytes(q.tobytes()); a.pop('byteOffset',None); a['count']=int(q.shape[0]); accs.append(a); oa=len(accs)-1
            else: oa=add_acc(sm['output'],v[idx])
            sm2.append({'input':ia,'output':oa,'interpolation':sm.get('interpolation','LINEAR')}); ch2.append({'sampler':len(sm2)-1,'target':ch['target']})
        an['channels']=ch2; an['samplers']=sm2
    j['accessors']=accs; j['bufferViews']=views; j['buffers']=[{'byteLength':len(out)}]
    while len(out)%4: out.append(0)
    js=json.dumps(j,separators=(',',':')).encode();
    while len(js)%4: js+=b' '
    glb=b'glTF'+struct.pack('<II',2,12+8+len(js)+8+len(out))+struct.pack('<I',len(js))+b'JSON'+js+struct.pack('<I',len(out))+b'BIN\x00'+bytes(out)
    open(fo,'wb').write(glb); return len(glb)
if __name__=='__main__':
    print(slim(sys.argv[1],sys.argv[2],int(sys.argv[3]) if len(sys.argv)>3 else 1))
