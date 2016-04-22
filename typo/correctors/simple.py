# -*- coding: utf-8 -*-
import logging
from collections import defaultdict, namedtuple

import Levenshtein
import marshal
from utils import register_typo

logger = logging.getLogger(__name__)

WordTuple = namedtuple('WordTuple', 'keyword, docs, hits, offset')


ONE_LETTER_IN_LAST_WORD = False # XXX make configurable


@register_typo
class TypoDefault(object):
    """ Bases on levenshtein_simple.py """
    typo_name = 'default'

    def __init__(self, index):
        self.filename = index
        self.reload()

    def reload(self):
        # load self.good_words, self.reverse, self.weights, self.corpus from marshal
        for (key, item) in marshal.loads(open(self.filename).read()).items():
            setattr(self, key, item)

    def find_candidates(self, word, max_candidates=3, skip_distance=3, is_last=False):

        candidates = defaultdict(list)
        better_candidates = []

        if word in self.good_words:
            return [word]

        def _ignore_candidate(cword):
            # do not reduce last word to one letter
            return (not ONE_LETTER_IN_LAST_WORD and is_last and \
                    len(cword) == 1 and len(word) > 1 and cword.isalpha())

        # check if two words are sticked together
        for i in range(1, len(word)):
            prefix, postfix = word[:i], word[i:]

            good_prefix = prefix in self.good_words or prefix.isdigit()
            good_postfix = postfix in self.good_words or postfix.isdigit()
            if good_prefix and good_postfix:
                weight_prefix = self.weights[prefix]
                weight_postfix = self.weights[postfix]

                cword = " ".join([prefix, postfix])
                cweight = ((skip_distance - 1) << 32) + (weight_prefix + weight_postfix) / 2
                candidates[1].append((cword, cweight))

        # handle the first letter
        # absent
        if word in self.reverse:
            cword, weight = self.reverse[word]
            cweight = ((skip_distance - 1) << 32) + weight
            candidates[1].append((cword, cweight))

        # changed
        key = word[1:]
        if key in self.reverse:
            cword, weight = self.reverse[key]
            cweight = ((skip_distance - 1) << 32) + weight
            candidates[1].append((cword, cweight))
        # added
        if key in self.good_words:
                weight = self.weights[key]
                cweight = ((skip_distance - 1) << 32) + weight
                candidates[1].append((key, cweight))

        # find all candidates which has distance <= skip_distance
        key = ord(word[0])
        if key in self.corpus:
            for cword, weight in self.corpus[key].items():
                if abs(len(cword) - len(word)) > skip_distance: # small optimization
                    continue
                d = Levenshtein.distance(cword, word)
                if d > skip_distance:
                    continue
                cweight = ((skip_distance - d) << 32) + weight
                candidates[d].append((cword, cweight))

        if not candidates:
            return []

        # now find the better ones
        for i in range(1, skip_distance + 1):
            better_candidates += candidates[i]
            if len(better_candidates) >= max_candidates:
                break

        # return the best
        # XXX rewrite without sort
        better_candidates.sort(key=lambda x: x[1], reverse=True)
        better_candidates = [cword for cword, cweight in better_candidates if not _ignore_candidate(cword)]
        return better_candidates[:max_candidates]

    def split_chunks(self, phrase):
        chunks = []
        chunk = ''
        mode = None

        for c in phrase:
            c = c.lower()
            # XXX rewrite in pythonic way
            flag = c.isalpha() | (c.isdigit() << 1)
            if mode is None:
                mode = flag
                chunk = c
                continue

            if bool(mode) ^ bool(flag):
                chunks.append((chunk, mode))
                chunk = c
                mode = flag
            else:
                chunk += c
                mode |= flag

        if chunk:
            chunks.append((chunk, mode))
        return chunks

    def suggestion(self, phrase):
        chunks = self.split_chunks(phrase)
        suggestion = ''
        suggestion_valid = True

        for i, (chunk, mode) in enumerate(chunks):
            is_last = i == len(chunks) - 1
            if mode and mode != 2:
                candidate = self.find_candidates(chunk,
                                                 max_candidates=1,
                                                 skip_distance=2,
                                                 is_last=is_last)
                if candidate:
                    suggestion += candidate[0]
                else:
                    suggestion += chunk
                    suggestion_valid = False
            else:
                suggestion += chunk

        return suggestion, suggestion_valid

    @classmethod
    def convert(cls, items):
        # XXX what is this??
        corpus = defaultdict(dict, {})
        reverse = {}
        weights = {}
        words = []
        for item in items:
            word = item.keyword
            weight = int(item.hits)
            first_byte = ord(word[0])
            corpus[first_byte][word] = weight
            words.append(word)

            weights[word] = weight
            if len(word) < 2:
                continue

            second_char = word[1:]
            if second_char not in reverse or weight > reverse[second_char][1]:
                reverse[second_char] = (word, weight)

        good_words = set(words)
        return dict(
            good_words=good_words,
            reverse=reverse,
            weights=weights,
            corpus=dict(corpus)
        )

