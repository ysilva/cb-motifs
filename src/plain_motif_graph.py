import pickle
from typing import override
from uuid import UUID

import igraph as ig


class PlainMotifGraph:
    def __init__(
        self,
        plain_motif_id: UUID,
        unit_id: int,
        size: int,
        iso_class: int,
        graph: ig.Graph,
        graph_hash: str,
    ) -> None:
        self.plain_motif_id: UUID = plain_motif_id
        self.unit_id: int = unit_id
        self.size: int = size
        self.iso_class: int = iso_class
        self.graph: ig.Graph = graph
        self.graph_hash: str = graph_hash

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PlainMotifGraph):
            return NotImplemented
        return self.plain_motif_id == other.plain_motif_id

    @override
    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    @override
    def __hash__(self) -> int:
        return hash(self.plain_motif_id)

    @override
    def __str__(self) -> str:
        return str(self.to_dict())

    @override
    def __repr__(self) -> str:
        return self.__str__()

    def to_dict(self) -> dict[str, UUID | int | str | bytes]:
        # Per the igraph source code, there are no issues pickling igraph objects as they are.
        # That's what the library authors do as well.
        serialized_motif = pickle.dumps(self.graph, pickle.HIGHEST_PROTOCOL)
        record = {
            "plain_motif_id": str(self.plain_motif_id),
            "unit_id": self.unit_id,
            "size": self.size,
            "iso_class": self.iso_class,
            "motif_hash": self.graph_hash,
            "serialized_motif": serialized_motif,
        }
        return record
