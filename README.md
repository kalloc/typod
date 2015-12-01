# Typod
Spelling errors correction for the search engine (based on [sphinx]) on your site.

## What is it?

Typod is a missing spelling correcter for [sphinx] and it uses sphinx dictionary as source for spell checking


## What we have?

We have python classes for spell checking and a tcp interface to them


## TODO
- support n-gram
- support noise channel model 
- support blocking-server
- support custom dictionaries

## How to use it?

We can use typo in your python application:
```
from typo import TypoDefault

TYPO = 'начь улеца фантан аптека бесмысленый и тусклий свед'.decode('utf8')
correcter = TypoDefault('examples/http/test.index')
corrected, is_converted = correcter.suggestion(TYPO)
print corrected
"""
ночь улица фонтан аптека бессмысленный и тусклый свет
"""
```
and you can use typo as service (TaaS)

```
x@y.z typod[master] $ python -m typo.cli --corrector-index examples/http/test.index server --port 3333
INFO:typo.cmd_server:Run server on 0.0.0.0:3333, using default corrector

x@y.z typod[master] $ (echo QUERY начь улеца фантан аптека бесмысленый и тусклий свед;sleep 1) | nc localhost 3333
ночь улица фонтан аптека бессмысленный и тусклый свет
```


## How to make an index?

```
# Run indextool to dump a sphinx dictionary
se@goat $ indextool --dumpdict texts_index  > ~/dumpdict.txt

# copy to your machine
scp se@goat:~/dumpdict.txt .

# Convert a sphinx dictionary to typo index
x@y.z typod[master*] $ python -m typo.cli --corrector-index typo.index convert --sphinx-dump dumpdict.txt
Convert indextool format to "TypoDefault" corrector format
Converting  [####################################]  100%
Export result to /usr/home/x/src/typod/typo.index
//EOE

# Test
x@y.z typod[master*] $ python -m typo.cli --corrector-index typo.index console
Phrase: w0rd
Result is word (True) spend time 0.000121, 216.26 mb usage
Phrase: ploy
Result is play (True) spend time 0.000217, 216.27 mb usage
Phrase: w0rld
Result is world (True) spend time 0.000109, 216.27 mb usage
```


## Special thanks:
- ashcan
- [sphinx]

[sphinx]: http://sphinxsearch.com/  "Sphinx Search"
