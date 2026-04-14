# pyright: basic
from uuid import UUID
import pickle
import statistics
from decimal import Decimal
from numbers import Real
from datetime import datetime
from typing import override
import networkx as nx

from src.session import Session
from src.author_role import AuthorRole


class SessionDiGraph(nx.DiGraph):
    """
    DiGraph container for Sessions
    While adding edges, it updates weights of an existing edge if present.
    """

    def __init__(
        self,
        unit_id: int,
        owner_username: str,
        owner_comment: str,
        num_likes: int,
        num_bullying_comments: int,
        num_comments: int,
    ) -> None:
        super().__init__()
        self.unit_id: int = unit_id
        self.owner_username: str = owner_username
        self.owner_comment: str = owner_comment
        self.num_likes: int = num_likes
        self.num_bullying_comments: int = num_bullying_comments
        self.num_comments: int = num_comments

    @classmethod
    def from_session(cls, session: Session) -> "SessionDiGraph":
        return cls(
            unit_id=session.unit_id,
            owner_username=session.owner_user_name,
            owner_comment=session.owner_comment,
            num_likes=session.num_likes,
            num_bullying_comments=session.num_bullying_comments,
            num_comments=session.num_comments,
        )

    @property
    def main_victim(self) -> AuthorRole:
        return self._main_victim

    @main_victim.setter
    def main_victim(self, value: AuthorRole) -> None:
        self._main_victim: AuthorRole = value

    def _process_degrees(self, iter) -> float:
        if isinstance(iter, Real):
            value = float(iter)
        elif isinstance(iter, Decimal):
            value = float(iter)
        else:
            list_values = [float(v) for _, v in iter]
            if len(list_values) > 0:
                value = statistics.mean(list_values)
            else:
                value = 0.0
        if not isinstance(value, float):
            raise TypeError(f"value was not a float, type of value {type(value)}")
        return value

    @property
    def percent_comments_bullying(self) -> float:
        return float(self.num_bullying_comments) / float(self.num_comments)

    @property
    def node_types(self) -> dict[AuthorRole, str]:
        node_types = nx.get_node_attributes(self, name="type")
        return node_types

    @property
    def defenders(self) -> set[AuthorRole]:
        defenders: set[AuthorRole] = set()
        for n, type_ in self.node_types.items():
            if (
                type_ == "non_aggressive_defender:support_of_the_victim"
                or type_ == "non_aggressive_defender:direct_to_the_bully"
                or type_ == "aggressive_defender"
            ):
                defenders.add(n)
        return defenders

    @property
    def victims(self) -> set[AuthorRole]:
        victims: set[AuthorRole] = set()
        for n, type_ in self.node_types.items():
            if (
                type_ == "aggressive_victim"
                or type_ == "non_aggressive_victim"
                or type_ == "main_victim"
            ):
                victims.add(n)
        return victims

    @property
    def bullies(self) -> set[AuthorRole]:
        bullies: set[AuthorRole] = set()
        for n, type_ in self.node_types.items():
            if type_ == "bully" or type_ == "bully_assistant":
                bullies.add(n)
        return bullies

    @property
    def num_bullies(self) -> int:
        return len(self.bullies)

    @property
    def num_nodes(self) -> int:
        nodes = nx.number_of_nodes(self)
        assert isinstance(nodes, int)
        return nodes

    @property
    def num_edges(self) -> int:
        edges = nx.number_of_edges(self)
        assert isinstance(edges, int)
        return edges

    @property
    def num_victims(self) -> int:
        return len(self.victims)

    @property
    def num_non_agg_victims(self) -> int:
        return len(
            {
                n
                for n, type_ in self.node_types.items()
                if type_ == "non_aggressive_victim"
            }
        )

    @property
    def num_agg_victims(self) -> int:
        return len(
            {n for n, type_ in self.node_types.items() if type_ == "aggressive_victim"}
        )

    @property
    def num_defenders(self) -> int:
        return len(self.defenders)

    @property
    def num_non_agg_defenders(self) -> int:
        return len(
            {
                n
                for n, type_ in self.node_types.items()
                if (
                    type_ == "non_aggressive_defender:support_of_the_victim"
                    or type_ == "non_aggressive_defender:direct_to_the_bully"
                )
            }
        )

    @property
    def num_agg_defenders(self) -> int:
        return len(
            {
                n
                for n, type_ in self.node_types.items()
                if type_ == "aggressive_defender"
            }
        )

    @property
    def main_victim_in_deg(self) -> float:
        degree = self.in_degree(self.main_victim)
        return self._process_degrees(degree)

    @property
    def main_victim_weighted_in_deg(self) -> float:
        degree = self.in_degree(self.main_victim, weight="weight")
        return self._process_degrees(degree)

    @property
    def main_victim_out_deg(self) -> float:
        degree = self.out_degree(self.main_victim)
        return self._process_degrees(degree)

    @property
    def main_victim_weighted_out_deg(self) -> float:
        degree = self.out_degree(self.main_victim, weight="weight")
        return self._process_degrees(degree)

    @property
    def victim_avg_in_deg(self) -> float:
        degree_view = self.in_degree(nbunch=self.victims)
        return self._process_degrees(degree_view)

    @property
    def victim_avg_weighted_in_deg(self) -> float:
        degree_view = self.in_degree(nbunch=self.victims, weight="weight")
        return self._process_degrees(degree_view)

    @property
    def victim_avg_out_deg(self) -> float:
        degree_view = self.out_degree(nbunch=self.victims)
        return self._process_degrees(degree_view)

    @property
    def victim_avg_weighted_out_deg(self) -> float:
        degree_view = self.out_degree(nbunch=self.victims, weight="weight")
        return self._process_degrees(degree_view)

    @property
    def bully_avg_in_deg(self) -> float:
        degree_view = self.in_degree(nbunch=self.bullies)
        return self._process_degrees(degree_view)

    @property
    def bully_avg_weighted_in_deg(self) -> float:
        degree_view = self.in_degree(nbunch=self.bullies, weight="weight")
        return self._process_degrees(degree_view)

    @property
    def bully_avg_out_deg(self) -> float:
        degree_view = self.out_degree(nbunch=self.bullies)
        return self._process_degrees(degree_view)

    @property
    def bully_avg_weighted_out_deg(self) -> float:
        degree_view = self.out_degree(nbunch=self.bullies, weight="weight")
        return self._process_degrees(degree_view)

    @property
    def bully_score(self) -> float:
        return self.bully_avg_out_deg - self.bully_avg_in_deg

    @property
    def bully_score_weighted(self) -> float:
        return self.bully_avg_weighted_out_deg - self.bully_avg_weighted_in_deg

    @property
    def victim_score(self) -> float:
        return self.victim_avg_out_deg - self.victim_avg_in_deg

    @property
    def victim_score_weighted(self) -> float:
        return self.victim_avg_weighted_out_deg - self.victim_avg_weighted_in_deg

    @property
    def main_victim_score(self) -> float:
        return self.main_victim_out_deg - self.main_victim_in_deg

    @property
    def main_victim_score_weighted(self) -> float:
        return self.main_victim_weighted_out_deg - self.main_victim_weighted_in_deg

    @property
    def comment_id(self):
        return self._comment_id

    @comment_id.setter
    def comment_id(self, value: UUID):
        self._comment_id = value

    @override
    def add_node(self, node: AuthorRole, node_type: str) -> None:
        if node.role == "main_victim":
            self.main_victim = node
            if self.has_node(node):
                raise AssertionError(
                    "Main Victim is already set. Did you mean to add it twice?"
                )
            else:
                super().add_node(node, type=node_type)
        else:
            super().add_node(node, type=node_type)

    @override
    def add_edge(self, u_of_edge: AuthorRole, v_of_edge: AuthorRole, **attrs) -> None:
        u, v = u_of_edge, v_of_edge
        if not self.has_node(u) or not self.has_node(v):
            raise ValueError("Either u or v was not added to the graph.")
        if self.has_edge(u, v):  # existing edge, update the weight
            self[u][v]["weight"] += attrs["weight"]
        else:
            super().add_edge(u, v, **attrs)

    def to_dict(self) -> dict[str, int | bool | bytes | float]:
        seralized_graph = pickle.dumps(self, protocol=pickle.HIGHEST_PROTOCOL)
        return {
            "unit_id": self.unit_id,
            "serialized_graph": seralized_graph,
            "num_nodes": self.num_nodes,
            "num_edges": self.num_edges,
            "num_bullies": self.num_bullies,
            "num_victims": self.num_victims,
            "num_agg_victims": self.num_agg_victims,
            "num_non_agg_victims": self.num_non_agg_victims,
            "num_defenders": self.num_defenders,
            "num_non_agg_defenders": self.num_non_agg_defenders,
            "num_agg_defenders": self.num_agg_defenders,
            "main_victim_in_deg": self.main_victim_in_deg,
            "main_victim_weighted_in_deg": self.main_victim_weighted_in_deg,
            "main_victim_out_deg": self.main_victim_out_deg,
            "main_victim_weighted_out_deg": self.main_victim_weighted_out_deg,
            "victim_avg_in_deg": self.victim_avg_in_deg,
            "victim_avg_weighted_in_deg": self.victim_avg_weighted_in_deg,
            "victim_avg_out_deg": self.victim_avg_out_deg,
            "victim_avg_weighted_out_deg": self.victim_avg_weighted_out_deg,
            "victim_score": self.victim_score,
            "victim_score_weighted": self.victim_score_weighted,
            "bully_avg_in_deg": self.bully_avg_in_deg,
            "bully_avg_weighted_in_deg": self.bully_avg_weighted_in_deg,
            "bully_avg_out_deg": self.bully_avg_out_deg,
            "bully_avg_weighted_out_deg": self.bully_avg_weighted_out_deg,
            "bully_score": self.bully_score,
            "bully_score_weighted": self.bully_score_weighted,
            "main_victim_score": self.main_victim_score,
            "main_victim_score_weighted": self.main_victim_score_weighted,
            "comment_id": self.comment_id,
        }
