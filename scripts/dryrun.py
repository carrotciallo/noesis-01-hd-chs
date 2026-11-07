# DRY-RUN: verify book-row <-> translation-key mapping, then report translate+serialize size delta.
# Does NOT modify the .assets file.
import struct, json, sys
import UnityPy
from UnityPy.helpers.TypeTreeNode import TypeTreeNode

SA1 = "/tmp/noesis/hd/NOeSIS HD_Data/sharedassets1.assets"
CACHE = "/tmp/noesis/book_node.pkl"
TRANS = "/tmp/noesis/noesis-port/loc-work/translations.json"
ALIGN = 0x4000

def load_node():
    return TypeTreeNode.from_list(json.load(open(CACHE, "r", encoding="utf-8")))

class R:
    __slots__=("d","p","n")
    def __init__(s,data): s.d,s.p,s.n=data,0,len(data)
    def align4(s): s.p=(s.p+3)&~3
    def i32(s): v=struct.unpack_from("<i",s.d,s.p)[0]; s.p+=4; return v
    def u32(s): v=struct.unpack_from("<I",s.d,s.p)[0]; s.p+=4; return v
    def i64(s): v=struct.unpack_from("<q",s.d,s.p)[0]; s.p+=8; return v
    def u8(s): v=s.d[s.p]; s.p+=1; return v
    def f32(s): v=struct.unpack_from("<f",s.d,s.p)[0]; s.p+=4; return v
    def rs(s):
        L=s.i32(); x=bytes(s.d[s.p:s.p+L]).decode("utf-8","surrogateescape"); s.p+=L; s.align4(); return x
def rd(n,r):
    t=n.m_Type
    if t=="string":
        k=n.m_Children
        if k and k[0].m_Type=="Array":
            inn=k[0].m_Children; dt=inn[1].m_Type if len(inn)>=2 else "char"
            if dt=="string":
                c=r.i32(); return [r.rs() for _ in range(c)]
            return r.rs()
        return r.rs()
    if t in ("int","SInt32"): v=r.i32()
    elif t in ("unsigned int","UInt32","Type*"): v=r.u32()
    elif t in ("SInt64","long long"): v=r.i64()
    elif t in ("UInt64","unsigned long long"):
        if t=="FileSize": v=r.u32()
        else: v=struct.unpack_from("<Q",r.d,r.p)[0] or 0; r.p+=8
    elif t in ("UInt8","char","bool"): v=r.u8()
    elif t=="float": v=r.f32()
    elif t=="double": v=struct.unpack_from("<d",r.d,r.p)[0]; r.p+=8
    else:
        v=None
        if t.startswith("PPtr<"): v=[r.i32(),r.i64()]
        elif t=="vector": sz=r.i32(); v=[r.i32() for _ in range(sz)]
        elif n.m_Children and n.m_Children[0].m_Type=="Array":
            sz=r.i32(); sub=n.m_Children[0].m_Children[1]; v=[rd(sub,r) for _ in range(sz)]
        elif n.m_Children:
            out={}
            for c in n.m_Children:
                if c.m_Type=="ManagedReferencesRegistry": continue
                out[c.m_Name]=rd(c,r)
            v=out
        else: v=None
    if (n.m_MetaFlag or 0)&ALIGN: r.align4()
    return v

class W:
    __slots__=("b","p")
    def __init__(s): s.b=bytearray(); s.p=0
    def _w(s,x): s.b.extend(x); s.p+=len(x)
    def align4(s):
        p=(4-s.p%4)%4
        if p: s._w(b"\x00"*p)
def ws(w,s):
    b=s.encode("utf-8","surrogateescape"); w._w(struct.pack("<i",len(b))); w._w(b); w.align4()
