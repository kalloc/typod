# -*- coding: utf-8 -*-
import logging
from collections import defaultdict, namedtuple

import Levenshtein
import marshal
from utils import register_typo
from functools import partial

logger = logging.getLogger(__name__)

ONE_LETTER_IN_LAST_WORD = False # XXX make configurable

GOOD_PARTICLES = {
    'ru': {u'у', u'к', u'а', u'а', u'о', u'я', u'с', u'и'},
    'en': {u'a', 'i'},
    }


@register_typo
class TypoDefault(object):
    """ Bases on levenshtein_simple.py """
    typo_name = 'default'
    max_candidates = 1

    def __init__(self, index, max_candidates=1, lang='ru'):
        self.filename = index
        self.reload()
        self.max_candidates = max_candidates
        self.lang = lang
        self.good_particles = GOOD_PARTICLES.get(self.lang, [])

    def reload(self):
        # load self.good_words, self.reverse, self.weights, self.corpus from marshal
        for (key, item) in marshal.loads(open(self.filename).read()).items():
            setattr(self, key, item)

    def calc_cweight(self, d, skip, w, word):
        if skip < d: return 0
        return  ((skip - d) << 32) + w

    def ignore_candidate(self, is_last, word, cword):
        if len(cword) == 1:
            # do not reduce last word to one letter
            if not ONE_LETTER_IN_LAST_WORD and is_last:
            
                if len(word) == 1 or cword.isalpha():
                    return True

            if cword.isalpha() and cword not in self.good_particles:
                return True
        return False

    def handle_reverse(self, word, tail, candidates, skip_distance):
        # handle the first letter
        # absent
        if tail in self.reverse:
            for cword, weight in self.reverse[tail]:
                d = Levenshtein.distance(cword, word)
                if d > skip_distance:
                    continue
                cweight = self.calc_cweight(d, skip_distance, weight, word)
                candidates[d].append((cword, cweight))

    def return_as_is(self, word):
        return [(word, 1)]

    def find_candidates(self, word, max_candidates=3, skip_distance=3, is_last=False):
        skip_distance = max(min(skip_distance, len(word) // 2), 1)

        candidates = defaultdict(list)

        if word in self.good_words:
            return self.return_as_is(word)

        _ignore_candidate = partial(self.ignore_candidate, is_last, word)

        # check if two words are sticked together
        for i in range(1, len(word)):
            prefix, postfix = word[:i], word[i:]

            good_prefix = prefix in self.good_words or prefix.isdigit()
            good_postfix = postfix in self.good_words or postfix.isdigit()
            if good_prefix and good_postfix:
                if not _ignore_candidate(postfix) and not self.ignore_candidate(False, word, prefix):
                    weight_prefix = self.weights[prefix]
                    weight_postfix = self.weights[postfix]
                    weight = (weight_prefix + weight_postfix) / 2

                    cword = " ".join([prefix, postfix])
                    cweight = self.calc_cweight(1, skip_distance, weight, word)
                    candidates[1].append((cword, cweight))

        # handle the first letter
        # absent
        self.handle_reverse(word, word, candidates, skip_distance)

        # changed
        tail = word[1:]
        self.handle_reverse(word, tail, candidates, skip_distance)
        # changed and swiped
        self.handle_reverse(word, word[:1] + word[2:], candidates, skip_distance)
        # added
        if tail in self.good_words:
            weight = self.weights[tail]
            cweight = self.calc_cweight(1, skip_distance, weight, word)
            candidates[1].append((tail, cweight))

        # find all candidates which has distance <= skip_distance
        key = ord(word[0])
        if key in self.corpus:
            for cword, weight in self.corpus[key].items():
                if abs(len(cword) - len(word)) > skip_distance: # small optimization
                    continue
                d = Levenshtein.distance(cword, word)
                if d > skip_distance:
                    continue
                cweight = self.calc_cweight(d, skip_distance, weight, word)
                candidates[d].append((cword, cweight))

        if _ignore_candidate(word) and len(word) == 1:
            cweight = self.calc_cweight(1, skip_distance, 1, word)
            candidates[1].append(('', cweight))

        return self.better_candidates(candidates, skip_distance, max_candidates, is_last, word)

    def better_candidates(self, candidates, skip_distance, max_candidates, is_last, word):
        if not candidates:
            return []

        better_candidates = []
        _ignore_candidate = partial(self.ignore_candidate, is_last, word)

        # now find the better ones
        for i in range(1, skip_distance + 1):
            better_candidates += candidates[i]
            if len(better_candidates) >= max_candidates:
                break

        # return the best
        better_candidates.sort(key=lambda x: x[1], reverse=True)
        max_weight = better_candidates[0][1]
        better_candidates = [(cword, cweight * 100 / max_weight) for cword, cweight
                             in better_candidates if not _ignore_candidate(cword)]
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
        suggestions = []
        suggestion_valid = True

        for i, (chunk, mode) in enumerate(chunks):
            is_last = i == len(chunks) - 1
            if mode and mode != 2:
                max_candidates = self.max_candidates if len(chunks) > 1 else 1
                candidate = self.find_candidates(chunk,
                                                 max_candidates=max_candidates,
                                                 skip_distance=2,
                                                 is_last=is_last)
                if candidate:
                    suggestions.append(candidate)
                else:
                    suggestions.append([(chunk, 1)])
                    suggestion_valid = False
            else:
                suggestions.append([(chunk, 1)])

        return suggestions, suggestion_valid

    @classmethod
    def convert(cls, items):
        # return a dict to be dumped as marshal structure
        # the items of dict will be set as attributes of corrector item
        corpus = defaultdict(dict, {})
        reverse = defaultdict(list)
        reverse_set = defaultdict(set)
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

            tail = word[1:]
            if word not in reverse_set[tail]:
                reverse[tail].append((word, weight))
                reverse_set[tail].add(word)

            tail = word[:1] + word[2:]
            if word not in reverse_set[tail]:
                reverse[tail].append((word, weight))
                reverse_set[tail].add(word)

        good_words = set(words)
        return dict(
            good_words=good_words,
            reverse=dict(reverse),
            weights=weights,
            corpus=dict(corpus)
        )

