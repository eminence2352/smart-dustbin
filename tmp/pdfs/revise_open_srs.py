from pathlib import Path
import re

p=Path('F:/smart dustbin/output/latex/Smart_Dustbin_SRS.tex')
s=p.read_text(encoding='utf-8')

def between(start,end,replacement):
    global s
    a=s.index(start);b=s.index(end,a)
    s=s[:a]+replacement+s[b:]

between(r'\subsection*{About this report}', '% Original report page 3', '')
between(r'\subsection*{A typical visit}', r'\subsection*{What the numbers mean}', '')
between('To prevent a lost server reply from causing double counting,', '% Original report page 7', '')
s=s.replace('Invalid payloads shall return 400 and unknown bin IDs shall return 404. Duplicate batches shall be acknowledged without adding the opening count again.', 'Invalid readings and unknown bin IDs shall be rejected. Repeated submissions shall not add the same opening count twice.')
s=s.replace('The server shall save readings, counts, and collection changes together in a database transaction. Committed data shall remain available after a server restart.', 'The server shall store readings, opening counts, and collection history. Saved records shall remain available after a server restart.')
s=s.replace('Node.js, Express, and SQLite replace the earlier proposal\'s Python dashboard and USB data connection. Plain JavaScript keeps the browser interface simple.', 'The dashboard uses Node.js, Express, SQLite, and plain JavaScript.')
s=s.replace('The course guideline [R3] provides the structure of this report. No interview or survey study is included.', 'These documents describe the monitoring features and hardware needed for the prototype.')
s=s.replace('A shared device API key may be added, but the baseline does not provide encrypted traffic or collector accounts.', 'Collector accounts and remote access are outside the current scope.')
between('The proposed server port is 3000.', '% Original report page 11', 'The dashboard and its chart files shall be available on the local server without an internet connection. The server shall save collection records and display times in Asia/Dhaka.\\par\n\n')

circuit=r'''\reportsubsection{5.1 Circuit Diagram}
The ESP32 connects the sensors, lid motor, and LCD. The IR sensor detects a hand, while one ultrasonic sensor measures the distance to the waste. Figure 5.1 shows the proposed connections.\par

\begin{center}
\begin{tikzpicture}[
  component/.style={draw,rounded corners=2pt,align=center,
    font=\small,text width=3.5cm,minimum height=1.65cm,
    inner sep=6pt,execute at begin node={\setlength{\parskip}{0pt}}},
  controller/.style={component,text width=3.0cm,minimum height=7.0cm},
  node distance=9mm]
% Nodes in each column are placed below the previous node's actual edge.
% Text wrapping can therefore increase a box height without overlap.
\node[component] (ultra) at (0,0)
  {\textbf{One ultrasonic sensor}\\HC-SR04\\TRIG and ECHO};
\node[component,below=of ultra] (ir)
  {\textbf{One IR obstacle sensor}\\Hand detection\\OUT to GPIO 27};
\node[component,below=of ir] (dht)
  {\textbf{DHT11}\\Temperature and humidity\\DATA to GPIO 4};
\node[controller,right=12mm of ir] (esp)
  {\textbf{ESP32}\\[4mm]
   GPIO 23: TRIG\\GPIO 18: ECHO\\[2mm]
   GPIO 27: IR input\\GPIO 4: DHT data\\[2mm]
   GPIO 13: servo\\GPIO 21: SDA\\GPIO 22: SCL};
\node[component] (servo) at ([xshift=4.8cm]esp.center |- ultra.center)
  {\textbf{SG90 servo}\\Lid movement\\Signal from GPIO 13};
\node[component,below=of servo] (lcd)
  {\textbf{16x2 I2C LCD}\\SDA from GPIO 21\\SCL from GPIO 22};
\node[component,below=of lcd] (power)
  {\textbf{Regulated 5 V supply}\\Board and powered modules\\Common ground};
\draw[arrow] ([yshift=2mm]esp.west |- ultra.east)
  -- ([yshift=2mm]ultra.east);
\draw[arrow] ([yshift=-2mm]ultra.east)
  -- ([yshift=-2mm]esp.west |- ultra.east);
\draw[arrow] (ir.east) -- (esp.west |- ir.east);
\draw[arrow] (dht.east) -- (esp.west |- dht.east);
\draw[arrow] (esp.east |- servo.west) -- (servo.west);
\draw[wire] (esp.east |- lcd.west) -- (lcd.west);
\draw[wire] (power.west) -- (esp.east |- power.west);
\end{tikzpicture}
\end{center}
\textbf{Figure 5.1} Proposed component connections for the physical bin.\par

The arrows show sensor and control signals. All components share a common ground. The ultrasonic input and LCD connection use suitable voltage matching, as required by the selected modules.\par

\textbf{Table 5.1 Sensor and control connections}\par
\begin{tabularx}{\textwidth}{@{}lY@{}}
\toprule
\textbf{Component signal} & \textbf{ESP32 connection} \\ \midrule
Ultrasonic TRIG & GPIO 23 \\
Ultrasonic ECHO & GPIO 18 through voltage matching \\
IR sensor OUT & GPIO 27 \\
DHT11 DATA & GPIO 4 \\
Servo control & GPIO 13 \\
LCD SDA and SCL & GPIO 21 and GPIO 22 through suitable I2C voltage matching \\
\bottomrule
\end{tabularx}

'''
between(r'\reportsubsection{5.1 Proposed circuit diagram}', '% Original report page 12',circuit)
s=s.replace('Figure 5.3','Figure 5.2').replace('Figure 5.4','Figure 5.3')

