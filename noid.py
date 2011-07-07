from random import randint

DIGIT = ['0','1','2','3','4','5','6','7','8','9']
XDIGIT = DIGIT + ['b','c','d','f','g',
          'h','j','k','m','n','p','q','r','s','t','v','w','x','z']
GENTYPES = {'r': 'random', 's': 'sequential', 'z': 'sequential'}
VERSION = 'pynoid 0.1'


def mint(template, n=None, scheme=None, naan=None):
    # template is of form 'prefix.mask' where prefix is any string 
    # and mask is a string of any combination 'e' and 'd',
    # optionally beginning with [r|s|z] and/or ending with 'k'
    if '.' in template:
        prefix, mask = template.rsplit('.', 1)
    else:
        mask = template
        prefix = ''

    try:
        _validateMask(mask)
    except:
        raise

    if not n:
        if mask[0] in GENTYPES:
            prefix = ':shrt:' + prefix
            mask = mask[1:]
        n = randint(0, _getTotal(mask))

    noid = prefix + _n2xdig(n, mask)
    if template[-1] == 'k':
        noid += _checkdigit(noid)

    if naan:
        noid = naan.strip('/') + noid
    if scheme:
        noid = scheme + noid

    return noid


def validate(noid):
    if not _checkdigit(noid[0:-1]) == noid[-1]:
        raise ValidationError("Noid check character '" + noid[-1] + "' doesn't match up for '" + noid + "'.")
    return True


def _n2xdig(n, mask):
    req = n
    xdig = ''
    for c in mask[::-1]:
        if c == 'e':
            div = len(XDIGIT)
        elif c == 'd':
            div = len(DIGIT)
        else:
            continue
        value = n % div
        n = n / div
        xdig += (XDIGIT[value])
        
    if mask[0] == 'z':
        while n > 0:
            c = mask[1]
            if c == 'e':
                div = len(XDIGIT)
            elif c == 'd':
                div = len(DIGIT)
            else:
                raise InvalidTemplateError("Template mask is corrupt. Cannot process character: " + c)
            value = n % div
            n = n / div
            xdig += (XDIGIT[value])
        
    # if there is still something left over, we've exceeded our namespace. 
    # checks elsewhere should prevent this case from ever evaluating true.
    if n > 0:
        raise NamespaceError("Cannot mint a noid for (counter = " + str(req) + ") within this namespace.")
    
    return xdig[::-1]


def _validateMask(mask):
    masks = ['e', 'd']
    checkchar = ['k']

    if not (mask[0] in GENTYPES or mask[0] in masks):
        raise InvalidTemplateError("Template is invalid.")
    elif not (mask[-1] in checkchar or mask[-1] in masks):
        raise InvalidTemplateError("Template is invalid.")
    else:
        for maskchar in mask[1:-1]:
            if not (maskchar in masks):
                raise InvalidTemplateError("Template is invalid.")

    return True         


def _getTotal(mask):
    if mask[0] == 'z':
        total = NOLIMIT
    else:
        total = 1
        for c in mask:
            if c == 'e':
                total *= len(XDIGIT)
            elif c == 'd':
                total *= len(DIGIT)
    return total            
        

def _checkdigit(s):
    def ordinal(x):
        try: return XDIGIT.index(x)
        except: return 0
    return XDIGIT[sum([x * (i+1) for i, x in enumerate(map(ordinal,s))]) % len(XDIGIT)]


class InvalidTemplateError(Exception):
    pass

class ValidationError(Exception):
    pass

class NamespaceError(Exception):
    pass

class BindingError(Exception):
    pass
