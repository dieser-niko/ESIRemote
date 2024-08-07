from __future__ import annotations

class FilterList(list):
    def __init__(self, iterable):
        super().__init__(iterable)

    def __repr__(self):
        return f"FilterList({repr(list(self))})"

    def by_attributes(self, **kwargs) -> FilterList:
        result = []
        for item in self:
            if all([getattr(item, key) == value for key, value in kwargs.items()]):
                result.append(item)
        return FilterList(result)

    def by_filter(self, function):
        assert callable(function), "filter must be callable"
        return FilterList(list(filter(function, self)))

    def first(self):
        return self[0]
