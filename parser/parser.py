import sys

from typing import List, Union, Iterator, Optional, Set


class Input:
    """An object that represents a call to the input() function."""
    def __init__(self):
        pass

    def __str__(self):
        return "input"

Var = str
Constant = int
Value = Union[Var, Constant, Input]

class Expr:
    """
    An object that represents an arithmetic expression "l op r".

    Args:
        op: The applied operation. One of '+', '-', '*'
        l: Left argument of the operation.
        r: Right argument of the operation.
    """

    def __init__(self, op: str, l: Value, r: Value):
        self.op = op
        self.l = l
        self.r = r

    def __str__(self):
        return f"{self.l} {self.op} {self.r}"


class Comp:
    """
    An object that represents an arithmetic comparison "l op r".

    Args:
        op: The applied comparison operation. One of '==', '<', '>', '<=', '>=', '!='.

        l: Left argument of the comparison.
        r: Right argument of the comparison.
    """

    def __init__(self, op: str, l: Value, r: Value):
        self.op = op
        self.l = l
        self.r = r

    def __str__(self):
        return f"{self.l} {self.op} {self.r}"


class Assignment:
    """
    An object that represents an assignment command "lhs = rhs".

    Args:
        lhs: Name of the variable to which is assigned.
        rhs: Value that is assigned to the variable.
    """

    def __init__(self, lhs: Var, rhs: Union[Value, Expr]):
        self.lhs = lhs
        self.rhs = rhs

    def __str__(self):
        return f"{self.lhs} = {self.rhs}"


class If:
    """
    An object that represents a condition "if cond then body end".

    Args:
        condition: The comparison that describes the if condition.
        body: Sequence of assignments that is executed if the condition holds.
    """

    def __init__(self, condition: Comp, body: List[Assignment]):
        self.condition = condition
        self.body = body

    def __str__(self):
        body = ("    " + str(cmd) for cmd in self.body)
        return "if {} then \n{}\nend".format(
            self.condition,
            "\n".join(body))


Command = Union[Assignment, If]

class Program:
    """
    An object that represents the input program.

    Args:
        commands: The body of the program.
        postCondition: The condition that should hold at the end.
        variables: The list of variables used by the program.
    """


    def __init__(self, commands: List[Command],
                 postCondition: Comp,
                 variables: Set[Var]):
        self.commands = commands
        self.postCondition = postCondition
        self.variables = variables

    def __str__(self):
        commands = map(str, self.commands)
        return "Variables: {}\n\nProgram:\n{}\n\nPostcondition:\n{}".format(
            ", ".join(sorted(self.variables)),
            "\n".join(commands),
            self.postCondition)


class Parser:
    """
    An internal object that is used for parsing.
    """

    def __init__(self):
        self.lineStream = []
        self.lastLine = None
        self.postCondition = None
        self.variables = set()


    def parse_value(self, token: str) -> Value:
        if token == "input()":
            return Input()

        try:
            return Constant(int(token))
        except:
            return Var(token)


    def parse_expr(self, tokens: List[str]) -> Union[Value, Expr]:
        if len(tokens) == 1:
            return self.parse_value(tokens[0])
        elif len(tokens) == 3:
            op = tokens[1]
            if op not in ("+", "-", "*"):
                raise RuntimeError(f"Unsupported operation {op}")

            return Expr(op,
                        self.parse_value(tokens[0]),
                        self.parse_value(tokens[2]))
        else:
            raise RuntimeError()


    def parse_cond(self, tokens: List[str]) -> Comp:
        if len(tokens) == 3:
            op = tokens[1]
            if op not in ("==", "<", ">", "<=", ">=", "!="):
                raise RuntimeError(f"Unsupported comparison {op}")

            return Comp(op,
                        self.parse_value(tokens[0]),
                        self.parse_value(tokens[2]))
        else:
            raise RuntimeError(f"Invalid condition {tokens}")


    def parse_command(self, line: str) -> Optional[Command]:
        tokens = line.split()

        if tokens[0] == "assert":
            if self.postCondition is not None:
                raise RuntimeError("Only one assertion can be defined")
            self.postCondition = self.parse_cond(tokens[1:])
            return None

        if tokens[0] == "if":
            if len(tokens) < 5:
                raise RuntimeError("Unexpected end of line")
            elif len(tokens) > 5:
                raise RuntimeError(f"Unexpected token {tokens[5]}")
            else:
                body = self.parse_commands(True)
                return If(self.parse_cond(tokens[1:4]), body)

        if tokens[1] == "=":
            var = tokens[0]
            self.variables.add(var)
            return Assignment(var, self.parse_expr(tokens[2:]))

        raise RuntimeError(f"Unexpected line {tokens}")

    def get_next_line(self):
        try:
            line = next(self.lineStream)
            self.lastLine = line
            return line
        except StopIteration:
            return None

    def parse_commands(self, innerBlock = False) -> List[Command]:
        commands = []

        line = self.get_next_line()
        while line is not None:
            if line.strip() == "end":
                return commands

            command = self.parse_command(line)
            if isinstance(command, If) and innerBlock:
                raise RuntimeError(
                    "Nested if-then blocks are not allowed")

            if command is not None:
                if self.postCondition:
                    raise RuntimeError(
                        "No further commands are allowed after a postcondition")

                commands.append(command)

            line = self.get_next_line()

        if innerBlock:
            raise RuntimeError("Unexpected end of file")
        else:
            return commands


    def parse_program(self, lineIterator: Iterator[str]) -> Program:
        self.lineStream = lineIterator
        commands = self.parse_commands()

        assert(self.postCondition is not None)
        return Program(commands, self.postCondition, self.variables)


def parse_file(filename: str) -> Program:
    """Parses the input program and returns its representation as Program
    object. Also parses the post-condition and passes it as an attribute of the
    Program object.
    """

    with open(filename) as f:
        parser = Parser()
        return parser.parse_program(f)

if __name__ == "__main__":
    program = parse_file(sys.argv[1])
    print(program)
