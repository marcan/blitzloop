# Command line options

You can run `blitzloop` with `-fs` flag - it'll force it to run in full screen
mode. You can also provide the location of songs as an argument to `blitzloop`,
like this:

```shell
blitzloop -fs ~/workarea/blitzloop/songs
```

The commandline above will launch blitzloop in full screen mode, and read songs
from `~/workarea/blitzloop/songs`.

# Configuration

Blitzloop reads a config file from `~/.blitzloop/cfg`. See [this
file][example.cfg] for an example. You don't **need** a config file, if you're
happy with defaults.

# One shot

You can use `blitzloop-single` to quickly play a song. This is useful for
song-testing, and when you're really desperate for a quick karaoke fix. You need
to point `blitzloop-single` at a specific `song.txt` file. See
`blitzloop-single`'s help for more details.
