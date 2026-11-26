import json,struct,numpy as np
def load(f):
    b=open(f,'rb').read(); n=struct.unpack('<I',b[12:16])[0]; j=json.loads(b[20:20+n]); o=20+n; bl=struct.unpack('<I',b[o:o+4])[0]; return j,bytearray(b[o+8:o+8+bl])
CT={5126:np.float32,5123:np.uint16,5125:np.uint32,5121:np.uint8}
NC={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def acc(j,bn,i):
    a=j['accessors'][i]; bv=j['bufferViews'][a['bufferView']]; o=bv.get('byteOffset',0)+a.get('byteOffset',0); nc=NC[a['type']]; dt=CT[a['componentType']]
    st=bv.get('byteStride'); 
    if st and st!=nc*np.dtype(dt).itemsize:
        raw=np.frombuffer(bn,dtype=np.uint8,count=st*a['count'],offset=o).reshape(a['count'],st)[:,:nc*np.dtype(dt).itemsize]; return raw.copy().view(dt).reshape(a['count'],nc)
    return np.frombuffer(bn,dtype=dt,count=a['count']*nc,offset=o).reshape(a['count'],nc)
def qmul(a,b):
    x1,y1,z1,w1=a; x2,y2,z2,w2=b
    return np.array([w1*x2+x1*w2+y1*z2-z1*y2, w1*y2-x1*z2+y1*w2+z1*x2, w1*z2+x1*y2-y1*x2+z1*w2, w1*w2-x1*x2-y1*y2-z1*z2])
def qrot(q,v):
    u=np.array(q[:3]); s=q[3]; return 2*np.dot(u,v)*u+(s*s-np.dot(u,u))*np.array(v)+2*s*np.cross(u,v)
def qinv(q): return np.array([-q[0],-q[1],-q[2],q[3]])
class Pose:
    def __init__(s,j,bn):
        s.j=j; s.bn=bn; s.N=j['nodes']; s.par={}
        for i,nd in enumerate(s.N):
            for c in nd.get('children',[]): s.par[c]=i
        s.name={nd.get('name'):i for i,nd in enumerate(s.N)}
    def sample(s,anim,t):
        T={i:np.array(nd.get('translation',[0,0,0]),float) for i,nd in enumerate(s.N)}; R={i:np.array(nd.get('rotation',[0,0,0,1]),float) for i,nd in enumerate(s.N)}; S={i:np.array(nd.get('scale',[1,1,1]),float) for i,nd in enumerate(s.N)}
        if anim is not None:
            for ch in anim['channels']:
                sm=anim['samplers'][ch['sampler']]; ti=acc(s.j,s.bn,sm['input'])[:,0]; v=acc(s.j,s.bn,sm['output']); k=np.searchsorted(ti,t); k=min(max(k,1),len(ti)-1); f=(t-ti[k-1])/max(1e-9,ti[k]-ti[k-1]); f=min(max(f,0),1)
                a=v[k-1]; b=v[k]; p=ch['target']['path']; nd=ch['target']['node']
                if p=='rotation':
                    if np.dot(a,b)<0: b=-b
                    q=a*(1-f)+b*f; R[nd]=q/np.linalg.norm(q)
                elif p=='translation': T[nd]=a*(1-f)+b*f
                elif p=='scale': S[nd]=a*(1-f)+b*f
        s.T,s.R,s.S=T,R,S; s.W={}
    def world(s,i):
        if i in s.W: return s.W[i]
        if i in s.par:
            pp,pq,ps=s.world(s.par[i]); p=pp+qrot(pq,ps*s.T[i]); q=qmul(pq,s.R[i]); sc=ps*s.S[i]
        else: p,q,sc=s.T[i],s.R[i],s.S[i]
        s.W[i]=(p,q,sc); return s.W[i]
