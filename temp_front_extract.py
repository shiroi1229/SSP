from pathlib import Path
text=Path('docs/roadmap/system_roadmap.json').read_text(encoding='utf-8')
start=text.index('"frontend": [')
append=text[:start].rstrip()+'\n'
print(text[start-200:start+10])
