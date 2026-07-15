"""Stage — Token Resolution.

Before the specification is assembled, this stage resolves the token graph the architect
proposed: it walks every alias/derivation reference to confirm it terminates at a real token,
rejects a dangling reference, and rejects any alias/derivation *cycle* (a token that
transitively aliases itself). It also confirms every token key referenced by a scale, a system,
a theme override, a component, or a component state exists.

It returns the computed **token integrity** as a :class:`Percentage` (``1.0`` when every
reference resolves cleanly) for the quality scorer, and raises :class:`UnresolvedTokenError`
otherwise. This makes "no hard-coded values, no dangling tokens" a gate, not a hope — the same
guarantee the aggregate enforces, surfaced early with a precise diagnosis.
"""

from __future__ import annotations

from core.errors import DesignDirectorError

from design_system.application.contracts import DesignSystemDraft
from design_system.domain.shared.value_objects import Percentage
from design_system.domain.token.token import TokenSet

__all__ = ["TokenResolver", "UnresolvedTokenError"]


class UnresolvedTokenError(DesignDirectorError):
    """Raised when a token reference dangles or an alias chain forms a cycle."""

    code = "unresolved_design_system_token"
    http_status = 422


class TokenResolver:
    """Resolves and integrity-checks the token graph; returns the integrity ratio."""

    def resolve(self, draft: DesignSystemDraft) -> Percentage:
        tokens = draft.token_set
        self._check_references_resolve(draft, tokens)
        self._check_no_alias_cycle(tokens)
        return Percentage.of(1.0)

    def _require(self, tokens: TokenSet, key: str, context: str) -> None:
        if not tokens.has(key):
            raise UnresolvedTokenError(
                f"{context} references token {key!r} absent from the token set.",
                details={"key": key, "context": context},
            )

    def _check_references_resolve(self, draft: DesignSystemDraft, tokens: TokenSet) -> None:
        for token in tokens.references():
            self._require(tokens, token.value.ref, f"token {token.key!r}")
        for step in (
            *draft.typography.role_tokens,
            *draft.spacing.step_tokens,
            *draft.radius.step_tokens,
            *draft.elevation.level_tokens,
            *draft.shadow.step_tokens,
            *draft.border.width_tokens,
        ):
            self._require(tokens, step, "a token scale")
        for gutter in draft.grid.gutter_tokens.values():
            self._require(tokens, gutter, "the grid system")
        for token_key in (*draft.motion.duration_tokens, *draft.motion.easing_tokens):
            self._require(tokens, token_key, "the motion system")
        for token_key in (
            draft.interaction.focus_ring_token,
            draft.interaction.hit_target_token,
            draft.interaction.transition_token,
        ):
            self._require(tokens, token_key, "the interaction tokens")
        for theme in draft.theme_set:
            for semantic_key, primitive_key in theme.overrides.items():
                self._require(tokens, semantic_key, f"theme {theme.name!r}")
                self._require(tokens, primitive_key, f"theme {theme.name!r}")
        for state in draft.states:
            for token_key in state.token_keys:
                self._require(tokens, token_key, f"state {state.state.value}")
        for spec in draft.component_specs:
            for token_key in spec.token_refs:
                self._require(tokens, token_key, f"component {spec.component.value}")
            for state in spec.states.states:
                for token_key in state.token_keys:
                    self._require(
                        tokens,
                        token_key,
                        f"component {spec.component.value} state {state.state.value}",
                    )

    def _check_no_alias_cycle(self, tokens: TokenSet) -> None:
        adjacency: dict[str, list[str]] = {k: [] for k in tokens.keys()}
        for token in tokens.references():
            adjacency[token.key].append(token.value.ref)

        WHITE, GREY, BLACK = 0, 1, 2
        colour = dict.fromkeys(adjacency, WHITE)

        def visit(key: str) -> None:
            colour[key] = GREY
            for nxt in adjacency.get(key, ()):
                if colour.get(nxt) == GREY:
                    raise UnresolvedTokenError(
                        "Token alias/derivation chain forms a cycle.", details={"key": nxt}
                    )
                if colour.get(nxt) == WHITE:
                    visit(nxt)
            colour[key] = BLACK

        for key in adjacency:
            if colour[key] == WHITE:
                visit(key)
