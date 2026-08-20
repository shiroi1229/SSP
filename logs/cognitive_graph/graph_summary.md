# Cognitive Graph Summary

- **Generated At:** 2025-11-05T23:46:36.258302
- **Total Nodes:** 30
- **Total Edges:** 24

## Node Types
- Module: 4 nodes
- Value: 4 nodes
- Contract Field: 13 nodes
- Context Key: 9 nodes

## Edge Relations
- Has Value: 9 edges
- Has Outputs Field: 5 edges
- Semantically Linked: 2 edges
- Has Inputs Field: 8 edges

## Example Nodes
- `context.short_term.session.state` (Type: context_key)
- `value.active_purchase` (Type: value)
- `context.short_term.user.intent` (Type: context_key)
- `value.purchase` (Type: value)
- `context.short_term.user.feedback_score` (Type: context_key)

## Example Edges
- `context.short_term.session.state` -[has_value]-> `value.active_purchase`
- `context.short_term.user.intent` -[has_value]-> `value.purchase`
- `context.short_term.user.feedback_score` -[has_value]-> `value.0.95`
- `context.mid_term.session.state` -[has_value]-> `value.active_purchase`
- `context.mid_term.user.feedback_score` -[has_value]-> `value.0.95`

