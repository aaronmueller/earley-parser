# Basic implementation of Earley
# NLP Homework 4 - Fall 2018
import sys
import numpy
import math

# This class represents a single grammar rule read in from .GR file
class GrRule:
    def __init__(self, prob, lhs, rhs):
        self.prob = prob
        self.lhs = lhs
        self.rhs = rhs
        self.log_prob = math.log(self.prob, 2)

    def to_string(self, index_period = -1):
        s = self.lhs + " -->"
        for i in range(0, len(self.rhs)):
            if i == index_period:
                s += " ."
            s += " " + self.rhs[i]
        if index_period == len(self.rhs):
            s += " . "
        return s


    def print(self, index_period = -1):
        s = self.to_string(index_period)
        print(s, end="")


# This class represents a single entry (i.e., the rule, the start index, and the period index)
class Entry:
    def __init__(self, rule_index, start_index, period_index, backpointers_to_copy = None):
        self.rule_index = rule_index
        self.start_index = start_index
        self.period_index = period_index
        self.backpointers = []  # list of list of *references* to entries upon which this is built
        self.debug_info = None
        if backpointers_to_copy is None:
            self.backpointers = []
            self.backpointers.append([]) # backpointers is a list of lists of references pointing back to entries
        else: # copies over all backpointers
            self.backpointers = []
            for list_backpointers in backpointers_to_copy:
                new_backpointers = list_backpointers.copy()
                self.backpointers.append(new_backpointers)


