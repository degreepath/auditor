import collections
import functools

import attr


class DuplicateVersion(ValueError):
    pass


@attr.s(slots=True, kw_only=True)
class LoadableRegistry:
    tag_prefix = '!'
    tag_shorthand = None

    # type => {version => function)
    dumpers = attr.ib(factory=collections.defaultdict(dict))

    # base tag => {version => function}
    loaders = attr.ib(factory=collections.defaultdict(dict))

    frozen = False

    def _check_tag(self, tag):
        # Good a place as any, I suppose
        if self.frozen:
            raise RuntimeError("Can't add to a frozen registry")

        if ';' in tag:
            raise ValueError(
                "Tags may not contain semicolons: {0!r}".format(tag))

    def dumper(self, cls, tag, version, inherit=False):
        self._check_tag(tag)

        store_in = self.dumpers

        if version in store_in[cls]:
            raise DuplicateVersion

        tag = self.tag_prefix + tag

        if version is None:
            full_tag = tag
        elif isinstance(version, int) and version > 0:
            full_tag = "{0};{1}".format(tag, version)
        else:
            raise TypeError(
                "Expected None or a positive integer version; "
                "got {0!r} instead".format(version))

        def decorator(f):
            store_in[cls][version] = functools.partial(
                self.run_representer, f, full_tag)
            return f

        return decorator

    def run_representer(self, representer, tag, dumper, data):
        canon_value = representer(data)
        # Note that we /do not/ support subclasses of the built-in types here,
        # to avoid complications from returning types that have their own
        # custom representers
        canon_type = type(canon_value)
        # TODO this gives no control over flow_style, style, and implicit.  do
        # we intend to figure it out ourselves?
        if canon_type is dict:
            return dumper.represent_mapping(tag, canon_value, flow_style=False)
        elif canon_type is collections.OrderedDict:
            # pyyaml tries to sort the items of a dict, which defeats the point
            # of returning an OrderedDict.  Luckily, it only does this if the
            # value it gets has an 'items' method; otherwise it skips the
            # sorting and iterates the value directly, assuming it'll get
            # key/value pairs.  So pass in the dict's items iterator.
            return dumper.represent_mapping(tag, canon_value.items(), flow_style=False)
        elif canon_type in (tuple, list):
            return dumper.represent_sequence(tag, canon_value, flow_style=False)
        elif canon_type in (int, float, bool, str, type(None)):
            return dumper.represent_scalar(tag, canon_value)
        else:
            raise TypeError(
                "Representers must return native YAML types, but the representer "
                "for {!r} returned {!r}, which is of type {!r}"
                    .format(data, canon_value, canon_type))

    def inject_dumpers(self, dumper, version_locks=None):
        if not version_locks:
            version_locks = {}

        for cls, versions in self.dumpers.items():
            version = version_locks.get(cls, max)
            if versions and version is max:
                if None in versions:
                    representer = versions[None]
                else:
                    representer = versions[max(versions)]
            elif version in versions:
                representer = versions[version]
            else:
                raise KeyError(f"Don't know how to dump version {version!r} of type {cls!r}")
            dumper.add_representer(cls, representer)

    # Loading
    # TODO implement "upgrader", which upgrades from one version to another

    def loader(self, tag, version):
        self._check_tag(tag)

        if version in self.loaders[tag]:
            raise DuplicateVersion

        tag = self.tag_prefix + tag

        def decorator(f):
            self.loaders[tag][version] = functools.partial(
                self.run_constructor, f, version)
            return f

        return decorator

    def run_constructor(self, constructor, version, *yaml_args):
        # Two args for add_constructor, three for add_multi_constructor
        if len(yaml_args) == 3:
            loader, suffix, node = yaml_args
            version = int(suffix)
        else:
            loader, node = yaml_args

        if isinstance(node, yaml.ScalarNode):
            data = loader.construct_scalar(node)
        elif isinstance(node, yaml.SequenceNode):
            data = loader.construct_sequence(node, deep=True)
        elif isinstance(node, yaml.MappingNode):
            data = loader.construct_mapping(node, deep=True)
        else:
            raise TypeError("Not a primitive node: {!r}".format(node))
        return constructor(data, version)

    def inject_loaders(self, loader):
        for tag, versions in self.loaders.items():
            # "all" loader overrides everything
            if all in versions:
                if None in versions:
                    loader.add_constructor(tag, versions[None])
                else:
                    loader.add_constructor(tag, versions[all])
                loader.add_multi_constructor(tag + ";", versions[all])
                continue

            # Otherwise, add each constructor individually
            for version, constructor in versions.items():
                if version is None:
                    loader.add_constructor(tag, constructor)
                elif version is any:
                    loader.add_multi_constructor(tag + ";", versions[any])
                    if None not in versions:
                        loader.add_constructor(tag, versions[any])
                else:
                    full_tag = "{0};{1}".format(tag, version)
                    loader.add_constructor(full_tag, constructor)
