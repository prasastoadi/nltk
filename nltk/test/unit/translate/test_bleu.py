# -*- coding: utf-8 -*-
"""
Tests for BLEU translation evaluation metric
"""

import functools
import io
import unittest

from nltk.data import find
from nltk.translate.bleu_score import modified_precision, brevity_penalty, closest_ref_length
from nltk.translate.bleu_score import sentence_bleu, corpus_bleu, SmoothingFunction


class TestBLEU(unittest.TestCase):
    def test_modified_precision(self):
        """
        Examples from the original BLEU paper
        http://www.aclweb.org/anthology/P02-1040.pdf
        """
        # Example 1: the "the*" example.
        # Reference sentences.
        ref1 = 'the cat is on the mat'.split()
        ref2 = 'there is a cat on the mat'.split()
        # Hypothesis sentence(s).
        hyp1 = 'the the the the the the the'.split()

        references = [ref1, ref2]

        # Testing modified unigram precision.
        hyp1_unigram_precision =  float(modified_precision(references, hyp1, n=1))
        assert (round(hyp1_unigram_precision, 4) == 0.2857)
        # With assertAlmostEqual at 4 place precision.
        self.assertAlmostEqual(hyp1_unigram_precision, 0.28571428, places=4)

        # Testing modified bigram precision.
        assert(float(modified_precision(references, hyp1, n=2)) == 0.0)


        # Example 2: the "of the" example.
        # Reference sentences
        ref1 = str('It is a guide to action that ensures that the military '
                   'will forever heed Party commands').split()
        ref2 = str('It is the guiding principle which guarantees the military '
                   'forces always being under the command of the Party').split()
        ref3 = str('It is the practical guide for the army always to heed '
                   'the directions of the party').split()
        # Hypothesis sentence(s).
        hyp1 = 'of the'.split()

        references = [ref1, ref2, ref3]
        # Testing modified unigram precision.
        assert (float(modified_precision(references, hyp1, n=1)) == 1.0)

        # Testing modified bigram precision.
        assert(float(modified_precision(references, hyp1, n=2)) == 1.0)


        # Example 3: Proper MT outputs.
        hyp1 = str('It is a guide to action which ensures that the military '
                   'always obeys the commands of the party').split()
        hyp2 = str('It is to insure the troops forever hearing the activity '
                   'guidebook that party direct').split()

        references = [ref1, ref2, ref3]

        # Unigram precision.
        hyp1_unigram_precision = float(modified_precision(references, hyp1, n=1))
        hyp2_unigram_precision = float(modified_precision(references, hyp2, n=1))
        # Test unigram precision with assertAlmostEqual at 4 place precision.
        self.assertAlmostEqual(hyp1_unigram_precision, 0.94444444, places=4)
        self.assertAlmostEqual(hyp2_unigram_precision, 0.57142857, places=4)
        # Test unigram precision with rounding.
        assert (round(hyp1_unigram_precision, 4) == 0.9444)
        assert (round(hyp2_unigram_precision, 4) == 0.5714)

        # Bigram precision
        hyp1_bigram_precision = float(modified_precision(references, hyp1, n=2))
        hyp2_bigram_precision = float(modified_precision(references, hyp2, n=2))
        # Test bigram precision with assertAlmostEqual at 4 place precision.
        self.assertAlmostEqual(hyp1_bigram_precision, 0.58823529, places=4)
        self.assertAlmostEqual(hyp2_bigram_precision, 0.07692307, places=4)
        # Test bigram precision with rounding.
        assert (round(hyp1_bigram_precision, 4) == 0.5882)
        assert (round(hyp2_bigram_precision, 4) == 0.0769)

    def test_brevity_penalty(self):
        # Test case from brevity_penalty_closest function in mteval-v13a.pl.
        # Same test cases as in the doctest in nltk.translate.bleu_score.py
        references = [['a'] * 11, ['a'] * 8]
        hypothesis = ['a'] * 7
        hyp_len = len(hypothesis)
        closest_ref_len =  closest_ref_length(references, hyp_len)
        self.assertAlmostEqual(brevity_penalty(closest_ref_len, hyp_len), 0.8669, places=4)

        references = [['a'] * 11, ['a'] * 8, ['a'] * 6, ['a'] * 7]
        hypothesis = ['a'] * 7
        hyp_len = len(hypothesis)
        closest_ref_len =  closest_ref_length(references, hyp_len)
        assert brevity_penalty(closest_ref_len, hyp_len) == 1.0

    def test_zero_matches(self):
        # Test case where there's 0 matches
        references = ['The candidate has no alignment to any of the references'.split()]
        hypothesis = 'John loves Mary'.split()

        # Test BLEU to nth order of n-grams, where n is len(hypothesis).
        for n in range(1,len(hypothesis)):
            weights = [1.0/n] * n # Uniform weights.
            assert(sentence_bleu(references, hypothesis, weights) == 0)

    def test_full_matches(self):
        # Test case where there's 100% matches
        references = ['John loves Mary'.split()]
        hypothesis = 'John loves Mary'.split()

        # Test BLEU to nth order of n-grams, where n is len(hypothesis).
        for n in range(1,len(hypothesis)):
            weights = [1.0/n] * n # Uniform weights.
            assert(sentence_bleu(references, hypothesis, weights) == 1.0)

    def test_partial_matches_hypothesis_longer_than_reference(self):
        references = ['John loves Mary'.split()]
        hypothesis = 'John loves Mary who loves Mike'.split()
        self.assertAlmostEqual(sentence_bleu(references, hypothesis), 0.4729, places=4)


