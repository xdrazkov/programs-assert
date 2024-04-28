import os
import parser.parser as parser
import math
from typing import Dict, List, Optional

'''
Works by storing states that can happen during execution.
New state can be created by encountering if statement - there can be 2 states created - one that satisfies the condition and one that doesn't.
Each state has a list of Input_values and remembers what values they can have.
Each state has a list of Variables - each consists of a constant value and a list of Input_values with their coefficient.

In the postCondition it goes through each state and checks whether the condition can be false in any of them.
It decides if it can be false in the state by evaluating the postCondition and checking if it's not always true
    (pretty naively, could be improved by computing the possible range of left side and right side and comparing).

Cases that don't work:
 - can't multiply variable by variable
 - some operations need specific order (x * 2 is invalid)
 - can't have if with more than one input value in condition
 - does not compute range when deciding if it's always true
'''


class Input_value:
    def __init__(self, name: str) -> None:
        self.name = name
        self.min_val: int = -math.inf
        self.max_val: int = math.inf
        self.excluded = set()

    def is_constant(self) -> bool:
        return self.min_val == self.max_val

    def get_constant(self) -> int:
        return self.min_val

    def copy(self) -> "Input_value":
        result = Input_value(self.name)
        result.min_val = self.min_val
        result.max_val = self.max_val
        result.excluded = self.excluded.copy()
        return result

    def is_correct(self) -> bool:
        return self.min_val <= self.max_val


class Input_value_times_x:
    def __init__(self, value: Input_value, times: int = 1) -> None:
        self.value = value
        self.name = value.name
        self.times = times

    def copy(self, values: Dict[str, Input_value]) -> "Input_value_times_x":
        result = Input_value_times_x(values[self.value.name], self.times)
        result.name = self.name
        return result


class Variable:
    def __init__(self, name: str = "") -> None:
        self.name = name
        self.value = 0
        self.values: Dict[str, Input_value_times_x] = {}

    def eval(self) -> Dict[str, int]:
        result = {"constant": self.value}
        for key, value in self.values.items():
            if value.value.is_constant():
                result["constant"] += value.value.get_constant() * value.times
            else:
                result[key] = value.times
        return result

    def copy(self, values: Dict[str, Input_value]) -> "Variable":
        result = Variable()
        result.value = self.value
        result.values = {name: value.copy(values) for name, value in self.values.items()}
        return result

    def number_of_input_values(self) -> int:
        sum = 0
        for _, value_times_x in self.values.items():
            if value_times_x.times != 0:
                sum += 1
        return sum


# Return True only if they are exactly same
def compare_variable_equals(left: Dict[str, int], right: Dict[str, int]) -> bool:
    if left["constant"] != right["constant"]:
        return False
    for key in (list(left.keys()) + list(right.keys())):
        if left.get(key, None) != right.get(key, None):
            return False
    return True


class State:
    def __init__(self) -> None:
        self.variables: Dict[str, Variable] = {}
        self.values: Dict[str, Input_value] = {}

    def copy(self) -> "State":
        result = State()
        result.values = {name: value.copy() for name, value in self.values.items()}
        result.variables = {name: variable.copy(result.values) for name, variable in self.variables.items()}
        return result

    def is_valid(self) -> bool:
        for value in self.values.values():
            if not value.is_correct():
                return False
        return True


def eval_value(value: parser.Value, state: State, new_name="") -> Variable:
    var = Variable()
    if isinstance(value, parser.Constant):
        var.value = value
    elif isinstance(value, parser.Input):
        new_val = Input_value(new_name)
        state.values[new_name] = new_val
        var.values[new_name] = Input_value_times_x(new_val)
    elif isinstance(value, parser.Var):
        var.value = state.variables[value].value
        var.values = state.variables[value].values
    return var


