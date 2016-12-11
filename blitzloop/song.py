#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012-2013 Hector Martin "marcan" <hector@marcansoft.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 or version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

from collections import OrderedDict
import codecs
import decimal
import fractions
import os.path
import re
import sys

from blitzloop import util


class ParseError(Exception):
    def __str__(self):
        return self.message.encode(sys.stderr.encoding)

class Particle(object):
    def __init__(self, text):
        self.text = text

    @property
    def steps(self):
        return 1

    def __unicode__(self):
            return "'%s'" % self.text

class Atom(Particle):
    def __init__(self, text):
        Particle.__init__(self, text)
        self.particles = None
        self.particle_edge = None

    @property
    def steps(self):
        if self.particles is None:
            return 1
        else:
            return sum(r.steps for r in self.particles)

    def __unicode__(self):
        if self.particles is None:
            return "'%s'" % self.text
        else:
            return "'%s'" % self.text + "(" + " ".join(map(str,self.particles)) + ")"

class Molecule(object):
    def __init__(self, source):
        self.source = source
        self.break_before = False
        self.break_after = False
        self.row = None
        self.parse(source)

    @property
    def steps(self):
        return sum(g.steps for g in self.atoms)

    @property
    def text(self):
        return "".join(g.text for g in self.atoms)

    @property
    def has_ruby(self):
        return any(atom.particles for atom in self.atoms)

    def __unicode__(self):
        return "Molecule<[%r]" % self.steps + " ".join(map(str, self.atoms)) + ">"

class JapaneseMolecule(Molecule):
    COMBINE_CHARS = "ぁぃぅぇぉゃゅょァィゥェォャュョ 　？！?!…。、.,-「」―-"
    SPACE = "　"

    def parse(self, source):
        self.atoms = []
        in_furi = False
        in_particle = False
        in_escape = False

        self.break_before = self.break_after = False
        self.row = None
        if source and source[0] in "＄$":
            self.break_before = True
            source = source[1:]
            if source and source[0] in "＾^":
                self.row = int(source[1])
                source = source[2:]
        if source and source[-1] in "＄$":
            if source[-2:] not in ("＼＄", "\\$"):
                self.break_after = True
                source = source[:-1]

        for c in source:
            if not in_escape:
                if c in "\\＼":
                    in_escape = True
                    continue
                elif c in "{｛":
                    if in_particle:
                        raise ParseError("Nested atoms")
                    in_particle = True
                    particle_text = ""
                    continue
                elif c in "}｝" and in_particle:
                    if not particle_text:
                        raise ParseError("Empty group")
                    in_particle = False
                    if in_furi:
                        self.atoms[-1].particles.append(Particle(particle_text))
                    else:
                        self.atoms.append(Atom(particle_text))
                    continue
                elif c in "(（":
                    if in_furi:
                        raise ParseError("Nested furigana (%s)" % source)
                    if in_particle:
                        raise ParseError("Furigana within atom (%s)" % source)
                    if not self.atoms:
                        raise ParseError("Furigana with no atom (%s)" % source)
                    in_furi = True
                    self.atoms[-1].particles = []
                    continue
                elif c in ")）" and in_furi:
                    self.atoms[-1].particle_edge = len(self.atoms[-1].text)
                    in_furi = False
                    continue
            else:
                in_escape = False
            if in_particle:
                particle_text += c
            elif c in self.COMBINE_CHARS and not in_escape and self.atoms:
                if in_furi:
                    self.atoms[-1].particles[-1].text += c
                else:
                    self.atoms[-1].text += c
            elif in_furi:
                self.atoms[-1].particles.append(Particle(c))
            else:
                self.atoms.append(Atom(c))
        if in_particle:
            raise ParseError("Incomplete particle")
        if in_furi:
            raise ParseError("Incomplete furigana")
        if in_escape:
            raise ParseError("Incomplete escape")

