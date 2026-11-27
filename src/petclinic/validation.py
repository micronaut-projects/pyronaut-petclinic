"""Jakarta Validation path handling across GraalPy's iterable conversion."""


def violation_path(violation) -> str:
    parts = []
    for node in violation.getPropertyPath():
        name = node.getName()
        if name:
            if node.isInIterable() and node.getIndex() is not None and parts:
                parts[-1] += '[' + str(node.getIndex()) + ']'
            parts.append(str(name))
    return '.'.join(parts)


def violation_field(violation) -> str:
    return violation_path(violation).rsplit('.', 1)[-1]
