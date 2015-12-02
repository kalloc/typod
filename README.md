# Typod
Spelling errors correction for the search engine (based on [sphinx]) on your site.

## What is it?

Typod is a missing spelling corrector for [sphinx], and it uses sphinx dictionary as source for spell checking


## What have we?

We have python classes for spell checking and a tcp interface to them


## How to use it?

You can use typod in your python application:
```
from typo import TypoDefault

TYPO = 'начь улеца фантан аптека бесмысленый и тусклий свед'.decode('utf8')
corrector = TypoDefault('examples/http/test.index')
corrected, ok = corrector.suggestion(TYPO)
print corrected
"""
ночь улица фонтан аптека бессмысленный и тусклый свет
"""
```
and you can use typod as service (TaaS)

```
x@y.z typod[master] $ python -m typo --corrector-index examples/http/test.index server --port 3333
INFO:typo.cmd_server:Run server on 0.0.0.0:3333, using default corrector
```


```
x@y.z typod[master] $ (echo QUERY начь улеца фантан аптека бесмысленый и тусклий свед;sleep 1) | nc localhost 3333
ночь улица фонтан аптека бессмысленный и тусклый свет
```
or

```
import socket

def suggest(query):
    sock = socket.socket()
    sock.settimeout(0.1)
    try:
        sock.connect(('localhost', 3333))
        sock.send('QUERY {}\n'.format(query.encode('utf-8')))
        data = sock.recv(4096).strip().decode('utf-8')
    except socket.error as e:
        # TODO: do something with connection error
        print e
        data = None
    except socket.timeout:
        data = None
    finally:
        sock.close()
    return data if data != query else query
    
print suggest('w0rd') # word
```


## How to make an index?

```
# Run indextool to dump a sphinx dictionary
se@goat $ indextool --dumpdict texts_index  > ~/dumpdict.txt

# copy to your machine
scp se@goat:~/dumpdict.txt .

# Convert a sphinx dictionary to typo index
x@y.z typod[master*] $ python -m typo --corrector-index typo.index convert --sphinx-dump dumpdict.txt
Convert indextool format to "TypoDefault" corrector format
Converting  [####################################]  100%
Export result to /usr/home/x/src/typod/typo.index
//EOE

# Test
x@y.z typod[master*] $ python -m typo --corrector-index typo.index console
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


## TODO
- support [n-gram]
- support [noisy_channel]
- support blocking-server
- support custom dictionaries
- add tests

[sphinx]: http://sphinxsearch.com/  "Sphinx Search"
[noisy_channel]: https://en.wikipedia.org/wiki/Noisy_channel_model "Noisy channel model"
[n-gram]: https://en.wikipedia.org/wiki/N-gram "N-gram"
