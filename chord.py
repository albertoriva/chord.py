#!/usr/bin/env python3

import os
import sys

CSS = """
.song {
    margin-left: 1in;
    margin-right: 0.5in;
}

.chords {
    color: blue;
    font-size: 12pt;
    font-weight: bold;
    line-height: 100%;
}

.text {
    font-size: 12pt;
    line-height: 100%;
}

.comment {
    font-style: italic;
    background: lightgrey;
    padding: 1px;
}

.title {
    font-family: Verdana, sans-serif;
    font-size: 30pt;
    margin: 0px;
}

.subtitle {
    font-family: Verdana, sans-serif;
    font-size: 24pt;
    margin: 0px;
}

.chorus {
    border-left: 6px solid black;
    padding-left: 12px;
}

.transpose {
    position: fixed;
    top: 10px;
    left: 10px;
    border: 2px solid blue;
}

@media print {
    BODY: {
	zoom: 80%;
    }
    .transpose {
      display: none;
    }
}
"""

JS = """

var notes = ["A", "Bb", "B", "C", "C#", "D", "Eb", "E", "F", "F#", "G", "G#"];

function transposeUp() {
  el = document.getElementById("transp");
  tv = parseInt(el.value);
  tv += 1;
  el.value = tv;
  transposeChords(tv);
}

function transposeDown() {
  el = document.getElementById("transp");
  tv = parseInt(el.value);
  tv += -1;
  el.value = tv;
  transposeChords(tv);
}

function buildChord(bases, mods, transpose) {
  res = "";
  nb = bases.length;
  for (var i=0; i<nb; i++) {
    if (i > 0) {
      res += "/";
    }
    var newbase = (parseInt(bases[i]) + transpose) % 12;
    if (newbase < 0) {
      newbase += 12;
    }
    res += notes[newbase] + mods[i];
  }
  return res;
}

function transposeChords(transpose) {
  allchords = document.getElementsByClassName("chordlist");
//  console.log(nc);
  for (var x=0; x<allchords.length; x++) {
      el = allchords[x];
//      console.log(el.id);
      var result = [];
      nc = 0;                   // last filled position in result
      chs = el.children;
      nch = chs.length;
//      console.log(x + " " + el.id + " " + nch);
      for (var y=0; y<nch; y++) { // loop over all chords in this line
        child = chs[y];
        bases = child.getAttribute("base").split(",");
        mods = child.getAttribute("mod").split(",");
        pos = parseInt(child.getAttribute("pos"));
        chord = buildChord(bases, mods, transpose);
        if (nc == 0) {
          cp = pos;
        } else {
          cp = Math.max(nc + 1, pos);    // we want at least one space between chords
        }
        while (nc < cp) {
          result.push(" ");
          nc += 1;
        }
        for (var i=0; i<chord.length; i++) {
          p = chord[i];
          result.push(p);
          nc += 1;
        }
      }
      for (var i=0; i<10; i++) {
        result.push(" ");
        nc += 1;
      }
      row = result.join("");
      dest = document.getElementById(el.id + "text");
      dest.innerText = row;
  }
}
"""

# 0 1  2 3 4  5 6  7 8 9  10 11
# A A# B C C# D D# E F F# G  G# 
#   Bb     Db   Eb     Gb    Ab

NOTEIDX = {"A": 0, "A#": 1, "Bb": 1, "B": 2,
           "C": 3, "C#": 4, "Db": 4, "D": 5,
           "D#": 6, "Eb": 6, "E": 7, "F": 8,
           "F#": 9, "Gb": 9, "G": 10, "G#": 11, "Ab": 11}

NOTEIDX = [
           ("A#", 1),
           ("C#", 4),
           ("D#", 6),
           ("F#", 9),
           ("G#", 11),
           ("Bb", 1),
           ("Db", 4),
           ("Eb", 6),
           ("Gb", 9),
           ("Ab", 11),
           ("A", 0),
           ("B", 2),
           ("C", 3),
           ("D", 5),
           ("E", 7),
           ("F", 8),
           ("G", 10)
           ]

IDXNOTE = ["A", "Bb", "B", "C", "C#", "D",
           "Eb", "E", "F", "F#", "G", "G#"]

