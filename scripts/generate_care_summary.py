"""Generate the care export's Python DTOs from its checked-in JSON Schema."""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / 'config/jsonschema/owner-care-summary.schema.json'
OUTPUT = ROOT / 'src/petclinic/dtos/care_summary.py'


def generate(schema):
    definitions = []

    def object_type(node, name):
        fields = []
        required = set(node.get('required', []))
        for key, value in node['properties'].items():
            kind = value['type']
            nullable = isinstance(kind, list) and 'null' in kind
            if isinstance(kind, list):
                kind = next(item for item in kind if item != 'null')
            if kind == 'array':
                nested = object_type(value['items'], name + key.rstrip('s').capitalize())
                hint = 'list[' + nested + ']'
            elif kind == 'integer':
                hint = 'int'
            elif kind == 'string':
                hint = 'LocalDate' if value.get('format') == 'date' else 'str'
            else:
                raise ValueError('Unsupported care-summary schema type: ' + str(kind))
            if nullable or key not in required:
                hint += ' | None'
            attribute = key.lstrip('_')
            if attribute != key:
                hint = f'Annotated[{hint}, JsonProperty({key!r})]'
            fields.append((key not in required, '    ' + attribute + ': ' + hint + (' = None' if key not in required else '')))
        definitions.append('@Serdeable\n@JsonInclude(JsonInclude.Include.NON_NULL)\n@dataclass\nclass ' + name + ':\n' + '\n'.join(line for optional, line in sorted(fields, key=lambda f: f[0])))
        return name

    object_type(schema, schema['title'])
    header = '''"""Generated from config/jsonschema/owner-care-summary.schema.json.

Regenerate with: python3 scripts/generate_care_summary.py
"""

from dataclasses import dataclass
from typing import Annotated
from com.fasterxml.jackson.annotation import JsonInclude, JsonProperty
from java.time import LocalDate
from micronaut.serde.annotation import Serdeable


'''
    return header + '\n\n\n'.join(definitions) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail when generated DTOs are stale')
    args = parser.parse_args()
    content = generate(json.loads(SCHEMA.read_text()))
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != content:
            raise SystemExit('Care-summary DTOs are stale; run python3 scripts/generate_care_summary.py')
    else:
        OUTPUT.write_text(content)


if __name__ == '__main__':
    main()
