import pygraphviz as pgv
from pprint import pprint as pp
import json, sys
from functools import partial
debug = partial(print, file = sys.stderr)

def set_attr_key(attr, key, value):
  attr[key] = value
#############
#           #
#############
class Annotatable:
  def annotate(self, wording: str):
    self._wording = wording
    return self

  ##############################################################################
  @property
  def name(self):
    raise NotImplemented()

  ##############################################################################

#############
#           #
#############
class Event:
  def __init__(self, name):
    self._type = name

#############
#           #
#############
class Transition(Annotatable):
  def __init__(self, *, 
    from_state, 
    to_state, 
    event = None, 
    guardian = None, 
    actions = None
  ):
    self._from = from_state
    self._to = to_state
    self._ev = event
    self._g = guardian
    self._acts = actions

  ##############################################################################
  @property
  def is_naive(self):
    return None == self._ev and (None == self._acts or len(self._acts) == 0)

  ##############################################################################
  def action(self, action):
    self._acts = [action]
    return self

  ##############################################################################
  def to(self, state):
    self._to = State(state)
    return self

  ##############################################################################
  @property
  def name(self):
    fn = ""
    tn = ""
    en = ""
    if None != self._from:
      fn = self._from._name
    if None != self._to:
      tn = self._to._name
    if None != self._ev:
      en = self._ev._type
    return fn + en + tn

  ##############################################################################

#############
#           #
#############
class State:
  def __init__(self, name):
    self._name = name
  
  ##############################################################################
  def to(self, state_name):
    return Transition(from_state = self, to_state = State(state_name))

  ##############################################################################
  def via(self, event_name:str):
    ev = Event(event_name)
    t = Transition(from_state = self, to_state = None, event = ev)
    return t

  ##############################################################################
  def on_entry(self, action_name):
    self._entry_action = action_name
    return self

  ##############################################################################
  def on_exit(self, action_name):
    self._exit_action = action_name
    return self

  ##############################################################################

