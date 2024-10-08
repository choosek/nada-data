"""
Defines the NadaArray class
"""
from __future__ import annotations
import inspect
from typing import List, Union, Set
from nada_dsl import (
    SecretInteger, audit, Input, Literal
)


secret_int_types = {SecretInteger, audit.SecretInteger}
secret_int = Union[*secret_int_types]


def _gather_parties(node):
    party_attributes = set()

    def traverse(n):

        if isinstance(n, Input):
            party = getattr(n, 'party')
            if party is not None:
                party_attributes.add(party.name)
            return

        if isinstance(n, Literal):
            # no parties associated with Literal instances
            return

        for attr in ['inner', 'left', 'right', 'arg_0', 'arg_1', 'this']:
            if hasattr(n, attr):
                traverse(getattr(n, attr))

    traverse(node)
    return party_attributes


class NadaArray:
    """
    Data structure for representing arrays of SecretIntegers. The constructor accepts
    tuples, lists, and generators and parses them accordingly.
    """
    def __init__(self: NadaArray, *args):

        self._data = []
        self._parties = set()

        if len(args) == 1:
            if isinstance(args[0], list):
                args = args[0]
            if inspect.isgenerator(args[0]):
                args = list(args[0])

        for item in args:
            self.append(item)

    def __len__(self: NadaArray):
        return len(self._data)

    def __iter__(self: NadaArray):
        return iter(self._data)

    def __str__(self: NadaArray):

        parties_str = ",".join(sorted([f"'{p}'" for p in self._parties]))
        return f"NadaArray | len={len(self._data)} | parties=[{parties_str}]"

    def __repr__(self: NadaArray):
        return str(self)

    def __add__(self: NadaArray, other: Union[NadaArray, List[secret_int]]):
        return NadaArray(self._data + other._data)

    def __setitem__(self: NadaArray, index: int, item: secret_int):

        self._check_type(item)
        self._data[index] = item
        self._update_parties()

    def __getitem__(self: NadaArray, index: int) -> secret_int:
        return self._data[index]

    def __delitem__(self: NadaArray, index: int):
        del self._data[index]
        self._update_parties()

    @staticmethod
    def _check_type(item: secret_int):
        """
        Determine whether :item: is of SecretInteger type
        """
        if type(item) not in secret_int_types:
            raise TypeError("all array values must be of type SecretInteger")

    def append(self: NadaArray, item: secret_int):
        """
        Append :item: to this instance
        """

        self._check_type(item)
        self._data.append(item)
        self._add_parties(item)

    def extend(self: NadaArray, iterable: Union[NadaArray, List[secret_int]]):
        """
        Extend this instance with an iterable
        """

        for item in iterable:
            self._check_type(item)
            self._add_parties(item)
        self._data.extend(iterable)

    def insert(self: NadaArray, index: int, item: secret_int):
        """
        Insert :item: at :index: of self._data
        """

        self._check_type(item)
        self._data.insert(index, item)
        self._add_parties(item)

    @staticmethod
    def _gather_parties(obj: secret_int) -> Set[str]:
        if isinstance(obj, audit.SecretInteger):
            return {p.name for p in obj.parties}
        if isinstance(obj, SecretInteger):
            return _gather_parties(obj)
        return set()

    def _update_parties(self: NadaArray):
        """
        Update the set of all Party values for this instance
        """
        self._parties = {party for obj in self for party in self._gather_parties(obj)}

    def _add_parties(self: NadaArray, item: secret_int):
        """
        Add all Party values for some :item: to this instance
        """
        self._parties = self._parties | self._gather_parties(item)

    def get_parties(self: NadaArray) -> Set[str]:
        """
        Return the set of all input parties associated with the data stored by this instance
        """
        return self._parties


def serialize_input_array(
        arr: List[int], party: audit.Party, prefix: str
) -> NadaArray:
    """
    Construct and return a NadaArray with inputs that match a certain :prefix: and :party:
    ownership. This is intended be used only for testing with the nada_dsl.audit module.

    :param arr: Input array
    :param party: Party instance to associate with :arr:
    :param prefix: String to add as prefix to input data names
    """
    return NadaArray(
        audit.SecretInteger(
            audit.Input(f"{prefix}{i}", party=party)
        ) for i in range(len(arr))
    )
