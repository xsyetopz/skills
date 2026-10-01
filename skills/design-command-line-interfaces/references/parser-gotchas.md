# Parser gotchas

Sources: [Python argparse](https://docs.python.org/3/library/argparse.html),
[Cobra](https://pkg.go.dev/github.com/spf13/cobra),
[clap](https://docs.rs/clap/latest/clap/).

## Flags before and after the subcommand

In `argparse`, adding the same flags to subparsers with `parents=[common]`
overwrites a value given before the subcommand with the subparser's default:
`todo --store x.json add t` then writes to the default path. `parents=` also
shares the `Action` objects, so `set_defaults` on one parser changes the
default for all of them. Suppress defaults on the shared parser and apply
them once after parsing:

```python
common = argparse.ArgumentParser(
    add_help=False, argument_default=argparse.SUPPRESS
)
# parents=[common] on the top parser and on every subparser
args = top.parse_args(argv)
for name, value in GLOBAL_DEFAULTS.items():
    vars(args).setdefault(name, value)
```

Cobra uses `PersistentFlags()`; clap uses `global = true` on the argument.
If the parser cannot accept both positions, reject the misplaced flag with
an error that says where it goes. Verify by running both orders against a
temporary path and comparing the effect.

## Aliases, deprecation, and hiding

| Parser | Alias | Deprecate or hide |
| --- | --- | --- |
| Python `argparse` | `add_parser(name, aliases=[...])`, shown in help | `deprecated=True` on `add_parser` and `add_argument` (3.13+); its warning does not name the replacement, so print your own |
| Go Cobra | `Command.Aliases` | `Command.Deprecated = "use X"`, `Command.Hidden`; pflag `MarkDeprecated(name, msg)`, `MarkHidden` |
| Rust clap | `alias`, `visible_alias` on `Command` and `Arg` | `hide(true)`; print the warning in the handler |

- `argparse` has no hide option for subcommands: `help=argparse.SUPPRESS`
  prints `==SUPPRESS==` in the command list. Register the old name as a
  second `add_parser` call without `help=` instead, and set `metavar` on
  `add_subparsers` to the visible names (`metavar='{add}'`), or the usage
  line still lists the alias.
- For env vars and config keys, read the new name first, fall back to the
  old one, and warn only when the old one alone is set.
- Test that the old name still works, warns on stderr, prints nothing extra
  to stdout, and is absent from `--help`.