#@unittest.skip("Skipping fringe cases for BLEU.")
class TestBLEUFringeCases(unittest.TestCase):

    def test_case_where_n_is_bigger_than_hypothesis_length(self):
        # Test BLEU to nth order of n-grams, where n > len(hypothesis).
        references = ['John loves Mary ?'.split()]
        hypothesis = 'John loves Mary'.split()
        n = len(hypothesis) + 1 #
        weights = [1.0/n] * n # Uniform weights.
        self.assertAlmostEqual(sentence_bleu(references, hypothesis, weights), 0.7165, places=4)

        # Test case where n > len(hypothesis) but so is n > len(reference), and
        # it's a special case where reference == hypothesis.
        references = ['John loves Mary'.split()]
        hypothesis = 'John loves Mary'.split()
        assert(sentence_bleu(references, hypothesis, weights) == 1.0)

    def test_empty_hypothesis(self):
        # Test case where there's hypothesis is empty.
        references = ['The candidate has no alignment to any of the references'.split()]
        hypothesis = []
        assert(sentence_bleu(references, hypothesis) == 0)

    def test_empty_references(self):
        # Test case where there's reference is empty.
        references = [[]]
        hypothesis = 'John loves Mary'.split()
        assert(sentence_bleu(references, hypothesis) == 0)

    def test_empty_references_and_hypothesis(self):
        # Test case where both references and hypothesis is empty.
        references = [[]]
        hypothesis = []
        assert(sentence_bleu(references, hypothesis) == 0)


class TestBLEUvsMteval13a(unittest.TestCase):

    def test_corpus_bleu(self):
        ref_file = find('models/wmt15_eval/ref.ru')
        hyp_file = find('models/wmt15_eval/google.ru')
        mteval_output_file = find('models/wmt15_eval/mteval-13a.output')

        # Reads the BLEU scores from the `mteval-13a.output` file.
        # The order of the list corresponds to the order of the ngrams.
        with open(mteval_output_file, 'r') as mteval_fin:
            # The numbers are located in the last 2nd line of the file.
            # The first and 2nd item in the list are the score and system names.
            mteval_bleu_scores = map(float, mteval_fin.readlines()[-2].split()[1:-1])

        with io.open(ref_file, 'r', encoding='utf8') as ref_fin:
            with io.open(hyp_file, 'r', encoding='utf8') as hyp_fin:
                # Whitespace tokenize the file.
                # Note: split() automatically strip().
                hypothesis = map(lambda x: x.split(), hyp_fin)
                # Note that the corpus_bleu input is list of list of references.
                references = map(lambda x: [x.split()],ref_fin)
                # Without smoothing.
                for i, mteval_bleu in zip(range(1,10), mteval_bleu_scores):
                    nltk_bleu = corpus_bleu(references, hypothesis, weights=(1.0/i,)*i)
                    # Check that the BLEU scores difference is less than 0.005 .
                    # Note: This is an approximate comparison; as much as
                    #       +/- 0.01 BLEU might be "statistically significant",
                    #       the actual translation quality might not be.
                    assert abs(mteval_bleu - nltk_bleu) < 0.005

                # With the same smoothing method used in mteval-v13a.pl
                chencherry = SmoothingFunction()
                for i, mteval_bleu in zip(range(1,10), mteval_bleu_scores):
                    nltk_bleu = corpus_bleu(references, hypothesis,
                                            weights=(1.0/i,)*i,
                                            smoothing_function=chencherry.method3)
                    assert abs(mteval_bleu - nltk_bleu) < 0.005
