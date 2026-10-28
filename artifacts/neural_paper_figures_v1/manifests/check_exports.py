"""File integrity and reproducible numeric-receipt checks, separate from visual review."""
from pathlib import Path
from hashlib import sha256
import json
from PIL import Image

OUT=Path(__file__).resolve().parents[1]
ROOT=OUT.parents[1]
checks=[]
for image in sorted((OUT/'figures').rglob('*.png')):
    with Image.open(image) as im:
        im.verify()
    with Image.open(image) as im:
        assert min(im.size)>500, image
        dpi=im.info.get('dpi',(0,0))
        assert all(abs(x-300)<.1 for x in dpi),(image,dpi)
    pdf=image.with_suffix('.pdf');svg=image.with_suffix('.svg')
    assert pdf.read_bytes().startswith(b'%PDF-'),pdf
    assert '<svg' in svg.read_text(encoding='utf-8')[:1000],svg
    checks.append({'png':str(image.relative_to(OUT)),'formats':['png300dpi','svg','pdf'],'status':'PASS'})
assert len(checks)==49, len(checks)
records=[]
for file in sorted((OUT/'manifests').glob('fig*.json')):
    d=json.loads(file.read_text(encoding='utf-8'))
    def verify(node):
        if isinstance(node,list):
            for v in node:verify(v)
        if isinstance(node,dict):
            for k,v in node.items():
                if isinstance(v,str) and len(v)==64 and all(c in '0123456789abcdef' for c in v) and ('/' in k or '\\' in k or '.' in k):
                    p=Path(k)
                    if not p.is_absolute():p=ROOT/p
                    if p.exists():assert sha256(p.read_bytes()).hexdigest()==v,(file,k,'stale hash')
                else:verify(v)
    verify(d); records.append(str(file.relative_to(OUT)))
result={'status':'PASS','figures':len(checks),'exports':len(checks)*3,'checks':checks,'checked_figure_manifests':records,
        'note':'File integrity is separate from actual-image visual and scientific review.'}
(OUT/'manifests/export_integrity.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'PASS','figure_versions':len(checks),'exports':len(checks)*3}))
