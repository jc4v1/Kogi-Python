#!/usr/bin/env python3
"""Sanitize PNML ids: places -> p0,p1,... transitions -> t1,t2,..."""
import argparse
import xml.etree.ElementTree as ET


def sanitize(input_path: str, output_path: str | None = None) -> None:
    tree = ET.parse(input_path)
    root = tree.getroot()

    # collect places and transitions in document order
    places = root.findall('.//place')
    transitions = root.findall('.//transition')

    place_map = {}
    for i, p in enumerate(places):
        old_id = p.get('id')
        if old_id is None:
            continue
        new_id = f'p{i}'
        place_map[old_id] = new_id

        # update id
        p.set('id', new_id)

        # update the <name><text> for places to the new id
        name_el = p.find('name')
        if name_el is None:
            name_el = ET.SubElement(p, 'name')
        text_el = name_el.find('text')
        if text_el is None:
            text_el = ET.SubElement(name_el, 'text')
        text_el.text = new_id

    trans_map = {}
    # For transitions we must only update the <name><text> if it matched the old id
    for i, t in enumerate(transitions, start=1):
        old_id = t.get('id')
        if old_id is None:
            continue
        new_id = f't{i}'
        trans_map[old_id] = new_id

        # record existing name text before changing id
        name_el = t.find('name')
        name_text = None
        if name_el is not None:
            text_el = name_el.find('text')
            if text_el is not None and text_el.text is not None:
                name_text = text_el.text

        # update id
        t.set('id', new_id)

        # only update the <name><text> if it exactly matched the old id
        if name_text == old_id:
            if name_el is None:
                name_el = ET.SubElement(t, 'name')
            text_el = name_el.find('text')
            if text_el is None:
                text_el = ET.SubElement(name_el, 'text')
            text_el.text = new_id

    id_map = {**place_map, **trans_map}

    # Update attributes that reference ids (common: arc@source/target, place@idref in finalmarkings)
    for arc in root.findall('.//arc'):
        src = arc.get('source')
        tgt = arc.get('target')
        if src in id_map:
            arc.set('source', id_map[src])
        if tgt in id_map:
            arc.set('target', id_map[tgt])

        # ensure an <inscription> exists; if missing, add with value '1'
        if arc.find('inscription') is None:
            ins = ET.SubElement(arc, 'inscription')
            # match common PNML styles: set direct text
            ins.text = '1'

    for elem in root.iter():
        # common attribute names referencing ids
        for attr in ('idref', 'source', 'target'):
            val = elem.get(attr)
            if val in id_map:
                elem.set(attr, id_map[val])

    if output_path is None:
        output_path = input_path

    tree.write(output_path, encoding='utf-8', xml_declaration=True)


def main() -> None:
    parser = argparse.ArgumentParser(description='Sanitize PNML ids for places and transitions')
    parser.add_argument('input', help='Input PNML file')
    parser.add_argument('-o', '--output', help='Output PNML file (default: overwrite input)', default=None)
    args = parser.parse_args()
    sanitize(args.input, args.output)


if __name__ == '__main__':
    main()