def getNoteValue(note):
    """Given a note, return its index and its modifiers as a tuple.
E.g. getNoteValue("C#maj7") => (4, "maj7")"""
    for (n, idx) in NOTEIDX:
        if note.startswith(n):
            return (idx, note[len(n):])
    return (None, None)

def destructureChord(chord):
    values = [getNoteValue(p) for p in chord.split("/")]
    return (",".join([ str(v[0]) for v in values]), ",".join([v[1] for v in values]))

def transposeNote(note, steps):
    (base, mods) = getNoteValue(note)
    if base is None:
        return note
    newb = (base + steps) % 12
    return IDXNOTE[newb] + mods

def transpose(note, steps):
#    sys.stderr.write("Transposing {} by {}\n".format(note, steps))
    return "/".join([ transposeNote(s, steps) for s in note.split("/") ])
        
class Chord():
    directory = "Songs/"        # -d
    infiles = []
    transpose = 0
    chord_num = 0
    
    out = None
    sections = []
    section = ""
    pages = []

    def __init__(self, args):
        prev = ""
        for a in args:
            if prev == "-d":
                self.directory = a
                prev = ""
            elif a in ["-d"]:
                prev = a
            elif a[0] == '@':
                with open(a[1:], "r") as f:
                    for line in f:
                        self.infiles.append(line.strip())
            else:
                self.infiles.append(a)
        os.makedirs(self.directory, exist_ok=True)
        
    def run(self):
        with open(self.directory + "/chord.css", "w") as out:
            out.write(CSS)
        with open(self.directory + "/chord.js", "w") as out:
            out.write(JS)
        for f in self.infiles:
            sys.stderr.write("Converting {}...\n".format(f))
            self.convert(f)
        self.saveSection()
        self.writeTOC()

    def writeTOC(self):
        toc = self.directory + "/index.html"
        with open(toc, "w") as out:
            out.write("""<!DOCTYPE html>
<HTML>
  <HEAD>
    <TITLE>Songs</TITLE>
  </HEAD>
  <BODY>
    <CENTER><H1>Songs</H1></CENTER>
    <OL>
""")
            for sec in sorted(self.sections, key=lambda x: x[0]):
                out.write("<LI>{}</LI><UL>\n".format(sec[0]))
                for pg in sorted(sec[1], key=lambda x: x[0]):
                    out.write("<LI><A href='{}'>{}</A></LI>\n".format(pg[1], pg[0]))
                out.write("</UL>\n")
            out.write("""</OL>
  </BODY>
</HTML>
""")
        
    def titleToFilename(self, title):
        return title.replace(" ", "_").replace("'", "_")
    
    def parseLine(self, line):
        chord_positions = []
        start = 0
        inchord = False
        pos = 0
        valid = 0

        chord_line = []
        text_line = []

        for ch in line:
            if inchord:
                if ch == "]":
                    chord_positions.append([valid, line[start+1:pos]])
                    inchord = False
            else:
                if ch == "[":
                    start = pos
                    inchord = True
                else:
                    text_line.append(ch)
                    valid += 1
            pos += 1

#        print(chord_positions)

        if self.transpose:
            for cp in chord_positions:
                cp[1] = transpose(cp[1], self.transpose)

