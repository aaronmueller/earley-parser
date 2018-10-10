# Basic implementation of Earley
# NLP Homework 4 - Fall 2018
import sys
import numpy

# Represents a grammar rule read in from .GR file
class GrRule:
  def __init__(self, prob, lhs, rhs):
    self.prob = prob
    self.lhs = lhs
    self.rhs = rhs

  def print(self):
    print("   " + self.lhs + " --> ", end="")
    for s in self.rhs:
      print(s, end="\t")

def read_grammar(filename):
  """Read grammar rules from an external file.
  The rules are read into a list of GrRule.
  """
  grammar_rules = []
  with open(filename) as infile:
    for line in infile:
      if len(line) > 2:
        arr = line.split()
        prob = float(arr.pop(0))
        lhs = arr.pop(0)
        grammar_rules.append(GrRule(prob, lhs, arr))

  return grammar_rules


# Represents a single entry (i.e., the rule, the start index, and the period index)
class Entry:
  def __init__(self, rule_index, start_index, period_index):
    self.rule_index = rule_index
    self.start_index = start_index
    self.period_index = period_index

  def print(self):
    print("  start_index " + str(self.start_index) + " period_index " + str(self.period_index))

# This main function coordinates all the code to run
def main():
  if len(sys.argv) != 3:
    sys.exit("Usage: basic_earley grammar.gr sentences.sen")
  grammar_rules = read_grammar(sys.argv[1])

  with open(sys.argv[2]) as sen_file:
    for sentence in sen_file:
      if len(sentence.strip()) > 2:
        words = sentence.split()
        N = len(words) + 1

        arr = [[] for x in range(0,N)]
        arr[0].append(Entry(0,0,0))

        rules_added = numpy.empty((len(grammar_rules), N), dtype=bool)
        rules_added.fill(False)
        rules_added[0][0] = True

        for icol in range(0, N): # iterates over columns in Earley table

          irow = 0  # this index into arr[i] keeps track of which item remains to predict or scan
          while irow < len(arr[icol]): # arr[i] can have additional items added in this loop
            len_rhs = len(grammar_rules[arr[icol][irow].rule_index].rhs)
            period_index = arr[icol][irow].period_index
            if period_index > len_rhs: # this means there is an error
              sys.exit("ERROR: period_index > len_rhs")
            elif period_index < len_rhs: # This means NOT finished
              entry_to_expand = grammar_rules[arr[icol][irow].rule_index].rhs[period_index]

              if icol < len(words) and entry_to_expand == words[icol]: # match to nonterminal
                new_entry = Entry(arr[icol][irow].rule_index, arr[icol][irow].start_index, 1)
                arr[icol+1].append(new_entry)
                rules_added[new_entry.rule_index][icol+1] = True

                print("SCANNER Added in Col=" + str(icol+1) + " Row=" + str(len(arr[icol+1])))
                grammar_rules[new_entry.rule_index].print()
                new_entry.print()

              else:
                for irule in range(0, len(grammar_rules)):
                  if not rules_added[irule][icol]:
                    if grammar_rules[irule].lhs == entry_to_expand:
                      new_entry = Entry(irule, icol, 0)
                      arr[icol].append(new_entry)
                      rules_added[irule][icol] = True  # note that this rule already added

                      print("PREDICTOR Added in Col=" + str(icol) + " Row=" + str(len(arr[icol])))
                      grammar_rules[new_entry.rule_index].print()
                      new_entry.print()
            else: # if we are here, we have a completed item and we need to run ATTACH (a/k/a COMPLETE)
              match_seeking = grammar_rules[arr[icol][irow].rule_index].lhs
              icol2 = arr[icol][irow].start_index
              for irow2 in range(0, len(arr[icol2])):
                entry2 = arr[icol2][irow2]
                if entry2.period_index < len(grammar_rules[entry2.rule_index].rhs):
                  # then this may be seeking a completion
                  possible_match = grammar_rules[entry2.rule_index].rhs[entry2.period_index]
                  if possible_match == match_seeking: # if this is true, we have a "customer" to "attach"
                    new_entry = Entry(entry2.rule_index, entry2.start_index, entry2.period_index + 1)
                    arr[icol].append(new_entry)

                    print("COMPLETER Added in Col=" + str(icol) + " Row=" + str(len(arr[icol])))
                    grammar_rules[new_entry.rule_index].print()
                    new_entry.print()

            irow += 1


main() # starts execution