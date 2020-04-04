
from krrt.utils import write_file, run_command

from pdkb.actions import Action
from pdkb.kd45 import PDKB
from pdkb.problems import Domain, parse_problem
from pdkb.rml import Belief, Possible, Literal, neg

from trust import gen_trust_props, Trust

class TWProblem(object):

    def __init__(self, name, max_depth, trust_settings, agents, types, capabilities, bargains, propositions, actions, instance_lines):

        self.name = name
        self.max_depth = max_depth
        self.agents = agents
        self.trust_settings = trust_settings
        self.types = types
        self.capabilities = capabilities
        self.bargains = bargains

        # Create our fearless leader (only required for trust)
        #self.agents.add('leader')

        # Create the initial domain and problem (which will be augmented)
        self.domain = Domain(agents, propositions, actions, max_depth, types, 'teamwork-formation-'+name)
        self.problem = parse_problem(instance_lines, self.domain)

        # Make the phase switch action
        self.setup_phase_transition()

        # Deal with trust issues
        #self.setup_trust()

        # Make the agent capability / persuation dialogue
        self.setup_capabilities()
        self.setup_persuation()


    def setup_capabilities(self):
        null_pdkb = PDKB(self.max_depth, self.agents, self.domain.props)
        for ag in self.capabilities:
            for _cap in self.capabilities[ag]:

                cap = Literal(_cap)

                a = Action("ask_cap_%s" % str(cap),
                           self.max_depth,
                           self.agents,
                           self.domain.props,
                           False)

                a.add_pre(self.fluent_formation_phase)
                a.add_pre(cap, True)
                a.add_pre(neg(cap), True)

                a.new_nondet_effect()
                a.add_pos_effect(null_pdkb, null_pdkb, cap)

                a.new_nondet_effect()
                a.add_pos_effect(null_pdkb, null_pdkb, neg(cap))

                a.expand()

                self.domain.actions.append(a)

    def setup_persuation(self):

        null_pdkb = PDKB(self.max_depth, self.agents, self.domain.props)

        for ag in self.agents:
            willing = Literal("willing_%s" % str(ag))
            satisfied = Literal("satisfied_%s" % str(ag))
            self.domain.props.add(satisfied)
            self.domain.props.add(willing)
            self.problem.goal.add_rml(satisfied)

            a = Action("satisfy_unconvinced_agent_%s" % str(ag),
                       self.max_depth,
                       self.agents,
                       self.domain.props,
                       False)
            a.add_pre(self.fluent_end_phase)
            a.add_pre(willing, True)
            a.new_nondet_effect()
            a.add_pos_effect(null_pdkb, null_pdkb, satisfied)
            a.add_pos_effect(null_pdkb, null_pdkb, neg(willing))
            a.expand()
            self.domain.actions.append(a)

            if not self.bargains[ag]:
                self.problem.init.add_rml(satisfied)
                self.problem.init.add_rml(willing)

            else:

                for _barg in self.bargains[ag]:

                    bargain = Literal(_barg)
                    convinced = Literal("convinced_%s_%s" % (str(ag), str(bargain)))
                    self.domain.props.add(convinced)

                    a = Action("bargain_with_%s_for_%s" % (str(ag), str(bargain)),
                               self.max_depth,
                               self.agents,
                               self.domain.props,
                               False)

                    a.add_pre(self.fluent_formation_phase)
                    a.add_pre(convinced, True)
                    a.add_pre(neg(convinced), True)

                    a.new_nondet_effect()
                    a.add_pos_effect(null_pdkb, null_pdkb, convinced)
                    a.add_pos_effect(null_pdkb, null_pdkb, willing)

                    a.new_nondet_effect()
                    a.add_pos_effect(null_pdkb, null_pdkb, neg(convinced))

                    a.expand()
                    self.domain.actions.append(a)


                    a = Action("satisfy_convinced_agent_%s_with_%s" % (str(ag), str(bargain)),
                               self.max_depth,
                               self.agents,
                               self.domain.props,
                               False)

                    a.add_pre(convinced)
                    a.add_pre(Belief(ag, bargain))
                    a.add_pre(self.fluent_end_phase)

                    a.new_nondet_effect()
                    a.add_pos_effect(null_pdkb, null_pdkb, satisfied)

                    a.expand()
                    self.domain.actions.append(a)



    def setup_phase_transition(self):

        null_pdkb = PDKB(self.max_depth, self.agents, self.domain.props)

        self.fluent_formation_phase = Literal('phase_formation')
        self.fluent_plan_phase = Literal('phase_planning')
        self.fluent_end_phase = Literal('phase_final')

        self.domain.props.add(self.fluent_formation_phase)
        self.domain.props.add(self.fluent_plan_phase)
        self.domain.props.add(self.fluent_end_phase)
        self.problem.init.add_rml(self.fluent_formation_phase)
        self.problem.init.add_rml(neg(self.fluent_plan_phase))
        self.problem.init.add_rml(neg(self.fluent_end_phase))

        for a in self.domain.actions:
            a.expand()
            a.add_pre(self.fluent_plan_phase)

        a = Action('xxx_start_planning',
                   self.max_depth,
                   self.agents,
                   self.domain.props,
                   False)
        a.new_nondet_effect()
        a.add_pre(self.fluent_formation_phase)
        a.add_pos_effect(null_pdkb, null_pdkb, self.fluent_plan_phase)
        a.add_pos_effect(null_pdkb, null_pdkb, neg(self.fluent_formation_phase))
        a.expand()
        self.domain.actions.append(a)

        a = Action('xxx_finish_planning',
                   self.max_depth,
                   self.agents,
                   self.domain.props,
                   False)
        a.new_nondet_effect()
        a.add_pre(self.fluent_plan_phase)
        a.add_pos_effect(null_pdkb, null_pdkb, self.fluent_end_phase)
        a.add_pos_effect(null_pdkb, null_pdkb, neg(self.fluent_plan_phase))
        a.expand()
        self.domain.actions.append(a)


    def setup_trust(self):
        # - New props
        self.domain.props += gen_trust_props(self.agents)

        # - Augmented initial state
        for (ag1, ag2) in self.trust_settings['trust']:
            trml = Trust(ag1, ag2)
            self.problem.init.add_rml(trml)
            self.problem.init.add_rml(Belief(ag1, trml))
            self.problem.init.add_rml(Belief('leader', trml))

        for (ag1, ag2) in self.trust_settings['mistrust']:
            trml = Trust(ag1, ag2, negate=True)
            self.problem.init.add_rml(trml)
            self.problem.init.add_rml(Belief(ag1, trml))
            self.problem.init.add_rml(Belief('leader', trml))

        self.problem.init.logically_close()

        # - Build the trust actions

        # - Guard the phase switch


    def compile(self):
        write_file('domain.pddl', self.domain.pddl())
        write_file('problem.pddl', self.problem.pddl())

    def solve(self):
        run_command('./generate-plan domain.pddl problem.pddl',
                    output_file='output.txt', error_file=None,
                   MEMLIMIT=3000, TIMELIMIT=1800)

    def output_solution(self):
        print "Check the output.txt for the plan computation and graph.png for the solution."