def is_always_true(cond: parser.Comp, state: State) -> bool:
    left = state.variables[cond.l]
    left_eval = left.eval()
    right = cond.r
    if not isinstance(cond.l, parser.Var):
        raise AssertionError("Cant compare")

    right_eval = {"constant": right}
    if isinstance(right, parser.Var):
        right_eval = state.variables[right].eval()

    if len(left_eval.keys()) == 2:
        the_only_variable = list(left.values.values())[0]

    if cond.op == "==":
        if compare_variable_equals(left_eval, right_eval):
            return True
    elif cond.op == "!=":
        if left_eval["constant"] != right_eval["constant"]:
            if len(left_eval.keys()) == 1 and len(right_eval.keys()) == 1:
                return True
    elif cond.op == ">":
        if len(left_eval.keys()) == 1 and len(right_eval.keys()) == 1:
            return left_eval["constant"] > right_eval["constant"]
        if len(left_eval.keys()) == 2 and len(right_eval.keys()) == 1:
            return the_only_variable.value.min_val * the_only_variable.times > right_eval["constant"] - left_eval["constant"]
    elif cond.op == ">=":
        if compare_variable_equals(left_eval, right_eval):
            return True
        if len(left_eval.keys()) == 1 and len(right_eval.keys()) == 1:
            return left_eval["constant"] >= right_eval["constant"]
        if len(left_eval.keys()) == 2 and len(right_eval.keys()) == 1:
            return the_only_variable.value.min_val * the_only_variable.times >= right_eval["constant"] - left_eval["constant"]
    elif cond.op == "<":
        if len(left_eval.keys()) == 1 and len(right_eval.keys()) == 1:
            return left_eval["constant"] < right_eval["constant"]
        if len(left_eval.keys()) == 2 and len(right_eval.keys()) == 1:
            return the_only_variable.value.max_val * the_only_variable.times < right_eval["constant"] - left_eval["constant"]
    elif cond.op == "<=":
        if compare_variable_equals(left_eval, right_eval):
            return True
        if len(left_eval.keys()) == 1 and len(right_eval.keys()) == 1:
            return left_eval["constant"] <= right_eval["constant"]
        if len(left_eval.keys()) == 2 and len(right_eval.keys()) == 1:
            return the_only_variable.value.max_val * the_only_variable.times <= right_eval["constant"] - left_eval["constant"]
    return False


# make 2 states from state and cond -> 2 possible outcomes
# returns False if cant do it, True if can be done
def split_by_cond(cond: parser.Comp, state: State, original: State) -> bool:
    # only support a < constant
    if not isinstance(cond.l, parser.Var):
        raise AssertionError("Unsupported if condition #1")
    left = state.variables[cond.l]
    left_original = original.variables[cond.l]
    right = cond.r

    right_value = cond.r
    right_values = {}
    if isinstance(right, parser.Var):
        right_value = state.variables[cond.r].value
        right_values = state.variables[cond.r].values

    # if theres only one input value on the left var
    if left.number_of_input_values() == 1:
        value_with_x = list(left.values.values())[0]
        original_value_with_x = list(left_original.values.values())[0]
        # input values to be changed to split by condition
        # new value satisfies if condition, original value are all other values
        new_input_value = value_with_x.value
        original_input_value = original_value_with_x.value

    if right_values != {} or len(left.values) > 1:
        raise AssertionError("Unsupported if condition #2")
    if cond.op == "==":
        if left.values == {}:
            return left.value == right_value
        if len(left.values) == 1:
            should_be = right_value // value_with_x.times
            new_input_value.min_val = should_be
            new_input_value.max_val = should_be
            original_input_value.excluded.add(should_be)
    elif cond.op == "!=":
        if left.values == {}:
            return left.value != right_value
        if len(left.values) == 1:
            should_be = right_value // value_with_x.times
            new_input_value.excluded.add(should_be)
            original_input_value.min_val = should_be
            original_input_value.max_val = should_be
    elif cond.op == ">" or cond.op == ">=":
        with_equal = cond.op == ">="
        if left.values == {}:
            if with_equal:
                return left.value >= right_value
            return left.value > right_value
        if len(left.values) == 1:
            should_be = right_value // value_with_x.times

            # choose direction in which it remains true to set bounds
            if (should_be + 1) * value_with_x.times > right_value:
                new_bound = should_be + 1
                if with_equal:
                    new_bound -= 1
                # if it moved to bound to the wrong direction, it can never be true
                if new_bound < new_input_value.min_val:
                    return False
                new_input_value.min_val = new_bound
                original_input_value.max_val = new_bound - 1
            else:
                new_bound = should_be - 1
                if with_equal:
                    new_bound += 1
                if new_bound > new_input_value.max_val:
                    return False
                new_input_value.max_val = new_bound
                original_input_value.min_val = new_bound + 1

    elif cond.op == "<" or cond.op == "<=":
        with_equal = cond.op == "<="
        if left.values == {}:
            if with_equal:
                return left.value <= right_value
            return left.value < right_value
        if len(left.values) == 1:
            should_be = right_value // value_with_x.times

            if (should_be + 1) * value_with_x.times < right_value:
                new_bound = should_be + 1
                if with_equal:
                    new_bound -= 1
                if new_bound < new_input_value.min_val:
                    return False
                new_input_value.min_val = new_bound
                original_input_value.max_val = new_bound - 1
            else:
                new_bound = should_be - 1
                if with_equal:
                    new_bound += 1
                if new_bound > new_input_value.max_val:
                    return False
                new_input_value.max_val = new_bound
                original_input_value.min_val = new_bound + 1
    return True