class RomajiMolecule(Molecule):
    SPACE = " "

    def parse(self, source):
        self.atoms = []
        in_particle = False
        in_escape = False
        last_consonant = None

        self.break_before = self.break_after = False
        if source and source[0] == "$":
            self.break_before = True
            source = source[1:]
            if source and source[0] == "^":
                self.row = int(source[1])
                source = source[2:]
        if source and source[-1] == "$":
            if source[-2:] != "\\$":
                self.break_after = True
                source = source[:-1]

        for c in source:
            if not in_escape:
                if c == "\\":
                    in_escape = True
                    continue
                elif c == "{":
                    if in_particle:
                        raise ParseError("Nested atoms")
                    in_particle = True
                    group_text = ""
                    continue
                elif c == "}" and in_particle:
                    if not group_text:
                        raise ParseError("Empty group")
                    in_particle = False
                    self.atoms.append(Atom(group_text))
                    continue
            else:
                in_escape = False
            if in_particle:
                group_text += c
                last_consonant = None
            elif c.lower() not in "abcdefghijklmnopqrstuvwxyz" and not in_escape and self.atoms:
                self.atoms[-1].text += c
                last_consonant = None
            elif c.lower() in "aiueo":
                if last_consonant is not None:
                    self.atoms[-1].text += c
                else:
                    self.atoms.append(Atom(c))
                last_consonant = None
            elif c == last_consonant:
                if c.lower() == "n":
                    self.atoms[-1].text += c
                    last_consonant = None
                else:
                    self.atoms.append(Atom(c))
                    last_consonant = c
            elif last_consonant is not None:
                pair = last_consonant + c
                if pair.lower() in ("sh", "ts", "ch", "dz") or c.lower() == "y":
                    self.atoms[-1].text += c
                else:
                    self.atoms.append(Atom(c))
                last_consonant = c
            else:
                self.atoms.append(Atom(c))
                last_consonant = c

        if in_particle:
            raise ParseError("Incomplete group")
        if in_escape:
            raise ParseError("Incomplete escape")

class LatinMolecule(Molecule):
    SPACE = " "
    VOWELS = "aeiouáéíóúäëïöü"
    CONSONANTS = "bcdfghjklmnñpqrstvwxyz0123456789'"
    VOWELS_END = VOWELS
    CONSONANTS_END = CONSONANTS

    def parse(self, source):
        self.atoms = []
        in_particle = False
        in_escape = False
        consonants = None
        preceding_vowel = False
        smash_first = False
        last_break = False

        self.break_before = self.break_after = False
        if source and source[0] == "$":
            self.break_before = True
            source = source[1:]
            if source and source[0] == "^":
                self.row = int(source[1])
                source = source[2:]
        if source and source[-1] == "$":
            if source[-2:] != "\\$":
                self.break_after = True
                source = source[:-1]

        for i, c in enumerate(source):
            next = None
            if i != len(source)-1:
                next = source[i + 1]
            if not in_escape:
                if c == "\\":
                    in_escape = True
                    continue
                elif c == "{":
                    if consonants:
                        if preceding_vowel:
                            self.atoms[-1].text += consonants
                        else:
                            self.atoms.append(Atom(consonants))
                        consonants = None
                    if in_particle:
                        raise ParseError("Nested atoms")
                    in_particle = True
                    group_text = ""
                    continue
                elif c == "}" and in_particle:
                    if not group_text:
                        raise ParseError("Empty group")
                    in_particle = False
                    self.atoms.append(Atom(group_text))
                    continue
                elif c == ".":
                    smash_first = False
                    last_break = True
                    if consonants is not None:
                        if preceding_vowel:
                            self.atoms[-1].text += consonants
                        else:
                            self.atoms.append(Atom(consonants))
                        consonants = None
                    preceding_vowel = False
                    continue
            else:
                in_escape = False
            next_letter = next and next in (self.CONSONANTS + self.VOWELS)
            if in_particle:
                group_text += c
            elif c.lower() in (self.CONSONANTS if next_letter else self.CONSONANTS_END):
                if consonants is not None:
                    consonants += c
                else:
                    preceding_vowel = False
                    consonants = c
            elif c.lower() in (self.VOWELS if next_letter else self.VOWELS_END):
                if preceding_vowel and consonants == "":
                    self.atoms[-1].text += c
                elif preceding_vowel and consonants:
                    split = len(consonants) // 2
                    self.atoms[-1].text += consonants[:split]
                    self.atoms.append(Atom(consonants[split:] + c))
                else:
                    if not smash_first:
                        self.atoms.append(Atom(""))
                    if consonants:
                        self.atoms[-1].text += consonants
                    self.atoms[-1].text += c
                preceding_vowel = True
                consonants = ""
                smash_first = False
            else:
                if consonants:
                    if preceding_vowel:
                        self.atoms[-1].text += consonants
                    else:
                        self.atoms.append(Atom(consonants))
                    consonants = None
                if self.atoms and not last_break:
                    self.atoms[-1].text += c
                else:
                    self.atoms.append(Atom(c))
                    smash_first = True
                preceding_vowel = False
            last_break = False

        if consonants:
            if preceding_vowel:
                self.atoms[-1].text += consonants
            else:
                self.atoms.append(Atom(consonants))

        if in_particle:
            raise ParseError("Incomplete group")
        if in_escape:
            raise ParseError("Incomplete escape")