# This class represents the entire parser
class EarleyParser:
    def __init__(self):
        self.grammar_rules = None
        self.num_rules = -1
        self.chart = None
        self.states_added = None
        self.print_build_info = False # Useful setting to turn to true for debugging

    # Read grammar rules from an external file.
    # The rules are read into a list of GrRule.
    def read_grammar_rules(self, grammar_filename):
        self.grammar_rules = []
        with open(grammar_filename) as infile:
            for line in infile:
                if len(line) > 2:
                    arr = line.split()
                    prob = float(arr.pop(0))
                    lhs = arr.pop(0)
                    self.grammar_rules.append(GrRule(prob, lhs, arr))
        self.num_rules = len(self.grammar_rules)

    # This is the first operator in Earley (out of three), see J&M p.444
    # It expands a possible operator into multiple
    def predictor(self, state, i_col, next_cat):
        for i_rule in range(0, len(self.grammar_rules)):
            if self.grammar_rules[i_rule].lhs == next_cat:
                new_entry = Entry(i_rule, i_col, 0)
                self.enqueue(new_entry, i_col, "PREDICTOR") # attempt to add new state, if not already added


    # This is the second operator in Earley (out of three), see J&M p.444
    # It puts a new completed entry in the NEXT column of the chart
    def scanner(self, state, i_col):
        new_entry = Entry(state.rule_index, state.start_index, state.period_index+1, state.backpointers)
        for backpointer_list in new_entry.backpointers:
            backpointer_list.append(None) # keep an empty entry for non-terminals, which is what scanner() handles
        self.enqueue(new_entry, i_col +1, "SCANNER")


    # This is the third operator in Earley, called "Completer" by J&M p.444
    # It goes back to PRIOR chart entries to find "customers" for a completed state
    def attach(self, state, i_col):
        match_seeking = self.grammar_rules[state.rule_index].lhs
        icol2 = state.start_index
        for irow2 in range(0, len(self.chart[icol2])):
            entry2 = self.chart[icol2][irow2]
            if entry2.period_index < len(self.grammar_rules[entry2.rule_index].rhs):
                # then this may be seeking a completion
                possible_match = self.grammar_rules[entry2.rule_index].rhs[entry2.period_index]
                if possible_match == match_seeking:  # if this is true, we have a "customer" to "attach"
                    new_entry = Entry(entry2.rule_index, entry2.start_index,
                                      entry2.period_index + 1, entry2.backpointers)
                    for backpointer_list in new_entry.backpointers:
                        backpointer_list.append(state) # adds backpointer

                    self.enqueue(new_entry, i_col, "ATTACH")


    # This is a crucial helper function in Earley, see J&M p.444
    # It tries to add a state to the chart a column i_col.
    # It only adds that state if it has not already been added in i_col.
    def enqueue(self, state, column, calling_function):
        tuple_version_of_state = (state.rule_index, state.start_index, state.period_index)

        if tuple_version_of_state in self.states_added[column] and calling_function == "ATTACH":
            existing_state = self.states_added[column][tuple_version_of_state]
            if len(state.backpointers) > 1:
                print("ERROR - incorrect assumption about backpointers being added")
            existing_state.backpointers.append(state.backpointers[0])
            if self.print_build_info:
                print("ADDED BACKPOINTER TO " + existing_state.debug_info)
                for i in range(0, len(existing_state.backpointers)):
                    print("    Backpointers List " + str(i))
                    for bp in existing_state.backpointers[i]:
                        if bp is not None:
                            print("        " + bp.debug_info)
                        else:
                            print("        None")

        elif tuple_version_of_state not in self.states_added[column]:
            self.chart[column].append(state)
            self.states_added[column][tuple_version_of_state] = state

            if self.print_build_info:
                s = str(state.start_index) + " "
                s += self.grammar_rules[state.rule_index].to_string(state.period_index)
                s += "  (Added by " + calling_function + " at Col = " + \
                        str(column) + " Row = " + str(len(self.chart[column]) - 1) + ")"
                print(s)
                state.debug_info = s

                if len(state.backpointers[0]) > 0:
                    for i in range(0, len(state.backpointers)):
                        print("    Backpointers List " + str(i))
                        for bp in state.backpointers[i]:
                            if bp is not None:
                                print("        " + bp.debug_info)
                            else:
                                print("        None")

    # This function starts the first column with all possible expansions of ROOT
    def add_ROOT_expansions(self):
        for i in range(0, len(self.grammar_rules)):
            if self.grammar_rules[i].lhs == "ROOT":
                self.enqueue(Entry(i, 0, 0), 0, "DUMMY START STATE")


    def parse(self, sentence):
        words = sentence.split()

        self.chart = [[] for x in range(0, len(words)+1)] # create the chart
        self.states_added = [{} for x in range(0, len(words)+1)] # list of dictionaries for state used
        self.add_ROOT_expansions() # add all ROOT rules to the start of the chart

        for i_col in range(0, len(words)+1):  # iterates over columns in Earley chart

            i_row = 0  # this index into chart[i] keeps track of which item remains to predict or scan
            while i_row < len(self.chart[i_col]):  # chart[i] can have additional items added during this loop
                state = self.chart[i_col][i_row]
                len_rhs = len(self.grammar_rules[state.rule_index].rhs)
                period_index = state.period_index

                if period_index > len_rhs:  # this means there is an error
                    sys.exit("ERROR: period_index > len_rhs")

                incomplete = period_index < len_rhs # an entry is "complete" if all rules are left of the period

                if incomplete:
                    next_cat = self.grammar_rules[state.rule_index].rhs[period_index]

                    if i_col < len(words) and next_cat == words[i_col]:
                        self.scanner(state, i_col)
                    else:
                        self.predictor(state, i_col, next_cat)
                else:  # if we are here, we have a completed item and we need to run ATTACH (a/k/a COMPLETE)
                    self.attach(state, i_col)

                i_row += 1


    # This recursive helper function prints the subtree
    def print_subtree(self, cur_entry):
        trees = []
        gr_rule = self.grammar_rules[cur_entry.rule_index]
        if len(cur_entry.backpointers[0]) == 0: # We are at a terminal
            trees.append("( " + gr_rule.lhs + " " + gr_rule.rhs[0] + ")")
        else: # not a non-terminal, so we need to go back through backpointers
            for bpl in cur_entry.backpointers:
                trees_bpl = []  # this will contain list of strings generated by just *bpl*'s backpointers
                trees_bpl.append("(" + gr_rule.lhs + " ")
                for i in range(0, len(gr_rule.rhs)):
                    cur_backpointer = bpl[i]
                    if cur_backpointer is None:
                        for j in range(0,len(trees_bpl)):
                            trees_bpl[j] += gr_rule.rhs[i] + " "
                    else:
                        subtrees = self.print_subtree(cur_backpointer)
                        if len(subtrees) == 1:
                            for j in range(0,len(trees_bpl)):
                                trees_bpl[j] = trees_bpl[j] + subtrees[0]
                        else: # this is if there are multiple subtrees
                            new_trees_bpl = []
                            for j in range(0,len(trees_bpl)):
                                for k in range(0, len(subtrees)):
                                    new_trees_bpl.append(trees_bpl[j] + subtrees[k])
                            trees_bpl = new_trees_bpl
                for j in range(0,len(trees_bpl)):
                    trees_bpl[j] = trees_bpl[j] + ")"
                trees = trees + trees_bpl
        return trees

    # This function does the actual printing
    def print(self):
        # first, find all instances of ROOT in the final column
        count_ROOT = 0
        for entry in self.chart[len(self.chart)-1]:
            if self.grammar_rules[entry.rule_index].lhs == "ROOT" and \
                    entry.start_index == 0 and \
                    entry.period_index == len(self.grammar_rules[entry.rule_index].rhs):
                count_ROOT += 1
                trees = self.print_subtree(entry)
                for s in trees:
                    print(s)
#        print("\ncount_ROOT = " + str(count_ROOT))


# This main function coordinates all the code to run
def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: basic_earley grammar.gr sentences.sen")
    parser = EarleyParser()
    parser.read_grammar_rules(sys.argv[1])

    sen_file = open(sys.argv[2])  # open .SEN file
    for sentence in sen_file:
        if len(sentence.strip()) > 0:
            print("***** PARSING SENTENCE: " + sentence)
            parser.parse(sentence)
            parser.print()

main() # starts execution