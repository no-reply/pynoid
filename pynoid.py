from random import randint

DIGIT = ['0','1','2','3','4','5','6','7','8','9']
XDIGIT = DIGIT + ['b','c','d','f','g','h','j','k','m','n','p','q','r','s','t','v','w','x','z']
GENTYPES = ['r', 's', 'z']
DIGTYPES = ['d', 'e']
SHORT = '.shrt.'
VERSION = 'pynoid 0.1'


def mint(template='zek', n=None, scheme=None, naa=None):
    ''' Mint identifiers according to template with a prefix of scheme + naa.

    Template is of form [mask] or [prefix].[mask] where prefix is any URI-safe string and mask is a string of any combination 'e' and 'd', optionally beginning with a mint order indicator ('r'|'s'|'z') and/or ending with a checkdigit ('k'):
    
    Example Templates:
    d      : 0, 1, 2, 3
    zek    : 00, xt, 3f0, 338bh
    123.zek: 123.00, 123.xt, 123.3f0, 123.338bh
    seddee : 00000, k50gh, 637qg
    seddeek: 000000, k06178, b661qj

    The result is appended to the scheme and naa as follows: scheme + naa + '/' + [id].

    There is no checking to ensure ids are not reminted. Instead, minting can be controlled by supplying a (int) value for 'n'. It is possible to implement ordered or random minting from available ids by manipulnating this number from another program. If no 'n' is given, minting is random from within the namespace. An indicator is added between '/' and [id] to mark these ids as for short term testing only. An override may be added later to accommodate applications which don't mind getting used ids. 
nn
    A note about 'r', 's', and 'z': 'z' indicates that a namespace should expand on its first element to accommodate any 'n' value (eg. 'de' becomes 'dde' then 'ddde' as numbers get larger). That expansion can be handled by this method. 'r' and 's' (typically meaning 'random' and 'sequential') are recognized as valid values, but ignored and must be implemented elsewhere.
    '''

    if '.' in template:
        prefix, mask = template.rsplit('.', 1)
    else:
        mask = template
        prefix = ''

    try:
        __validateMask(mask)
    except:
        raise

    if n == None:
        if mask[0] in (GENTYPES):
            mask = mask[1:]
        # If we hit this point, this is a random (and therefore, short-term) identifier. 
        prefix = SHORT + prefix
        n = randint(0, __getTotal(mask) -1)

    noid = prefix + __n2xdig(n, mask)
    if naa:
        noid = naa.strip('/') + '/' + noid
    if template[-1] == 'k':
        noid += __checkdigit(noid)
    if scheme:
        noid = scheme + noid

    return noid


def validate(s):
    '''Checks if the final character is a valid checkdigit for the id. Will fail for ids with no checkdigit.

    This will also attempt to strip scheme strings (eg. 'doi:', 'ark:/') from the beginning of the string. This feature is limited, however, so if you haven't tested with your particular namespace, it's best to pass in ids with that data removed.

    Returns True on success, ValidationError on failure.
    '''
    if not __checkdigit(s[0:-1]) == s[-1]:
        raise ValidationError("Noid check character '" + s[-1] + "' doesn't match up for '" + s + "'.")
    return True


def version():
    '''Returns the current version of the pynoid software.
    '''
    return VERSION


def __n2xdig(n, mask):
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
        c = mask[1]
        while n > 0:
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


def __validateMask(mask):
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


def __getTotal(mask):
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
        

def __checkdigit(s):
    # TODO: Fix checkdigit to autostrip scheme names shorter or longer than 3 chars.
    try:
        if s[3] == ':':
            s = s[4:].lstrip('/')
    except IndexError:
        pass
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
