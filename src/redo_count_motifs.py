# pyright: basic
from collections import defaultdict
from uuid import uuid4


import igraph as ig
from loguru import logger
from tqdm import tqdm
import pyarrow as pa
import pyarrow.parquet as pq

from src import database
from src import graph_hashing
from src.plain_motif_graph import PlainMotifGraph
from src.flavored_motif_graph import FlavoredMotifGraph
from src.session_digraph import SessionDiGraph

NODE_FLAVORS = ["fine", "coarse"]
EDGE_FLAVORS = ["fine", "coarse", "unweighted", "light"]
SIZES = [3, 4]


def compute_motifs_randesu(
    session_igraph: ig.Graph, size: int
) -> dict[int, list[tuple[int]]]:
    collected_motify_vertices: dict[int, list[tuple[int]]] = defaultdict(list)

    def motifs_callback(graph, vertices, iso_class):
        # Not fully sure hat vertices contains...
        collected_motify_vertices[iso_class].append(tuple(vertices))

    session_igraph.motifs_randesu(size=size, callback=motifs_callback)
    return collected_motify_vertices


def find_session_graph_motifs(
    session_G: SessionDiGraph, size: int
) -> list[PlainMotifGraph]:
    """
    Transform and store the found motifs for the associated unit_id session digraph.
    """
    session_igraph = ig.Graph.from_networkx(session_G)
    unit_id = session_G.unit_id
    motifies_vertices = compute_motifs_randesu(session_igraph, size)
    plain_motifs: list[PlainMotifGraph] = []
    for iso_class, subgraphs_vertices in tqdm(motifies_vertices.items()):
        for motif_vertices in subgraphs_vertices:
            motif_sub_graph = session_igraph.induced_subgraph(motif_vertices)
            plain_graph_hash = graph_hashing.weisfeiler_lehman_graph_hash(
                motif_sub_graph
            )
            plain_motif_id = uuid4()
            plain_motif = PlainMotifGraph(
                plain_motif_id,
                unit_id,
                size,
                iso_class,
                motif_sub_graph,
                plain_graph_hash,
            )
            plain_motifs.append(plain_motif)

    if len(plain_motifs) == 0:
        msg = f"Failed to find any motifs for {unit_id}"
        logger.warning(msg)
    return plain_motifs


def flavor_plain_motifs(
    plain_motifs: list[PlainMotifGraph],
):
    for node_flavor in NODE_FLAVORS:
        for edge_flavor in EDGE_FLAVORS:
            flavored_motifs: list[FlavoredMotifGraph] = []
            for plain_motif in tqdm(plain_motifs):
                flavored_motif = FlavoredMotifGraph.from_plain_motif(
                    plain_motif, node_flavor, edge_flavor
                )
                flavored_motifs.append(flavored_motif)
            database.insert_flavored_motifs(flavored_motifs)


def find_plain_motifs(
    session_graphs: list[SessionDiGraph],
) -> list[PlainMotifGraph]:
    plain_motifs: list[PlainMotifGraph] = []
    for session_G in session_graphs:
        for size in SIZES:
            plain_motifs += find_session_graph_motifs(session_G, size)
    return plain_motifs


def find_and_insert_all_motifs():
    session_graphs = database.query_session_graphs()
    plain_motifs = find_plain_motifs(session_graphs)
    database.insert_plain_motifs(plain_motifs)
    flavor_plain_motifs(plain_motifs)