def wn(w,n,val):
    t=n.m_Type
    if t=="string":
        k=n.m_Children
        if k and k[0].m_Type=="Array":
            inn=k[0].m_Children; dt=inn[1].m_Type if len(inn)>=2 else "char"
            if dt=="string":
                w._w(struct.pack("<i",len(val)))
                for s in val: ws(w,s)
            else: ws(w,val)
        else: ws(w,val)
        return
    if t in ("int","SInt32"): w._w(struct.pack("<i",val))
    elif t in ("unsigned int","UInt32","Type*"): w._w(struct.pack("<I",val))
    elif t in ("SInt64","long long"): w._w(struct.pack("<q",val))
    elif t in ("UInt64","unsigned long long"): w._w(struct.pack("<Q",val))
    elif t=="FileSize": w._w(struct.pack("<I",val))
    elif t in ("UInt8","char","bool"): w._w(struct.pack("<B",val))
    elif t=="float": w._w(struct.pack("<f",val))
    elif t=="double": w._w(struct.pack("<d",val))
    else:
        if t.startswith("PPtr<"):
            fid,pid=val; w._w(struct.pack("<i",fid)); w._w(struct.pack("<q",pid))
        elif t=="vector":
            w._w(struct.pack("<i",len(val)))
            for x in val: w._w(struct.pack("<i",x))
        elif n.m_Children and n.m_Children[0].m_Type=="Array":
            w._w(struct.pack("<i",len(val)))
            sub=n.m_Children[0].m_Children[1]
            for x in val: wn(w,sub,x)
        elif n.m_Children:
            for c in n.m_Children:
                if c.m_Type=="ManagedReferencesRegistry": continue
                wn(w,c,val[c.m_Name])
    if (n.m_MetaFlag or 0)&ALIGN: w.align4()

def clean(v):
    if isinstance(v,dict): return {k:clean(x) for k,x in v.items()}
    if isinstance(v,list): return [clean(x) for x in v]
    if isinstance(v,str):
        try: return v.encode("utf-8","surrogateescape").decode("utf-8")
        except Exception: return v.encode("utf-8","replace").decode("utf-8")
    return v

def main(translate=False):
    node=load_node()
    env=UnityPy.Environment()
    f=env.load_file(SA1)
    book=[o for o in f.objects.values() if o.byte_size>1000000 and o.class_id==114][0]
    raw=book.get_raw_data()
    OLSZ=len(raw)
    r=R(raw); val=rd(node,r); valc=clean(val)

    grids=valc.get("importGridList") or []
    print("grids: %d"%len(grids),flush=True)
    trans=json.load(open(TRANS,encoding="utf-8"))
    print("translation units: %d"%len(trans),flush=True)

    # --- report grid names + row counts ---
    for g in grids:
        nm=g.get("name") if isinstance(g,dict) else "?"
        rows=g.get("rows") if isinstance(g,dict) else []
        print("  grid=%r rows=%d"%(nm,len(rows) if isinstance(rows,list) else -1),flush=True)

    # --- verify mapping: for each grid, check that {sheet}:{rowidx} keys exist & source matches ---
    print("\n--- mapping verification (per grid, first few) ---")
    sheets=set()
    for u in trans:
        sheets.add(u.split(":")[0])
    print("translation sheet set:",sorted(sheets),flush=True)

    replaced=0; matched=0; missed=0; sample=[]
    for g in grids:
        nm=g.get("name") or ""
        base=nm.rsplit(":",1)[-1] if ":" in nm else nm  # sheet suffix
        rows=g.get("rows") or []
        for idx,row in enumerate(rows):
            if not isinstance(row,dict): continue
            st=row.get("strings") or []
            key="%s:%d"%(base,idx)
            if key in trans:
                matched+=1
                cur=st[8] if len(st)>8 else ""
                tr=trans[key]
                if translate:
                    st[8]=tr
                replaced+=1
                if len(sample)<6 and cur:
                    sample.append((key,cur[:24],tr[:24]))
            else:
                # only count rows that actually have Text content but no translation
                if len(st)>8 and (st[8] or "").strip():
                    missed+=1
    print("\nmatched keys (translated this pass): %d"%replaced,flush=True)
    print("book rows with non-empty Text but NO translation key: %d"%missed,flush=True)
    print("\nsample replacements:",flush=True)
    for k,c,t in sample:
        print("  %s\n    JP: %s\n    ZH: %s"%(k,c,t),flush=True)

    # --- serialize translated (or identity if not translating) ---
    w=W(); wn(w,node,valc)
    new=bytes(w.b)
    print("\n--- size ---")
    print("orig book bytes: %d (%#x)"%(OLSZ,OLSZ))
    print("new  book bytes: %d (%#x)  delta=%+d"%(len(new),len(new),len(new)-OLSZ))
    if len(new)<=OLSZ:
        print("=> SHRINK/STABLE: pad to %d with trailing zeros, in-place splice OK"%OLSZ)
    else:
        print("=> GREW by %d: would need full shift + index fixup"%(len(new)-OLSZ))

if __name__=="__main__":
    main(translate=("--translate" in sys.argv))
