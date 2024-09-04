from __future__ import annotations


class FilterList(list):
    """
    Basically a list but with the ability to filter.
    """
    def __init__(self, iterable=()):
        super().__init__(iterable)

    def __repr__(self):
        return f"FilterList({repr(list(self))})"

    def by_attribute(self, **kwargs) -> FilterList:
        """
        returns a FilterList that has been filtered with the given values.
        Example: my_list.by_attribute(name="foo", type="bar")
        """
        result = []
        for item in self:
            if all([getattr(item, key) == value for key, value in kwargs.items()]):
                result.append(item)
        return FilterList(result)

    def by_filter(self, function):
        """
        It's almost equivalent to filter().
        Might be removed as it's somewhat useless.
        """
        assert callable(function), "filter must be callable"
        return FilterList(list(filter(function, self)))

    def first(self):
        """
        Returns first element in list.
        Might be removed as it's somewhat useless.
        """
        return self[0]
