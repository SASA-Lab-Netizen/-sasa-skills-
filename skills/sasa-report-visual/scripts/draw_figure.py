"""Render validated research/process/matrix specs as editable SVG. Standard library only."""
import argparse,json
from pathlib import Path
from html import escape

THEMES={'blue':('#1764B7','#203A5F','#EAF1FA'),'gold':('#B47A00','#304562','#FFF3CE'),'orange':('#D96613','#8A3D16','#FFF0E5')}

def render(spec):
    kind=spec.get('type')
    if kind not in ('research','process','matrix'): raise ValueError('type must be research, process or matrix')
    if spec.get('theme','blue') not in THEMES:raise ValueError('Unknown theme')
    primary,dark,tint=THEMES[spec.get('theme','blue')]
    body=[]
    def text(x,y,value,size=17,color=dark,bold=False,width=17):
        value=str(value)
        lines=[]
        for para in value.split('\n'):
            lines.extend([para[i:i+width] for i in range(0,len(para),width)] or [''])
        if len(lines)>3:raise ValueError('Label too long; shorten or split the figure')
        spans=''.join(f'<tspan x="{x}" dy="{0 if i==0 else size*1.45}">{escape(line)}</tspan>' for i,line in enumerate(lines))
        body.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{700 if bold else 400}">{spans}</text>')
    def rect(x,y,w,h,fill,stroke='none'):
        body.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{fill}" stroke="{stroke}"/>')
    def arrow(x1,y1,x2,y2):
        body.append(f'<path d="M{x1},{y1} L{x2},{y2}" stroke="{primary}" stroke-width="2" fill="none" marker-end="url(#arrow)"/>')
    def required(obj,keys):
        if any(not isinstance(obj.get(k),str) or not obj[k].strip() for k in keys):raise ValueError('Missing nonempty strings: '+','.join(keys))
    required(spec,['title','source'])
    if len(spec['title'])>34 or '\n' in spec['title']:raise ValueError('Title must fit one line (34 characters)')
    if len(spec['source'])>58 or '\n' in spec['source']:raise ValueError('Use a short source label (58 characters); put full citation in the report')
    text(25,34,spec['title'],24,bold=True,width=34)
    if kind=='research':
        rows=spec.get('rows',[])
        if not 2<=len(rows)<=6:raise ValueError('research requires 2–6 rows')
        for x,label in [(25,'阶段'),(180,'研究问题'),(435,'分析方法'),(700,'阶段产物')]:text(x,94,label,18,bold=True)
        for i,row in enumerate(rows):
            required(row,['stage','question','method','output']);y=112+i*139
            rect(20,y,115,108,primary);text(30,y+34,row['stage'],18,'white',True,5)
            for x,key in [(155,'question'),(415,'method'),(680,'output')]:
                rect(x,y,235,108,tint if key!='output' else 'white',primary if key=='output' else 'none');text(x+14,y+35,row[key],17,width=12)
            arrow(393,y+53,411,y+53);arrow(654,y+53,675,y+53)
            if i<len(rows)-1:arrow(797,y+111,797,y+132)
        height=112+len(rows)*139+34
    elif kind=='process':
        nodes=spec.get('nodes',[])
        if not 2<=len(nodes)<=5:raise ValueError('process requires 2–5 nodes')
        cell=900/len(nodes)
        for i,node in enumerate(nodes):
            required(node,['label','detail']);x=20+i*cell
            if len(node['label'])>2*max(5,int((cell-40)/18)):raise ValueError('Process label must fit two lines')
            rect(x,110,cell-20,155,tint,primary);text(x+13,148,node['label'],18,bold=True,width=max(5,int((cell-40)/18)))
            text(x+13,196,node['detail'],16,width=max(5,int((cell-40)/16)))
            if i<len(nodes)-1:arrow(x+cell-17,184,x+cell-4,184)
        height=330
    else:
        cols=spec.get('columns',[]);rows=spec.get('rows',[])
        if not 2<=len(cols)<=5 or not 1<=len(rows)<=12:raise ValueError('matrix requires 2–5 columns and 1–12 rows')
        cell=900/len(cols);width=max(6,int((cell-26)/16))
        for i,col in enumerate(cols):rect(20+i*cell,92,cell-2,58,primary);text(30+i*cell,116,col,16,'white',True,width)
        for j,row in enumerate(rows):
            if not isinstance(row,list) or len(row)!=len(cols):raise ValueError('matrix row width mismatch')
            for i,value in enumerate(row):
                rect(20+i*cell,154+j*108,cell-2,104,tint if j%2==0 else 'white');text(30+i*cell,185+j*108,value,16,width=width)
        height=154+len(rows)*108+60
    text(25,height-20,spec['source'],14,'#5B6572',width=58)
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="940" height="{height}" viewBox="0 0 940 {height}" role="img"><title>{escape(spec["title"])}</title><defs><marker id="arrow" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="{primary}"/></marker></defs><rect width="100%" height="100%" fill="white"/><g font-family="Microsoft YaHei,Noto Sans CJK SC,sans-serif">'+''.join(body)+'</g></svg>'

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('spec');parser.add_argument('--output',required=True);args=parser.parse_args()
    spec=json.loads(Path(args.spec).read_text(encoding='utf-8-sig'))
    result=render(spec);target=Path(args.output);target.parent.mkdir(parents=True,exist_ok=True);target.write_text(result,encoding='utf-8');print(target)
