import math
from textwrap import dedent
import pydbml.classes
import pydot

from dbml2dot.utils import debug



def generate_table_label(name: str, attributes: list[str]):
    attribute_list: list[str] = []
    for attr in attributes:
        if (str(attr).startswith('<TD port=')):
            attribute_list += [f"""<TR>{attr}</TR>"""]
        else:
            attribute_list += [f"""<TR><TD align="left">{attr}</TD></TR>"""]
    attribute_list_str = "\n".join(attribute_list)
    return dedent(f'''
        <<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="1">
        <TR><TD><I>{name}</I></TD></TR><HR></HR>
        {attribute_list_str}
        </TABLE>>''').strip().replace('\n', '\n\t')


def generate_column_node(name: str, column_attributes: pydbml.classes.Column, enums: list[str]):
    col_string = f'{name}'
    if column_attributes.pk:
        col_string = f"<B>{col_string}</B>"
    if column_attributes.unique:
        col_string = f"<I>{col_string}</I>"
    attribute_str = f'<TD port="{name}" align="left" cellpadding="5">{col_string} : <font color="grey60">{column_attributes.type}</font></TD>'

    enums_used = []
    if str(column_attributes.type).strip() in enums:
        enums_used += [str(column_attributes.type)]
        

    return attribute_str, enums_used


def generate_table_nodes(name: str, contents: pydbml.classes.Table, enums: list[str]) -> tuple[
    pydot.Node, list[pydot.Edge]]:
    debug(f"{name}: {contents}")

    attributes = []
    enums_used = []
    for column_name, column_attributes in contents.column_dict.items():
        attribute_str, enums_used_by_column = generate_column_node(column_name, column_attributes, enums)
        attributes += [attribute_str]
        enums_used += enums_used_by_column

    node: pydot.Node = pydot.Node(
        name,
        label=generate_table_label(name, attributes)
    )

    edges: list[pydot.Edge] = []
    for enum_used in enums_used:
        debug(f"{enum_used} is in enums")
        edges += [
            pydot.Edge(
                enum_used, name,
                style="invis"
            )
        ]

    return node, edges


def generate_graph_from_dbml(dbml: pydbml.PyDBML,name:str) -> pydot.Dot:
    #graph = pydot.Graph()
    graph = pydot.Dot() #change to Dot to enable export

    # using styles from https://github.com/ehne/ERDot
    graph.set_node_defaults(fontname="Helvetica",shape="none")
    graph.set_edge_defaults(
        dir="both",
        fontsize=12,
        arrowsize=0.9,
        penwidth=1.0,
        labelangle=32,
        labeldistance=1.8,
        fontname="Helvetica")
    graph.set_graph_defaults(
        nodesep=0.5,
        rankdir="LR",
        concentrate="true",
        splines="spline",
        fontname="Helvetica",
        pad="0.2,0.2",
        label=f"<<font point-size='30'>{name}</font>>",
        labelloc = "t"
    )
    enums = []
    for enum in dbml.enums:
        enum: pydbml.classes.Enum = enum

        graph.add_node(pydot.Node(
            enum.name,
            label=generate_table_label(f"<I>Enum</I><BR></BR>{enum.name}", enum.items)
        ))

        enums.append(enum.name.strip())

    debug(f"{enums=}")
    debug("Tables:", list(dbml.table_dict.keys()))

    for table_name, table_contents in dbml.table_dict.items():
        node, edges = generate_table_nodes(table_name, table_contents, enums)

        graph.add_node(node)
        for edge in edges:
            graph.add_edge(edge)

    for reference in dbml.refs:
        reference: pydbml.classes.Reference = reference

        orig = reference.col1.name
        dest = reference.col2.name

        label_len = (len(dest) + len(orig))

        if reference.table1.name == reference.table2.name:
            debug("Origin and destination are identical", reference.table1.name)
            for i in range(label_len // 8):
                graph.add_edge(pydot.Edge(reference.table1.name, reference.table2.name, style="invis"))
                # graph.




        graph.add_edge(pydot.Edge(
            reference.table1.name, reference.table2.name,
            headport=dest,
            tailport=orig,
            arrowhead="noneotee",
            arrowtail="ocrow"))
        
        

    # graph.set_simplify(True)
    graph.set_type("digraph")

    return graph
