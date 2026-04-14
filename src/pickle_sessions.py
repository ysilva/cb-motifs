from uuid import uuid4

from tqdm.auto import tqdm

from src import database
from src.session import Session
from src.session_digraph import SessionDiGraph
from src.graph_builder import GraphBuilder
from src.author_role import AuthorRole


def load_sessions_and_comments() -> tuple[list[Session], dict[int, list[AuthorRole]]]:
    sessions = database.query_sessions()
    comments = database.query_comments()
    session_comments: dict[int, list[AuthorRole]] = {}
    for comment in comments:
        if comment.unit_id in session_comments:
            session_comments[comment.unit_id].append(comment)
        else:
            session_comments[comment.unit_id] = [comment]
    return sessions, session_comments


def build_session_graphs() -> None:
    sessions, session_comments = load_sessions_and_comments()
    for session in tqdm(sessions):
        session_G = SessionDiGraph.from_session(session)
        builder = GraphBuilder(session_G)
        MAIN_VICTIM = "main_victim"
        # As the main_victim acts as a surrogate comment,
        # we use the session posted at timestamp as a surrogate
        # comment_created_at field.
        builder.add_node(
            AuthorRole(
                unit_id=session.unit_id,
                comment_id=uuid4(),
                author_name=session.owner_user_name,
                role=MAIN_VICTIM,
                severity=0.0,
            )
        )
        comments = session_comments[session.unit_id]
        for author_role in comments:
            builder.add_node(author_role)
            builder.add_edge(author_role)
            database.insert_session_digraph(session_G)
