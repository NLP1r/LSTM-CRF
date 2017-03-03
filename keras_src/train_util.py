#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on 2017-02-20 16:54:20

@author: heshenghuan (heshenghuan@sina.com)
http://github.com/heshenghuan
"""

import sys
import numpy as np
import codecs as cs
import cPickle as pickle
from neural_lib import ArrayInit


def read_matrix_from_file(fn, dic, ecd='utf-8'):
    """
    Reads embedding matrix from file.

    ## Parameters
        fn: embeddings file path
        dic: a vocabulary stored words you need and their indices
        ecd: file encoding

    ## Return
        M:
            The embeddings matrix of shape(len(dic), emb_dim),
            this means M does not include all embeddings stored in fn.
            Only include the embeddings of words appeared in dic.
        idx_map:
            A dict stored the original line num of a word index that in dic.
            Might be useless.
    """
    # multiplier = np.sqrt(1.0 / 3)
    not_in_dict = 0
    with cs.open(fn, encoding=ecd, errors='ignore') as inf:
        row, column = inf.readline().rstrip().split()
        dim = int(column)
        # print row, column
        idx_map = dict()
        line_count = 0
        M = ArrayInit(ArrayInit.normal).initialize(len(dic) + 1, dim)
        for line in inf:
            elems = line.rstrip().split(' ')
            if elems[0] in dic:
                idx = dic[elems[0]]
                vec_elem = elems[1:]
                r = np.array([float(_e) for _e in vec_elem])
                # np.linalg.norm: 求范数
                # M[idx] = (r / np.linalg.norm(r)) * multiplier
                M[idx] = r
                idx_map[idx] = line_count
            else:
                not_in_dict += 1
            line_count += 1
        print 'load embedding! %s words,' % (row),
        print '%d not in the dictionary.' % (not_in_dict),
        print ' Dictionary size: %d' % (len(dic))
        # print M.shape, len(idx_map)
        return M, idx_map


def save_parameters(path, params):
    pickle.dump(params, open(path, 'w'))


def load_params(path, params):
    """
    Loads saved params of model, using cPickle to do save and load.
    """
    pp = pickle.load(open(path, 'r'))
    for kk, vv in pp.iteritems():
        print 'updating parameter:', kk
        params[kk] = pp[kk]
    return params


def conv_data(feature_arry, lex_arry, label_arry, win_size, feat_size):
    """
    Converts features, lexs, labels(all of them are lists of idxs) into
    int32 ndarray.
    """
    fv = []
    lexv = []
    labv = []
    for i, (f, x, y) in enumerate(zip(feature_arry, lex_arry, label_arry)):
        words = x  # _conv_x(x, M_emb, win_size)
        features = _conv_feat(f, feat_size)
        labels = _conv_y(y)
        fv.append(features)
        lexv.append(words)
        labv.append(labels)
    return fv, lexv, labv


def _conv_feat(x, feat_size):
    """
    Converts the features list into a int32 array.
    """
    lengths = [len(elem) for elem in x]
    max_len = max(lengths)
    features = np.ndarray(len(x), max_len).astype('int32')
    for i, feat in enumerate(x):
        fpadded = feat + [feat_size] * (max_len - len(feat))
        features[i] = fpadded
    return features


def _conv_y(y):
    """
    Converts the labels list to a int32 arrary.
    """
    labels = np.ndarray(len(y)).astype('int32')
    for i, label in enumerate(y):
        labels[i] = label
    return labels


def viterbi_decode(lb_probs, trans_matrix, init_matrix):
    """
    Viterbi algorithm to decode a best label sequence by given probability
    sequence.

    # Parameters
        lb_probs: a sequence of label probability of words
        trans_matrix: transition probability matrix
        init_matrix: initial probability matrix

    # Returns
        Returns the best label sequence.
    """
    # Note that 0 is a reserved state
    state_size = trans_matrix.shape[0]
    N = len(lb_probs)
    prb = 0.
    prb_max = 0.
    toward = np.zeros((N, state_size)) - np.inf
    backward = np.zeros((N, state_size), dtype='int32')

    # run viterbi
    for i in range(1, state_size):
        toward[0][i] = init_matrix[i] + lb_probs[0][i]
        backward[0][i] = -1

    # toward algorithm
    for t in range(1, N):
        for s in range(1, state_size):
            prb = -np.inf
            prb_max = -np.inf
            state_max = 1  # the index of 'O'
            for i in range(1, state_size):
                prb = toward[t - 1][i] + trans_matrix[i][s] + lb_probs[t][s]
                if prb > prb_max:
                    prb_max = prb
                    state_max = i
            toward[t][s] = prb_max
            backward[t][s] = state_max
    # backward algorithm
    index = N - 1
    taglist = []
    prb_max = -np.inf
    state_max = 0
    for s in range(1, state_size):
        prb = toward[N - 1][s]
        if prb > prb_max:
            prb_max = prb
            state_max = s
    taglist.append(state_max)
    while index >= 1:
        pre_state = backward[index][taglist[-1]]
        taglist.append(pre_state)
        index -= 1
    taglist.reverse()
    return taglist


def sequence_labeling(sntc, sntc_lens, trans_matrix=None, init_matrix=None,
                      ner_model=None):
    assert trans_matrix is not None, (
        "You must pass an instance of numpy.array which is the transition "
        + "probability matrix to this function's parameter 'trans_matrix'."
    )
    assert init_matrix is not None, (
        "You must pass an instance of numpy.array which is the initial "
        + "probability matrix to this function's parameter 'init_matrix'."
    )
    assert ner_model is not None, (
        "The NER-Model must be an instance of class which has a classmethod "
        + "named predict "
    )

    lb_probs = ner_model.predict(sntc, sntc_lens)
    labels = []
    for i in range(len(lb_probs)):
        lb_prob = lb_probs[i][0:sntc_lens[i]]
        labels.append(viterbi_decode(lb_prob, trans_matrix, init_matrix))
    return labels


def dict_from_argparse(apobj):
    return dict(apobj._get_kwargs())
