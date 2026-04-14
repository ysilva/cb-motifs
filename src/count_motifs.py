# pyright: basic
import itertools
from collections import defaultdict
from uuid import uuid4

import igraph as ig
from loguru import logger


from src import database
from src import graph_hashing
from src.plain_motif_graph import PlainMotifGraph
from src.flavored_motif_graph import FlavoredMotifGraph
from src.session_digraph import SessionDiGraph


def compute_motifs_randesu(
    session_igraph: ig.Graph, size: int
) -> dict[int, list[tuple[int]]]:
    collected_motify_vertices: dict[int, list[tuple[int]]] = defaultdict(list)

    def motifs_callback(graph, vertices, iso_class):
        # Not fully sure hat vertices contains...
        collected_motify_vertices[iso_class].append(tuple(vertices))

    session_igraph.motifs_randesu(size=size, callback=motifs_callback)
    return collected_motify_vertices


def find_session_graph_plain_motifs(
    session_G: SessionDiGraph,
    size: int,
) -> list[PlainMotifGraph]:
    """
    Transform and store the found motifs for the associated unit_id session digraph.
    """
    session_igraph = ig.Graph.from_networkx(session_G)
    unit_id = session_G.unit_id
    motifies_vertices = compute_motifs_randesu(session_igraph, size)
    motifs: dict[int, PlainMotifGraph] = {}
    for iso_class, subgraphs_vertices in motifies_vertices.items():
        for motif_vertices in subgraphs_vertices:
            if iso_class not in motifs:
                motif_sub_graph = session_igraph.induced_subgraph(motif_vertices)
                motif_graph_hash = graph_hashing.weisfeiler_lehman_graph_hash(
                    motif_sub_graph
                )
                motif = PlainMotifGraph(
                    uuid4(),
                    unit_id,
                    size,
                    iso_class,
                    motif_sub_graph,
                    motif_graph_hash,
                    1,
                )
                motifs[iso_class] = motif
            else:
                motifs[iso_class].count += 1
    if len(motifs) == 0:
        msg = f"Failed to find any motifs for {unit_id}"
        logger.warning(msg)
    return [motif for _, motif in motifs.items()]


def find_plain_motifs(session_graphs: list[SessionDiGraph]) -> list[PlainMotifGraph]:
    SIZES = [3, 4]
    plain_motifs: list[PlainMotifGraph] = []
    for session_G in session_graphs:
        for size in SIZES:
            plain_motifs += find_session_graph_plain_motifs(session_G, size)
    return plain_motifs


def flavor_plain_motifs(
    plain_motifs: list[PlainMotifGraph],
) -> list[FlavoredMotifGraph]:
    NODE_FLAVORS = ["fine", "coarse"]
    EDGE_FLAVORS = ["fine", "coarse", "unweighted"]
    flavored_motifs: list[FlavoredMotifGraph] = []
    for plain_motif in plain_motifs:
        for node_flavor, edge_flavor in itertools.product(NODE_FLAVORS, EDGE_FLAVORS):
            flavored_motif = FlavoredMotifGraph.from_plain_motif(
                plain_motif, node_flavor, edge_flavor
            )
            flavored_motifs.append(flavored_motif)
    return flavored_motifs


def find_and_insert_all_motifs():
    session_graphs = database.query_session_graphs()
    plain_motifs = find_plain_motifs(session_graphs)
    flavored_motifs = flavor_plain_motifs(plain_motifs)
    database.insert_plain_motifs(plain_motifs)
    database.insert_flavored_motifs(flavored_motifs)
