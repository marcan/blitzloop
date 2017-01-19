# Configuration

There's a couple of command line flags you can use with `blitzloop` - run
`blitzloop --help` to see them. All of them can be overriden via one of two
config files:

 * `/etc/blitzloop/blitzloop.conf`
 * `$XDG_CONFIG_HOME/blitzloop/blitzloop.conf` (generally
   `~/.config/blitzloop/blitzloop.conf`)

See [this file][example.conf] for an example. You don't **need** a config file,
if you're happy with defaults.

# One shot

You can use `blitzloop-single` to quickly play a particular song. This is useful
for song-testing, and when you're really desperate for a quick karaoke fix. You
need to point `blitzloop-single` at a specific `song.txt` file. See
`blitzloop-single`'s help for more details.
