import pickle
from dataclasses import dataclass
from typing import Any, cast

import psycopg
from psycopg import sql
from psycopg.rows import class_row

from src.author_role import AuthorRole
from src.session import Session
from src.session_digraph import SessionDiGraph
from src.flavored_motif_graph import FlavoredMotifGraph
from src.plain_motif_graph import PlainMotifGraph


URI = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"


def _query_postgres[T](query_statement: str, cls: type[T]) -> list[T]:
    with psycopg.connect(URI) as con:
        with con.pipeline():
            with con.cursor(row_factory=class_row(cls)) as cur:
                rows = cur.execute(query_statement).fetchall()
    return rows


def _insert_or_update_postgres(
    insert_statement: str,
    rows: list[dict[str, Any]],  # pyright: ignore[reportExplicitAny]
) -> None:
    if len(rows) == 0:
        raise ValueError("No records were passed for an insertion.")
    sql_insert = sql.SQL(insert_statement)
    with psycopg.connect(URI) as con:
        with con.cursor() as cur:
            cur.executemany(sql_insert, rows)
            con.commit()


def query_comments() -> list[AuthorRole]:
    comment_query = """
    SELECT 
        unit_id,
        comment_id,
        comment_author AS author_name,
        role,
        severity
    FROM cyberbullying_motifs.comments
    ORDER BY unit_id, comment_created_at;
    """
    rows = _query_postgres(comment_query, AuthorRole)
    return rows


def query_sessions() -> list[Session]:
    SESSION_QUERY = """
    WITH count_comments AS (
        SELECT
            unit_id,
            sum(is_cyberbullying::INTEGER) AS num_bullying_comments,
            count(*) AS num_comments
        FROM cyberbullying_motifs.comments
        WHERE comment_content <> ''
        GROUP BY unit_id
    )
    SELECT 
        sessions.unit_id,
        sessions.session_posted_at AS posted_at,
        sessions.owner_user_name,
        COALESCE(sessions.owner_comment, '') AS owner_comment,
        sessions.session_likes AS num_likes,
        count_comments.num_bullying_comments,
        count_comments.num_comments,
        sessions.main_victim
    FROM cyberbullying_motifs.sessions
        INNER JOIN count_comments
        ON count_comments.unit_id = sessions.unit_id
    WHERE sessions.main_victim IN ('OP', 'Participants');
    """
    rows = _query_postgres(SESSION_QUERY, Session)
    return rows


def insert_plain_motifs(motifs: list[PlainMotifGraph]) -> None:
    INSERT_MOTIFS = """
    INSERT INTO cyberbullying_motifs.plain_motifs(
        plain_motif_id,
        unit_id,
        size,
        iso_class,
        motif_hash,
        serialized_motif
    ) VALUES (
        %(plain_motif_id)s,
        %(unit_id)s,
        %(size)s,
        %(iso_class)s,
        %(motif_hash)s,
        %(serialized_motif)s
    );
    """
    seralized_motifs = [motif.to_dict() for motif in motifs]
    _insert_or_update_postgres(INSERT_MOTIFS, seralized_motifs)


def insert_flavored_motifs(motifs: list[FlavoredMotifGraph]) -> None:
    INSERT_MOTIFS = """
    INSERT INTO cyberbullying_motifs.flavored_motifs(
        flavored_motif_id,
        plain_motif_id,
        node_flavor,
        edge_flavor,
        motif_hash,
        serialized_motif
    ) VALUES (
        %(flavored_motif_id)s,
        %(plain_motif_id)s,
        %(node_flavor)s,
        %(edge_flavor)s,
        %(motif_hash)s,
        %(serialized_motif)s
    );
    """
    seralized_motifs = [motif.to_dict() for motif in motifs]
    _insert_or_update_postgres(INSERT_MOTIFS, seralized_motifs)


def query_session_graphs() -> list[SessionDiGraph]:
    @dataclass
    class SerializedGraph:
        serialized_graph: bytes

    QUERY_GRAPHS = """
    SELECT serialized_graph
    FROM cyberbullying_motifs.session_digraphs;
    """
    serialized_graphs = _query_postgres(QUERY_GRAPHS, SerializedGraph)
    graphs: list[SessionDiGraph] = []
    for graph_bytes in serialized_graphs:
        graph = cast(SessionDiGraph, pickle.loads(graph_bytes.serialized_graph))
        graphs.append(graph)
    assert len(graphs) > 0, "Query should return at least one graph."
    return graphs


def insert_session_digraph(session_graph: SessionDiGraph | list[SessionDiGraph]):
    INSERT_DIAGRAPH = """ 
    INSERT INTO cyberbullying_motifs.session_digraphs (
    unit_id,
    serialized_graph,
    num_nodes,
    num_edges,
    num_bullies,
    num_victims,
    num_non_agg_victims,
    num_agg_victims,
    num_defenders,
    num_non_agg_defenders,
    num_agg_defenders,
    main_victim_in_deg,
    main_victim_weighted_in_deg,
    main_victim_out_deg,
    main_victim_weighted_out_deg,
    victim_avg_in_deg,
    victim_avg_weighted_in_deg,
    victim_avg_out_deg,
    victim_avg_weighted_out_deg,
    victim_score,
    victim_score_weighted,
    bully_avg_in_deg,
    bully_avg_weighted_in_deg,
    bully_avg_out_deg,
    bully_avg_weighted_out_deg,
    bully_score,
    bully_score_weighted,
    main_victim_score,
    main_victim_score_weighted,
    comment_id 
    ) VALUES (
    %(unit_id)s,
    %(serialized_graph)s,
    %(num_nodes)s,
    %(num_edges)s,
    %(num_bullies)s,
    %(num_victims)s,
    %(num_non_agg_victims)s,
    %(num_agg_victims)s,
    %(num_defenders)s,
    %(num_non_agg_defenders)s,
    %(num_agg_defenders)s,
    %(main_victim_in_deg)s,
    %(main_victim_weighted_in_deg)s,
    %(main_victim_out_deg)s,
    %(main_victim_weighted_out_deg)s,
    %(victim_avg_in_deg)s,
    %(victim_avg_weighted_in_deg)s,
    %(victim_avg_out_deg)s,
    %(victim_avg_weighted_out_deg)s,
    %(victim_score)s,
    %(victim_score_weighted)s,
    %(bully_avg_in_deg)s,
    %(bully_avg_weighted_in_deg)s,
    %(bully_avg_out_deg)s,
    %(bully_avg_weighted_out_deg)s,
    %(bully_score)s,
    %(bully_score_weighted)s,
    %(main_victim_score)s,
    %(main_victim_score_weighted)s,
    %(comment_id)s
    );"""
    if isinstance(session_graph, list):
        rows = [graph.to_dict() for graph in session_graph]
    elif isinstance(session_graph, SessionDiGraph):
        rows = [session_graph.to_dict()]
    else:
        raise AssertionError("Passed incorrect object types.")
    return _insert_or_update_postgres(INSERT_DIAGRAPH, rows)
