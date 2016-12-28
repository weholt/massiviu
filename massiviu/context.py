from item_cache import ItemCache
from operations import Operations
from db_context import DbContext
from model_context import ModelContext
from exceptions import ValueValidatorException


class NullLogger:

    def debug(self, msg):
        pass
    def info(self, msg):
        pass
    def warn(self, msg):
        pass
    def warning(self, msg):
        pass
    def error(self, msg):
        pass


class MassContext(object):
    """

    """
    def __init__(self, model, connection, value_validator_cls=None, logger=None, db_context_cls=DbContext, model_context_cls=ModelContext,
                 operations_cls=Operations, item_cache_cls=ItemCache):
        """

        """
        self.logger = logger or NullLogger()
        self.db_context = db_context_cls(connection)
        self.model_context = model_context_cls(model, self.db_context)
        self.operations = operations_cls(self.logger, self.db_context, self.model_context)
        self.item_cache = item_cache_cls(self.model_context, self.operations)
        if value_validator_cls and not callable(value_validator_cls):
            raise ValueValidatorException('Supplied value validator is not callable.')
        self.value_validator_cls = value_validator_cls

    def __exit__(self, type, value, traceback):
        """
        Calls flush when exiting the with-block.
        """
        self.item_cache.flush()

    def __enter__(self):
        """
        When using with MassContext(...) as cntx:
        """
        return self

    def reset(self):
        """

        """
        self.item_cache.reset()

    def update(self, values):
        """
        Adds a set of values to execute as update using cursor.executemany.
        """
        if self.value_validator_cls:
            values = self.value_validator_cls(values)

        self.item_cache.update(values)

    def bulk_update(self, values):
        """
        Adds a set of values to use for alternative bulk updates, using Model.objects.filter(id__in=...).update().
        See the README.md for more details.
        """
        if self.value_validator_cls:
            values = self.value_validator_cls(values)

        self.item_cache.bulk_update(values)

    def insert(self, values):
        """
        Adds a dictionary with values to insert/update
        """
        if self.value_validator_cls:
            values = self.value_validator_cls(values)

        self.item_cache.insert(values)

    def delete(self, pk):
        """

        """
        self.item_cache.delete(pk)

