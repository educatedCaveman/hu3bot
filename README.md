# hu3bot

discord bot for my 3d printer

This bot is currently geared to fetching/posting snapshots of the Voron cams to my 3d printing discord channel.

the current commands are:

| command                           | function                                                                                                                                                   |
| --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `!snapshot (main\|alt)`           | takes a snapshot of either the main or alt camera. defaults to the main cam if no argument provided.                                                       |
| `!snapshit`                       | alias of `!snapshot`, because i keep mistyping it.                                                                                                         |
| `!test`                           | just sends a message for testing                                                                                                                           |
| `Your printer completed printing` | same function as `!snapshot`, but used for responding to a completed print. this is a bad way of doing this, but i can't figure out a better way to do it. |
