from os import makedirs
from os.path import curdir, join, realpath
from datetime import date
from bsddb3 import db

DIGIT = range(10)
XDIGIT = ['0','1','2','3','4','5','6','7','8','9','b','c','d','f','g',
          'h','j','k','m','n','p','q','r','s','t','v','w','x','z']
SEQNUM_MIN = 1
SEQNUM_MAX = 1000000
NOLIMIT = -1
GENTYPES = {'r': 'random', 's': 'sequential', 'z': 'sequential'}
MASKS = ['e','d']
HOWS = ['new', 'replace', 'set', 'append', 'prepend', 'add', 'insert', 
        'delete', 'purge', 'mint', 'peppermint']
R = ':/' # admin variable prefix
DBNAME = 'noid.bdb'
VERSION = 'pynoid 0.1'


def dbCreate(dbdir=None, template=".zd", term="medium", NAAN=None, NAA=None, SubNAA=None):
    # try to make a new 
    if not dbdir:
        dbdir = curdir
    dbdir = join(dbdir, 'NOID')
    try:
        makedirs(dbdir)
        # TODO: add log files & implement logging @ parity w/ perl implementation
    except OSError as (errno, strerror):
        print "Minter could not be created at:", realpath(dbdir), ' One may already exist. --', strerror
    except:
        raise

    # set template parts and validate template
    if not ('.' in template):
        raise InvalidTemplateError("Template must contain exactly one '.' character to seperate the prefix from the mask.")
    try:
        prefix, mask = template.split('.')
    except ValueError:
        raise InvalidTemplateError("Template must contain exactly one '.' character to seperate the prefix from the mask.")
    if NAAN:
        firstpart = NAAN + '/' + prefix
    else:
        firstpart = prefix
    genonly = False
    if not (mask[0] in GENTYPES):
        raise InvalidTemplateError("Generator Type must be one of" + str(GENTYPES))
    else:
        gen = GENTYPES[mask[0]]

    if (not all([x in MASKS for x in mask[1:-1]])) or not (mask[-1] in MASKS or mask[-1] == 'k'): 
        raise InvalidTemplateError("Template mask characters must be one of" + str(MASKS) + "orfinal 'k' for checkdigit.")

    # everything looks good, create the database
    noiddb = db.DB()
    noiddb.open(join(dbdir, DBNAME), DBNAME, db.DB_HASH, db.DB_CREATE)

    # write properties to db    
    total = _getTotal(mask)
    if total == NOLIMIT:
        padwidth = 16 + len(mask)
    else:
        padwidth = 2 + len(mask)

    properties = dict([
        ('naa', NAA), ('naan', NAAN), ('subnaa', SubNAA),
        ('longterm', (term == 'long')), ('wrap', (term == 'short')),
        ('template', template), ('prefix', prefix), ('mask', mask), ('firstpart', firstpart),
        ('addcheckchar', (mask[-1] == 'k')), ('generator_type', gen), ('genonly', genonly),
        ('limit', total), ('padwidth', padwidth),
        ('oacounter', 0), ('oatop', total), ('held', 0), ('queued', 0),
        ('fseqnum', SEQNUM_MIN), ('gseqnum', SEQNUM_MIN), ('gseqnum_date', 0),
        ('version', VERSION)
        ])

    for key in properties.keys():
        noiddb.put(R + key, str(properties[key]))

    noiddb.close()

               
def mint(dbdir=None):
    if not dbdir:
        dbdir = curdir
    dbdir = join(dbdir, 'NOID')
    # get some variables from the db
    noiddb = db.DB()
    noiddb.open(join(dbdir, DBNAME), DBNAME, db.DB_HASH)
    props = _getProperties(noiddb)
    # has the counter reached the limit?
    if (props['limit'] != NOLIMIT) and (props['counter'] >= props['limit']):
        # we're out of space. What do we do?
        if props['longterm'] or (not wrap):
            # panic. (if we aren't minting shortterm)
            raise NamespaceError("Identifiers exhusted; stopped at " + limit)
        else:
            # or reset counters. (if we are minting shortterm)
            props['gen'] = noiddb.get(R + 'generator_type')
            if props['gen'] == GENTYPES['s']:
                props['counter'] = 0
            else:
                _initCounters(noiddb)
    # Counter is lower than limit (& may have been reset).
    if props['gen'] == GENTYPES['r']:
        # mint quasi-randomly
        # TODO: implement quasi-random minting
        n = props['counter']
    else:
        # mint sequentially
        n = props['counter']

    noid = _n2xdig(n, props['mask'])
    props['counter'] += 1
    noiddb.put(R + 'oacounter', str(props['counter']))

    noid = props['prefix'] + noid
    if props['check']:
        noid += checkdigit(noid)
    setCircRec(noid)
    return noid


def bind(noid, element, value, dbdir=None):
    if not dbdir:
        dbdir = curdir
    dbdir = join(dbdir, 'NOID')
    noiddb = db.DB()
    noiddb.open(join(dbdir, DBNAME), DBNAME, db.DB_HASH)
    # write the binding
    noiddb.put(noid, uri)

# validation is very limited and assumes checkchar is on.
# this is really only for dev testing, not a true validation method yet.
# TODO: make a proper validation method
def validate(noid, dbdir=None):
    if not checkdigit(noid[0:-1]) == noid[-1]:
        raise ValidationError("Noid check character doesn't match up for [" + noid + "].")
    return True


def checkdigit(s):
    def ordinal(x):
        try: return XDIGIT.index(x)
        except: return 0
    return XDIGIT[sum([x * (i+1) for i, x in enumerate(map(ordinal,s))]) % len(XDIGIT)]


def setCircRec(noid):
    pass


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


def _getProperties(noiddb):
    def s2bool(s): return s == 'True' 
    return {
        'counter': int(noiddb.get(R + 'oacounter')),
        'mask': noiddb.get(R + 'mask'),
        'limit': int(noiddb.get(R + 'oatop')),
        'longterm': s2bool(noiddb.get(R + 'longterm')),
        'wrap': s2bool(noiddb.get(R + 'wrap')),
        'check': s2bool(noiddb.get(R + 'addcheckchar')),
        'gen': noiddb.get(R + 'generator_type'),
        'prefix': noiddb.get(R + 'prefix'),
        'activeCount': noiddb.get(R + 'saclist'),
        'inactiveCount': noiddb.get(R + 'siclist')
        }


def _initCounters(noiddb):
    maxcounters = 293     # prime.
    oacounter = 0
    total = noiddb.get(R + 'limit')
    percounter = (total / maxcounters + 1)
    saclist = ''
    counters = {}
    n, t = 0, total
    while t > 0:
        if t >= percounter:
            counters[n] = percounter
        else: 
            counters[n] = t
        saclist += "c" + str(n) + " "
        t -= percounter
        n += 1

    for key in counters.keys():
        cname = R + "c" + key + "/"
        top, value = counters[key]
        noiddb.put(cname + 'top', str(top))
        noiddb.put(cname + 'value', '0')
    
    properties = {
        'oacounter': oacounter,
        'percounter': percounter,
        'saclist': saclist, 
        'siclist': ''
        }
    for key in properties.keys():
        noiddb.put(R + key, str(properties[key]))


def _getTotal(mask):
    if mask[0] == 'z':
        total = NOLIMIT
    else:
        total = 1
        for c in mask[1:]:
            if c == 'e':
                total *= len(XDIGIT)
            elif c == 'd':
                total *= len(DIGIT)
    return total            
        


class InvalidTemplateError(Exception):
    pass

class ValidationError(Exception):
    pass

class NamespaceError(Exception):
    pass
