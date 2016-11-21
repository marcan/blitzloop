# BlitzLoop songfile format

BlitzLoop songs are simple textfiles along with associated resource files. The songs should have the .txt extension, as the songfile scanner will pick up all .txt files as songs. Generally, one song should live in a single directory, with a song.txt file and associated data. However, sometimes it may be convenient to have multiple songs residing in the same directory, if they share resources (e.g. the same background video for multiple versions of the same song).

Songfiles follow a roughly INI-style format, with `[sections]` in brackets and `key=value` pairs, except for the `Lyrics` section. Lines starting with `#` are comments (inline comments after a line are not supported). Blank lines are generally ignored but have significance in the `Lyrics` section. Songfiles always use the UTF-8 character encoding.

## `[Meta]`

The interpretation and supported keys of the `Meta` section are likely to change and expand as more metadata-aware features are added to BlitzLoop, but this is the general design and intent.

Song metadata is defined in a key=value format. Keys can be suffixed by a language qualifier in brackets. The unqualified key should be used with the value in the original native language (e.g. if the song artist is Japanese, their name or stage name in Kanji should generally be used, unless they write preferentially it out in romaji or another script). Qualified keys specify alternative versions of the same metadata value.

The language qualifier can be any lowercase 2-letter language code to specify the localization of that value into a particular language, but this feature should rarely be used and isn't fully supported yet. Instead, the following special single-character qualifiers are supported:

* `[l]`: the value in the Latin alphabet, i.e. romanized. This is not strictly specified, but should generally be a reasonable romanization of the original title. English terms may be used where reasonable (not for actual name portions). For example, 「ももいろクローバーZ & 吉田兄弟」 might be romanized as *Momoiro Clover Z & Yoshida Brothers*. If the unqualified value is already in the Latin alphabet, this is optional.
* `[k]`: the value in the Japanese kana alphabet (hiragana and katakana are both acceptable and will be normalized by the software). This is not yet used, but will be used to implement search and sorting by kana. This will not be displayed, and should not contain non-kana characters.
* `[*]`: the value is a word or phrase in English or a special identifier that is to be looked up in the global localization tables. This is used for the (not yet used) `genre` and `lang` keys, which are expected to be localized into supported UI languages globally.

Currently defined keys are:

* `title`: Title of the song
* `artist`: Artist (generally vocalist) of the song
* `album`: Album (if multiple, generally the original release)
* `seenon`: If the song was promimently featured in another work (e.g. game, TV series, etc.), the name of that work.
* `genre`: Genre, in English (use the `[*]` qualifier).
* `lang`: The ISO 639-1 two-letter language code (use the `[*]` qualifier). If the language does not have an assigned ISO code, spell it out in English. If multiple languages are prominently used, list them in decreasing order of importance, separated by commas.

## `[Song]`

This section defines the audio/video content of the song.

* `audio`: The audio file for the song, relative to the songfile. See the following section for the requirements. Required.
* `video`: The background video to play during the song. This may double as the audio file if it has appropriate multichannel audio muxed in, in which case, the file should be specified in *both* the `audio` and `video` keys.
* `video_offset`: Adjusts the A-V sync between the audio and video, in seconds.
* `aspect`: Forces a specific aspect ratio for the song, specified as a rational or decimal number (e.g. `16/9` is valid). This does not stretch the video itself. Instead, this defines the aspect ratio of the song display. By default, the song aspect ratio is determined from the video file, lyrics are rendered within the bounds of that aspect ratio, and then the result is letterboxed or pillarboxed to match the display aspect. Specifying this value will force the aspect ratio of the song display: `16/9` for a 4:3 video will result in the video being cropped to 16:9, then the song will be rendered on the 16:9 canvas, which will then be letterboxed or pillarboxed to match the display. This is mainly useful for 16:9 source videos that are already letterboxed into 4:3: instead of having the video be pillarboxed again on a widescreen display, this crops it and causes it to display full screen on a 16:9 display, and makes the lyrics fit within the bounds of the image.
* `cover`: Album cover image, for the remote control UI. This should be nearly square, as currently aspect is not preserved (this may change in the future).
* `channels`: The number of additional stereo channels expected in the audio file. Defaults to 1, for a 4-track karaoke audio track. Specify 0 for a standard stereo track. See the following section for details.
* `fade_in`: Time over which to fade in the video at the beginning of the song, in seconds.
* `fade_out`: Time over which to fade out the video at the end of the song, in seconds.
* `volume`: Adjust the playback volume of the audio (defaults to 1, linear scale). Eventually there should be some tool to automatically calculate this based on ReplayGain normalization.

