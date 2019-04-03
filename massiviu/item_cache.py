import sys
import types

# Python 3.x or 2.x
from .exceptions import PrimaryKeyInInsertValues, PrimaryKeyMissingInInsertValues

PY3 = sys.version_info[0] == 3 or False
ITEM_LIMIT = 999  # How many items to cache before forcing an executemany.


class ItemCache(object):
    """
    Holds item waiting to be inserted or updated.
    """

    def __init__(self, model_context, operations, value_parsers={}, cache_limit=ITEM_LIMIT):
        """

        """
        self.value_parsers = value_parsers
        self.model_context = model_context
        self.operations = operations
        self.cache_limit = cache_limit
        self.reset()

    def flush(self):
        """

        """
        self.operations.execute_sql(self)

    def reset(self):
        """

        """
        self.item_counter = 0
        self.insert_items = []
        self.delete_items = []
        self.bulk_updates = {}
        self.update_items = []
        self.bulk_updates = {}
        for field in self.model_context.fields:
            self.bulk_updates[field] = {}

    def is_full(self):
        """

        """
        return self.item_counter >= self.cache_limit

    def _on_add(self):
        """

        """
        if self.is_full():
            self.operations.execute_sql(self)
            self.reset()

    def parse_values(self, values):
        """
        Executes any values parsers found in model.
        """
        for parser in self.value_parsers:
            values = parser(values)
            if not values:
                return
        return values

    def update(self, values):
        """
        Adds a set of values to execute as update using cursor.executemany.
        """
        if not self.model_context.pk in values:
            raise PrimaryKeyMissingInInsertValues(self.model_context.pk)

        values = self.parse_values(values)
        if not values:
            return

        self.update_items.append(values)
        self.item_counter += 1
        self._on_add()

    def bulk_update(self, values):
        """
        Adds a set of values to use for alternative bulk updates, using Model.objects.filter(id__in=...).update().
        See the README.md for more details.
        """
        pk = values.get(self.model_context.pk, None)
        if not pk:
            raise PrimaryKeyMissingInInsertValues("Missing primary key. Required for call to prepare.")

        values = self.parse_values(values)
        if not values:
            return

        del values[self.model_context.pk]
        for k, v in values.items():
            self.bulk_updates.setdefault(k, {}).setdefault(v, []).append(pk)
        self.item_counter += 1
        self._on_add()

    def insert(self, values):
        """
        Adds a dictionary with values to insert/update
        """
        if self.model_context.pk in values and self.model_context.pk_is_auto_field:
            raise PrimaryKeyInInsertValues('Primary key in insert values: %s' % values)

        final_values = {}
        for k, v in self.model_context.default_values.items():
            if callable(v):
                final_values[k] = v()
            else:
                final_values[k] = v

        final_values.update(values)

        final_values = self.parse_values(final_values)
        if not final_values:
            return

        self.insert_items.append(final_values)
        self.item_counter += 1
        self._on_add()

    def delete(self, pk):
        """
        Adds a primary key to the deletion queue.
        """
        if not PY3:
            assert types.IntType == type(pk), "pk argument must be integer."
        self.delete_items.append(int(pk))
        self.item_counter += 1
        self._on_add()
