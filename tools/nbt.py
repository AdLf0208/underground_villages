"""A minimal, read-only NBT reader for the structure-template checks.

Minecraft writes a structure template as one gzip-compressed named tag whose
root is a compound. This module reads exactly that shape and nothing else: it
is a checker's reader, not a general NBT library.

The binary format (Java Edition, big-endian) is taken from the game's own
`NbtIo`/`TagTypes` specification: a tag type byte, a big-endian name, then the
payload for that type.
"""

import gzip
import io
import struct

#: Tag ids by name, as the format numbers them.
TAG_NAMES = {
    0: "end",
    1: "byte",
    2: "short",
    3: "int",
    4: "long",
    5: "float",
    6: "double",
    7: "byte_array",
    8: "string",
    9: "list",
    10: "compound",
    11: "int_array",
    12: "long_array",
}

#: Template compounds may nest a list inside a list; the game's own reader
#: allows a depth of 512, so anything past that is corrupt rather than deep.
MAX_DEPTH = 512


class NbtError(Exception):
    """The bytes are not a structure template this reader can read."""


class _Reader:
    def __init__(self, data):
        self._data = data
        self._at = 0
        self._limit = len(data)

    def _take(self, count):
        end = self._at + count
        if end > self._limit:
            raise NbtError(f"truncated: wanted {count} bytes at {self._at}")
        chunk = self._data[self._at:end]
        self._at = end
        return chunk

    def unpack(self, fmt):
        size = struct.calcsize(fmt)
        return struct.unpack(fmt, self._take(size))[0]

    def string(self):
        length = self.unpack(">H")
        return self._take(length).decode("utf-8")

    def payload(self, tag_id, depth):
        if depth > MAX_DEPTH:
            raise NbtError("compound or list nested past the format's depth")
        if tag_id == 1:
            return self.unpack(">b")
        if tag_id == 2:
            return self.unpack(">h")
        if tag_id == 3:
            return self.unpack(">i")
        if tag_id == 4:
            return self.unpack(">q")
        if tag_id == 5:
            return self.unpack(">f")
        if tag_id == 6:
            return self.unpack(">d")
        if tag_id == 7:
            return self._take(self.unpack(">i"))
        if tag_id == 8:
            return self.string()
        if tag_id == 9:
            element = self.unpack(">b")
            count = self.unpack(">i")
            if element == 0:
                # An empty list has no element type; the game reads zero items.
                if count != 0:
                    raise NbtError("list of end tags with entries")
                return []
            return [self.payload(element, depth + 1) for _ in range(count)]
        if tag_id == 10:
            compound = {}
            while True:
                child = self.unpack(">b")
                if child == 0:
                    return compound
                name = self.string()
                compound[name] = self.payload(child, depth + 1)
        if tag_id == 11:
            return [self.unpack(">i") for _ in range(self.unpack(">i"))]
        if tag_id == 12:
            return [self.unpack(">q") for _ in range(self.unpack(">i"))]
        raise NbtError(f"tag id {tag_id} is not in the format")


def read(path):
    """The root compound of a gzip-compressed named tag."""
    with open(path, "rb") as handle:
        raw = handle.read()
    if raw[:2] != b"\x1f\x8b":
        raise NbtError(f"{path}: not gzip")
    data = gzip.decompress(raw)
    reader = _Reader(data)
    tag_id = reader.unpack(">b")
    if tag_id != 10:
        raise NbtError(f"{path}: root tag is {TAG_NAMES.get(tag_id, tag_id)}, not a compound")
    reader.string()  # the root's name, which vanilla leaves empty
    root = reader.payload(10, 0)
    if reader._at != len(data):
        raise NbtError(f"{path}: {len(data) - reader._at} trailing bytes")
    return root


def palette_names(template):
    """The block ids a template's palette names, without their properties."""
    names = []
    for entry in template.get("palette", []):
        name = entry.get("Name")
        if not isinstance(name, str):
            raise NbtError("palette entry without a Name")
        names.append(name)
    return names


def block_counts(template):
    """How many cells each palette block id fills, in the template."""
    names = palette_names(template)
    counts = {}
    for block in template.get("blocks", []):
        state = block.get("state")
        if not isinstance(state, int) or not 0 <= state < len(names):
            raise NbtError(f"block state {state!r} is outside the palette")
        counts[names[state]] = counts.get(names[state], 0) + 1
    return counts


def entity_ids(template):
    """The `id` of every entity a template carries."""
    ids = []
    for entity in template.get("entities", []):
        inner = entity.get("nbt", {})
        if isinstance(inner, dict) and isinstance(inner.get("id"), str):
            ids.append(inner["id"])
    return ids


def size(template):
    """The template's size as (x, y, z); the game requires all three."""
    value = template.get("size")
    if not isinstance(value, list) or len(value) != 3:
        raise NbtError("template without a three-part size")
    return tuple(value)