# Remove API implementation tables, the standalone test plan, repeated settings,
# and the demonstration checklist. Keep source references as supporting material.
ref_start=s.index(r'\subsection*{References}')
refs=s[ref_start+len(r'\subsection*{References}'):s.index(r'\end{document}')]
between('% Original report page 16',r'\end{document}',r'''\clearpage
\reportsection{8 Appendix}
\reportsubsection{8.1 References}
'''+refs+'\n')
s=s.replace('A unique action ID shall make a retry safe if a server reply is lost.', 'Retrying the same action shall not record a second collection.')
s=s.replace('Prepare a batch with a sequence ID','Prepare the sensor readings')
s=s.replace('Keep new openings separately','Include the opening count')
s=s.replace('Acknowledged: release pending batch','Acknowledged: clear sent readings')
s=s.replace('No reply: retry the same batch','No reply: retain readings for retry')
s=s.replace('Server checks and saves data\\\\Calculate fill and collection state','Server checks and saves readings\\\\Calculate fill and collection state')
s=re.sub(r'% Original report page \d+\n','',s)
s=s.replace('% Self contained source. Compile twice with pdfLaTeX to update the contents.','% Compile twice with pdfLaTeX to update the contents.')
p.write_text(s,encoding='utf-8')
print('Updated the open source in place:',p)
print('Characters:',len(s),'Planned content sections:',s.count('\\clearpage')+2)

# Structural checks do not replace compilation.
stack=[]
for m in re.finditer(r'\\(begin|end)\{([^}]+)\}',s):
    action,env=m.groups()
    if action=='begin':stack.append(env)
    else:
        assert stack and stack.pop()==env,(action,env)
assert not stack
clean=re.sub(r'(?m)%.*$','',re.sub(r'\\[{}%]','',s))
depth=0
for ch in clean:
    if ch=='{':depth+=1
    elif ch=='}':depth-=1
    assert depth>=0
assert depth==0
for removed in ['Protecting the ultrasonic input','Figure 5.4','API endpoints','8.2 Test Plan','About this report','Appendix 8.1 explains']:
    assert removed not in s,removed
assert 'One ultrasonic sensor' in s and 'One IR obstacle sensor' in s
print('Passed source structure and removed-content checks.')
