from typing import Any, Callable, Dict, Generic, Optional, TypeVar, cast

from typing_extensions import ParamSpec, TypedDict

from polyfactory.exceptions import ParameterError
from polyfactory.pytest_plugin import FactoryFixture

T = TypeVar("T")
P = ParamSpec("P")


class WrappedCallable(TypedDict):
    value: Callable


class Require:
    """A placeholder class used to mark a given factory attribute as a required build-time kwarg."""


class Ignore:
    """A placeholder class used to mark a given factory attribute as ignored."""


class Use(Generic[P, T]):
    """Factory field used to wrap a callable.

    The callable will be invoked whenever building the given factory
        attribute.
    """

    __slots__ = ("fn", "kwargs", "args")

    def __init__(self, fn: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> None:
        """Wrap a callable.

        :param fn: A callable to wrap.
        :param args: Any args to pass to the callable.
        :param kwargs: Any kwargs to pass to the callable.
        """
        self.fn: WrappedCallable = {"value": fn}
        self.kwargs = kwargs
        self.args = args

    def to_value(self) -> T:
        """Invokes the callable.

        :return: The output of the callable.
        """
        return cast("T", self.fn["value"](*self.args, **self.kwargs))


class PostGenerated:
    """Factory field that allows generating values after other fields are generated by the factory."""

    __slots__ = ("fn", "kwargs", "args")

    def __init__(self, fn: Callable, *args: Any, **kwargs: Any) -> None:
        """Designate field as post-generated.

        :param fn: A callable.
        :param args: Args for the callable.
        :param kwargs: Kwargs for the callable.
        """
        self.fn: WrappedCallable = {"value": fn}
        self.kwargs = kwargs
        self.args = args

    def to_value(self, name: str, values: Dict[str, Any]) -> Any:
        """Invoke the post-generation callback passing to it the build results.

        :param name: Field name.
        :param values: Generated values.

        :return: An arbitrary value.
        """
        return self.fn["value"](name, values, *self.args, **self.kwargs)


class Fixture:
    """Factory field to create a pytest fixture from a factory."""

    __slots__ = ("fixture", "size", "kwargs")

    def __init__(self, fixture: Callable, size: Optional[int] = None, **kwargs: Any) -> None:
        """Create a fixture from a factory.

        :param fixture: A factory that was registered as a fixture.
        :param size: Optional batch size.
        :param kwargs: Any build kwargs.
        """
        self.fixture: WrappedCallable = {"value": fixture}
        self.size = size
        self.kwargs = kwargs

    def to_value(self) -> Any:
        """Calls the factory's build or batch methodsmethod either its build method - or if size is given, batch.

        :raises: ParameterError
        :return: The build result.
        """

        if factory := FactoryFixture.factory_class_map.get(self.fixture["value"]):
            if self.size:
                return factory.batch(self.size, **self.kwargs)
            return factory.build(**self.kwargs)

        raise ParameterError("fixture has not been registered using the register_factory decorator")
