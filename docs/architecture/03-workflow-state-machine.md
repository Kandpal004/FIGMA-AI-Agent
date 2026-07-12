# The Workflow State Machine

The design pipeline is an explicit, data-defined state machine. Its **definition**
lives in `core/contracts/workflow.py` (so the API and orchestrator share one
source of truth); its **execution** lives in `orchestration/state_machine.py`.

## States

| State | Meaning | Owning agent |
|-------|---------|--------------|
| `CREATED` | Run initialized | — (bootstrap) |
| `RESEARCH` | Market/competitor/user research | Research |
| `STRATEGY` | Business & conversion strategy | Business Analyst |
| `UX` | UX architecture & flows | UX Architect |
| `WIREFRAME` | Low-fidelity structure | Information Architect |
| `WIREFRAME_REVIEW` | Reviewer gate on the wireframe | Reviewer |
| `UI` | High-fidelity visual design | Senior UI Designer |
| `UI_REVIEW` | Reviewer gate on the UI | Reviewer |
| `DESIGN_SYSTEM_VALIDATION` | Token/component conformance | Design System Architect |
| `ACCESSIBILITY_VALIDATION` | WCAG conformance | Accessibility Expert |
| `PERFORMANCE_VALIDATION` | Core Web Vitals budget | Performance Expert |
| `CREATIVE_DIRECTOR_GATE` | Final authority | Creative Director |
| `SECTION_COMPLETE` | Terminal — success | — |
| `FAILED` | Terminal — error/escalation | — |

## The graph

```text
CREATED ──advance──► RESEARCH ──► STRATEGY ──► UX ──► WIREFRAME
                                              ▲          │
                                              │          ▼
                              (reject)  WIREFRAME_REVIEW ─┤
                                              │ advance
                                              ▼
                                              UI ◄──────────────┐
                                              │                 │
                                              ▼                 │ reject
                                        UI_REVIEW ──reject──────┤
                                              │ advance         │
                                              ▼                 │
                          DESIGN_SYSTEM_VALIDATION ──reject──────┤
                                              │ advance         │
                                              ▼                 │
                          ACCESSIBILITY_VALIDATION ──reject──────┤
                                              │ advance         │
                                              ▼                 │
                          PERFORMANCE_VALIDATION ──reject────────┤
                                              │ advance         │
                                              ▼                 │
                          CREATIVE_DIRECTOR_GATE ──reject────────┘
                                              │ approve
                                              ▼
                                       SECTION_COMPLETE
```

`FAIL` is legal from **any** non-terminal state and always targets `FAILED`; it
is synthesized by `next_states()` rather than enumerated, since failure handling
is uniform across the pipeline.

## The two loops that matter

1. **Review loops.** The Reviewer can bounce a wireframe back to `UX` and a UI
   back to `UI`. Each validation stage (design-system, accessibility, performance)
   can likewise bounce work back to `UI`.

2. **The Creative-Director veto.** From `CREATIVE_DIRECTOR_GATE`, `REJECT` loops
   the entire section back to `UI` for redesign and increments `redesign_count`.
   The Creative Director holds **final authority**: nothing ships as
   `SECTION_COMPLETE` without its `ADVANCE` (approval).

## Auditability

Every applied transition appends a `TransitionRecord` (`from_state`, `event`,
`to_state`, `agent_role`, `notes`, timestamp) to the run's history. The sequence
of these **is** the answer to "why did the Creative Director reject this?" — each
rejection is persisted with its notes.

## Purity & resumability

`StateMachine.apply()` returns a new `RunRecord` and performs no I/O. Persistence
is the mediator's job. This separation makes transitions referentially
transparent, keeps the rules testable without infrastructure, and — because every
transition is saved — makes any run resumable from its last persisted state.
