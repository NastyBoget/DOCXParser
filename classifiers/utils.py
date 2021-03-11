from typing import List, Iterable, TypeVar, Optional

T = TypeVar("T")


def flatten(data: List[List[T]]) -> Iterable[T]:
    for group in data:
        for item in group:
            yield item


def identity(x: T):
    return x


def list_get(ls: List[T], index: int) -> Optional[T]:
    if 0 <= index < len(ls):
        return ls[index]
    return None
