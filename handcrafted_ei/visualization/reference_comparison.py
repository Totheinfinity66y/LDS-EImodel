"""Private three-column source/method-check/LDS comparison, no copied results."""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from .style import configure,save_figure
from ..evaluation.reference_dynamics import cross_temporal_distance
from ..evaluation.reference_reproduction import ROOT,DEFAULT,dump


def run(root=DEFAULT):
    configure();folder=root/'figures/source_comparisons';folder.mkdir(parents=True,exist_ok=True)
    source=ROOT/'artifacts/neural_representation_v2/reference_evidence'
    records=[]
    for name,image_name,npz in [('inagaki','Inagaki2019_fig5.png','fixed_points.npz'),('zhou','Zhou2023_p10.png','input_source_time_7.npz')]:
        fig,ax=plt.subplots(1,3,figsize=(18,7),layout='constrained')
        ax[0].imshow(plt.imread(source/image_name));ax[0].axis('off');ax[0].set_title('Original paper — internal reference only')
        # Analytical input check is visibly labelled synthetic, never source data.
        t=np.linspace(0,2,201)
        if name=='inagaki':
            a=-1+.6*np.exp(-4*t);b=1-.6*np.exp(-4*t)
            ax[1].plot(t,a,color='#0072B2');ax[1].plot(t,b,color='#D55E00')
            ax[1].set(xlabel='Synthetic time',ylabel='Synthetic coordinate',title='SYNTHETIC illustration; method tests separate\nno author model runtime or experimental data')
            with np.load(root/'lds_results/one_hot'/npz) as z:
                for i in z['coding_pair_trial_indices']:ax[2].plot(z['times_ms'],z['coding_coordinate'][i])
            ax[2].set(xlabel='LDS extension time (ms)',ylabel='Pairwise CD coordinate',title='LDS adaptation — actual recorded states\nnot experimental ALM reproduction')
        else:
            control=np.c_[t,np.sin(t)];pert=control+np.exp(-8*t)[:,None]*[.2,.3]
            im=ax[1].imshow(cross_temporal_distance(control,pert),origin='lower',aspect='auto');fig.colorbar(im,ax=ax[1],shrink=.6)
            ax[1].set(xlabel='Synthetic perturbed sample',ylabel='Synthetic control sample',title='Methods unit check: full-state cdist\nSYNTHETIC; missing author Figure7 pipeline')
            with np.load(root/'lds_results/one_hot'/npz) as z:
                im=ax[2].imshow(z['cross_temporal_distance'],origin='lower',aspect='auto');fig.colorbar(im,ax=ax[2],shrink=.6)
            ax[2].set(xlabel='Perturbed sample',ylabel='Control sample',title='LDS adaptation — actual paired input assay\nnot trained-network reproduction')
        fig.suptitle('Source → reconstructed method check → LDS adaptation | methods/data differences remain explicit')
        paths=save_figure(fig,folder,f'{name}_SOURCE_VS_REPRODUCTION_VS_LDS')
        records.append(dict(paper=name,paths=paths,middle=('synthetic illustration; method tests separate' if name=='inagaki' else 'synthetic Euclidean method validation')+', not original-data reproduction',publication='private source comparison; do not publish copyrighted panels'))
    dump(root/'audit/source_comparison_manifest.json',records)


if __name__=='__main__':run()
