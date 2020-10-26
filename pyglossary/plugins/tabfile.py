# -*- coding: utf-8 -*-

from formats_common import *
from pyglossary.text_reader import TextGlossaryReader
from pyglossary.text_utils import (
	unescapeNTB,
	splitByBarUnescapeNTB,
)

enable = True
format = "Tabfile"
description = "Tabfile (txt, dic)"
extensions = (".txt", ".tab", ".tsv")
singleFile = True
optionsProp = {
	"encoding": EncodingOption(),
	"writeInfo": BoolOption(),
	"resources": BoolOption(),
}

# https://en.wikipedia.org/wiki/Tab-separated_values


class Reader(TextGlossaryReader):
	def isInfoWord(self, word: str) -> bool:
		return word.startswith("#")

	def fixInfoWord(self, word: str) -> str:
		return word.lstrip("#")

	def nextPair(self) -> "Tuple[str, str]":
		if not self._file:
			raise StopIteration
		line = self._file.readline()
		if not line:
			raise StopIteration
		line = line.rstrip("\n")
		if not line:
			return
		###
		word, tab, defi = line.partition("\t")
		if not tab:
			log.error(
				f"Warning: line starting with {line[:10]!r} has no tab!"
			)
			return
		###
		if self._glos.getConfig("enable_alts", True):
			word = splitByBarUnescapeNTB(word)
			if len(word) == 1:
				word = word[0]
		else:
			word = unescapeNTB(word, bar=False)
		###
		defi = unescapeNTB(defi)
		###
		return word, defi


class Writer(object):
	_encoding: str = "utf-8"
	_writeInfo: bool = True
	_resources: bool = True

	compressions = stdCompressions

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = None

	def open(
		self, 
		filename: str,
	):
		self._filename = filename

	def finish(self):
		pass

	def write(self) -> "Generator[None, BaseEntry, None]":
		yield from self._glos.writeTabfile(
			self._filename,
			encoding=self._encoding,
			writeInfo=self._writeInfo,
			resources=self._resources,
		)
