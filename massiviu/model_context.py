from django.db.models import AutoField


PK_ID = 'id'  # default name of primary key field


class value_parser(classmethod):
    """

    """

    def __init__(self, *args, **kw):
        """

        """
        func = args[0]
        func.is_value_parser = True
        super(value_parser, self).__init__(*args, **kw)


def get_value_parsers_from_class(klass):
    """

    """
    return [getattr(klass, name) for name, parser in klass.__dict__.items() if isinstance(parser, value_parser)]


def get_default_value_for_field_from_model(model, field):
    """
    Get default value, if any, for a specified field in a specified model.
    """
    if not hasattr(model._meta, 'fields'):
        return None

    for f in model._meta.fields:
        if field == f.name:
            if hasattr(f.default, '__name__'):
                if f.default.__name__ == 'NOT_PROVIDED':
                    return None
            return f.default
    return None


def get_fields(table_name, cursor, dbtype, _quote):
    """

    """
    default_sql = 'select * from %s LIMIT 1' % _quote(table_name)
    sql = {
        'sqlite': default_sql,
        'mysql': default_sql,
        'postgres': default_sql
    }
    cursor.execute(sql.get(dbtype, 'select * from %s where 1=2' % _quote(table_name)))
    fields = []
    for idx, field_attrs in enumerate(cursor.description):
        fields.append(field_attrs[0])
    return fields


class ModelContext:
    """

    """
    def __init__(self, model, db_context):
        """

        """
        self.model = model
        self.table_name = model._meta.db_table
        self.object_name = model._meta.object_name
        self.value_parsers = get_value_parsers_from_class(model)
        self.pk = model._meta.pk.name
        self.pk_is_auto_field = isinstance(model._meta.pk, AutoField)
        self.fields = get_fields(self.table_name, db_context.cursor, db_context.db_type, db_context.quote)
        self.default_values = {}

        for key in self.fields:
            if key != self.pk:
                self.default_values[key] = get_default_value_for_field_from_model(model, key)