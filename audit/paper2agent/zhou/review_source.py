"""Record actual 18-page visual review and explicit extraction repairs."""
import json
from pathlib import Path
import fitz

ROOT=Path(__file__).parent/'paper-review'
DOC=ROOT/'documents/s001-zhou2023'
pdf=fitz.open(DOC/'source.pdf')
notes={
1:'Visually checked title, authors, affiliations, abstract, received/accepted dates and actual published-online date. Apparent table is page layout, not data; retained source image and searchable native abstract. Native hidden publication placeholder differs from visible 20 April 2023 and is not used as evidence.',
2:'Visually checked two-column introduction/Results order, dDMS/ISA definitions, 80/20 standard-reverse structure, human ANOVA statistics, WM/T+WM/ISA distinctions; body follows columns.',
3:'Visually checked Figure1 a/b/c and full two-column caption: task schema, blue/magenta condition colors, inverse efficiency mean+/-SEM, n27/n22; lower RNN Results and transition paragraph.',
4:'Visually checked multiplexing and connectivity Results plus complete Figure2 caption at bottom. Reordered the bottom caption after both main text columns to avoid splitting the paragraph continuing across columns.',
5:'Visually checked complete Figure2 a-m including three task rows, AA/BA sorting, activity colorbars, motor/timing outputs, performance/dimensionality/sequentiality box plots; caption is on previous page.',
6:'Visually checked complete Figure3 a-e, Unit89, sorted neurograms, training curves with epoch markers and SEM, dimensionality/time-decoding correlation, plus lower connectivity/hyperparameter prose and cross-page continuation.',
7:'Visually checked Figure4 a-d, actual/predicted 100ms cue-time bins, performance/MSE, short-long correlations and network-level whiskers; lower softplus/hyperparameter discussion.',
8:'Visually checked Figure5 a-g, presynaptic rows/postsynaptic columns, Ex/Inh segmentation, log abs weights versus linear mean weights, DeltaOrder and complete caption; dynamic-attractors paragraph continues next page.',
9:'Visually checked Figure6 a-d noise0.005/0.05 Ex-to-Ex ablation comparison, all panels/caption; lower Results states cross-Euclidean diagonal temporal recovery and local transient-channel interpretation; Discussion follows.',
10:'Visually checked full Figure7 a-c: black/red sample units, 3PC trajectories/time spheres, cross-Euclidean heatmap, 17-network mean+/-SEM and box-whiskers; no velocity field. Lower fixed-point/dynamic and ramps/sequences Discussion checked.',
11:'Visually checked both Discussion columns, limitations on silent-memory models and hyperparameters, conclusions/predictions, and start of human Methods with UCLA ethics and browser constraints.',
12:'Visually checked human inclusion, dDMS/ISA protocol and analysis, complete RNN equations as source images, rate definition, 32 topographic inputs, output sigmoid, Dale80/20 and weight initialization. Equations retained visually rather than guessed transcription.',
13:'Visually checked Euler tau50/dt10, costs, delay jitter, dimensionality matrix256x320 and95percent PCA, SVM25-trial leave-one-out, mutual information/Schur, input perturbation pi/channel17 amplitude0.25 cue+500ms duration50ms frozen noise, statistics and source links.',
14:'Visually checked References6-53 across columns, including dynamic-attractor citations47/48 and Inagaki53; no figure/table/equation omitted.',
15:'Visually checked References54-70, acknowledgements, author contributions, competing interests, supplementary/correspondence/reprint information and license paragraph; preserved material text.',
16:'Visually checked reporting summary page1, checked/NA statistics boxes, TF2.1/MatlabR2022a provenance, LIBSVM1.2 and OSF link. Checkbox block retained as source image to preserve semantics.',
17:'Visually checked reporting summary page2 demographic/recruitment/ethics and study-design tables, selected behavioural/social-science box and exclusions. Tables retained, checkbox selection preserved as image.',
18:'Visually checked reporting summary page3 all material/system/method N/A boxes. Preserve whole matrix as source image, because plain CSV loses checkbox state.'}

pages={}
for i in range(1,19):
    path=DOC/'pages'/f'page-{i:04d}.json'
    p=json.loads(path.read_text(encoding='utf-8'))
    p['reviewed']=True;p['review_notes']=notes[i]
    # Figure identities verified from originals, not inferred from PDF page.
    num={3:1,5:2,6:3,7:4,8:5,9:6,10:7}.get(i)
    for item in p['items']:
        if item['kind']=='figure' and num:
            item['label']=f'Figure {num}';item['asset_name']=f'figure-{num}'
    if i==1:
        item=p['items'][4]
        item.update(kind='figure',label='Title-page author and abstract source layout',asset_name='title-page-abstract',markdown='')
        item.pop('rows',None)
        abstract=next(b for b in pdf[0].get_text('blocks') if b[0]>200 and 250<b[1]<270)
        p['items'].insert(5,{'id':'p0001-abstract-searchable','kind':'text','bbox':list(abstract[:4]),'markdown':' '.join(abstract[4].split())})
    if i==4:
        by={x['id']:x for x in p['items']}
        ordered=[x for x in p['items'] if x['id'] not in ('p0004-b007','p0004-b012','p0004-b013')]
        ordered += [by['p0004-b007'],by['p0004-b012'],by['p0004-b013']]
        p['items']=ordered
    if i==16:
        for item in p['items']:
            if item['id']=='p0016-b004':
                item.update(kind='omit',markdown='',reason='Decorative natureportfolio logo, not a research figure.')
        p['items'].append({'id':'p0016-statistics-checkboxes','kind':'figure','bbox':[15,250,555,470],'markdown':'','label':'Reporting summary statistics checkbox states','asset_name':'reporting-statistics-checkboxes','category':'supp_figs'})
    if i==17:
        p['items'].append({'id':'p0017-field-checkboxes','kind':'figure','bbox':[15,290,555,307],'markdown':'','label':'Reporting summary selected field checkbox','asset_name':'reporting-field-checkboxes','category':'supp_figs'})
    if i==18:
        item=next(x for x in p['items'] if x['kind']=='table')
        item['rows']=None; item['asset_name']='reporting-materials-checkboxes';item['label']='Reporting summary materials and methods checkbox matrix'
    path.write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
    pages[i]=p

plan_path=DOC/'plan.json';plan=json.loads(plan_path.read_text())
plan['title']='Multiplexing working memory and time in the trajectories of neural networks'
plan['notes']=['All 18 supplied PDF pages visually reviewed. Supplementary-figure PDF was not supplied; its separate content is not included. Reporting-summary checkbox semantics preserved as images; equations preserved as source crops. Original author Figure7 raw recurrent trajectories and MATLAB analysis are absent from the public repository.']
plan_path.write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
bundle_path=ROOT/'bundle.json';bundle=json.loads(bundle_path.read_text())
bundle['sources'][0].update(reviewed=True,review_notes='All 18 supplied pages opened individually; see page-specific review notes and source-review coverage. Equations/checkbox states retained as source images. Independent fresh verification pending.',title=plan['title'])
bundle_path.write_text(json.dumps(bundle,ensure_ascii=False,indent=2),encoding='utf-8')
(Path(__file__).parent/'SOURCE_REVIEW_COVERAGE.json').write_text(json.dumps(notes,ensure_ascii=False,indent=2),encoding='utf-8')
print('Recorded actual visual review of 18 pages; repaired figure identities, abstract layout and Figure2 caption order.')
