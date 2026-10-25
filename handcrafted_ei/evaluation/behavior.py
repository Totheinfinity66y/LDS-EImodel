import numpy as np


def accuracy(outputs, references):
    correct=np.asarray(outputs)==np.asarray(references)
    return {'sequences_correct':int(correct.all(axis=1).sum()),'n':len(correct),
            'stage_accuracy':correct.mean(axis=0).tolist()}
