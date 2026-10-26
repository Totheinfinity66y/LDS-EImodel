"""File-level QA and contact sheets, to complement human visual inspection."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image,ImageDraw,ImageStat


def check(output):
    root=Path(output); manifest=json.loads((root/'figure_manifest.json').read_text(encoding='utf-8')); rows=[]
    for record in manifest['figures']:
        row={'id':record['id'],'encoding':record['encoding'],'checks':[]}
        for filename in record['paths']:
            p=Path(filename)
            if not p.exists(): raise ValueError('missing '+filename)
            if sha256(p.read_bytes()).hexdigest()!=record['output_sha256'][filename]: raise ValueError('changed '+filename)
            if p.suffix=='.png':
                with Image.open(p) as im:
                    im.load(); stats=ImageStat.Stat(im.convert('RGB')); dpi=im.info.get('dpi',(0,0))
                    if min(im.size)<500 or max(stats.stddev)<2 or min(dpi)<299: raise ValueError('blank/low-resolution PNG '+filename)
                    row['png_size']=im.size; row['dpi']=dpi
            elif p.suffix=='.svg':
                tree=ET.parse(p)
                if not tree.getroot().tag.endswith('svg'): raise ValueError('invalid SVG')
            elif p.suffix=='.pdf':
                raw=p.read_bytes()
                if not raw.startswith(b'%PDF-') or b'%%EOF' not in raw[-1024:]: raise ValueError('invalid PDF')
            row['checks'].append(p.suffix+' integrity/hash')
        rows.append(row)
    qa=root/'manifests'; qa.mkdir(exist_ok=True)
    sheets=[]
    for mode in ('one_hot','ring','topology','comparison'):
        paths=[Path(p) for r in manifest['figures'] if r['encoding']==mode for p in r['paths'] if p.endswith('.png')]
        for start in range(0,len(paths),6):
            selected=paths[start:start+6]; sheet=Image.new('RGB',(1800,1800),'#eeeeee'); draw=ImageDraw.Draw(sheet)
            for i,path in enumerate(selected):
                with Image.open(path) as source:
                    source=source.convert('RGB'); source.thumbnail((880,550)); x=(i%2)*900+(900-source.width)//2; y=(i//2)*600+30
                    sheet.paste(source,(x,y)); draw.text(((i%2)*900+10,(i//2)*600+8),path.stem,fill='black')
            dest=qa/f'contact_{mode}_{start//6+1}.jpg'; sheet.save(dest,quality=90); sheets.append(str(dest))
    (qa/'figure_quality.json').write_text(json.dumps({'file_checks':'PASS','figures':rows,'contact_sheets':sheets,'visual_review':'Separate visual review required; file integrity alone is not layout acceptance'},indent=2)+'\n',encoding='utf-8')
    print(f'Integrity PASS: {len(rows)} figure groups; {len(sheets)} contact sheets',flush=True)
    return rows


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('output'); check(parser.parse_args().output)
