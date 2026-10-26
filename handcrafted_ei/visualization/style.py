"""Shared vector and 300 dpi raster style."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ENCODING_COLORS={'one_hot':'#0072B2','ring':'#D55E00','topology':'#009E73'}
D_COLORS={1:'#0072B2',-1:'#D55E00'}
NAMES={'one_hot':'One-hot','ring':'1D Ring','topology':'2D Topology'}


def configure():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.titlesize':9,
        'axes.labelsize':8,'legend.fontsize':6,'xtick.labelsize':7,'ytick.labelsize':7,
        'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none',
        'pdf.fonttype':42,'savefig.facecolor':'white','figure.facecolor':'white'})


def panels(axes):
    for i,ax in enumerate(np.asarray(axes,dtype=object).ravel()):
        label=ax.text2D if hasattr(ax,'text2D') else ax.text
        label(-.12,1.04,chr(65+i),transform=ax.transAxes,fontweight='bold',fontsize=11)


def timeline(ax,events,labels=False):
    ax.axvspan(0,events['sample_end'],color='#E69F00',alpha=.1)
    ax.axvspan(events['sample_end'],events['delay_end'],color='#56B4E9',alpha=.06)
    for s in range(1,5):
        ax.axvline(events[f'readout{s}'],color='#777777',lw=.65,ls=':')
        if labels: ax.text(events[f'readout{s}'],1,f'R{s}',rotation=90,va='top',transform=ax.get_xaxis_transform(),fontsize=6)
    for s in range(1,4):
        ax.axvline(events[f'to_R{s+1}'],color='#009E73',alpha=.45,lw=.6)
        ax.axvline(events[f'retire{s}'],color='#CC79A7',alpha=.4,lw=.6,ls='--')


def save_figure(fig,out,stem,formats=('png','svg','pdf')):
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    paths=[]
    for ext in formats:
        p=out/f'{stem}.{ext}'; fig.savefig(p,dpi=300,bbox_inches='tight'); paths.append(str(p))
    plt.close(fig)
    return paths


def image(ax,values,title,xlabel='',ylabel='',vmin=None,vmax=None,cmap='viridis'):
    im=ax.imshow(values,aspect='auto',origin='lower',interpolation='nearest',vmin=vmin,vmax=vmax,cmap=cmap)
    ax.set(title=title,xlabel=xlabel,ylabel=ylabel)
    return im
