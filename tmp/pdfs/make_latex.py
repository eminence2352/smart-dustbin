import ast
import re
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path('F:/smart dustbin')
source = ROOT / 'tmp/pdfs/build_srs.py'
dest = ROOT / 'output/latex/Smart_Dustbin_SRS.tex'
dest.parent.mkdir(parents=True, exist_ok=True)

def escape(s):
    replace = {'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}','×':r'\(\times\)','’':"'",'‘':"'",'“':'``','”':"''",'→':r'\(\rightarrow\)'}
    return ''.join(replace.get(ch,ch) for ch in str(s))

class Convert(HTMLParser):
    def __init__(self):
        super().__init__(); self.out=[]
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if tag=='b':self.out.append(r'\textbf{')
        elif tag=='br':self.out.append(r'\newline ')
        elif tag=='link':self.out.append(r'\href{'+attrs['href']+'}{')
    def handle_endtag(self, tag):
        if tag in ['b','link']:self.out.append('}')
    def handle_data(self, text):self.out.append(escape(text))
def tex(s):
    p=Convert();p.feed(str(s));return ''.join(p.out)

pages=[]
def new(t=None):pages.append({'title':t,'items':[]})
def para(t,*args,**kwargs):pages[-1]['items'].append(('para',t))
def sub(t):pages[-1]['items'].append(('sub',t))
def table(h,rows,widths):pages[-1]['items'].append(('table',h,rows,widths))
def req(i,t):para('<b>'+i+'.</b> '+t)
def noop(*args,**kwargs):pass
class Dummy:
    def __getattr__(self,key):return noop
class DummyParagraph:
    def __init__(self,*args,**kwargs):pass
    def wrap(self,*args):return (0,0)
    def drawOn(self,*args):pass
tree=ast.parse(source.read_text(encoding='utf-8-sig'))
start=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='new')
nodes=tree.body[start:]
nodes=[n for n in nodes if not (isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='print')]
env=dict(new=new,para=para,sub=sub,table=table,req=req,box=noop,line=noop,label=noop,c=Dummy(),Paragraph=DummyParagraph,styles={'center':None},muted=None,ink=None,L=50,R=545,CW=495,H=842,OUT=dest)
exec(compile(ast.Module(body=nodes,type_ignores=[]),'capture','exec'),env)

preamble=r'''% Smart Dustbin SRS
% Self contained source. Compile twice with pdfLaTeX to update the contents.
% Diagrams are editable TikZ code. No external image files are needed.
\documentclass[11pt,a4paper]{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage[margin=20mm,headheight=14pt]{geometry}
\usepackage{microtype}
\usepackage{array,tabularx,longtable,booktabs}
\usepackage{amsmath}
\usepackage{tikz}
\usetikzlibrary{arrows.meta,positioning,shapes.geometric,calc}
\usepackage{fancyhdr}
\usepackage{titlesec}
\usepackage[hidelinks]{hyperref}
\hypersetup{pdftitle={Smart Dustbin System Requirements Specification},pdfauthor={Group 06}}
\setlength{\parindent}{0pt}
\setlength{\parskip}{7pt}
\setlength{\emergencystretch}{3em}
\renewcommand{\arraystretch}{1.14}
\setlength{\tabcolsep}{5pt}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\footnotesize Smart Dustbin}
\fancyhead[R]{\footnotesize System Requirements Specification}
\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0pt}
\titleformat{\section}{\large\bfseries}{}{0pt}{}
\titleformat{\subsection}{\normalsize\bfseries}{}{0pt}{}
\titlespacing*{\section}{0pt}{0pt}{12pt}
\titlespacing*{\subsection}{0pt}{10pt}{5pt}
\newcolumntype{Y}{>{\raggedright\arraybackslash}X}
\tikzset{block/.style={draw,rounded corners=2pt,align=center,font=\small,text width=3.5cm,minimum height=1.15cm,inner sep=5pt},arrow/.style={-{Latex[length=2mm]},thin},wire/.style={thin}}
\newcommand{\reportsection}[1]{\section*{#1}\addcontentsline{toc}{section}{#1}}
\newcommand{\reportsubsection}[1]{\subsection*{#1}\addcontentsline{toc}{subsection}{#1}}
\begin{document}
\begin{titlepage}
\centering
\vspace*{12mm}
{\Large\bfseries Bangladesh University of Professionals\par}
\vspace{5mm}
Faculty of Science and Technology\par
Department of Computer Science and Engineering\par
\vspace{22mm}
{\LARGE\bfseries System Requirements Specification\par}
\vspace{8mm}
{\Large\bfseries ESP32 Based Smart Waste Bin\par}
\vspace{3mm}
Real Time Monitoring and Collector Dashboard\par
\vspace{18mm}
Computer Interfacing Laboratory\par
Course Code: CSE 4102\par
Section: B\par
Group: 06\par
\vspace{12mm}
\textbf{Submitted by}\par
\vspace{4mm}
\begin{tabular}{@{}ll@{}}
Sheikh Sifat Rahman & 23524242108 \\
Sajid Al Adeeb & 23524242030 \\
Abdullah Towhid & 23524242054 \\
Taqi Tahmid & 23524242110
\end{tabular}
\vfill
Date of Submission: 5 October 2026\par
\vspace*{12mm}
\end{titlepage}
\setcounter{page}{2}
\tableofcontents
'''