class EnglishMolecule(LatinMolecule):
    SPACE = " "
    VOWELS_END = "aiouy"
    CONSONANTS_END = "bcdfghjklmnñpqrstvwxz0123456789'"

class MultiString(OrderedDict):
    def __getitem__(self, key=None):
        if key is None:
            return self.get(None, "")
        elif isinstance(key, str):
            return self[[key]]
        elif isinstance(key, list) or isinstance(key, tuple):
            for k in key:
                if k in self:
                    return self.get(k)
            if "*" in self:
                return self.get("*")  # TODO: i18n
            return self.get(None, "")
        else:
            raise TypeError()
    def __eq__(self, other):
        for k in self:
            if other.get(k) != self.get(k):
                return False
        return True

FORMATS = {
    "Japanese": JapaneseMolecule,
    "Romaji": RomajiMolecule,
    "Latin": LatinMolecule,
    "English": EnglishMolecule,
}

I_FORMATS = dict((v, k) for k, v in FORMATS.items())

class Compound(OrderedDict):
    def __init__(self, song_timing):
        OrderedDict.__init__(self)
        self.start = None
        self.timing = None
        self.song_timing = song_timing

    @property
    def steps(self):
        return self[list(self.keys())[0]].steps

    @property
    def end(self):
        return self.start + sum(self.timing)

    def get_atom_time(self, steps, length):
        if self.timing is not None and self.song_timing is not None:
            start = self.start + sum(self.timing[i] for i in range(steps))
            end = start + sum(self.timing[i] for i in range(steps, steps + length))
            start = self.song_timing.beat2time(start)
            end = self.song_timing.beat2time(end)
        else:
            start = self.start + steps
            end = start + length
        return start, end

class BeatCounter(object):
    def __init__(self):
        self.beats = []

    def add(self, time, beat):
        self.beats.append((time, beat))

    def time2beat(self, t):
        time1 = None
        for time2, beat2 in self.beats:
            if time2 > t:
                if time1 is None:
                    return 0
                else:
                    frac = (t - time1) / (time2 - time1)
                    return beat1 + frac * (beat2 - beat1)
            time1, beat1 = time2, beat2
        time1, beat1 = self.beats[-2]
        frac = (t - time1) / (time2 - time1)
        return beat1 + frac * (beat2 - beat1)

    def beat2time(self, beat):
        beat = float(beat)
        beat1 = None
        for time2, beat2 in self.beats:
            if beat2 > beat:
                if beat1 is None:
                    return 0
                else:
                    frac = (beat - beat1) / (beat2 - beat1)
                    return time1 + frac * (time2 - time1)
            time1, beat1 = time2, beat2
        time1, beat1 = self.beats[-2]
        frac = (beat - beat1) / (beat2 - beat1)
        return time1 + frac * (time2 - time1)

class MixedFraction(fractions.Fraction):
    def __new__(cls, a, b=None):
        if b is not None:
            return super(MixedFraction, cls).__new__(cls, a, b)
        if isinstance(a, str):
            match = re.match(r"(-?\d+)\+(\d+)/(\d+)", a)
            if match:
                whole, num, den = (int(match.group(i)) for i in (1, 2, 3))
                return super(MixedFraction, cls).__new__(cls, num + whole * den, den)
        return super(MixedFraction, cls).__new__(cls, a)

    def __str__(self):
        whole = int(self.numerator / self.denominator)
        part = self - whole
        if part == 0:
            return "%d" % whole
        elif whole == 0:
            return "%d/%d" % (part.numerator, part.denominator)
        else:
            return "%d+%d/%d" % (whole, part.numerator, part.denominator)

