"""One-shot tooling to pull Zwift's own official workout library out of the
game's `workouts.wad` asset archive and turn it into `.zwo` files this app
can ingest — as an alternative to scraping whatsonzwift.com (robots.txt on
that site disallows automated collection; see 2026-09 conversation record).

`workouts.wad` ships inside a licensed Zwift install (e.g.
`.../ZwiftApp/assets/Workouts/workouts.wad`); this script only reads a copy
the owner already possesses.

Two independent steps — run separately since you'll normally only need to
re-run `convert` after re-running `extract` on a new wad:

    python3 tools/wad_to_zwo.py extract  <path/to/workouts.wad> <out_dir>
    python3 tools/wad_to_zwo.py convert  <out_dir>/Workouts

`extract` decodes the wad's custom LZ-style compression (algorithm ported
from the public domain-equivalent BSD-3 script at
gitlab.com/r3dey3/zwift-utils/-/blob/master/decode_wad.py — CRC validation
is skipped here since we only need to read the data) and unpacks every
entry, preserving the wad's internal `Workouts/` + `TrainingPlans/` layout
as-is. `TrainingPlans/*.xml` are schedule/index files with no `<workout>`
block (verified 2026-09: 0/33 contain one) — they are not individual
workouts and `convert` ignores that folder entirely, same for the
`Workouts/workouts.categories` taxonomy file.

`convert` walks `Workouts/` in place and, for each `*.xml`:
  - reads `<sportType>` and skips anything that isn't bike/ride (run/swim
    workouts carry a `pace` attribute alongside `Power` and aren't
    meaningful under this app's %FTP-based TSS/IF/zone analysis — decided
    2026-09). Skipped files are left untouched as `.xml` so ingest's
    `.zwo`-only scan naturally ignores them; nothing is deleted.
  - folds the file's own `<category>` / `<categoryOverride>` values (if
    present) into its `<tags>` block as plain `<tag name="...">` entries,
    since zwo_parser.py already reads that element as-is — no app code
    changes needed. (Decided 2026-09: import for now, reassess once these
    are visible in the UI.)
  - renames the file from `.xml` to `.zwo` in place.

No changes to workout_selector/*.py are required for either step.
"""
import argparse
import os
import struct
import sys
import tempfile
# workouts.wad is game data, not attacker-controlled, but the extracted
# XML is handled the same way as any other .zwo source in this app —
# defusedxml guards against entity-expansion DoS payloads; see
# workout_selector/zwo_parser.py for the full rationale.
import defusedxml.ElementTree as ET
from defusedxml.common import DefusedXmlException

# --- stage 1: extract -----------------------------------------------------


def _uncompress_chunk(infile, outfile):
    buf = infile.read(2)
    if len(buf) < 2:
        return 0
    enc_type = buf[0] & 0xE0
    if enc_type < 0xC0:
        ret_val = buf[0] & 3
        copy_len = (buf[0] >> 5) + 4
        copy_off = buf[1] | ((buf[0] & 0xC) << 6)
    elif enc_type == 192:
        buf += infile.read(1)
        ret_val = buf[1] & 3
        copy_len = (buf[0] & 0x1F) + 4
        copy_off = buf[2] | ((buf[1] & 0xFC) << 6)
    elif enc_type == 224:
        buf += infile.read(1)
        copy_len = (buf[0] & 0xF) + 3
        if (buf[0] & 0xF) != 0:
            ret_val = buf[1] & 3
            v15 = (buf[1] & 0xFC) | (16 * (buf[0] & 0x10))
            copy_off = buf[2] | (v15 << 6)
        else:
            copy_len = buf[1] + 18
            buf += infile.read(1)
            if copy_len <= 0x12:
                buf += infile.read(2)
                ret_val = buf[4] & 3
                copy_len = buf[3] | (buf[2] << 8)
                v15 = (buf[4] & 0xFC) | (16 * (buf[0] & 0x10))
                copy_off = buf[5] | (v15 << 6)
            else:
                ret_val = buf[2] & 3
                v15 = (buf[2] & 0xFC) | (16 * (buf[0] & 0x10))
                copy_off = buf[3] | (v15 << 6)
    else:
        return 0

    outfile.seek(-copy_off, os.SEEK_END)
    data = outfile.read(copy_len)
    outfile.seek(0, os.SEEK_END)
    outfile.write(data)
    return ret_val


def _simple_chunk(infile, outfile):
    b = infile.read(1)
    if not b:
        return
    copy_len = b[0]
    if copy_len != 0:
        copy_len += 2
    else:
        buf = infile.read(2)
        copy_len = buf[0] | (buf[1] << 8)
    outfile.write(infile.read(copy_len))


