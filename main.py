from dataclasses import dataclass, field
from collections import defaultdict
from typing import Optional

OutWire = type(None)

@dataclass
class Node:
    type: str
    principal: Optional[OutWire]
    auxiliaries: list[OutWire] = field(default_factory = list)
    name: str = ""
    flip: int = None
    reduced: bool = True
    def create_wire_to_self(self, name):
        if self.principal.name == name:
            print("Yay", self.principal.name, name)
            return OutWire(self, None, name)
        else:
            i = list(filter(lambda x: x[1].name == name, enumerate(self.auxiliaries)))
            if len(i) == 0:
                raise ValueError("Not found")
            elif len(i) > 1:
                raise ValueError("Too many!")
            else:
                return OutWire(self, i[0][0], name)
                
    def is_in_active_pair(self):
        return self.principal.port is None
    def pretty(self):
        print(f'Node: {id(self)>>4&0xFF:X}/{self.type}')
        print(f' P -> {self.principal.short_show()}')
        for idx, i in enumerate(self.auxiliaries):
            print(f' {idx} -> {i.short_show()}')
    def reduce(self, inet):
        other = self.principal.destination
        algo = (self.type, other.type)
        if algo == ("dup", "con") or (algo[1] == "era" and algo[0] != "era"):
            return other.reduce(inet)
        inet.remove(self)
        inet.remove(other)
        print(algo)
        if algo[0] == "era":
            if algo[1] in ("con", "dup"):
                e1 = Node("era", other.auxiliaries[0])
                e2 = Node("era", other.auxiliaries[1])
                other.auxiliaries[0].opposite().port = None
                other.auxiliaries[0].opposite().destination = e1
                other.auxiliaries[1].opposite().port = None
                other.auxiliaries[1].opposite().destination = e2
                inet.extend((e1, e2))
                
        elif algo == ("con", "dup"):
            cp1 = self.auxiliaries[0]
            cp2 = self.auxiliaries[1]
            dp1 = other.auxiliaries[0]
            dp2 = other.auxiliaries[1]
            
            d1 = Node("dup", cp1, [WireRef("tmp11"), WireRef("tmp12")])
            d2 = Node("dup", cp2, [WireRef("tmp21"), WireRef("tmp22")])
            c1 = Node("con", dp1, [WireRef("tmp12"), WireRef("tmp22")])
            c2 = Node("con", dp2, [WireRef("tmp11"), WireRef("tmp21")])
            
            print("--------")
            connect_named_wires(d1, c1, "tmp12")
            d1.pretty()
            c2.pretty()
            connect_named_wires(d1, c2, "tmp11")
            d1.pretty()
            c2.pretty()
            connect_named_wires(d2, c1, "tmp22")
            connect_named_wires(d2, c2, "tmp21")
            
            cp1.opposite().destination = d1
            cp1.opposite().port = None
            
            cp2.opposite().destination = d2
            cp2.opposite().port = None
            
            dp1.opposite().port = None
            dp1.opposite().destination = c1
            
            dp2.opposite().port = None
            dp2.opposite().destination = c2
            
            validate_edge(cp1)
            validate_edge(cp2)
            validate_edge(dp1)
            validate_edge(dp2)
            
            inet.extend((d1, d2, c1, c2))
            
        elif algo == ("con", "con"):
            self.auxiliaries[0].opposite().destination = other.auxiliaries[1].destination
            self.auxiliaries[1].opposite().destination = other.auxiliaries[0].destination
            other.auxiliaries[0].opposite().destination = self.auxiliaries[1].destination
            other.auxiliaries[1].opposite().destination = self.auxiliaries[0].destination
        elif algo == ("dup", "dup"):
            self.auxiliaries[0].opposite().destination = other.auxiliaries[0].destination
            self.auxiliaries[1].opposite().destination = other.auxiliaries[1].destination
            other.auxiliaries[0].opposite().destination = self.auxiliaries[0].destination
            other.auxiliaries[1].opposite().destination = self.auxiliaries[1].destination
            
            
            
            
    
@dataclass
class OutWire:
    destination: Node
    port: Optional[int]
    name: str = ""
    def short_show(self):
        return f'{id(self.destination)>>4&0xFF:X}/{self.destination.type}/{self.port}'
    def resolve_get(self):
        if self.port is None:
            return self.destination.principal
        else:
            return self.destination.auxiliaries[self.port]
    def resolve_set(self, value):
        if self.port is None:
            self.destination.principal = value
        else:
            self.destination.auxiliaries[self.port] = value
    def opposite(self):
        return self.resolve_get()
    def to_direction(self, flip):
        cond = flip < 0
        if self.port is None:
            return "n" if cond else "s"
        else:
            if self.port == 0:
                return "sw" if cond else "ne"
            if self.port == 1:
                return "se" if cond else "nw"
            raise NotImplementedError
            return "s" if cond else "n"

def connect_named_wires(v0, v1, name):
    w0 = v0.create_wire_to_self(name)
    w1 = v1.create_wire_to_self(name)
    w0.resolve_set(w1)
    w1.resolve_set(w0)
    if name.startswith("tmp"):
        w0.name = None
        w1.name = None
    
