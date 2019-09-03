# init for 'sim' package : Discrete-event simulation
import copy
from collections import namedtuple, OrderedDict

from six import iteritems

#
# TODO: belongs in separate 'utils' submodule
#
class SlotsHolder(object):
    """
    A generic container of named slots.

    Like a dictionary with fixed keys, but with the syntax convenience of
    property (dot) access instead of indexing,
    e.g. "myobj.myprop" rather than "myobj['myprop']".
    Or... like a namedtuple, but mutable.

    Create a subclass with SlotsHolder.newtype(classname, slotnames).
    Implements printable forms (str + repr); copying (deepcopy) and comparison.

    """
    def __init__(self, *args, **kwargs):
        for key in self.__slots__:
            if len(args) > 0:
                val = args[0]
                args = args[1:]
            else:
                val = None
            setattr(self, key, val)
        for key, val in iteritems(kwargs):
            # keywords overwrite
            setattr(self, key, val)

    @staticmethod
    def newtype(classname, slot_names):
        """Return a new SlotsHolder subclass with given name + slots."""
        class InnerClass(SlotsHolder):
            __slots__ = slot_names  # needed during class creation, probably?

        InnerClass.__name__ = classname
        InnerClass.slot_names = slot_names[:]  # A public access to the names
        return InnerClass

    def as_odict(self):
        return OrderedDict([(key, getattr(self, key)) for key in self.__slots__])

    def __str__(self):
        selfdict = self.as_odict()
        datamsg = ', '.join(['{!s}={!r}'.format(key, val)
                             for key, val in iteritems(selfdict)])
        msg = '{!s}({!s})'.format(self.__class__.__name__, datamsg)
        return msg

    def __repr__(self):
        return str(self)

    def copy(self):
        return copy.deepcopy(self)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            result = False
        else:
            result = all(getattr(self, key) == getattr(other, key)
                         for key in self.__slots__)
        return result

    def __ne__(self, other):
        return not self == other
