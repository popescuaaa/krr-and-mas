0. [IMPL(p, q), IMPL(q, r), p, ~r] 

1. [~p, impl(q, r), p, ~r] (expand)

2. [q, impl(q, r), p, ~r] (expand)

3. [~p, ~q, p, ~r] X

4. [~p, r, p, ~r] X

[comment]: <> (5. [q, ~q, p, ~r] X)

[comment]: <> (6. [q, r, p, ~r] X)

- check weather the leaves has no children
- carry the whole `universe` of props to the leaves