#############
#           #
#############
class StateChart:
  def visualize_dot(self, *, output = None):
    transition_table = self.transition_table
    g = pgv.AGraph(strict = False, directed = True)
    g.graph_attr["layout"] = "dot"
    g.graph_attr["layout"] = "neato"
    g.graph_attr["layout"] = "circo"
    g.graph_attr["layout"] = "sfdp"
    # g.graph_attr["rankdir"] = "LR"
    g.graph_attr["concentrate"] = True
    g.graph_attr["dim"] = 2
    g.graph_attr["splines"] = 'ortho'
    g.node_attr['shape'] = "box"
    g.node_attr['style'] = "rounded"
    g.edge_attr["decorate"] = True
    for i, t in enumerate(transition_table):
      self.visualize_transition(t, g)
    self.visualize_annotations(g)
    self.visualize_special_states(g)
    self.visualize_state_actions(g)
    text = g.string()
    print(text)

  ##############################################################################
  def visualize_state_actions(self, g):
    sas = self.state_actions
    for sa in sas:
      if sa._name in set(["*", "X"]):
        continue
      n = g.get_node(sa._name)
      entry_row = ""
      if None != sa._entry_action:
        entry_row = f"""
        <TR><TD>Entry:</TD><TD><I>{sa._entry_action}</I></TD></TR>
        """.strip()
      exit_row = ""
      if None != sa._exit_action:
        exit_row = f"""
        <TR><TD>Exit:</TD><TD><I>{sa._exit_action}</I></TD></TR>
        """.strip()
      label = f"""
      <<TABLE 
        cellborder="0"
        border = "1"
        style = "rounded"
      >
        <TR><TD>{sa._name}</TD></TR>
        <HR/>
        {entry_row}
        {exit_row}
      </TABLE>>
      """.strip()
      n.attr['shape'] = 'plaintext'
      n.attr['label'] = label

  ##############################################################################
  def visualize_annotations(self, g):
    transition_table = self.transition_table
    td = dict([(t.name, t) for t in transition_table])
    for annotate in self.annotates:
      anno = td.get(annotate.name, None)
      if None == anno:
        continue
      anno.visualize_annotate(annotate._wording)
      # node = g.get_node(vname)
      # debug(node)
      # pass


  ##############################################################################
  def visualize_make_transition_name(self, t):
    fs = t._from
    ts = t._to
    fn = fs._name
    tn = ts._name
    ev_part = ""
    action_part = ""
    transition_name = ""
    td = dict(
      fs = fn,
      ts = tn,
    )
    if None != t._ev:
      td['ev'] = t._ev._type
    if None != t._acts and len(t._acts) > 1:
      td['act'] = t._acts[0]
    transition_name = json.dumps(td)
    return transition_name

  ##############################################################################
  def visualize_naive_transition(self, t, g):
    fs = t._from
    ts = t._to
    fn = fs._name
    tn = ts._name
    g.add_edge(fs._name, ts._name)
    e = g.get_edge(fs._name, ts._name)
    # t.visualize_annotate = lambda a: (e.attr['edgetooltie'] = a, e)
    t.visualize_annotate = partial(set_attr_key, e.attr, 'tooltip')

  ##############################################################################
  def visualize_complex_transition(self, t, g):
    fs = t._from
    ts = t._to
    fn = fs._name
    tn = ts._name
    ev_name = t._ev._type
    transition_name = self.visualize_make_transition_name(t)
    g.add_edge(fn, transition_name)
    e = g.get_edge(fn, transition_name)
    e.attr['arrowhead'] = "none"
    e.attr['tooltip'] = " "
    # e.attr["len"] = 2
    n = g.get_node(transition_name)
    n.attr['tooltip'] = " "
    label = ev_name
    if None != t._acts and len(t._acts) > 0:
      act_name = t._acts[0]
      label = f"""
      <<TABLE 
        border="0"
        cellborder="0"
      >
        <TR><TD>{ev_name}</TD></TR>
        <HR/>
        <TR><TD><I>{act_name}</I></TD></TR>
      </TABLE>>
      """.strip()
    n.attr['label'] = label
    n.attr['shape'] = "plaintext"
    g.add_edge(transition_name, tn)
    e = g.get_edge(transition_name, tn)
    e.attr['tooltip'] = " "
    t.visualize_annotate = partial(set_attr_key, n.attr, 'tooltip')

  ##############################################################################
  def visualize_transition(self, t: Transition, g):
      fs = t._from
      ts = t._to
      fn = fs._name
      tn = ts._name
      if False == t.is_naive:
        self.visualize_complex_transition(t, g)
      else:
        self.visualize_naive_transition(t, g)

  ##############################################################################
  def visualize_special_states(self, g):
    # initial state
    n = g.get_node("*")
    n.attr['label'] = ""
    n.attr["shape"] = "circle"
    n.attr["style"] = "filled"
    n.attr["fillcolor"] = "black"
    # terminal state
    n = g.get_node("X")
    n.attr['label'] = ""
    n.attr["shape"] = "doublecircle"
    n.attr["style"] = "filled"
    n.attr["fillcolor"] = "black"

  ##############################################################################
  def gen_code(self, *, state_class_name = "States"):
    tt = self.transition_table
    lines = []
    first_state_name = None
    initial_transition_made = False
    for t in tt:
      fn = t._from._name
      tn = t._to._name
      if fn == '*':
        first_state_name = tn
        continue
      init_trans = ""
      if fn == first_state_name and False == initial_transition_made:
        init_trans = "*"
        initial_transition_made = True
      ev = ""
      if None != t._ev:
        ev = f" + (event<{t._ev._type}>) "
      if None != t._acts and len(t._acts) > 0:
        ev = f"{ev}/ {t._acts[0]} "
      line = f'{init_trans}("{t._from._name}"_s){ev}= ("{t._to._name}"_s)'
      lines.append(line)
    sas = self.state_actions
    for sa in sas:
      if None != sa._entry_action:
        line = f'"{sa._name}"_s + sml::on_entry<_> / {sa._entry_action}'
        lines.append(line)
      if None != sa._exit_action:
        line = f'"{sa._name}"_s + sml::on_exit<_> / {sa._exit_action}'
        lines.append(line)
      print(line)
    table_content = '\n,'.join(lines)
    code_txt = f"""
    struct {state_class_name}
    {{
      auto operator()()
      {{
        using namespace boost::sml;
        return make_transition_table(
          {table_content}
        );
      }}
    }}
    """
    print(code_txt)

  ##############################################################################

#############
#           #
#############
state = State
state_chart = StateChart