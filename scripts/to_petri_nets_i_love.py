#!/usr/bin/env python3
"""Ensure PNML arcs have an <inscription> child, adding one with text '1' if missing."""
import argparse
import xml.etree.ElementTree as ET


def add_inscription(input_path: str, output_path: str | None = None) -> None:
    """Parse PNML, add missing <inscription> elements to <arc> elements, and write output.

    This function intentionally does nothing else: it will not rename ids or alter other
    elements or attributes.
    """
    tree = ET.parse(input_path)
    root = tree.getroot()

    for arc in root.findall('.//arc'):
        # prefer the explicit <inscription> tag name used in many PNMLs
        ins = arc.find('inscription')
        if ins is None:
            ins = ET.SubElement(arc, 'inscription')
            ins.text = '1'

    if output_path is None:
        output_path = input_path

    tree.write(output_path, encoding='utf-8', xml_declaration=True)


def main() -> None:
    parser = argparse.ArgumentParser(description='Add missing <inscription> to PNML arcs')
    parser.add_argument('input', help='Input PNML file')
    parser.add_argument('-o', '--output', help='Output PNML file (default: overwrite input)', default=None)
    args = parser.parse_args()
    add_inscription(args.input, args.output)


if __name__ == '__main__':
    main()
