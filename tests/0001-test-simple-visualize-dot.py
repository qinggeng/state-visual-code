import sys
sys.path.append("src")
import state_visual_code as svc
s = svc.state
state_chart = svc.state_chart
transition_table = [
  s("*").to("idle"),
  s("idle").via("set_value").action("set_value").to("value_changed"),
  s("value_changed").via("reset").to("idle"),
  s("idle").via("terminate").to("X"),
]

annotates = [
  s("*").to("idle").annotate("""
  初始变换，没有任何动作
  """.strip())
]
state_actions = [
  s("idle").on_entry("on_entry_idle").on_exit("on_exit_idle"),
]

sc = state_chart()
sc.transition_table = transition_table
sc.annotates = annotates
sc.state_actions = state_actions
sc.visualize_dot(output = sys.stdout)