def parse_time(t):
    if re.match(r"-?\d+\.\d*", t):
        return decimal.Decimal(t)
    else:
        return MixedFraction(t)


class Style(object):
    def __init__(self, data):
        self.data = data
        self.font = "TakaoPGothic.ttf"
        self.ruby_font = None
        self.size = 16
        self.ruby_size = None
        self.outline_width = 0.1
        self.border_width = 0.8
        self.colors = ((255, 255, 255), (0, 128, 255), (0, 0, 0))
        self.colors_on = ((0, 128, 255), (255, 255, 255), (0, 0, 0))

        if self.data:
            for key, value in self.data.items():
                if key in ("font", "ruby_font"):
                    setattr(self, key, value)
                elif key in ("size", "ruby_size", "outline_width", "border_width"):
                    setattr(self, key, float(value))
                elif key in ("colors", "colors_on"):
                    setattr(self, key, self._parse_colors(value))
                else:
                    raise ParseError("Unknown style option %s=%s" % (key, value))

        if self.ruby_font is None:
            self.ruby_font = self.font
        if self.ruby_size is None:
            self.ruby_size = self.size / 2.0

    def _parse_colors(self, value):
        vals = [c.strip() for c in value.split(",")]
        if len(vals) not in (2, 3):
            raise ParseError("Expected 2 or 3 colors: %s" % value)
        colors = []
        for val in vals:
            if len(val) != 6:
                raise ParseError("Expected 6 hex digits: %s" % val)
            colors.append((int(val[:2], 16), int(val[2:4], 16), int(val[4:], 16)))
        if len(colors) == 2:
            colors.append((0, 0, 0))
        return tuple(colors)

class TagInfo(object):
    BOTTOM = 1
    TOP = 2
    def __init__(self, style=None, edge=BOTTOM):
        self.style = style
        self.edge = edge

class Variant(object):
    def __init__(self, data):
        self.data = data
        self.name = None
        self.tags = None
        self.tag_list = None
        self.style = None
        self.default = False
        self.tag_data = {}

        if data is None:
            return

        for key, value in self.data.items():
            if key in ("name", "style"):
                setattr(self, key, value)
            elif key == "tags":
                if value:
                    self.tag_list = [i.strip() for i in value.split(",")]
                else:
                    self.tag_list = []
            elif key == "default":
                self.default = value.lower() in ("1", "true")
            elif "." in key:
                tag, key = key.split(".", 1)
                if tag not in self.tag_data:
                    self.tag_data[tag] = {}
                self.tag_data[tag][key] = value
            else:
                raise ParseError("Unknown variant option %s=%s" % (key, value))

        if self.name is None:
            raise ParseError("Variant must have a name")
        if self.tag_list is None:
            raise ParseError("Variant %s must have a tags= entry" % self.name)

    def load_tags(self, styles):
        default_style = None
        if self.style is not None:
            try:
                default_style = styles[self.style]
            except KeyError:
                raise ParseError("Unknown style %s for variant %s" % (self.style, self.name))
        self.tags = {}
        for tag in self.tag_list:
            tag_info = TagInfo()
            self.tags[tag] = tag_info
            if tag in self.tag_data:
                for key, value in self.tag_data[tag].items():
                    if key == "style":
                        try:
                            tag_info.style = styles[value]
                        except KeyError:
                            raise ParseError("Unknown style %s for variant %s tag %s" % (value, self.name, tag))
                    elif key == "edge":
                        if value.upper() not in ("TOP", "BOTTOM"):
                            raise ParseError("Unknown edge %s in variant %s tag %s" % (value, self.name, tag))
                        tag_info.edge = getattr(TagInfo, value.upper())
                    else:
                        raise ParseError("Unknown key %s in variant %s tag %s" % (key, self.name, tag))
            if tag_info.style is None:
                if default_style:
                    tag_info.style = default_style
                else:
                    raise ParseError("Tag %s in variant %s must have a style" % (tag, self.name))

