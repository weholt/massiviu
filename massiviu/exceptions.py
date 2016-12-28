
class ValueValidatorException(Exception):
    pass


class BaseException(Exception):
    """

    """
    action = 'unknown'

    def __init__(self, msg):
        """

        """
        self.msg = msg

class InsertManyException(BaseException):
    """

    """
    action = 'Insert'

    def __init__(self, exception, table, sql, params):
        self.table = table
        self.sql = sql
        self.params = params
        self.exception = exception

    def __str__(self):
        return "BaseException.%sError on table %s.\nSQL: %s.\nNumber of params: %s.\nException: %s" % \
               (self.action, self.table, self.sql, len(self.params), self.exception)


class UpdateManyException(BaseException):
    """

    """
    action = 'UpdateMany'


class UpdateOneException(BaseException):
    """

    """
    action = 'UpdateOne'

    def __str__(self):
        return "BaseException.%sError on table %s.\nSQL: %s.\nParams: %s.\nException: %s" % \
               (self.action, self.table, '\n'.join(self.sql), self.params, self.exception)


class DeleteManyException(BaseException):
    """

    """
    action = 'DeleteMany'


class PrimaryKeyMissingInInsertValues(BaseException):
    """

    """
    pass


class PrimaryKeyInInsertValues(BaseException):
    """

    """
    pass