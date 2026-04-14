# pyright: basic
from collections import Counter
from hashlib import blake2b
import igraph as ig


def _hash_label(label, digest_size):
    return blake2b(label.encode("ascii"), digest_size=digest_size).hexdigest()


def _init_node_labels_ig(ig_G: ig.Graph, edge_attr: str, node_attr: str):
    """
    iGraph version of _init_node_labels in nx
    turn node attributes into strings
    """
    if node_attr:
        labels = {int(u.index): str(u[node_attr]) for u in ig_G.vs()}
    elif edge_attr:
        labels = {int(u.index): "" for u in ig_G.vs()}
    else:
        # fall back to node degrees
        labels = {u.index: str(u.degree(mode="all")) for u in ig_G.vs()}
    return labels


def _neighborhood_aggregate_ig(ig_G: ig.Graph, node, node_labels, edge_attr=None):
    """
    Compute new labels for given node by aggregating the labels of each node's neighbors.
    """
    label_list = []

    for incident_edge in ig_G.vs[
        node
    ].out_edges():  # networkx's neighbors function only iterates thru successors
        nbr = (
            incident_edge.source
            if incident_edge.source != node
            else incident_edge.target
        )
        if edge_attr is None:
            prefix = ""
        else:
            prefix = str(incident_edge[edge_attr])
        label_list.append(prefix + node_labels[nbr])

    return node_labels[node] + "".join(sorted(label_list))


def weisfeiler_lehman_step(ig_G, labels, digest_size, edge_attr=None):
    """
    Apply neighborhood aggregation to each node in the graph.
    Computes a dictionary with labels for each node.
    """
    new_labels = {}
    for node in ig_G.vs():
        label = _neighborhood_aggregate_ig(
            ig_G, node.index, labels, edge_attr=edge_attr
        )
        new_labels[node.index] = _hash_label(label, digest_size)
    return new_labels


def weisfeiler_lehman_graph_hash(
    ig_G: ig.Graph,
    edge_attr=None,
    node_attr=None,
    iterations=3,
    digest_size=16,
):
    """
    The function iteratively aggregates and hashes neighborhoods of each node.
    After each node's neighbors are hashed to obtain updated node labels,
    a hashed histogram of resulting labels is returned as the final hash.
    """

    # set initial node labels
    node_labels = _init_node_labels_ig(ig_G, edge_attr, node_attr)

    subgraph_hash_counts = []
    for _ in range(iterations):
        # keys are node ids, values are hashes
        node_labels = weisfeiler_lehman_step(
            ig_G, node_labels, digest_size, edge_attr=edge_attr
        )

        # keys are WL hashes: values are counts
        counter = Counter(node_labels.values())

        # sort the counter, extend total counts
        subgraph_hash_counts.extend(
            sorted(
                counter.items(),
                key=lambda x: x[0],  # sort by WL hash strings (NOT node ids)
            )
        )

    # hash the final counter
    return _hash_label(
        str(tuple(subgraph_hash_counts)),
        digest_size=digest_size,
    )
