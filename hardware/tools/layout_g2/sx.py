import re
class Sym(str): pass
def parse(t):
    toks=re.findall(r'"(?:[^"\\]|\\.)*"|\(|\)|[^\s()"]+',t)
    st=[[]]
    for k in toks:
        if k=='(': st.append([])
        elif k==')':
            x=st.pop(); st[-1].append(x)
        elif k[0]=='"': st[-1].append(k[1:-1].encode().decode('unicode_escape') if '\\' in k else k[1:-1])
        else: st[-1].append(Sym(k))
    return st[0][0]
def q(s):
    return '"'+s.replace('\\','\\\\').replace('"','\\"').replace('\n','\\n')+'"'
def ser(x,ind=0):
    if isinstance(x,list):
        simple=all(not isinstance(i,list) for i in x)
        if simple:
            return '('+' '.join(ser(i) for i in x)+')'
        out='('+' '.join(ser(i) for i in x if not isinstance(i,list)) if False else None
        parts=[]; head=[]
        for i in x:
            if isinstance(i,list): parts.append('\n'+'\t'*(ind+1)+ser(i,ind+1))
            else:
                if parts: parts.append(' '+ser(i))
                else: head.append(ser(i))
        return '('+' '.join(head)+''.join(parts)+'\n'+'\t'*ind+')'
    if isinstance(x,Sym): return str(x)
    if isinstance(x,str): return q(x)
    if isinstance(x,float):
        s=f"{x:.6f}".rstrip('0').rstrip('.'); return s if s not in('-0','') else '0'
    return str(x)
def find(x,name): return [i for i in x if isinstance(i,list) and i and i[0]==name]
def find1(x,name):
    r=find(x,name); return r[0] if r else None
