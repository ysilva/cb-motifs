# pyright: basic
from pathlib import Path
from random import random

import igraph as ig
import networkx as nx
import plotly.graph_objects as go
import plotly.io as pio
from matplotlib import pyplot as plt

from src.flavored_motif_graph import FlavoredMotifGraph
from src.session_digraph import SessionDiGraph

pio.templates.default = "plotly_white"


def umap_layout_pos(G, **kwargs):
    """
    Get UMAP coordinates from iGraph
    """
    ig_G = ig.Graph.from_networkx(G)
    umap_min_dist = kwargs.get("umap_min_dist", 1)
    epochs = kwargs.get("umap_epochs", 2_000)
    layout = ig_G.layout_umap(min_dist=umap_min_dist, epochs=epochs)
    umap_pos_d = {v["_nx_name"]: pos_vec for v, pos_vec in zip(ig_G.vs, layout.coords)}
    nx.set_node_attributes(G, name="pos", values=umap_pos_d)
    return umap_pos_d


def get_node_trace(
    x,
    y,
    name,
    text,
    marker,
    marker_color,
    marker_size=40,
    show_roles=True,
    hovertext=None,
    show_names=True,
    **kwargs,
):
    if not show_names:
        name = ""
        mode = "markers"
    else:
        mode = "markers+text"

    if isinstance(text, list):
        if show_roles:
            text = [f"<b>{t.split()[0]}</b><br>{t.split()[1]}" for t in text]
        else:
            text = [f"<b>{t.split()[0]}</b>" for t in text]
    else:
        if isinstance(text, str):
            text_split = text.split()
            if len(text_split) >= 2:
                text = f"<b>{text_split[0]}</b><br>{text_split[1]}"
            elif len(text_split) == 1:
                text = f"<b>{text_split[0]}</b>"
            else:
                text = ""
        else:
            text = ""

    if hovertext is None:
        hovertext = text

    return go.Scatter(
        x=x,
        y=y,
        name=name,
        text=text,
        mode=mode,
        hovertext=hovertext,
        textposition="middle center",
        textfont=dict(
            shadow="5px 5px 5px white",
        ),
        marker=dict(
            size=marker_size,
            opacity=1,
            symbol=marker,
            color=marker_color,
            line=dict(color="black", width=3),
        ),
        **kwargs,
    )


def get_edge_trace(
    p0, p1, edge_color, width, text=None, backoff=30, max_width=8, **kwargs
):
    x0, y0 = p0
    x1, y1 = p1
    if text is not None:
        text = f"weight = {text}"
    return go.Scatter(
        x=[x0, x1],
        y=[y0, y1],
        marker=dict(
            symbol="arrow",
            size=25,
            line=dict(color="black", width=1.5),
            angleref="previous",
            standoff=backoff,
        ),
        line=dict(
            width=min(max_width, width),
            color=edge_color,
            backoff=backoff,
        ),
        name="",
        mode="lines+markers",
        text=text,
        hoverinfo="text",
        opacity=0.5,
        **kwargs,
    )