#        print(chord_positions)
#        input()
                
        pos = 0
        for cp in chord_positions:
            chord = cp[1]
            cdata = destructureChord(chord)
            chord_line.append("<CHORD class='chord' base='{}' mod='{}' pos='{}'></CHORD>".format(cdata[0], cdata[1], cp[0]))

            # while pos < cp[0]:
            #     chord_line.append(" ")
            #     pos += 1
            # chord = cp[1]
            # cdata = destructureChord(chord)
            # chord_line.append("<SPAN class='chord' id='ch{}' base='{}' mod='{}' pos='{}'>".format(self.chord_num, cdata[0], cdata[1], cp[0]))
            # self.chord_num += 1
            # for ch in chord:
            #     chord_line.append(ch)
            #     pos += 1
            # chord_line.append("</SPAN>")
        return ("".join(chord_line), "".join(text_line))

    def processDirective(self, line):
        col = line.find(":")
        end = line.find("}")
        if end < 0:
            return
        if col < 0:
            directive = line[1:end].lower()
        else:
            directive = line[1:col].lower()
            content = line[col+1:end].strip()
        if directive in ["c", "comment"]:
            self.out.write("<SPAN class='comment'>{}</SPAN>\n".format(content))
        elif directive in ["ti", "title"]:
            if self.out:
                self.closeFile()
            filename = self.titleToFilename(content) + ".html"
            self.openFile(self.directory + "/" + filename, content)
            self.transpose = 0
            self.chord_num = 1
            self.pages.append((content, filename))
            sys.stderr.write("  {} => {}\n".format(content, filename))
            self.out.write("<CENTER><SPAN class='title'>{}</SPAN></CENTER>\n".format(content))
        elif directive == "transpose":
            self.transpose = int(content)
            sys.stderr.write("Transposing by {} steps.\n".format(self.transpose))
        elif directive in ["st", "subtitle"]:
            self.out.write("<CENTER><SPAN class='subtitle'>{}</SPAN></CENTER>\n".format(content))
        elif directive in ["soc", "start_of_chorus"]:
            self.out.write("<DIV class='chorus'>")
        elif directive in ["eoc", "end_of_chorus"]:
            self.out.write("</DIV>")
        elif directive == "section":
            self.saveSection()
            self.section = content

    def saveSection(self):
        if self.section and self.pages:
            self.sections.append((self.section, self.pages))
        self.pages = []
            
    def openFile(self, filename, title):
        self.out = open(filename, "w")
        self.out.write("""<!DOCTYPE html>
    <HTML>
      <HEAD>
        <LINK rel="stylesheet" href="chord.css" />
        <SCRIPT lang="Javascript" src="chord.js"></SCRIPT>
        <TITLE>{}</TITLE>
      </HEAD>
      <BODY onload="javascript:transposeChords(0);">
        <DIV class='transpose'>Transpose by: <INPUT type='text' size='3' value='0' id="transp" onchange="javascript:transposeChords(parseInt(this.value));"> <BUTTON onclick="javascript:transposeUp();">+</BUTTON> <BUTTON onclick="javascript:transposeDown();">-</BUTTON>
        </DIV>
        <DIV class="song">
        <PRE>
        """.format(title))

    def closeFile(self):
        self.out.write("""
        </PRE>
        </DIV>
      </BODY>
    </HTML>
""")
        self.out.close()
        self.out = None
        
    def convert(self, infile):
        cline = 0
        with open(infile, "r") as f:
            for line in f:
                if line == '\n':
                    self.out.write("\n")
                elif line[0] == "#":
                    continue
                elif line[0] == "{":
                    self.processDirective(line)
                else:
                    (chords, text) = self.parseLine(line.rstrip("\r\n"))
                    if chords:
                        self.out.write("<span class='chordlist' id='cl{}'>{}</span><span class='chords' id='cl{}text'></span>\n".format(cline, chords, cline))
                        cline += 1
                    self.out.write("<span class='text'>{}</span>\n".format(text))
        self.closeFile()

def usage():
    sys.stdout.write("""chord.py - convert song files to HTML

Usage: chord.py [options] files...

This program reads the input files (which should be in chopro format) and writes
an HTML file for each song in each input file. The HTML files are written to a
subdirectory whose name can be changed with the -d option. The program will also
create an index.html file in that subdirectory with links to all generated HTML
files. 

Options:

    -h, --help | This help message
    -d DIR     | Write files to directory DIR

The following chopro directives are interpreted by this program:

    ti, title            | Define song title (also used as filename)
    st, subtitle         | Define song subtitle
    c, comment           | Write the rest of the line as a comment
    soc, start_of_chorus | Start of chorus (marked by black bar to the left)
    eoc, end_of_chorus   | End of chorus

    transpose            | Transpose all chords up or down by the specified number of halftones
    section              | Define a section in the table of contents

The chopro format is documented here:

  https://www.chordpro.org/chordpro/ChordPro-File-Format-Specification.html

(c) 2020, Alberto Riva.

""")
        
if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 0 or "-h" in args or "--help" in args:
        usage()
    else:
        C = Chord(args)
        C.run()
