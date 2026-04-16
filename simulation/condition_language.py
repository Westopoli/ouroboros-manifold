"""
Restricted expression language for behavior script transition conditions and
reactive hook predicates.

Supported grammar:
    expr         ::= or_expr
    or_expr      ::= and_expr ("or" and_expr)*
    and_expr     ::= not_expr ("and" not_expr)*
    not_expr     ::= "not" not_expr | compare_expr
    compare_expr ::= atom (OP atom)?
    atom         ::= NUMBER | STRING | BOOL
                   | "bus." IDENT
                   | "timer." ("elapsed_sec" | "expired")
                   | force_hp_fraction
                   | force_unit_count
                   | "enemy_unit_in_range" "(" STRING "," NUMBER ")"
                   | "player_force_hp_fraction_in_zone" "(" STRING ")"
                   | "structure_owner" "(" STRING ")"

No eval(), no exec(), no arbitrary Python. Unknown identifiers are rejected at
parse time.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable

from trigger_bus import TriggerBus


# ── AST nodes ─────────────────────────────────────────────────────────────────

@dataclass
class NumLit:
    value: float

@dataclass
class StrLit:
    value: str

@dataclass
class BoolLit:
    value: bool

@dataclass
class BusAccess:
    flag: str

@dataclass
class TimerAccess:
    field: str  # "elapsed_sec" | "expired"

@dataclass
class ForceFrac:
    pass

@dataclass
class ForceCount:
    pass

@dataclass
class EnemyInRange:
    zone_id: str
    radius: float

@dataclass
class PlayerFracInZone:
    zone_id: str

@dataclass
class StructureOwner:
    structure_id: str

@dataclass
class Compare:
    left: Any
    op: str
    right: Any

@dataclass
class BinOp:
    left: Any
    op: str   # "and" | "or"
    right: Any

@dataclass
class Not:
    operand: Any


# ── Evaluation context ─────────────────────────────────────────────────────────

@dataclass
class EvaluationContext:
    force_hp_fraction: float
    force_unit_count: int
    timer_elapsed_sec: float
    timer_expired: bool
    bus: TriggerBus
    enemy_unit_in_range_fn: Callable[[str, float], bool] | None = None
    player_force_hp_in_zone_fn: Callable[[str], float] | None = None
    structure_owner_fn: Callable[[str], str] | None = None


# ── Validation error ───────────────────────────────────────────────────────────

@dataclass
class ValidationError:
    message: str

    def __str__(self):
        return self.message


# ── Tokenizer ─────────────────────────────────────────────────────────────────

_KNOWN_PREDICATES = frozenset({
    "force_hp_fraction",
    "force_unit_count",
    "enemy_unit_in_range",
    "player_force_hp_fraction_in_zone",
    "structure_owner",
})

_KEYWORD_TOKENS = {"and": "AND", "or": "OR", "not": "NOT", "true": "TRUE", "false": "FALSE"}


class _Token:
    __slots__ = ("type", "value")

    def __init__(self, type_: str, value: Any):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f"Token({self.type!r}, {self.value!r})"


def _tokenize(expr: str) -> list[_Token]:
    tokens: list[_Token] = []
    i = 0
    n = len(expr)

    while i < n:
        c = expr[i]

        if c.isspace():
            i += 1
            continue

        # Number (including leading minus for negative literals)
        if c.isdigit() or (c == '-' and i + 1 < n and expr[i + 1].isdigit()):
            j = i + 1
            while j < n and (expr[j].isdigit() or expr[j] == '.'):
                j += 1
            tokens.append(_Token("NUMBER", float(expr[i:j])))
            i = j
            continue

        # Single-quoted string
        if c == "'":
            j = i + 1
            while j < n and expr[j] != "'":
                j += 1
            if j >= n:
                raise SyntaxError(f"Unterminated string literal at position {i}")
            tokens.append(_Token("STRING", expr[i + 1:j]))
            i = j + 1
            continue

        # Identifier, keyword, or special prefix (bus., timer.)
        if c.isalpha() or c == '_':
            j = i
            while j < n and (expr[j].isalnum() or expr[j] == '_'):
                j += 1
            word = expr[i:j]

            if word in _KEYWORD_TOKENS:
                tokens.append(_Token(_KEYWORD_TOKENS[word], word))
                i = j
                continue

            # bus.<flag> — must be followed by '.'
            if word == "bus":
                if j < n and expr[j] == '.':
                    k = j + 1
                    while k < n and (expr[k].isalnum() or expr[k] == '_'):
                        k += 1
                    if k == j + 1:
                        raise SyntaxError("Expected flag name after 'bus.'")
                    tokens.append(_Token("BUS", expr[j + 1:k]))
                    i = k
                else:
                    raise SyntaxError("'bus' must be used as 'bus.<flag_name>'")
                continue

            # timer.<field> — must be followed by '.'
            if word == "timer":
                if j < n and expr[j] == '.':
                    k = j + 1
                    while k < n and (expr[k].isalnum() or expr[k] == '_'):
                        k += 1
                    field = expr[j + 1:k]
                    if field not in ("elapsed_sec", "expired"):
                        raise SyntaxError(
                            f"Unknown timer field {field!r}; valid: elapsed_sec, expired"
                        )
                    tokens.append(_Token("TIMER", field))
                    i = k
                else:
                    raise SyntaxError("'timer' must be used as 'timer.elapsed_sec' or 'timer.expired'")
                continue

            if word in _KNOWN_PREDICATES:
                tokens.append(_Token("PREDICATE", word))
                i = j
                continue

            raise SyntaxError(f"Unknown identifier: {word!r}")

        # Two-character operators
        if c in ('<', '>', '=', '!'):
            if i + 1 < n and expr[i + 1] == '=':
                tokens.append(_Token("OP", expr[i:i + 2]))
                i += 2
            else:
                tokens.append(_Token("OP", c))
                i += 1
            continue

        if c == '(':
            tokens.append(_Token("LPAREN", "("))
            i += 1
            continue
        if c == ')':
            tokens.append(_Token("RPAREN", ")"))
            i += 1
            continue
        if c == ',':
            tokens.append(_Token("COMMA", ","))
            i += 1
            continue

        raise SyntaxError(f"Unexpected character {c!r} at position {i}")

    tokens.append(_Token("EOF", None))
    return tokens


# ── Recursive-descent parser ───────────────────────────────────────────────────

class _Parser:
    def __init__(self, tokens: list[_Token]):
        self._tokens = tokens
        self._pos = 0

    def _peek(self) -> _Token:
        return self._tokens[self._pos]

    def _consume(self, type_: str | None = None) -> _Token:
        tok = self._tokens[self._pos]
        if type_ is not None and tok.type != type_:
            raise SyntaxError(f"Expected {type_!r} but got {tok.type!r} ({tok.value!r})")
        self._pos += 1
        return tok

    def parse(self) -> Any:
        node = self._parse_or()
        if self._peek().type != "EOF":
            raise SyntaxError(f"Unexpected token: {self._peek()!r}")
        return node

    def _parse_or(self) -> Any:
        left = self._parse_and()
        while self._peek().type == "OR":
            self._consume()
            right = self._parse_and()
            left = BinOp(left, "or", right)
        return left

    def _parse_and(self) -> Any:
        left = self._parse_not()
        while self._peek().type == "AND":
            self._consume()
            right = self._parse_not()
            left = BinOp(left, "and", right)
        return left

    def _parse_not(self) -> Any:
        if self._peek().type == "NOT":
            self._consume()
            return Not(self._parse_not())
        return self._parse_compare()

    def _parse_compare(self) -> Any:
        left = self._parse_atom()
        if self._peek().type == "OP":
            op = self._consume().value
            right = self._parse_atom()
            return Compare(left, op, right)
        return left

    def _parse_atom(self) -> Any:
        tok = self._peek()

        if tok.type == "NUMBER":
            self._consume()
            return NumLit(tok.value)

        if tok.type == "STRING":
            self._consume()
            return StrLit(tok.value)

        if tok.type == "TRUE":
            self._consume()
            return BoolLit(True)

        if tok.type == "FALSE":
            self._consume()
            return BoolLit(False)

        if tok.type == "BUS":
            self._consume()
            return BusAccess(tok.value)

        if tok.type == "TIMER":
            self._consume()
            return TimerAccess(tok.value)

        if tok.type == "PREDICATE":
            return self._parse_predicate()

        raise SyntaxError(f"Unexpected token in atom position: {tok!r}")

    def _parse_predicate(self) -> Any:
        name = self._consume("PREDICATE").value

        if name == "force_hp_fraction":
            return ForceFrac()

        if name == "force_unit_count":
            return ForceCount()

        if name == "enemy_unit_in_range":
            self._consume("LPAREN")
            zone_id = self._consume("STRING").value
            self._consume("COMMA")
            radius = self._consume("NUMBER").value
            self._consume("RPAREN")
            return EnemyInRange(zone_id, radius)

        if name == "player_force_hp_fraction_in_zone":
            self._consume("LPAREN")
            zone_id = self._consume("STRING").value
            self._consume("RPAREN")
            return PlayerFracInZone(zone_id)

        if name == "structure_owner":
            self._consume("LPAREN")
            structure_id = self._consume("STRING").value
            self._consume("RPAREN")
            return StructureOwner(structure_id)

        raise SyntaxError(f"Unknown predicate: {name!r}")  # shouldn't reach here


# ── Parse cache ────────────────────────────────────────────────────────────────

_parse_cache: dict[str, Any] = {}


def _parse(expression: str) -> Any:
    if expression in _parse_cache:
        return _parse_cache[expression]
    tokens = _tokenize(expression)
    node = _Parser(tokens).parse()
    _parse_cache[expression] = node
    return node


def cache_size() -> int:
    return len(_parse_cache)


# ── Evaluator ──────────────────────────────────────────────────────────────────

def _eval(node: Any, ctx: EvaluationContext) -> Any:
    if isinstance(node, NumLit):
        return node.value

    if isinstance(node, StrLit):
        return node.value

    if isinstance(node, BoolLit):
        return node.value

    if isinstance(node, BusAccess):
        return ctx.bus.get_flag(node.flag)

    if isinstance(node, TimerAccess):
        return ctx.timer_elapsed_sec if node.field == "elapsed_sec" else ctx.timer_expired

    if isinstance(node, ForceFrac):
        return ctx.force_hp_fraction

    if isinstance(node, ForceCount):
        return float(ctx.force_unit_count)

    if isinstance(node, EnemyInRange):
        if ctx.enemy_unit_in_range_fn is None:
            return False
        return ctx.enemy_unit_in_range_fn(node.zone_id, node.radius)

    if isinstance(node, PlayerFracInZone):
        if ctx.player_force_hp_in_zone_fn is None:
            return 0.0
        return ctx.player_force_hp_in_zone_fn(node.zone_id)

    if isinstance(node, StructureOwner):
        if ctx.structure_owner_fn is None:
            return "unknown"
        return ctx.structure_owner_fn(node.structure_id)

    if isinstance(node, Compare):
        lv = _eval(node.left, ctx)
        rv = _eval(node.right, ctx)
        try:
            if node.op == "<":  return lv < rv
            if node.op == "<=": return lv <= rv
            if node.op == "==": return lv == rv
            if node.op == ">=": return lv >= rv
            if node.op == ">":  return lv > rv
        except TypeError as e:
            raise TypeError(
                f"Type mismatch in comparison: {type(lv).__name__} {node.op} {type(rv).__name__} — {e}"
            )
        raise RuntimeError(f"Unknown comparison operator: {node.op!r}")

    if isinstance(node, BinOp):
        lv = _eval(node.left, ctx)
        if node.op == "and":
            return lv and _eval(node.right, ctx)
        return lv or _eval(node.right, ctx)

    if isinstance(node, Not):
        return not _eval(node.operand, ctx)

    raise RuntimeError(f"Unhandled AST node type: {type(node).__name__}")


# ── Static analysis passes (validate) ─────────────────────────────────────────

def _collect_bus_flags(node: Any, out: list[str]) -> None:
    if isinstance(node, BusAccess):
        out.append(node.flag)
    elif isinstance(node, (BinOp, Compare)):
        _collect_bus_flags(node.left, out)
        _collect_bus_flags(node.right, out)
    elif isinstance(node, Not):
        _collect_bus_flags(node.operand, out)


# "unknown" means we can't infer statically (callable predicates whose return
# type depends on runtime data). Type checks are skipped for unknown operands.
_NUMERIC  = "numeric"
_STRING   = "string"
_BOOLEAN  = "boolean"
_UNKNOWN  = "unknown"

_ORDERING_OPS = frozenset({"<", "<=", ">", ">="})


def _infer_type(node: Any) -> str:
    if isinstance(node, NumLit):         return _NUMERIC
    if isinstance(node, StrLit):         return _STRING
    if isinstance(node, BoolLit):        return _BOOLEAN
    if isinstance(node, BusAccess):      return _BOOLEAN
    if isinstance(node, TimerAccess):
        return _NUMERIC if node.field == "elapsed_sec" else _BOOLEAN
    if isinstance(node, ForceFrac):      return _NUMERIC
    if isinstance(node, ForceCount):     return _NUMERIC
    if isinstance(node, PlayerFracInZone): return _NUMERIC
    if isinstance(node, StructureOwner): return _STRING
    # EnemyInRange is boolean but is only valid as a standalone condition, not as
    # a comparison operand — treat as unknown so Compare wrapping it is flagged
    # by the "unexpected comparison operand" path, not the type-mismatch path.
    if isinstance(node, EnemyInRange):   return _BOOLEAN
    if isinstance(node, Compare):        return _BOOLEAN
    if isinstance(node, BinOp):          return _BOOLEAN
    if isinstance(node, Not):            return _BOOLEAN
    return _UNKNOWN


def _check_types(node: Any, errors: list[ValidationError]) -> None:
    if isinstance(node, Compare):
        lt = _infer_type(node.left)
        rt = _infer_type(node.right)
        if lt != _UNKNOWN and rt != _UNKNOWN:
            if lt != rt:
                errors.append(ValidationError(
                    f"Type mismatch: cannot compare {lt} {node.op} {rt} "
                    f"(left={type(node.left).__name__}, right={type(node.right).__name__})"
                ))
            elif node.op in _ORDERING_OPS and lt != _NUMERIC:
                errors.append(ValidationError(
                    f"Operator {node.op!r} requires numeric operands, got {lt}"
                ))
        _check_types(node.left, errors)
        _check_types(node.right, errors)
    elif isinstance(node, BinOp):
        _check_types(node.left, errors)
        _check_types(node.right, errors)
    elif isinstance(node, Not):
        _check_types(node.operand, errors)


# ── Public API ─────────────────────────────────────────────────────────────────

def evaluate(expression: str, ctx: EvaluationContext) -> bool | float:
    node = _parse(expression)
    return _eval(node, ctx)


def validate(
    expression: str,
    declared_bus_flags: set[str] | None = None,
) -> list[ValidationError]:
    errors: list[ValidationError] = []
    try:
        node = _parse(expression)
    except SyntaxError as e:
        errors.append(ValidationError(f"Syntax error: {e}"))
        return errors

    _check_types(node, errors)

    if declared_bus_flags is not None:
        used_flags: list[str] = []
        _collect_bus_flags(node, used_flags)
        for flag in used_flags:
            if flag not in declared_bus_flags:
                errors.append(ValidationError(f"Undeclared bus flag: {flag!r}"))

    return errors
