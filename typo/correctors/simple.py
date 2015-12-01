# -*- coding: utf-8 -*-
import logging
from collections import defaultdict, namedtuple

import Levenshtein
import marshal
from utils import register_typo

logger = logging.getLogger(__name__)

WordTuple = namedtuple('WordTuple', 'keyword, docs, hits, offset')


@register_typo
class TypoDefault(object):
    """ Bases on levenshtein_simple.py """
    typo_name = 'default'

    def __init__(self, index):
        self.filename = index
        self.reload()

    def reload(self):
        for (key, item) in marshal.loads(open(self.filename).read()).items():
            setattr(self, key, item)

    def find_candidates(self, word, max_candidates=3, skip_distance=3):

        candidates = defaultdict(list)
        better_candidates = []

        if word in self.good_words:
            return [word]

        # check if two words together
        for i in range(1, len(word)):
            prefix, postfix = word[:i], word[i:]
            if prefix in self.good_words and postfix in self.good_words:
                weight_prefix = self.weights[prefix]
                weight_postfix = self.weights[postfix]
                candidates[1].append((" ".join([prefix, postfix]),
                                      ((skip_distance - 1) << 32) + (weight_prefix + weight_postfix) / 2))

        # handle the first letter
        # absent
        if word in self.reverse:
            cword, weight = self.reverse[word]
            candidates[1].append((cword, ((skip_distance - 1) << 32) + weight))

        # changed
        key = word[1:]
        if key in self.reverse:
            cword, weight = self.reverse[key]
            candidates[1].append((cword, ((skip_distance - 1) << 32) + weight))
        # added
        if key in self.good_words:
            weight = self.weights[key]
            candidates[1].append((key, ((skip_distance - 1) << 32) + weight))

        # find all candidates which has distance <= skip_distance
        key = ord(word[0])
        if key in self.corpus:
            for w, weight in self.corpus[key].items():
                if abs(len(w) - len(word)) > skip_distance:  # small optimization
                    continue
                d = Levenshtein.distance(w, word)
                if d > skip_distance:
                    continue
                candidates[d].append((w, ((skip_distance - d) << 32) + weight))

        if not candidates:
            return []

        # now find the better ones
        for i in range(1, skip_distance + 1):
            better_candidates += candidates[i]
            if len(better_candidates) >= max_candidates:
                break

        # return the best
        better_candidates.sort(key=lambda x: x[1], reverse=True)
        return [x[0] for x in better_candidates[:max_candidates]]

    def suggestion(self, phrase):
        chunks = []
        chunk = ''
        suggestion = ''
        mode = None
        suggestion_valid = True

        for c in phrase:
            c = c.lower()
            flag = c.isalpha() or c.isdigit()
            if mode is None:
                mode = flag
                chunk = c
                continue

            if mode == flag:
                chunk += c
                continue
            else:
                chunks.append((chunk, mode))
                chunk = c
                mode = flag

        if chunk:
            chunks.append((chunk, mode))

        for chunk, mode in chunks:
            if mode:
                candidate = self.find_candidates(chunk, max_candidates=1, skip_distance=2)
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

