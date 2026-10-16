import yaml
class PaLoader(yaml.SafeLoader):
    pass
# Power Apps writes a bare '=' for an empty formula; PyYAML reads that as the
# yaml 'value' tag. Treat it as the plain string it is.
PaLoader.add_constructor('tag:yaml.org,2002:value', lambda l, n: l.construct_scalar(n))
def load(path):
    return yaml.load(open(path), PaLoader)
