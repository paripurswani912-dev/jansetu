import difflib
from models import Person
from normalize import name_key

LINK_THRESHOLD = 0.80


def name_score(a: str, b: str) -> float:
    if a == b:
        return 1.0
    ta, tb = a.split(), b.split()
    # "r kumar" vs "ramesh kumar": same surname, first name is an initial
    if len(ta) == len(tb) and len(ta) > 1 and ta[-1] == tb[-1]:
        ok = all(x == y
                 or (len(x) == 1 and y.startswith(x))
                 or (len(y) == 1 and x.startswith(y))
                 for x, y in zip(ta, tb))
        if ok:
            return 0.88
    return round(difflib.SequenceMatcher(None, a, b).ratio(), 2)


def score(person: Person, cand_name: str, cand_dob: str):
    """Compare an incoming Person with an existing citizen.
    Returns (confidence, match_type)."""
    ns = name_score(person.name_key, name_key(cand_name))
    same_dob = person.dob is not None and person.dob == cand_dob
    conf = ns if same_dob else round(ns * 0.5, 2)
    if conf >= 1.0:
        return conf, "EXACT"
    if conf >= LINK_THRESHOLD:
        return conf, "FUZZY"
    return conf, "NO_MATCH"