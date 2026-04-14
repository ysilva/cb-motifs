from pathlib import Path

from src.author_role import AuthorRole
from src.session_digraph import SessionDiGraph


class GraphBuilder:
    def __init__(
        self,
        session_G: SessionDiGraph,
    ) -> None:
        self.current_bullies: set[AuthorRole] = set()
        self.current_defenders: set[AuthorRole] = set()
        self.current_victims: set[AuthorRole] = set()
        self.session_G: SessionDiGraph = session_G
        self.existing_author_roles: set[AuthorRole] = set()

    def add_node(self, author_role: AuthorRole) -> None:
        # We need to ensure that this code always execute when we add a node to graph.
        # This code enables us to have a per comment snapshot timestamp documented in the database.
        # Since its GraphBuilders responsibility to build the graph, this line
        # of lives here, as opposed pickle_sessions.py
        self.session_G.comment_id = author_role.comment_id
        if author_role.role == "main_victim":
            self.current_victims.add(author_role)
        elif author_role.role in ["aggressive_victim", "non_aggressive_victim"]:
            self.current_victims.add(author_role)
        elif author_role.role in ["bully", "bully_assistant"]:
            self.current_bullies.add(author_role)
        elif author_role.role in [
            "non_aggressive_defender:support_of_the_victim",
            "non_aggressive_defender:direct_to_the_bully",
            "aggressive_defender",
        ]:
            self.current_defenders.add(author_role)
        elif author_role.role == "passive_bystander":
            return None
        else:
            raise ValueError(f"Unknown role: {author_role.role}")

        if author_role not in self.existing_author_roles:
            self.session_G.add_node(
                author_role,
                node_type=author_role.role,
            )
            self.existing_author_roles.add(author_role)

    def add_edge(
        self,
        author_role: AuthorRole,
    ) -> None:
        """
        Set the edges of a session graph.

        We start with an inital Vicitm node, then, we parse each comment in
        order their commented created timestamp (posted order).
        Nodes can only react to nodes that have already added to the graph.

        Bullies attacks the victim, that is, bully -> victim
        Defenders supports the victim, that is, victim -> defender
        Aggressive Defenders attack the bully but also pacifies victim, that is, agg_defender -> bullies (currently)
        Aggressive Victim attacks the bullies, that is, victim -> bully
        """
        if author_role.role in [
            "non_aggressive_defender:direct_to_the_bully",
            "aggressive_victim",
        ]:
            type_ = f"{author_role.role}->bully"
            for bully in self.current_bullies:
                if author_role.should_add_edge(bully):
                    self.session_G.add_edge(
                        author_role,
                        bully,
                        weight=author_role.severity,
                        node_type=type_,
                    )
        elif author_role.role in [
            "bully",
            "bully_assistant",
        ]:
            type_ = f"{author_role.role}->victim"
            for victim in self.current_victims:
                if author_role.should_add_edge(victim):
                    self.session_G.add_edge(
                        author_role,
                        victim,
                        weight=author_role.severity,
                        node_type=type_,
                    )
        elif author_role.role == "non_aggressive_defender:support_of_the_victim":
            # add edges from victim -> non-agg defender
            type_ = f"victim->{author_role.role}"
            for victim in self.current_victims:
                if author_role.should_add_edge(victim):
                    self.session_G.add_edge(
                        victim,
                        author_role,
                        weight=author_role.severity,
                        node_type=type_,
                    )
        elif author_role.role == "aggressive_defender":
            type_ = f"{author_role.role}->bully"
            for bully in self.current_bullies:
                if author_role.should_add_edge(bully):
                    self.session_G.add_edge(
                        author_role,
                        bully,
                        weight=author_role.severity,
                        node_type=type_,
                    )
            type_ = f"victim->{author_role.role}"
            for victim in self.current_victims:
                if author_role.should_add_edge(victim):
                    self.session_G.add_edge(
                        victim,
                        author_role,
                        weight=author_role.severity,
                        node_type=type_,
                    )
        # The non_aggressive_victims only receive incoming edges from the other nodes.
        # So we simply skip over them in the edge adding process.
        elif author_role.role in ["non_aggressive_victim", "passive_bystander"]:
            pass
        else:
            raise ValueError(f"Unknown role: {author_role.role}")
