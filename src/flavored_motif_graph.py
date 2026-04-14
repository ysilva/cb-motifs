import pickle
from uuid import UUID, uuid4
from typing import override

import igraph as ig
import numpy as np

from src.graph_hashing import weisfeiler_lehman_graph_hash
from src.plain_motif_graph import PlainMotifGraph


def _remap_role_flavor_fine(role: str) -> int:
    """
    Remap the roles into their most granular labels.
    """
    if role == "main_victim":
        return 0
    elif role == "non_aggressive_victim":
        return 1
    elif role == "aggressive_victim":
        return 2
    elif role == "aggressive_defender":
        return 3
    elif "non_aggressive_defender" in role:
        return 4
    elif role == "bully":
        return 5
    elif role == "bully_assistant":
        return 6
    else:
        raise ValueError(f"Unknown role {role}")


def _remap_role_flavor_coarse(role: str) -> int:
    """
    Remap the roles into higher level, coarser labels.
    """
    if role in ["main_victim", "non_aggressive_victim", "aggressive_victim"]:
        return 0
    elif role in [
        "aggressive_defender",
        "non_aggressive_defender:support_of_the_victim",
        "non_aggressive_defender:direct_to_the_bully",
    ]:
        return 3
    elif role in ["bully", "bully_assistant"]:
        return 5
    else:
        raise ValueError(f"Unknown role {role}")


def _remap_node_roles(role: str, node_flavor: str) -> int:
    if node_flavor == "fine":
        return _remap_role_flavor_fine(role)
    elif node_flavor == "coarse":
        return _remap_role_flavor_coarse(role)
    else:
        raise ValueError(f"Unknown node flavor {node_flavor}")


def _remap_edge_weights(edge_flavor: str) -> list[int]:
    if edge_flavor == "fine":
        return [
            1,
            2,
            3,
        ]
    elif edge_flavor == "coarse":
        # If right = False, then 3.0 and 3.5 will be in the same bucket.
        return [3]
    elif edge_flavor == "light":
        # If right = False, then 3.0 and 3.5 will be in the same bucket.
        return [2]
    elif edge_flavor == "unweighted":
        return [1]
    else:
        raise ValueError(f"Unknown edge flavor {edge_flavor}")


def _transform_motif(
    motif_graph: ig.Graph,
    node_flavor: str,
    edge_flavor: str,
) -> ig.Graph:
    """
    Apply transformations to 'paint' the the uncolored motifies.

    By default, igraph randesu returns motifys without consideration to their properties.
    """
    edgewt_bins = _remap_edge_weights(edge_flavor)
    motif_graph.vs["mapped_type"] = [
        _remap_node_roles(role, node_flavor) for role in motif_graph.vs["type"]
    ]
    # The plus 1 is to prevent the zero edge weights.
    motif_graph.es["binned_weight"] = (
        np.digitize(motif_graph.es["weight"], bins=edgewt_bins, right=False) + 1
    )
    return motif_graph


class FlavoredMotifGraph:
    def __init__(
        self,
        flavored_motif_id: UUID,
        plain_motif_id: UUID,
        node_flavor: str,
        edge_flavor: str,
        graph: ig.Graph,
        graph_hash: str,
    ) -> None:
        self.flavored_motif_id: UUID = flavored_motif_id
        self.plain_motif_id: UUID = plain_motif_id
        self.node_flavor: str = node_flavor
        self.edge_flavor: str = edge_flavor
        self.graph: ig.Graph = graph
        self.graph_hash: str = graph_hash

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FlavoredMotifGraph):
            return NotImplemented
        return self.flavored_motif_id == other.flavored_motif_id

    @override
    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    @override
    def __hash__(self) -> int:
        return hash(self.flavored_motif_id)

    @override
    def __str__(self) -> str:
        return str(self.to_dict())

    @override
    def __repr__(self) -> str:
        return self.__str__()

    @classmethod
    def from_plain_motif(
        cls, plain_motif: PlainMotifGraph, node_flavor: str, edge_flavor: str
    ) -> "FlavoredMotifGraph":
        transformed_graph = _transform_motif(
            plain_motif.graph, node_flavor, edge_flavor
        )
        transformed_graph_hash = weisfeiler_lehman_graph_hash(
            transformed_graph, "binned_weight", "mapped_type"
        )
        flavored_motif_id = uuid4()
        return cls(
            flavored_motif_id,
            plain_motif.plain_motif_id,
            node_flavor,
            edge_flavor,
            transformed_graph,
            transformed_graph_hash,
        )

    def to_dict(self) -> dict[str, UUID | str | bytes]:
        # Per the igraph source code, there are no issues pickling igraph objects as they are.
        # That's what the library authors do as well.
        serialized_motif = pickle.dumps(self.graph, pickle.HIGHEST_PROTOCOL)
        record = {
            "flavored_motif_id": str(self.flavored_motif_id),
            "plain_motif_id": str(self.plain_motif_id),
            "node_flavor": self.node_flavor,
            "edge_flavor": self.edge_flavor,
            "motif_hash": self.graph_hash,
            "serialized_motif": serialized_motif,
        }
        return record