def draw_motify(motif: FlavoredMotifGraph, motif_frequency: int, ax=None, title=None):
    G = motif.graph

    if ax is None:
        _, ax = plt.subplots()
        title_prefix = f"Session: {motif.unit_id}"
    else:
        title_prefix = ""

    if title is None:
        title = (
            f"{title_prefix}    version: {motif.version}    "
            f"size: {motif.size}   iso: {motif.iso_class}   "
            f"count: {motif_frequency}x"
        )

    if motif.version == "v1":
        node_features = {
            "main_victim": ("diamond", "LightGreen", 50, "Main\nVictim"),
            "aggressive_victim": ("square", "LightSkyBlue", 50, "Agg\nVictim"),
            "non_aggressive_victim": ("square", "LightCyan", 50, "Non-Agg\nVictim"),
            "bully": ("circle", "Moccasin", 40, "Bully"),
            "bully_assistant": ("circle", "Coral", 40, "Bully\nAsst"),
            "aggressive_defender": ("^", "Pink", 50, "Agg\nDef"),
            "non_aggressive_defender:direct_to_the_bully": (
                "v",
                "LightPink",
                50,
                "Non-Agg\nDef",
            ),
            "non_aggressive_defender:support_of_the_victim": (
                "v",
                "LightPink",
                50,
                "Non-Agg\nDef",
            ),
        }
    elif motif.version == "v2":
        victim_ = ("square", "MediumAquamarine", 50, "Victim")
        bully_ = ("circle", "LemonChiffon", 15, "Bully")
        defender_ = ("^", "MistyRose", 35, "Def")

        node_features = {
            "main_victim": victim_,
            "aggressive_victim": victim_,
            "non_aggressive_victim": victim_,
            "bully": bully_,
            "bully_assistant": bully_,
            "aggressive_defender": defender_,
            "non_aggressive_defender": defender_,
        }
    else:
        raise NotImplementedError(f"Motif version {motif.version} not supported")

    style = {
        "vertex_size": 70,
        "bbox": (350, 350),
        "margin": 25,
        "vertex_color": [node_features[type_][1] for type_ in G.vs["type"]],
        "vertex_label": [node_features[type_][3] for type_ in G.vs["type"]],
        "vertex_shape": [node_features[type_][0] for type_ in G.vs["type"]],
        "edge_label": G.es["weight"],
        "edge_font": "Verdana",
        "edge_width": G.es["weight"],
        "edge_background": "white",
    }

    ig.plot(G, target=ax, **style)
    ax.set_title(title)
    ax.patch.set_edgecolor("black")
    ax.patch.set_linewidth(1.5)
    return ax


def get_node_info(node_type):
    if node_type == "main_victim":
        shape = "diamond"
        color = "lightgreen"
        size = 50
        legend_text = "Main Victim"
    elif node_type == "aggressive_victim":
        shape = "square"
        color = "lightblue"
        size = 50
        legend_text = "Agg Victim"
    elif node_type == "non_aggressive_victim":
        shape = "square"
        color = "teal"
        size = 50
        legend_text = "Non-Agg Victim"
    elif node_type == "bully":
        shape = "circle"
        color = "orange"
        size = 40
        legend_text = "Bully"
    elif node_type == "bully_assistant":
        shape = "circle"
        color = "coral"
        size = 40
        legend_text = "Bully Asst"
    elif node_type == "aggressive_defender":
        shape = "pentagon"
        color = "orchid"
        size = 50
        legend_text = "Agg Def"
    elif node_type == "non_aggressive_defender:direct_to_the_bully":
        shape = "pentagon"
        color = "lightpink"
        size = 50
        legend_text = "Non-Agg Def"
    elif node_type == "non_aggressive_defender:support_of_the_victim":
        shape = "pentagon"
        color = "lightpink"
        size = 50
        legend_text = "Non-Agg Def"
    else:
        raise ValueError(f"Invalid node type {node_type}")
    return shape, color, size, legend_text


def get_edge_info(edge_type: str):
    if edge_type == "aggressive_defender->victim":
        edge_color = "orchid"
        legend_text = "Agg Def → Victim"
    elif edge_type == "aggressive_defender->bully":
        edge_color = "orchid"
        legend_text = "Agg Def → Bully"
    elif edge_type == "aggressive_victim->bully":
        edge_color = "green"
        legend_text = "Agg Victim → Bully"
    elif edge_type == "non_aggressive_defender:support_of_the_victim->victim":
        edge_color = "blue"
        legend_text = "Non-Agg Def → Victim"
    elif edge_type == "non_aggressive_defender:direct_to_the_bully->bully":
        edge_color = "green"
        legend_text = "Non-Agg Def → Bully"
    elif edge_type == "non_aggressive_defender:direct_to_the_bully->victim":
        edge_color = "palevioletred"
        legend_text = "Non-Agg Def → Victim"
    elif edge_type == "bully->victim":
        edge_color = "orange"
        legend_text = "Bully → Victim"
    elif edge_type == "bully_assistant->victim":
        edge_color = "orange"
        legend_text = "Bully Assit → Victim"
    elif edge_type == "victim->aggressive_defender":
        edge_color = "orchid"
        legend_text = "Victim → Agg Def"
    elif edge_type == "victim->non_aggressive_defender:direct_to_the_bully":
        edge_color = "lightblue"
        legend_text = "Victim → Non-Agg Def"
    elif edge_type == "victim->non_aggressive_defender:support_of_the_victim":
        edge_color = "lightblue"
        legend_text = "Victim → Non-Agg Def"
    else:
        raise ValueError(f"Invalid edge type {edge_type}")
    return edge_color, legend_text


