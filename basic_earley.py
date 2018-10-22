'''
Authors: Aaron Mueller, Andrew Blair-Stanek
Date: 24 October 2018
Course: Natural Language Processing
Instructor: Jason Eisner
Assignment: HW4 -- Parsing
'''
# Basic implementation of (non-probabilistic) Earley parser

import sys
import numpy
import math

# This class represents a single grammar rule read in from .GR file
class GrRule:
    def __init__(self, prob, lhs, rhs):
        self.prob = prob
        self.weight = -math.log(self.prob, 2)
        self.lhs = lhs
        self.rhs = rhs

    def print(self, index_period = -1):
        print("   " + self.lhs + " --> ", end="")
        for i in range(0, len(self.rhs)):
            if i == index_period:
                print(" . ", end="")
            print(self.rhs[i], end="  ")

        if index_period == len(self.rhs):
            print(" . ", end="")


# This class represents a single entry (i.e., the rule, the start index, and the period index)
class Entry:
    def __init__(self, rule_index, start_index, period_index):
        self.rule_index = rule_index
        self.start_index = start_index
        self.period_index = period_index
        self.back = []


# This class represents the entire parser
class EarleyParser:
    def __init__(self):
        self.grammar_rules = None
        self.num_rules = -1
        self.chart = None
        self.states_added = None

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
        new_entry = Entry(state.rule_index, state.start_index, state.period_index+1)
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
                                      entry2.period_index + 1)
                    new_entry.back.append(state)
                    new_entry.back.extend(entry2.back)

                    self.enqueue(new_entry, i_col, "COMPLETER")


    # This is a crucial helper function in Earley, see J&M p.444
    # It tries to add a state to the chart a column i_col.
    # It only adds that state if it has not already been added in i_col.
    def enqueue(self, state, column, which_function):
        tuple_version_of_state = (state.rule_index, state.start_index, state.period_index)
        if tuple_version_of_state not in self.states_added[column]:
            self.chart[column].append(state)
            self.states_added[column][tuple_version_of_state] = True

            # print(which_function + " resulted in adding the following at Col = " +
            #         str(column) + " Row = " + str(len(self.chart[column])))
            # print(str(state.start_index), end="  ")
            # self.grammar_rules[state.rule_index].print(state.period_index)
            # print(" (period_index " + str(state.period_index) + ")")

    def dfs(self, state):
        children = state.back
        while children:
            node = children.pop()
            print("("+self.grammar_rules[node.rule_index].lhs,end=" ")
            if not node.back:
                print(self.grammar_rules[node.rule_index].rhs[0],end="")
            self.dfs(node)
        print(")",end=" ")

    def parse(self, sentence_filename):
        sen_file = open(sentence_filename)  # open .SEN file
        for sentence in sen_file:
            if len(sentence.strip()) > 2:
                words = sentence.split()

                self.chart = [[] for x in range(0, len(words)+1)]       # create the chart columns
                self.states_added = [{} for x in range(0, len(words)+1)] # list of dictionaries for state used
                self.enqueue(Entry(0, 0, 0), 0, "DUMMY START STATE") # add the first rule to the start of the chart

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
            
            # print whether sentence was in grammar and parse tree
            valid_sentence = False
            for state in self.chart[-1]:
                rule = self.grammar_rules[state.rule_index]
                if rule.lhs == "ROOT":
                    valid_sentence = True
                    self.dfs(state)
                    break
            
            if not valid_sentence:
                print("Invalid sentence.")


# This main function coordinates all the code to run
def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: basic_earley grammar.gr sentences.sen")
    parser = EarleyParser()
    parser.read_grammar_rules(sys.argv[1])
    parser.parse(sys.argv[2])

main() # starts execution