### Audio file structure

BlitzLoop supports user-controllable audio mixing, mainly intended to allow playing back the original vocals at an arbitrary volume. To allow for this, audio files should contain multiple stereo stracks, ideally perfectly synchronized in time. The following cases are supported:

#### `channels=0`

This is a simple stereo audio file. No user controllable mixing is available.

#### `channels=1`

The file should contain two stereo pairs (4 tracks). The first stereo pair should be the instrumental version of the song, while the second stereo pair should be the complete version, with vocals. It is critical that both pairs of tracks are perfectly in phase (or nearly so, to within less than one sample), as any phase mismatches will result in comb filtering effects when the vocal mix slider is at any value other than 0% or 100%.

Note that the vocals slider goes up to 200%. In this case, the end result is that the full track is played at 200% volume, while the instrumental track is played at -100% volume (antiphase). If the phase alignment is correct, this should result in a normal 100% instrumental backing volume, and a 200% vocal volume.

The reason why this case differs from the n > 2 case is that most songs are available as instrumental and full versions, not with a separate vocal track. However, if you're lucky enough to have a clean vocal track, just mix it in with the instrumental and use that as the second pair: the phase alignment will be perfect in this case.

There is a rather primitive tool to help align the tracks into phase in the [blitzloop-tools](https://github.com/marcan/blitzloop-tools) repo.

#### `channels=<n>` for <n> > 2

The file should contain n + 1 stereo pairs. The first stereo pair should be the instrumental version of the song, and each subsequent stereo pair represents an optional channel that will be mixed in (added) to the base instrumental track. The controls allow for mixing volumes from 0% to 200%. This could be used to have multiple vocal tracks that can be independently mixed in.

## `[Timing]`

BlitzLoop internally times songs using beats, which are a piecewise-linear mapping of beat numbers to the song time. This section defines this mapping. It consists of a number of `@<time>=<beat>` control points, where `<time>` is specified in seconds and `<beat>` is an integer beat number. Both values should always be in ascending order. The mapping will interpolate between control points, and extrapolate at the edges. At least two entries are required.

For a song with a constant BPM (timed to a metronome), only two timing entries are required. For example, if you know that the song is 130BPM and the beats have a 300ms offset (i.e. the beats are 300ms late compared to a natural 130BPM grid on the audio file starting at time zero), you can specify it like this:

```ini
[Timing]
@0.3=0
@60.3=130
```

If the song was recorded without a metronome and thus has a slightly inconsistent beat, you will need many entries in order to accurately track the beat of the song. Some songs have variable BPM, or may have an intro recorded without a metronome while the rest of the song has a consistent beat.

If you prefer to time a song in absolute time rather than beats (why would you?), you can specify a dummy timing section:

```ini
[Timing]
@0=0
@1=1
```

This will make beat numbers just correspond to seconds.

## `[Formats]`

BlitzLoop has multiple parsers for lyrics lines optimized for different languages. Songs may contain a mix of lines in various languages and scripts. The song lines are identified with a tag, which maps them to song variants, styles, and parser. This section maps tags to the required parser, in `<tag>=<parser>` format. Tags can be arbitrary alphanumeric strings.

The following parsers are supported:
* `Japanese`
* `Romaji`
* `Latin`
* `English`

These are documented later in this document.

## `[Styles]`

Lyrics can be displayed in multiple styles. This section defines each style with a sub-section header in curly braces (e.g. `{japanese}`), followed by key-value pairs. The style identifier can be any alphanumeric text.

Font characters are doubly stroked: first using a (generally thick) border, and then further using a (generally thinner) outline. The border provides the main visual border effect for the text and is generally used to implement the karaoke scroll effect, while the outline is intended to make it easier to discern the border when the background video is of the same color, and would generally be a fixed color (e.g. black) and not change.

The following keys are supported:

* `font`: The font file to use for the text. There are three built-in fonts that may be used: TakaoMincho.ttf, TakaoPGothic.ttf, TakaoPMincho.ttf. Songs may use custom font files, relative to the songfile directory.
* `ruby_font`: Font used for the ruby text (furigana). Defaults to the same as `font`.
* `size`: Font size, in rather arbitrary units relative to the display width. Try something like 14 for Japanese and 11 for English lyrics. Decimals are supported.
* `ruby_size`: Font size for ruby text. Defaults to half of `size`. May be set to 0 to disable ruby characters, even if the lyrics data contains them.
* `border_width`: Width of the main border around the characters. Defaults to 0.8.
* `outline_width`: Width of the outline around the main border. Defaults to 0.1.
* `colors`: Three comma-separated hex color codes (6 characters each) defining the color of the fill, border, and outline parts of the characters.
* `colors_on`: Same as colors, but after the karaoke "wipe" has passed. This must be different in some discernible way, unless you don't want the wipe effect at all.

## `[Variants]`

Each song can have multiple variants, usually used for different styles or languages. A typical Japanese song will have 3 variants: Japanese, Romaji, and Japanese + Romaji. This section ties together tags and styles to define a particular song variant. It consists of sub-sections headed by an arbitrary identifier in `{curly_braces}`, followed by key=value pairs.

* `name`: The user-visible name for this variant. As the name is not localized, this should generally reflect the language that the variant itself is written in (under the assumption that if the user can read the lyrics they can read the variant name). For example, typical variant names for a Japanese song would be 日本語, Romaji, 日本語 + Romaji.
* `tags`: Comma-separated list of tags that will be shown for this song variant.
* `style`: Style to use by default for all tags.
* `default`: Specify `default=1` to mark the default variant. By default, the first variant is the default choice, but this can be used to specify otherwise if the tags are sorted in some kind of logical way that precludes listing the default first.

Additionally, some settings can be overridden per tag:

* `<tag>.style`: Override the style for this tag
* `<tag>.edge`: Place the lyrics for this tag along the given edge of the screen, `top` or `bottom`. Defaults to `bottom`.

## `[Lyrics]`

This section defines the actual lyrics for the song, and is not in key=value format like the others. Let's look at an example:

```
J: {sis}({シス}){ter}({ター}){'s}(ズ) {noise}({ノイズ}) 捜(さが)し続(つづ)ける$
R: {sis}{ter}{'s} {noise} sagashi tsuzukeru$
@: 66  1 1/2 1/4 3/4 1/2 1/2 1/2 3/4 3/4 1/2 1

J: {彷徨}(さまよ)う心(こころ)の{場所}(ばしょ)を$
R: samayou kokoro no basho wo$
@: 74  1 1/2 1/4 3/4 1/2 1/2 1/2 3/4 3/4 1/2 1
```

A song file consists of a series of *compounds*, which are groups of lyrics lines (*molecules*) that share the same timing. The above example contains two compounds, each containing two molecules and a timing line. The timing lines, which are prefixed by `@`, specify the starting absolute beat (e.g. 32+1/2, which is equivalent to 32.5) and a list of note/syllable durations, called steps (which can be decimal or rational). All molecules in a compound must have the same number of steps. There should be one timing line per compound, though a song file that has not yet been timed may lack timing lines. Compounds are delimited by a blank line.

*Molecules* represent a single indivisible line of lyrics text - they must not overflow the screen width. Molecules are parsed using specific parsers listed in the `[Formats]` section and documented below. Molecules contain *atoms*. For example, the following represents one molecule's contents:

`{彷徨}(さまよ)う心(こころ)の{場所}(ばしょ)を$`

*Atoms* are units of text layout, and are used for grouping ruby text (furigana). An atom consists of a base *particle*\* and a list of ruby (furigana) particles. Atoms by default have a duration of one step, but an atom with ruby particles inherits its length from the number of particles it contains. The above molecule can be broken into atoms like this, with the length in steps:

```
(3) {彷徨}(さまよ)
(1) う
(3) 心(こころ)
(1) の
(2) {場所}(ばしょ)
(1) を
```

Fundamental *particles* are truly indivisible units of text. They may contain more than one character (glyph), but are always treated as one unit. A fundamental particle alone is always one step, and an atom inherits its duration in steps from the number of ruby particles in that atom. In English, we would call a fundamental particle a syllable. In Japanese, we would call it a mora.

The above atoms are broken into particles (in angle brackets) as follows:

```
(3) base: <彷徨> ruby:<さ><ま><よ>
(1) base: <う>
(3) base: <心> ruby:<こ><こ><ろ>
(1) base: <の>
(2) base: <場所> ruby:<ば><しょ>
(1) base: <を>
```

Or, for the more complex first molecule:

```
(1) base: <sis> ruby:<シス>
(1) base: <ter> ruby:<ター>
(1) base: <'s> ruby:<ズ>
(1) base: <noise> ruby:<ノイズ>
(2) base: <捜> ruby:<さ><が>
(1) base: <し>
(2) base: <続> ruby:<つ><づ>
(1) base: <け>
(1) base: <る>
```

And its romaji (tag `R`) version:

```
(1) base: <sis>
(1) base: <ter>
(1) base: <s's>
(1) base: <noise>
(1) base: <sa>
(1) base: <ga>
(1) base: <shi>
(1) base: <tsu>
(1) base: <zu>
(1) base: <ke>
(1) base: <ru>
```

Note that in the `R` molecule all step durations are 1 (as the romaji parser does not support furigana), but the sum of step durations of both the `R` and `J` molecules match. BlitzLoop will complain if there is a duration mismatch, and this is a useful sanity check when writing a song with two variants, which will help catch many syllable splitting/markup errors before the song is timed.

\* In the future, atoms will be extended to support more than one base particle. This will be useful to allow grouping of ruby text for single words (especially English words, but also Kanji compounds) while keeping the timing of the base text accurate, but the syntax for this has not been specified yet. It'll probably involve angle brackets and periods.

### Common parser features

All parsers support escaping special characters with a backslash (`\`).

### Layout control

By default, molecules are laid out on the screen in the order of appearance in the songfile (for those tags which are enabled in the current song variant), which may not match the time of appearance on the screen (which depends on the timing lines). In other words, visual order may not match temporal order, but you should only do this where it makes sense (chiefly, in some duets or when several things are going on at once).

First, molecules are combined into visual lines of text (wrapping, effectively, operates at the molecule level). This means that you should not be afraid to create smaller molecules than one physical line on the screen and, indeed, this is the only way to implement certain effects in a single line, such as simultaneously scrolling portions or changes in style/color.

However, you may find that two molecules with a long pause between them are combined into one line, which then lingers on the screen half-scrolled for the entire duration of the pause. To avoid this, you can use a dollar sign (`$`) as the first or last character of a molecule, to force a line break. Doing this after verses also keeps things neat by tending to align the start with the left side of the screen.

Screen lines are laid out in two groups, from the bottom of the screen or from the top, depending on the tag assignment in the song variant. There is no protection from overlapping both sides of the layout or from running off the screen if too many things are happening at once. The exact algorithm to lay our lines attempts to heuristically do the right thing, and is too convoluted to describe exactly. However, this is how it works, in broad strokes. Assume that lines are numbered from the bottom of the screen, starting with line 0.

* First try to use line 1.
* Then try to use line 0.
* If both are taken, backtrack and try to "push back" previous lines into lines 2, 3, or further.
* Horizontal alignment is left for the topmost/earliest line, right for the bottommost/last line, and center for any intermediate lines. If a single line is on the screen, it is centered.

This works well in the vast majority of cases, but sometimes you may need to hint a line allocation to the layout engine to fix a corner case (typically with duets and simultaneous scrolling, or just to make the flow of verses fit a nice top-bottom rhythm). To do this, prefix a line with `$^<n>` where `<n>` is the line number from the bottom (last = 0, previous = 1, etc.). Note that this is a hint only: it will only take effect if that line position is vacant at the time the current line is laid out, and it will be overridden if subsequent layout requirements force a backtracking for the current line. This only affects bottom-up layout lines: top-down layout uses a simpler algorithm (just start at the top and continue down until the first line is vacant again) that isn't subject to as many corner cases.

### Japanese parser

The `Japanese` parser is designed for Japanese (kanji/kana) text. It considers every character as a single atom, except that certain characters are combined with the preceding character:

`ぁぃぅぇぉゃゅょァィゥェォャュョ 　？！?!…。、.,-「」―-`

Characters may be grouped into a single atom by using curly braces (`{...}`), which is used when they should have a musical value of one step, or to group them for furigana. This can also be used to split up characters that would normally be considered a single atom into multiple steps, e.g. `{ね}{ぇ}`.

Furigana is specified with parentheses after character or group: `心(こころ)` or `{明日}(あした)`. Furigana itself is parsed the same way as base text, that is, may further contain `{}` groups to override the default splitting of characters into particles.

All of these control characters are also interpreted in their doublewidth versions (e.g. `（）` instead of `()`).

As a special case, trailing characters after a furigana group (e.g. punctuation, spaces) will be combined into the same atom, but a special layout flag will be set so that the furigana is centered around the portion before the punctuation. For example, `何(なに)？` will be parsed into a single
`base: <何？> ruby: <な><に>` atom, but the furigana will be centered on top of the 何.

### Romaji parser

The `Romaji` parser is intended for romanized transliterations of Japanese text. It generally works as you would expect for romaji text. The actual algorithm works like this:

* Nonalphabetic characters are appended to the previous atom
* A single vowel after a consonant is part of the same atom
* Consonant pairs like "sh" "ts" "ch" "dz" and "?y" are merged

You can use `{}` groups to override the default splitting into atoms.

### Latin parser

The `Latin` parser is designed as a general parser for languages based on the
Latin alphabet, which heuristically splits syllables. It generally works like this:

* One or more vowels in sequence (aeiouáéíóúäëïöü) anchor an atom (syllable)
* Vowels "own" the consonants around them (until punctuation or whitespace). If there is an odd number of consonants between two vowels, the latter vowel wins the middle consonant.
* Other characters (whitespace, punctuation except for `'`) are appended to the previous syllable.

To force a syllable break, use a period (`.`), e.g. `Wahr.heit`. If you want an actual full stop, you need to escape it (`\.`). You can also use `{}` groups to override the default splitting into atoms.

### English parser

The `English` parser works just like the Latin parser, but `y` at the end of a word is considered a vowel, and `e` at the end of a word is considered neither a consonant nor a vowel (but mostly works like a consonant), because English is a terrible language.

To force a syllable break, use a period (`.`), e.g. `i.ota`. If you want an actual full stop, you need to escape it (`\.`). You can also use `{}` groups to override the default splitting into atoms, as in `{some}thing`.

## Sample songfile

This is a partial example of what a song file looks like. The `R2` and `J2` tags here are used for backing vocals, and are not visible in the `{both}` variant.

```ini
[Meta]
title=光の旋律
title[l]=Hikari no Senritsu
artist=Kalafina
album=光の旋律
album[l]=Hikari no Senritsu
seenon=ソ・ラ・ノ・ヲ・ト
seenon[l]=Sora no Woto
genre[*]=Anime
lang[*]=JA

[Song]
audio=hikarinosenritsu.flac
video=hikari_no_senritsu.mp4
video_offset=0.1
fade_in=5
fade_out=4
cover=cover.jpg

[Timing]
@0.469582=0
@352.901842=564

[Formats]
J=Japanese
J2=Japanese
R=Romaji
R2=Romaji

[Styles]
{japanese}
font=TakaoPGothic.ttf
size=15
outline_width=0.15
border_width=0.8
colors=ffffff,008069,000000
colors_on=208040,ffffff,000000

{japanese_bg}
font=TakaoPGothic.ttf
size=15
outline_width=0.15
border_width=0.8
colors=ffffff,a00000,000000
colors_on=a00000,ffffff,000000

{romaji}
font=TakaoPGothic.ttf
size=12
outline_width=0.15
border_width=0.8
colors=ffffff,008069,000000
colors_on=208040,ffffff,000000

{romaji_bg}
font=TakaoPGothic.ttf
size=12
outline_width=0.15
border_width=0.8
colors=ffffff,a00000,000000
colors_on=a00000,ffffff,000000


[Variants]
{japanese}
name=日本語
tags=J,J2
style=japanese
J2.style=japanese_bg
J2.edge=top

{romaji}
name=romaji
tags=R,R2
style=romaji
R2.style=romaji_bg
R2.edge=top

{both}
name=日本語 + romaji
tags=J,R
J.style=japanese
R.style=romaji
R.edge=top

[Lyrics]

J: この空(そら)の輝(かがや)き
R: kono sora no kagayaki
@: 22  1 1/2 1/2 1 1 1 1/2 1/2 1

J: 君(きみ)の胸(むね)に届(とど)いてる？
R: kimi no mune ni todoiteru?
@: 29  1/2 1/2 1 1/2 1/2 1 1 1 1/2 1/2 1

J: 夢(ゆめ)見(み)てた調(しら)べは
R: yume miteta shirabe wa
@: 38  1 1/2 1/2 1 1 1 1/2 1/2 1

J: 静(しず)けさのように$
R: shizukesa no you ni$
@: 45  1/2 1/2 1 1/2 1/2 1 1 3

```