@dataclass
class WireRef:
    name: str
    def short_show(self):
        return repr(self.name)

def parse(s) -> list[Node]:
    
    
    inet = list()
    wires = defaultdict(list)
    for line in s.splitlines():
        if not line.strip():
            continue
        line = line.strip().split(" ")
        
        
        node = Node(
            line[0],
            WireRef(line[1]),
            [WireRef(i) for i in line[2:]]
        )
        inet.append(node)
        wires[line[1]].append(node)
        for i in line[2:]:
            wires[i].append(node)
            
    for k, v in wires.items():
        if len(v) != 2:
            raise ValueError(f'Wire `{k}` does not have two nodes connecting it! (has `{len(v)}`)')
        connect_named_wires(*v, k)
    
    return inet

def reduce_one(inet):
    for i in inet.copy():
        if i.is_in_active_pair():
            i.reduced = True
            i.reduce(inet)
            break

def validate_edge(edge):
    try:
        assert edge.opposite().opposite() is edge
    except AssertionError:
        print("Src:")
        edge.opposite().destination.pretty()
        print("Dest:")
        edge.destination.pretty()
        raise

def create_graph_file(content):
    
    HEADER = '''digraph inet {
    graph [margin=20]
    node [penwidth=3,fontsize=30]
    edge [penwidth=3]
    
    
    compound=true;
    '''
    
    FOOTER = '''
    }
    '''
    return HEADER + content + FOOTER

def create_graphs(inets):
    f = ""
    for idx, inet in enumerate(inets):
        if idx != 0:
            f += f"dummy_{idx-1}:s -> dummy_{idx}:s [constraint=false,ltail=cluster_step{idx-1},lhead=cluster_step{idx}];\n"
        f += f"subgraph cluster_step{idx} {{\n"
        f += f"dummy_{idx} [shape=point,style=invis];\n"
        f += create_graph(inet, f'sg{idx}')
        f += "}\n"
    return f

def create_graph(inet, prefix):
    formats = {
        "con": '[label="γ", margin=0,shape=triangle,fixedsize=true,width=1,fillcolor=black,height=1,style=filled,fontcolor=white]',
        #"con": '[label="", margin=0,shape=box,fixedsize=true,width=1,fillcolor=black,height=0.1,style=filled]',
        "dup": '[label="δ", margin=0,shape=triangle,fixedsize=true,width=1,fillcolor=black,height=1,style=stroke,fontcolor=black]',
        #"dup": '[label="", margin=0,shape=point,fixedsize=true,width=0.1,fillcolor=black,height=0.1,style=stroke]',
        "era": '[label="ε", shape=circle, width=0.2,fixedsize=true,height=0.5,fontcolor=black]',
    }
    
    
    f = ""
    for idx, node in enumerate(inet):
        #if not node.name:
        node.name = prefix + "n" + str(idx)
        
    added_edges = set()
    added_nodes = set()
    def edge_between(n1, n2):
        [n1, n2] = sorted([n1, n2], key= lambda a: id(a))
        return n1.name + n2.name
    def recursive_add_node(node):
        nonlocal f
        # Every time there's two back-to-back nodes, or face-to-face nodes, we flip it (it's easier that way)
        if id(node) in added_nodes:
            return
        added_nodes.add(id(node))
        principal_node = node.principal.destination
        print(node.name, principal_node.name, principal_node.principal.destination.name)
        
        if node.flip is None:
            node.flip = 1
        if principal_node.flip is None:
            if node.principal.port is None:
                # this means that they're face-to-face
                principal_node.flip = node.flip * -1
                print("Q", principal_node.name)
            else:
                principal_node.flip = node.flip
        
        for edge in [node.principal, *node.auxiliaries]:
            validate_edge(edge)
            other = edge.destination
            if (not id(edge) in added_edges) and (not id(edge.opposite()) in added_edges):
                added_edges.add(id(edge))
                if other.flip is None:
                    other.flip = 1
                if other.type == "era":
                    other.flip = -1
                
                f += f'\t "{node.name}":{edge.opposite().to_direction(node.flip)}'
                f += f'-> "{other.name}":{edge.to_direction(other.flip)}'
                if edge.opposite().destination.reduced or edge.destination.reduced:
                    f += " [color=red]"
                if edge.port is None and edge.opposite().port is None:
                    f += " [color=blue]"
                if edge.port is not None and edge.opposite().port is not None:
                    f += " [color=black]"
                f += " [arrowhead=none]"
                f += ';\n'
            
            recursive_add_node(other)
        print(node.flip)
        f += f'\t"{node.name}" {formats[node.type]} [orientation={180 if node.flip == 1 else 0}];\n'
    for node in inet:
        recursive_add_node(node)
        
        
    return f
        
NET1 = """
dup a c b
con a b d
era c
era d
"""

NET2 = """
era 1
dup 1 2 3
con 4 2 5
dup 4 5 6
con 7 3 6
era 7
"""

from copy import deepcopy

if __name__ == '__main__':
    a = parse(NET1)
    
    l = []
    for i in range(7):
        reduce_one(a)
        l.append(deepcopy(a))
    a = create_graph_file(create_graphs(l))
        
        
    open("inet.gv", "w").write(a)