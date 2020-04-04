
from pdkb.rml import Literal

class Trust(Literal):

    # What do we actually want to take in / pass up to the superclass?
    def __init__(self, ag1, ag2, negate=False):
        Literal.__init__(self, "%s_trusts_%s" % (str(ag1), str(ag2)), negate)
        self.ag1 = ag1
        self.ag2 = ag2

    def negate(self):
        return Trust(self.ag1, self.ag2, not self.negated)

    def get_prop(self):
        return Trust(self.ag1, self.ag2)

def gen_trust_props(agents):
    for ag1 in agents:
        for ag2 in agents:
            yield Trust(ag1, ag2)