class Song(object):
    def __init__(self, filename=None, ignore_steps=False):
        parsers = {
            "Meta": self.parse_meta,
            "Song": self.parse_song,
            "Timing": self.parse_timing,
            "Formats": self.parse_formats,
            "Styles": self.parse_styles,
            "Variants": self.parse_variants,
            "Lyrics": self.parse_lyrics,
        }
        self.ignore_steps = ignore_steps
        self.pathbase = os.path.dirname(filename) if filename else None
        section = None
        lines = []
        self.meta = None
        self.song = None
        self.timing = None
        self.formats = None
        self.styles = None
        self.variants = None
        self.compounds = None

        self.fake_time = 0
        self.line = 0
        self.section_line = 0

        if not filename:
            self.meta = OrderedDict()
            self.song = OrderedDict()
            self.timing = BeatCounter()
            self.formats = OrderedDict()
            self.styles = OrderedDict()
            self.variants = OrderedDict()
            self.compounds = []
            return

        for line in codecs.open(filename, encoding='utf-8', mode='r'):
            self.line += 1
            line = line.replace("\n","").replace("\r","")
            if line.startswith("#"):
                continue
            if section is None:
                if not line:
                    continue
                if line[0] != "[" or line[-1] != "]":
                    raise ParseError("Expected section header")
                section = line[1:-1]
                self.section_line = self.line
                continue
            if line and line[0] == "[" and line[-1] == "]":
                if section not in parsers:
                    raise ParseError("Unknown section %s" % section)
                parsers[section](lines)
                lines = []
                section = line[1:-1]
                self.section_line = self.line
            else:
                lines.append(line)
        if section is not None:
            parsers[section](lines)

        if self.variants and self.styles:
            for variant in self.variants.values():
                variant.load_tags(self.styles)

    def keyvalues(self, lines):
        for line in lines:
            if not line:
                continue
            if "=" not in line:
                raise ParseError("Expected key=value format (%s)" % line)
            key, val = line.split("=", 1)
            yield key, val

    def parse_meta(self, lines):
        self.meta = OrderedDict()
        for key, val in self.keyvalues(lines):
            lang = None
            m = re.match(r"(.*)\[(.*)\]", key)
            if m:
                key = m.group(1)
                lang = m.group(2)
            if key not in self.meta:
                self.meta[key] = MultiString()
            self.meta[key][lang] = val

    def parse_song(self, lines):
        self.song = OrderedDict()
        for key, val in self.keyvalues(lines):
            self.song[key] = val

    def parse_timing(self, lines):
        self.timing = BeatCounter()
        for time, beat in self.keyvalues(lines):
            if time[0] != "@":
                raise ParseError("Expected @time")
            self.timing.add(float(time[1:]), int(beat))

    def parse_formats(self, lines):
        self.formats = OrderedDict()
        for tag, fmt in self.keyvalues(lines):
            if fmt not in FORMATS:
                raise ParseError("Unknown format %s" % fmt)
            self.formats[tag] = FORMATS[fmt]

    def parse_twolevel(self, lines):
        inner = None
        for line in lines:
            if not line:
                continue
            if line[0] == "{":
                if line[-1] != "}":
                    raise ParseError("Expected {...} (%s)" % line)
                if inner is not None:
                    yield name, inner
                name = line[1:-1]
                inner = OrderedDict()
                continue
            if inner is None:
                raise ParseError("Expected {...} (%s)" % line)
            if "=" not in line:
                raise ParseError("Expected key=value format (%s)" % line)
            key, val = line.split("=", 1)
            inner[key] = val
        if inner is not None:
            yield name, inner

    def parse_styles(self, lines):
        self.styles = OrderedDict()
        for name, data in self.parse_twolevel(lines):
            self.styles[name] = Style(data)

    def parse_variants(self, lines):
        self.variants = OrderedDict()
        for name, data in self.parse_twolevel(lines):
            self.variants[name] = Variant(data)

    def parse_lyrics(self, lines):
        self.compounds = []
        compounds = None
        compound = None
        lineno = self.section_line
        for s in (lines + [""]):
            lineno += 1
            if not s and compound:
                first = compound[list(compound.keys())[0]]
                for key,val in compound.items():
                    if first.steps != val.steps:
                        raise ParseError("%d: Duration mismatch: %d!=%d (%s) (%s)" % (lineno, first.steps, val.steps, str(first), str(val)))
                if compound.timing is not None:
                    if compound.steps != len(compound.timing):
                        raise ParseError("%d: Timing line length mismatch: %d!=%d" % (lineno, len(compound.timing), compound.steps))
                else:
                    compound.start = self.fake_time
                    self.fake_time += compound.steps
                compound = None

            if not s:
                continue
            if compound is None:
                compound = Compound(self.timing)
                self.compounds.append(compound)

            if ":" not in s:
                raise ParseError("Expected 'X: value': %r" % s)

            tag, text = s.split(":", 1)
            tag = tag.strip()
            text = text.strip()

            if tag == "@":
                if self.ignore_steps:
                    continue
                timing = list(map(parse_time, text.split()))
                compound.start = timing[0]
                compound.timing = timing[1:]
                if compound:
                    first = compound[list(compound.keys())[0]]
                    if first.steps != len(compound.timing):
                        raise ParseError("%d: Timing line length mismatch: %d!=%d" % (lineno, len(compound.timing), compound.steps))
                continue

            if tag not in self.formats:
                raise ParseError("Undefined format %r" % tag)

            compound[tag] = self.formats[tag](text)

    def dump(self):
        s = ""
        if self.meta is not None:
            s += "[Meta]\n"
            for tag, value in self.meta.items():
                for lang, text in value.items():
                    if lang is None:
                        s += "%s=%s\n" % (tag, text)
                    else:
                        s += "%s[%s]=%s\n" % (tag, lang, text)
            s += "\n"
        if self.song is not None:
            s += "[Song]\n"
            for tag, value in self.song.items():
                s += "%s=%s\n" % (tag, value)
            s += "\n"
        if self.timing is not None:
            s += "[Timing]\n"
            for time, beat in self.timing.beats:
                s += "@%f=%d\n" % (time, beat)
            s += "\n"
        if self.formats is not None:
            s += "[Formats]\n"
            for tag, fmt in self.formats.items():
                s += "%s=%s\n" % (tag, I_FORMATS[fmt])
            s += "\n"
        if self.styles is not None:
            s += "[Styles]\n"
            for name, style in self.styles.items():
                s += "{%s}\n" % name
                for key, value in style.data.items():
                    s += "%s=%s\n" % (key, value)
                s += "\n"
        if self.variants is not None:
            s += "[Variants]\n"
            for name, variant in self.variants.items():
                s += "{%s}\n" % name
                for key, value in variant.data.items():
                    s += "%s=%s\n" % (key, value)
                s += "\n"
        if self.compounds is not None:
            s += "[Lyrics]\n\n"
            for compound in self.compounds:
                for tag, molecule in compound.items():
                    s += "%s: %s\n" % (tag, molecule.source)
                if compound.timing is not None:
                    s += "@: %s  %s\n" % (str(compound.start), ' '.join(map(str,compound.timing)))
                s += "\n"
                if any(i.break_before or i.break_after for i in compound.values()):
                    s += "\n"
        return s

    def save(self, filename):
        fd = open(filename, "w")
        fd.write(self.dump())
        fd.close()

    @property
    def audiofile(self):
        return os.path.join(self.pathbase, self.song["audio"])

    @property
    def videofile(self):
        if "video" not in self.song:
            return None
        else:
            return os.path.join(self.pathbase, self.song["video"])

    @property
    def coverfile(self):
        if "cover" not in self.song:
            return None
        else:
            return os.path.join(self.pathbase, self.song["cover"])

    @property
    def aspect(self):
        if "aspect" not in self.song:
            return None
        else:
            return fractions.Fraction(self.song["aspect"])

    def get_lyric_snippet(self, variant_id, length=100):
        variant = self.variants[variant_id]
        tags = set(i for i in variant.tag_list if variant.tags[i].edge == TagInfo.BOTTOM)
        lyrics = ""
        broke = False
        for compound in self.compounds:
            if len(lyrics) >= length:
                break
            for tag, molecule in compound.items():
                if tag not in tags:
                    continue
                if molecule.break_before and not broke:
                    lyrics += "/" + molecule.SPACE
                broke = False
                lyrics += molecule.text + molecule.SPACE
                if molecule.break_after:
                    lyrics += "/" + molecule.SPACE
                    broke = True

        return lyrics

    def get_font_path(self, font):
        song_font = os.path.join(self.pathbase, font)
        if os.path.exists(song_font):
            return song_font
        resfont = util.get_resfont_path(font)
        if os.path.exists(resfont):
            return resfont
        raise IOError("Font %s not found" % font)