diagrams={
'5.1':r'''
\begin{center}
\begin{tikzpicture}[node distance=6mm and 12mm]
\node[block,text width=3.4cm,minimum height=5.8cm] (esp) {\textbf{ESP32}\\[3mm]GPIO 23: TRIG\\GPIO 18: ECHO\\GPIO 27: IR input\\GPIO 13: servo\\GPIO 4: DHT data\\GPIO 21: SDA\\GPIO 22: SCL\\[3mm]3.3 V logic};
\node[block,text width=3.2cm,left=of esp,yshift=2cm] (ultra) {\textbf{One HC-SR04}\\5 V supply\\TRIG and ECHO};
\node[block,text width=3.2cm,left=of esp] (ir) {\textbf{One IR sensor}\\3.3 V compatible\\OUT to GPIO 27};
\node[block,text width=3.2cm,left=of esp,yshift=-2cm] (dht) {\textbf{DHT11}\\3.3 V supply\\DATA to GPIO 4};
\node[block,text width=3.2cm,right=of esp,yshift=2cm] (servo) {\textbf{SG90 servo}\\5 V supply\\Signal from GPIO 13};
\node[block,text width=3.2cm,right=of esp] (lcd) {\textbf{16x2 I2C LCD}\\SDA and SCL through\\3.3 V to 5 V level shifter};
\node[block,text width=3.2cm,right=of esp,yshift=-2cm] (power) {\textbf{Regulated 5 V}\\Servo, ultrasonic, LCD\\Approved board input};
\draw[arrow] (esp.west |- ultra.east) -- (ultra.east);
\draw[arrow] ([yshift=-3mm]ultra.east) -- ([yshift=-3mm]esp.west |- ultra.east);
\draw[arrow] (ir) -- (esp);
\draw[arrow] (dht.east) -- (esp.west |- dht.east);
\draw[arrow] (esp.east |- servo.west) -- (servo.west);
\draw[wire] (esp) -- (lcd);
\draw[wire] (power.west) -- (esp.east |- power.west);
\node[align=center,font=\small,below=6mm of esp,text width=14cm] {All components share ground. Ultrasonic ECHO uses the divider in Figure 5.2.};
\end{tikzpicture}
\end{center}
''',
'5.2':r'''
\begin{center}
\begin{tikzpicture}
\node (echo) at (0,0) {ECHO, 5 V};
\node[draw,minimum width=1.5cm,minimum height=6mm] (r1) at (3,0) {1 k$\Omega$};
\coordinate (join) at (5,0);
\node (gpio) at (8,0) {GPIO 18, about 3.3 V};
\node[draw,minimum width=1.5cm,minimum height=6mm] (r2) at (5,-1) {2 k$\Omega$};
\node (gnd) at (5,-1.8) {GND};
\draw (echo) -- (r1) -- (join) -- (gpio);
\fill (join) circle (1.5pt);
\draw (join) -- (r2) -- (gnd);
\end{tikzpicture}
\end{center}
''',
'5.3':r'''
\begin{center}
\begin{tikzpicture}[node distance=8mm and 12mm]
\node[block,text width=3.3cm] (server) {Node.js and Express\\Check and calculate};
\node[block,text width=3.1cm,left=of server,yshift=9mm] (physical) {Physical ESP32 bin\\Readings and openings};
\node[block,text width=3.1cm,left=of server,yshift=-9mm] (sim) {Simulated bins\\Same API};
\node[block,text width=3.1cm,right=of server] (web) {Browser\\Collector dashboard};
\node[block,below=of server] (db) {SQLite database};
\draw[arrow] (physical) -- (server);
\draw[arrow] (sim) -- (server);
\draw[arrow] (server) -- (web);
\draw[arrow] (server) -- (db);
\end{tikzpicture}
\end{center}
''',
'5.4':r'''
\begin{center}
\begin{tikzpicture}[node distance=5mm and 16mm,block/.append style={text width=5.4cm,minimum height=1.1cm,font=\footnotesize}]
\node[block,text width=7cm] (start) {Start and initialize hardware, settings, and Wi-Fi};
\node[block,below=8mm of start,xshift=-3.2cm] (local) {LOCAL CONTROL LOOP\\Read IR presence};
\node[block,below=8mm of start,xshift=3.2cm] (data) {DATA LOOP\\Wait for the next send interval};
\node[block,below=of local] (hand) {Hand present?\\Yes: open or keep lid open\\No: start clear timer};
\node[block,below=of hand] (count) {Opening completed?\\Count the cycle once\\Do not recount a held hand};
\node[block,below=of count] (close) {Clear for 3 seconds?\\Close, then allow cooldown\\New presence: reopen};
\node[block,below=of data] (measure) {Lid closed and settled?\\Yes: measure distance\\No: distance is unavailable};
\node[block,below=of measure] (batch) {Read temperature and humidity\\Prepare a batch with a sequence ID\\Keep new openings separately};
\node[block,below=of batch] (send) {Send batch to the server\\If the request fails, retain it for retry};
\node[block,below=of send] (save) {Server checks and saves data\\Calculate fill and collection state\\Update estimate and acknowledge};
\node[block,below=of save] (ack) {Acknowledged: release pending batch\\No reply: retry the same batch};
\node[block,below=of ack] (view) {Dashboard requests updates\\Show readings and history};
\foreach \a/\b in {start/local,start/data,local/hand,hand/count,count/close,data/measure,measure/batch,batch/send,send/save,save/ack,ack/view}{\draw[arrow] (\a) -- (\b);}
\draw[arrow] (close.west) -- ++(-5mm,0) |- (local.west);
\node[below=7mm of close,align=center,text width=5cm,font=\small] {Local lid control continues\\when Wi-Fi is unavailable.};
\end{tikzpicture}
\end{center}
''',
'6.1':r'''
\begin{center}
\begin{tikzpicture}[font=\small]
\draw (2,-0.5) rectangle (12,6.5);
\node[anchor=west] at (2.2,6.15) {SMART DUSTBIN SYSTEM};
\foreach \y/\name in {5.3/Bin user,3.1/Collector,0.9/Operator}{
\draw (0,\y+0.35) circle (0.15);
\draw (0,\y+0.2) -- (0,\y-0.3);
\draw (-0.25,\y) -- (0.25,\y);
\draw (0,\y-0.3) -- (-0.2,\y-0.65);
\draw (0,\y-0.3) -- (0.2,\y-0.65);
\node at (0,\y-0.92) {\name};}
\node[ellipse,draw,minimum width=8.3cm,minimum height=8mm] (lid) at (7,5.3) {Use automatic lid};
\node[ellipse,draw,minimum width=8.3cm,minimum height=8mm] (view) at (7,3.9) {View bins and readings};
\node[ellipse,draw,minimum width=8.3cm,minimum height=8mm] (collect) at (7,2.5) {Mark a bin as collected};
\node[ellipse,draw,minimum width=8.3cm,minimum height=8mm] (config) at (7,0.9) {Configure and test the system};
\draw (0.3,5.3) -- (lid.west);
\draw (0.3,3.1) -- (view.west);
\draw (0.3,3.1) -- (collect.west);
\draw (0.3,0.9) -- (config.west);
\end{tikzpicture}
\end{center}
'''
}

