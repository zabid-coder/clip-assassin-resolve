"""Validated, persistent folder templates with identical preview and creation paths."""
import ast
import json
import operator
import re
from datetime import datetime
from pathlib import Path

from models.ingest_template import IngestTemplate, ParameterType


class TemplateEngine:
    variable_pattern = re.compile(r'\{\{?(\w+)(?::([^{}]+))?\}?\}')

    def _prepare_values(self, template, values):
        prepared = {name: definition.get('default', datetime.now().strftime(definition.get('default_format', '%Y-%m-%d'))
                    if definition.get('type') == 'date' else '')
                    for name, definition in template.builtin_params.items()}
        prepared.update({p.name: p.default if p.default is not None else '' for p in template.parameters})
        prepared.update(values)
        for key, value in list(prepared.items()):
            if isinstance(value, str) and value in ('{today}', '{date}'):
                prepared[key] = datetime.now().strftime('%Y-%m-%d')
        return prepared

    def validate_parameters(self, template, values):
        errors = []
        for name, definition in template.builtin_params.items():
            if definition.get('required') and values.get(name) in (None, ''):
                errors.append(f'Missing required parameter: {name}')
        for param in template.parameters:
            value = values.get(param.name)
            if value in (None, ''):
                if param.required:
                    errors.append(f'Missing required parameter: {param.label}')
                continue
            try:
                if param.type == ParameterType.NUMBER:
                    number = float(value)
                    if not number.is_integer() or not -10000 <= number <= 10000:
                        raise ValueError('must be a finite whole number between -10000 and 10000')
                    if param.min_value is not None and number < param.min_value:
                        raise ValueError(f'must be >= {param.min_value}')
                    if param.max_value is not None and number > param.max_value:
                        raise ValueError(f'must be <= {param.max_value}')
                    values[param.name] = int(number)
                elif param.type == ParameterType.DATE:
                    datetime.strptime(str(value), param.date_format or '%Y-%m-%d')
                elif param.type == ParameterType.SELECT and param.options and value not in param.options:
                    raise ValueError('select one of: ' + ', '.join(param.options))
                elif param.type == ParameterType.BOOLEAN:
                    if value not in (True, False, 'true', 'false', 'True', 'False', 0, 1):
                        raise ValueError('must be true or false')
                    values[param.name] = value in (True, 'true', 'True', 1)
                if param.validation_pattern and not re.fullmatch(param.validation_pattern, str(value)):
                    raise ValueError('does not match the required pattern')
            except (ValueError, TypeError, re.error) as exc:
                errors.append(f'{param.label}: {exc}')
        return not errors, errors

    def substitute_variables(self, text, values, date_format='%Y-%m-%d'):
        def replace(match):
            name, spec = match.group(1), match.group(2)
            if name not in values:
                raise ValueError(f'Unknown variable: {name}')
            value = values[name]
            if name == 'date' and spec:
                return datetime.strptime(str(value), date_format).strftime(spec)
            return format(value, spec) if spec else str(value if value is not None else '')
        return self.variable_pattern.sub(replace, text)

    def evaluate_condition(self, condition, values):
        if not condition:
            return True
        comparisons = {ast.Eq: operator.eq, ast.NotEq: operator.ne, ast.Gt: operator.gt,
                       ast.GtE: operator.ge, ast.Lt: operator.lt, ast.LtE: operator.le,
                       ast.In: lambda a, b: a in b, ast.NotIn: lambda a, b: a not in b}
        def visit(node):
            if isinstance(node, ast.Constant): return node.value
            if isinstance(node, (ast.List, ast.Tuple)): return [visit(item) for item in node.elts]
            if isinstance(node, ast.Name):
                if node.id not in values: raise ValueError(f'Unknown condition variable: {node.id}')
                return values[node.id]
            if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not): return not visit(node.operand)
            if isinstance(node, ast.BoolOp):
                parts = [bool(visit(v)) for v in node.values]
                return all(parts) if isinstance(node.op, ast.And) else any(parts)
            if isinstance(node, ast.Compare):
                left = visit(node.left)
                for op, right_node in zip(node.ops, node.comparators):
                    if type(op) not in comparisons: raise ValueError('Unsupported condition operator')
                    right = visit(right_node)
                    if not comparisons[type(op)](left, right): return False
                    left = right
                return True
            raise ValueError('Conditions support parameter comparisons, and, or, and not')
        return bool(visit(ast.parse(condition, mode='eval').body))

    def generate_structure(self, template, values, base_path, dry_run=False):
        items = []
        try:
            if not base_path.strip(): raise ValueError('Choose a base directory')
            prepared = self._prepare_values(template, values)
            valid, errors = self.validate_parameters(template, prepared)
            if not valid: raise ValueError('; '.join(errors))
            base = Path(base_path).expanduser().resolve()
            def process(node, parent, scope, depth=0):
                if depth > 30 or len(items) > 10000: raise ValueError('Template is too large')
                if not self.evaluate_condition(node.condition, scope): return
                scopes = [scope]
                if node.loop_variable:
                    count = node.loop_end if node.loop_end is not None else scope.get(node.loop_variable, 1)
                    count = int(count)
                    if count < node.loop_start or count - node.loop_start >= 1000:
                        raise ValueError('Loops must create between 1 and 1000 items')
                    scopes = [{**scope, node.loop_index or node.loop_variable: i} for i in range(node.loop_start, count + 1)]
                for local in scopes:
                    name = self.substitute_variables(node.name, local)
                    if not name or name in ('.', '..') or any(c in name for c in '/\\\0'):
                        raise ValueError(f'Invalid folder/file name: {name!r}')
                    path = (parent / name).resolve()
                    if not path.is_relative_to(base): raise ValueError('Template path escapes the base directory')
                    if node.type not in ('folder', 'file'): raise ValueError(f'Unsupported node type: {node.type}')
                    if node.type == 'file' and node.children: raise ValueError('Files cannot contain child nodes')
                    content = self.substitute_variables(node.placeholder_content or '', local)
                    items.append({'name': name, 'path': str(path), 'type': node.type, 'depth': depth, 'content': content})
                    for child in node.children or []: process(child, path, local, depth + 1)
            for node in template.structure: process(node, base, prepared)
            # Preflight all paths before creating anything. Existing files are preserved.
            seen = {}
            for item in items:
                path = Path(item['path'])
                if path in seen and seen[path] != item['type']: raise ValueError(f'Conflicting node types: {path}')
                seen[path] = item['type']
                if path.exists() and path.is_dir() != (item['type'] == 'folder'):
                    raise ValueError(f'Existing path has a different type: {path}')
            if not dry_run:
                for index, item in enumerate(items):
                    from services.jobs import checkpoint
                    checkpoint(10+index/max(1,len(items))*85, f"Creating {item['name']}")
                    path = Path(item['path'])
                    if item['type'] == 'folder': path.mkdir(parents=True, exist_ok=True)
                    elif not path.exists():
                        path.parent.mkdir(parents=True, exist_ok=True)
                        with path.open('x', encoding='utf-8') as handle: handle.write(item['content'])
            public = [{k: v for k, v in item.items() if k != 'content'} for item in items]
            return {'success': True, 'errors': [], 'created': [] if dry_run else public,
                    'preview': public, 'total_items': len(public), 'base_path': str(base)}
        except (ValueError, TypeError, OSError, SyntaxError) as exc:
            return {'success': False, 'errors': [str(exc)], 'created': [], 'preview': [], 'total_items': 0, 'base_path': base_path}

    def get_preview_tree(self, template, values, base_path='/preview'):
        result = self.generate_structure(template, values, base_path, dry_run=True)
        if not result['success']: return 'Error: ' + '; '.join(result['errors'])
        return '\n'.join('    ' * item['depth'] + ('📁 ' if item['type'] == 'folder' else '📄 ') + item['name'] for item in result['preview'])

    def export_template(self, template, filepath):
        Path(filepath).write_text(template.to_json(), encoding='utf-8')

    def import_template(self, filepath):
        return IngestTemplate.from_json(Path(filepath).read_text(encoding='utf-8'))


template_engine = TemplateEngine()