def _uncompress(infile, outfile, end):
    _simple_chunk(infile, outfile)
    while infile.tell() < end:
        ret = _uncompress_chunk(infile, outfile)
        if ret != 3 and infile.tell() < end:
            if ret:
                outfile.write(infile.read(ret))
            else:
                _simple_chunk(infile, outfile)


def _decode(infile, outfile) -> int:
    name = infile.read(0x60).strip(b"\x00").decode("ascii", "replace")
    print(f"decoding wad: {name}", file=sys.stderr)
    infile.read(0x90)  # reserved
    _sig, version, decomp_size, comp_size = struct.unpack("<LLLL", infile.read(0x10))
    print(f"  version={version} decomp_size={decomp_size} comp_size={comp_size}", file=sys.stderr)
    end = os.fstat(infile.fileno()).st_size
    _uncompress(infile, outfile, end)
    return decomp_size


def _extract_entries(infile, out_dir: str) -> list:
    infile.seek(0x2000, os.SEEK_SET)
    file_size = os.fstat(infile.fileno()).st_size
    entries = []
    while infile.tell() < file_size:
        if len(infile.read(4)) < 4:
            break
        name = infile.read(0x60)
        if len(name) < 0x60:
            break
        name = name.strip(b"\x00").decode("ascii", "replace")
        rest = infile.read(8)
        if len(rest) < 8:
            break
        _unk, size = struct.unpack("<LL", rest)
        infile.seek(0x54, os.SEEK_CUR)
        data = infile.read(size)
        if len(data) < size:
            break
        if size % 0x40:
            infile.seek(0x40 - (size % 0x40), os.SEEK_CUR)
        if not name or name.startswith("..") or name.startswith("/"):
            continue
        safe_name = name.replace("\\", "/").lstrip("/")
        dest = os.path.join(out_dir, safe_name)
        if not os.path.abspath(dest).startswith(os.path.abspath(out_dir)):
            continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(data)
        entries.append((safe_name, size))
    return entries


def cmd_extract(wad_path: str, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    with open(wad_path, "rb") as fin, tempfile.TemporaryFile() as ftemp:
        _decode(fin, ftemp)
        ftemp.seek(0)
        entries = _extract_entries(ftemp, out_dir)
    print(f"extracted {len(entries)} entries to {out_dir}")


# --- stage 2: convert (filter sportType, fold in tags, rename) ------------

INCLUDE_SPORT_TYPES = {"bike", "ride"}


def _add_tags(root: ET.Element, tag_values: list) -> None:
    if not tag_values:
        return
    tags_el = root.find("tags")
    if tags_el is None:
        tags_el = ET.SubElement(root, "tags")
    existing = {t.attrib.get("name") for t in tags_el.findall("tag")}
    for value in tag_values:
        value = " ".join(value.split()).replace(",", "/").strip()
        if value and value not in existing:
            ET.SubElement(tags_el, "tag", {"name": value})
            existing.add(value)


def cmd_convert(workouts_dir: str):
    converted = skipped_sport = errors = 0
    for dirpath, _dirnames, filenames in os.walk(workouts_dir):
        for fname in filenames:
            if not fname.lower().endswith(".xml"):
                continue
            path = os.path.join(dirpath, fname)
            try:
                tree = ET.parse(path)
                root = tree.getroot()
                if root.tag != "workout_file" or root.find("workout") is None:
                    continue  # not an individual workout definition

                sport = (root.findtext("sportType") or "bike").strip().lower()
                if sport == "ride":
                    sport = "bike"
                if sport not in INCLUDE_SPORT_TYPES:
                    skipped_sport += 1
                    continue

                tag_values = [
                    v for v in (root.findtext("category"), root.findtext("categoryOverride"))
                    if v and v.strip()
                ]
                _add_tags(root, tag_values)

                new_path = path[: -len(".xml")] + ".zwo"
                tree.write(new_path, encoding="unicode", xml_declaration=False)
                os.remove(path)
                converted += 1
            except (ET.ParseError, DefusedXmlException) as e:
                print(f"  skip (parse error): {path}: {e}", file=sys.stderr)
                errors += 1

    print(f"converted {converted} -> .zwo, skipped {skipped_sport} (non-bike sportType), errors {errors}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_extract = sub.add_parser("extract", help="decompress a workouts.wad into a directory")
    p_extract.add_argument("wad_path")
    p_extract.add_argument("out_dir")

    p_convert = sub.add_parser("convert", help="filter/tag/rename extracted .xml files to .zwo in place")
    p_convert.add_argument("workouts_dir", help="the extracted Workouts/ directory")

    args = parser.parse_args()
    if args.cmd == "extract":
        cmd_extract(args.wad_path, args.out_dir)
    elif args.cmd == "convert":
        cmd_convert(args.workouts_dir)
