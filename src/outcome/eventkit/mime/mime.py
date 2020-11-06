"""Tools to parse and register MIME types."""

from typing import Dict, List, Optional, Tuple, TypeVar

from lark import Lark, Tree
from lark.visitors import Interpreter
from outcome.utils.transformer_dict import TransformerDict

type_separator = '/'
subtype_separator = '.'
suffix_separator = '+'
param_separator = ';'


class MIMEType:
    type: str  # noqa: WPS125, A003
    subtype: str
    suffix: Optional[str]
    parameters: Dict[str, str]

    def __init__(self, default_charset: Optional[str]) -> None:
        if default_charset:
            self.parameters = {'charset': default_charset.lower()}
        else:
            self.parameters = {}
        self.suffix = None

    @property
    def charset(self) -> Optional[str]:
        return self.parameters.get('charset', None)

    @property
    def name(self) -> str:
        name = type_separator.join([self.type, self.subtype])

        if self.suffix:
            name = f'{name}+{self.suffix}'

        if self.parameters:
            params = param_separator.join(sorted(f'{key}={val}'.lower() for key, val in self.parameters.items()))
            name = f'{name}{param_separator}{params}'

        return name  # noqa: R504

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, MIMEType):  # pragma: no cover
            return False
        return o.name == self.name

    def __repr__(self) -> str:  # pragma: no cover
        return self.name

    def __hash__(self) -> int:  # pragma: no cover
        return hash(self.name)


class MIMEParseTreeInterpreter(Interpreter):
    """This class interprets the AST that results from the MIME parser.

    As the nodes of the AST are encountered, the MIMEType instance is built.

    The `type`, `subtype`, etc. methods are called for each node with the
    same name in the AST.
    """

    def __init__(self, default_charset: Optional[str]):
        self.mime_type = MIMEType(default_charset)

    def type(self, tree: Tree) -> None:  # noqa: WPS125, A003
        # There is only one root type, and it only has one token
        self.mime_type.type = tree.children[0].value.lower()  # noqa: WPS125

    def subtype(self, tree: Tree) -> None:
        # A subtype is made up of a sequence of dot-separated terms, followed
        # by an optional suffix
        children: List[Tree] = []
        for child in tree.children:
            if child.data == 'subtype_suffix':
                # The suffix only has one token
                self.mime_type.suffix = child.children[0].value.lower()
            else:
                children.append(child)

        # Each part of the subtype only has one token
        self.mime_type.subtype = subtype_separator.join(c.children[0].value for c in children).lower()

    def parameter(self, tree: Tree) -> None:
        # The parameters are made up of two tokens, after stripping whitespace
        param_key_token, param_value_token = [t for t in tree.children if not (isinstance(t, Tree) and t.data == 'whitespace')]

        param_key = param_key_token.value.lower()
        param_value = param_value_token.value.lower()

        self.mime_type.parameters[param_key] = param_value


_parser = None
CacheKey = Tuple[str, Optional[str]]
_cache: Dict[CacheKey, MIMEType] = {}


def parse_mime_type(mime_type_str: str, default_charset: Optional[str] = 'utf-8') -> MIMEType:
    # It's easier to build a mini-parser than try to do this with regex
    global _parser
    if not _parser:
        _parser = Lark.open('mime.lark', rel_to=__file__)  # noqa: WPS442,WPS122

    key = (mime_type_str, default_charset)

    if key not in _cache:
        try:
            tree = _parser.parse(mime_type_str)  # noqa: WPS442,WPS122,WPS121
        except Exception:
            raise ValueError(f'Invalid MIME type: {mime_type_str}')

        interpreter = MIMEParseTreeInterpreter(default_charset)
        interpreter.visit(tree)

        _cache[key] = interpreter.mime_type

    return _cache.get(key)


T = TypeVar('T')


def normalize_key(key: str) -> str:
    return parse_mime_type(key).name


class MIMETypeDict(TransformerDict[str, T, str]):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, transformer=normalize_key, **kwargs)