captions={'System':'Table 2.1 Comparison of existing approaches','ID and quality':'Table 3.1 Quality requirements','Component and quantity':'Table 4.1 Hardware and planned costs','Part':'Table 4.2 Software requirements','Field':'Table 8.1 Reading fields','Method and path':'Table 8.2 API endpoints','Test and coverage':'Table 8.3 Planned acceptance tests','Setting':'Table 8.4 Proposed starting settings'}
out=[preamble]
for page_no,page in enumerate(pages[1:],2):
    out.append('\n% Original report page '+str(page_no)+'\n')
    if page_no>2:
        out.append(r'\clearpage'+'\n')
        title=page['title']
        command='reportsection' if re.match(r'^\d+ ',title) else 'reportsubsection'
        if 'Continued' in title:command='section*'
        out.append('\\'+command+'{'+tex(title)+'}\n')
    for item in page['items']:
        kind=item[0]
        if kind=='sub':
            command='reportsubsection' if re.match(r'^\d+\.\d+ ',item[1]) else 'subsection*'
            out.append('\\'+command+'{'+tex(item[1])+'}\n')
        elif kind=='para':
            match=re.match(r'<b>Figure (\d+\.\d+)</b>',item[1])
            if match:out.append(diagrams[match.group(1)])
            out.append(tex(item[1])+'\par\n\n')
        elif kind=='table':
            headers,rows,widths=item[1:]
            out.append('\\textbf{'+tex(captions[headers[0]])+'}\\par\n')
            usable=16.3-0.36*len(widths)
            cols=''.join('>{\\raggedright\\arraybackslash}p{'+f'{usable*w/sum(widths):.3f}'+'cm}' for w in widths)
            out.append('{\\small\n\\begin{longtable}{@{}'+cols+'@{}}\n\\toprule\n')
            out.append(' & '.join('\\textbf{'+tex(h)+'}' for h in headers)+r' \\ \midrule'+'\n\\endhead\n')
            for row in rows:out.append(' & '.join(tex(v) for v in row)+r' \\[3pt]'+'\n')
            out.append('\\bottomrule\n\\end{longtable}\n}\n')
out.append('\\end{document}\n')
dest.write_text(''.join(out),encoding='utf-8')
print(f'Saved {dest}; {len(pages)} source pages; {dest.stat().st_size} bytes')