def prepare_session_figure(session_G: SessionDiGraph, show_names: bool = False):
    if len(nx.get_node_attributes(session_G, "layer")) == 0:
        layer_dict = {}
        for node, data in session_G.nodes(data=True):
            if 'victim' in node.role:
                layer = 0
            elif 'defender' in node.role:
                layer = -1
            elif 'bully' in node.role:
                layer = 1
            else:
                layer = -2
            layer_dict[node] = layer
        nx.set_node_attributes(session_G, name="layer", values=layer_dict)
    pos = nx.multipartite_layout(
        session_G, subset_key="layer", align="horizontal", center=(0, 0)
    )
    # Giving the positions some gitters to avoid awkward overlap
    pos = {
        n: (p[0] + (random() * 0.03), p[1] + (random() * 0.03)) for n, p in pos.items()
    }
    node_traces = []
    node_types = {}
    for node, data in session_G.nodes(data=True):
        type_ = data["type"]
        text = str(node)
        hovertext = text
        marker, marker_color, marker_size, legendgroup_text = get_node_info(type_)
        if type_ not in node_types:
            node_types[type_] = set()
            show_legend = True
        else:
            show_legend = False
        node_types[type_].add(node)
        node_traces.append(
            get_node_trace(
                x=[pos[node][0]],
                y=[pos[node][1]],
                text=text,
                name=type_,
                marker=marker,
                marker_color=marker_color,
                marker_size=marker_size,
                hovertext=hovertext,
                show_names=show_names,
                legendgroup=type_,
                legendgrouptitle_text=legendgroup_text,
                showlegend=show_legend,
            )
        )
    edge_traces = []
    edge_types = {}
    for node_u, node_v, data in session_G.edges(data=True):
        p0, p1 = pos[node_u], pos[node_v]
        wt = data["weight"]
        type_ = data["type"]
        edge_color, legendgroup_text = get_edge_info(type_)
        if type_ not in edge_types:
            edge_types[type_] = set()
            show_legend = True
        else:
            show_legend = False
        edge_traces.append(
            get_edge_trace(
                p0=p0,
                p1=p1,
                edge_color=edge_color,
                width=wt,
                text=wt,
                legendgroup=type_,
                legendgrouptitle_text=legendgroup_text,
                showlegend=show_legend,
            )
        )
    fig = go.Figure(data=edge_traces + node_traces)
    # title = f'Session: {self.session_id}, {self.timestamp}.'
    # title += f'<br>{len(self.comments):,} comments, {self.session_G.order():,} nodes, {self.session_G.size():,} edges.'
    fig.update_layout(
        width=1000,
        height=1000,
        legend=dict(
            bordercolor="black",
            borderwidth=1,
            orientation="h",
            yanchor="bottom",
            y=0.01,
            xanchor="center",
            x=0.5,
            xref="container",
            yref="container",
        ),
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def draw_session_graph(session_G: SessionDiGraph, show_names: bool = True):
    """
    Draw the session graph using Plotly
    """
    fig = prepare_session_figure(session_G, show_names=show_names)
    overall_topic = session_G.most_frequent_topic()
    if session_G.posted_timestamp is None:
        timestamp = "<missing>"
    else:
        timestamp = session_G.posted_timestamp.strftime("%a %b %-d %Y")

    legend_text = (
        f"<b>Session:</b> {session_G.unit_id}    <b>{timestamp}</b> <br>"
        f"<b>Comments: </b> {session_G.num_comments}, <b>Cyberbullying</b>: {session_G.num_bullies} ({session_G.percent_comments_bullying:.1%})"
        f"   <b>Majority Topic:</b> {overall_topic}<br>"
        f"<b>Nodes:</b> {session_G.num_nodes}   <b>Edges:</b> {session_G.num_edges}<br>"
        f"<b>Main Victim In-Degree:</b> {session_G.main_victim_in_deg:,} ({session_G.main_victim_weighted_in_deg:,})"
        f"   <b>Out-Degree:</b> {session_G.main_victim_out_deg:,} ({session_G.main_victim_weighted_out_deg:,})"
        f"   <b>Score (out - in):</b> {session_G.main_victim_score} ({session_G.main_victim_score_wt})<br>"
        f"<b>All Victims ({session_G.num_victims}) Avg In-Degree:</b> {session_G.victim_avg_in_deg:.2g} ({session_G.victim_avg_weighted_in_deg:.2g})"
        f"   <b>Avg Out-Degree:</b> {session_G.victim_avg_out_deg:.2g} ({session_G.victim_avg_weighted_out_deg:.2g})"
        f"   <b>Avg Score (out - in):</b> {session_G.avg_victim_score:.2g} ({session_G.avg_victim_score_wt:.2g})<br>"
    )

    if session_G.num_bullies > 0:
        bully_legend = (
            f"<b>Bullies ({session_G.num_bullies}) "
            f"In-Degree</b>: {session_G.bully_avg_in_deg:.2g} ({session_G.bully_avg_weighted_out_deg:.2g})   "
            f"<b>Out-Degree:</b> {session_G.bully_avg_out_deg:.2g} ({session_G.bully_avg_weighted_out_deg:.2g})    "
            f"<b>Score (out - in):</b> {session_G.bully_score:.2g} ({session_G.bully_score_wt:.2g})<br>"
        )
        legend_text += bully_legend
    # TODO: Need to talk to Satyaki about what we want to do here.
    # Separate legend with the topic totals here
    # topics_legend_text = f"<b>Top 3 Comment Topics:</b><br>"
    # top_5_topics = sorted(self.topic_counts.items(), key=lambda x: -x[1])[:3]

    # for topic, count in top_5_topics:
    #     topic_str = str(topic).replace("_", " ").title()
    #     topics_legend_text += (
    #         f"<b>{topic_str}</b>: {count} ({count / cb_count:.1%})<br>"
    #     )

    # Add legend
    fig.add_annotation(
        xref="paper",
        yref="paper",
        x=0,  # Right side of the graph
        y=1.1,  # Top of the graph
        text=legend_text,
        showarrow=False,
        yanchor="top",
        font=dict(size=12, color="black"),
        align="left",
        bordercolor="black",
        borderwidth=1,
        bgcolor="white",
        opacity=0.8,
    )
    # TODO: Add Topic Legend and make use of topic vector
    # fig.add_annotation(
    #     xref="paper",
    #     yref="paper",
    #     yanchor="top",
    #     x=1,  # Right side of the graph
    #     y=1.1,  # Bottom of the graph
    #     text=topics_legend_text,
    #     showarrow=False,
    #     font=dict(size=12, color="black"),
    #     align="left",
    #     bordercolor="black",
    #     borderwidth=1,
    #     bgcolor="white",
    #     opacity=0.8,
    # )

    return fig


def save_graph_snapshot(
    session_G: SessionDiGraph,
    snapshot_dir: Path,
    step: int,
    show_names: bool = False,
):
    """
    Save a snapshot of the current graph as an image or serialized object.
    param snapshot_dir: Directory to save the snapshot.
    param step: The step number for the snapshot.
    """
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    fig = draw_session_graph(session_G, show_names=show_names)

    PALEWHITE = "#FAF7F2"

    fig.update_layout(paper_bgcolor="white", plot_bgcolor=PALEWHITE)
    fig.write_image(snapshot_dir / f"{session_G.unit_id}_graph_step_{step:05d}.png")
