
from exceptions import InsertManyException, PrimaryKeyMissingInInsertValues, \
    PrimaryKeyInInsertValues, UpdateManyException, UpdateOneException


class Operations(object):
    """
    
    """
    def __init__(self, logger, db_context, model_context, debug=True):
        """

        """
        self.debug = debug
        self.db_context = db_context
        self.model_context = model_context
        self.logger = logger
        self.insert_sql = self._generate_insert_sql()
        self.update_sql = self._generate_update_sql()
        self.records_processed = 0
        self.sql_calls = 0
        self.do_clean_house = True

    def _generate_insert_sql(self):
        sql = 'insert into %s (%s) values (%s)' % (
            self.db_context.quote(self.model_context.table_name),
            ','.join(self.db_context.quote(f) for f in self.model_context.fields if f != self.model_context.pk or not self.model_context.pk_is_auto_field),
            ','.join(self.db_context.param_token for f in self.model_context.fields if f != self.model_context.pk or not self.model_context.pk_is_auto_field),
        )
        return sql

    def _generate_update_sql(self):
        sql = ['update %s set' % self.db_context.quote(self.model_context.table_name)]
        m = []
        for field_name in self.model_context.fields:
            if field_name == self.model_context.pk:
                continue
            m.append("%s = %s" % (self.db_context.quote(field_name), self.db_context.param_token))
        sql.append(',\n'.join(m))
        sql.append('where %s = %s' % (self.db_context.quote(self.model_context.pk), self.db_context.param_token))
        return '\n'.join(sql)

    def execute_insert_statements(self, insert_items):
        """
        Executes all bulk insert statements.
        """
        field_values = []
        for items in insert_items:
            m = []
            for field_name in self.model_context.fields:
                if field_name in items:
                    m.append(items[field_name])
                elif field_name != self.model_context.pk or not self.model_context.pk_is_auto_field:
                    m.append(None)
            field_values.append(m)
            self.records_processed += 1

        if self.debug:
            self.logger.debug("Executing insert: %s" % self.insert_sql)
            for f in field_values:
                self.logger.debug(str(f))
        try:
            self._execute(self.insert_sql, field_values, many=True)
        except Exception as e:
            raise InsertManyException(e, self.model_context.table_name, self.insert_sql, field_values)

    def execute_delete_statements(self, delete_items):
        """
        Executes all bulk delete statements.
        """
        self.model_context.model.objects.filter(**{"%s__in" % self.model_context.pk: delete_items}).delete()
        self.records_processed += 1

    def execute_sql(self, item_cache):
        """
        Executes all cached sql statements.
        """
        if item_cache.bulk_updates:
            self.execute_bulk_updates(item_cache.bulk_updates)

        if item_cache.update_items:
            self.execute_updates(item_cache.update_items)

        if item_cache.insert_items:
            self.execute_insert_statements(item_cache.insert_items)

        if item_cache.delete_items:
            self.execute_delete_statements(item_cache.delete_items)

    def _execute(self, sql, field_values, many=True):
        self.sql_calls += 1
        try:
            if many:
                self.cursor.executemany(sql, field_values)
            else:
                self.cursor.execute(sql, field_values)
        except:
            self.cursor = self.db_context.cursor
            if many:
                self.cursor.executemany(sql, field_values)
            else:
                self.cursor.execute(sql, field_values)
        finally:
            self.clean_house()

    def execute_updates(self, update_items):
        """
        Executes all bulk update statements.
        """
        params_for_executemany = []
        params_for_execute = []
        # If there all fields are present we can optimize and use executemany,
        # if not we must execute each SQL call in sequence
        for items in update_items:
            if len(items.keys()) != len(self.model_context.fields):
                params_for_execute.append(items)
            else:
                found_all_fields = True
                for field in self.model_context.fields:
                    if not field in items:
                        found_all_fields = False
                        break

                if found_all_fields:
                    params_for_executemany.append(items)
                else:
                    params_for_execute.append(items)

        if params_for_executemany:
            field_values = []
            for items in params_for_executemany:
                m = []
                for field_name in self.model_context.fields:
                    if field_name == self.model_context.pk:
                        continue
                    if field_name in items:
                        m.append(items[field_name])
                    else:
                        m.append(None)
                m.append(items.get(self.model_context.pk))
                field_values.append(m)
                self.records_processed += 1

            if self.debug:
                self.logger.debug("Executing update: %s" % self.update_sql)
                for f in field_values:
                    self.logger.debug(str(f))

            try:
                self._execute(self.update_sql, field_values, many=True)
            except Exception as e:
                raise UpdateManyException(e, self.model_context.table_name, self.update_sql, field_values)

        for items in params_for_execute:
            sql = ['update %s set' % self.db_context.quote(self.model_context.table_name)]
            m = []
            field_values = []
            for field_name in items.keys():
                if field_name == self.model_context.pk or field_name not in self.model_context.fields:
                    continue
                m.append("%s = %s" % (self.db_context.quote(field_name), self.db_context.param_token))
                field_values.append(items[field_name])
            sql.append(',\n'.join(m))
            sql.append('where %s = %s' % (self.db_context.quote(self.model_context.pk), self.db_context.param_token))
            field_values.append(items[self.model_context.pk])
            self.records_processed += 1
            if self.debug:
                self.logger.debug("Executing update: %s" % '\n'.join(sql))
                for f in field_values:
                    self.logger.debug(str(f))

            try:
                self._execute('\n'.join(sql), field_values, many=False)
            except Exception as e:
                raise UpdateOneException(e, self.model_context.table_name, sql, field_values)

    def execute_bulk_updates(self, bulk_updates):
        """
        Executes the bulk bulk update statements
        """
        for field, values in bulk_updates.items():
            for value, ids in values.items():
                self.model_context.model.objects.filter(**{"%s__in" % self.model_context.pk: ids}).update(**{field: value})
                self.records_processed += 1

    def clean_house(self):
        """
        This method removes the last query from the list of queries stored in the django connection
        object. The django-debug-toolbar modifies that list and if we leave our dse based query lying around
        it will cause the debug-toolbar to crash.

        To disable this feature set dse.CLEAN_HOUSE = False.
        This method might later on be used for other things as well.
        """
        #if self.do_clean_house:
         #   self.db_context.connection.queries = self.db_context.connection.queries[:-1]
        pass