# if the condition is not always true, then create split state - one that satisfies the condition and one that doesnt
def eval_if(command: parser.If, state: State) -> Optional[State]:
    always_true = is_always_true(command.condition, state)
    if not always_true:
        new_state = state.copy()
        result = split_by_cond(command.condition, new_state, state)
        if not result or not state.is_valid():
            return None
        state = new_state
    for body_command in command.body:
        eval_command(body_command, state)
    if not always_true:
        return state


def sum_variable_input_values(var1: Variable, var2: Variable, multiply_by: int, possible_variables: List[str]) -> Dict[str, Input_value_times_x]:
    result: Dict[str, Input_value_times_x] = {}
    for variable in possible_variables:
        total = 0
        value_obj = None
        if variable in var1.values:
            total += var1.values[variable].times
            value_obj = var1.values[variable].value
        if variable in var2.values:
            total += var2.values[variable].times * multiply_by
            value_obj = var2.values[variable].value
        if total != 0:
            result[variable] = Input_value_times_x(value_obj, total)
    return result


def eval_expression(expr: parser.Expr, state: State) -> Variable:
    new_var = Variable()
    left_value = eval_value(expr.l, state)
    right_value = eval_value(expr.r, state)
    if expr.op == "+":
        new_var.value = left_value.value + right_value.value
        new_var.values = sum_variable_input_values(left_value, right_value, 1, list(state.variables.keys()))
    elif expr.op == "-":
        new_var.value = left_value.value - right_value.value
        new_var.values = sum_variable_input_values(left_value, right_value, -1, list(state.variables.keys()))
    elif expr.op == "*":
        # Only accepts format 2 * x, not x * 2
        if left_value.values != {}:
            raise AssertionError("Cant multiply variable by variable")
        new_var.value *= left_value.value
        for key, value_times_x in right_value.values.items():
            new_var.values[key] = Input_value_times_x(value_times_x.value, value_times_x.times * left_value.value)
    return new_var


def eval_assignment(command: parser.Assignment, state: State) -> None:
    left = command.lhs
    right = command.rhs
    if isinstance(right, parser.Value):
        new_var = eval_value(right, state, left)
    elif isinstance(right, parser.Expr):
        new_var = eval_expression(right, state)
    if new_var is None:
        new_var = Variable()
        new_var.value = 0
    new_var.name = left
    state.variables[left] = new_var


def eval_command(command: parser.Command, state: State) -> Optional[State]:
    if isinstance(command, parser.If):
        return eval_if(command, state)
    elif isinstance(command, parser.Assignment):
        eval_assignment(command, state)
    else:
        raise AssertionError("Unknown command")
    return None


def eval_file(parsed: parser.Program) -> bool:
    state = State()
    for var in parsed.variables:
        state.values[var] = Input_value(var)
    states = [state]

    for command in parsed.commands:
        new_states = []
        for state in states:
            new_state = eval_command(command, state)
            if new_state is not None:
                new_states.append(new_state)
        states.extend(new_states)

    for state in states:
        if not state.is_valid():
            continue
        if not is_always_true(parsed.postCondition, state):
            return True
    return False


def main() -> None:
    files = []
    for file in os.listdir("programs/other"):
        files.append(file)

    # with open("results.txt", "w") as f:
    #     for file in files:
    #         parsed = parser.parse_file("programs/other/" + file)
    #         result = "Assert is true"
    #         try:
    #             false_assert = eval_file(parsed)
    #             if false_assert:
    #                 result = "Assert can be false"
    #         except AssertionError as e:
    #             print(e)
    #             result = str(e)
    #         f.write(str(parsed) + "\n\n" + result + "\n")
    #         f.write("--------------------------------------------------------\n")

    with open("results2.txt", "w") as f:
        for file in files:
            parsed = parser.parse_file("programs/other/" + file)
            result = "Assert is true"
            try:
                false_assert = eval_file(parsed)
                if false_assert:
                    result = "Assert can be false"
            except AssertionError as e:
                print(e)
                result = str(e)
            f.write(file + ": " + result + "\n")


if __name__ == "__main__":
    main()
