PARAM_TOKEN = '%s'


class DbContext(object):
    """

    """
    def __init__(self, connection, param_token=PARAM_TOKEN):
        self.param_token = param_token
        self.connection = connection
        self.cursor = connection.cursor()
        mod = self.cursor.connection.__class__.__module__.split('.', 1)[0]

        # a mapping of different database adapters/drivers, needed to handle different
        # quotations/escaping of sql fields, see the quote-method.
        DBNAME_MAP = {
            'psycopg2': 'postgres',
            'MySQLdb': 'mysql',
            'sqlite3': 'sqlite',
            'sqlite': 'sqlite',
            'pysqlite2': 'sqlite'
        }
        self.db_type = DBNAME_MAP.get(mod)
        if self.db_type == 'postgres':
            self.quote = lambda x: '"%s"' % x
        else:
            self.quote = lambda x: '`%s`' % x
