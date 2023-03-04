import os
import configparser
import mariadb


class PotentialSQLInjectionAttempt(Exception):
    """
    Exception that indicates a POTENTIAL attempt of SQL injection.
    It does NOT, however, confirm for certain that it is one!
    """

    def __init__(self, message="Potential SQL Injection Attempt"):
        self.message = message
        super().__init__(self.message)


class ConnectionNotEstablished(Exception):
    """
    Exception that indicates when a connection isn't established.
    """
    def __init__(self, message="Connection not established"):
        self.message = message
        super().__init__(self.message)


class MariaDBHelper(object):
    """
    MariaDB Class Helper: manages a connection to a local or remote MariaDB database.
    """

    # MariaDB Reserved keywords
    KEYWORDS = [
        "ACCESSIBLE",
        "ADD",
        "ALL",
        "ALTER",
        "ANALYZE",
        "AND",
        "AS",
        "ASC",
        "ASENSITIVE",
        "BEFORE",
        "BETWEEN",
        "BIGINT",
        "BINARY",
        "BLOB",
        "BOTH",
        "BY",
        "CALL",
        "CASCADE",
        "CASE",
        "CHANGE",
        "CHAR",
        "CHARACTER",
        "CHECK",
        "COLLATE",
        "COLUMN",
        "CONDITION",
        "CONSTRAINT",
        "CONTINUE",
        "CONVERT",
        "CREATE",
        "CROSS",
        "CURRENT_DATE",
        "CURRENT_ROLE",
        "CURRENT_TIME",
        "CURRENT_TIMESTAMP",
        "CURRENT_USER",
        "CURSOR",
        "DATABASE",
        "DATABASES",
        "DAY_HOUR",
        "DAY_MICROSECOND",
        "DAY_MINUTE",
        "DAY_SECOND",
        "DEC",
        "DECIMAL",
        "DECLARE",
        "DEFAULT",
        "DELAYED",
        "DELETE",
        "DESC",
        "DESCRIBE",
        "DETERMINISTIC",
        "DISTINCT",
        "DISTINCTROW",
        "DIV",
        "DO_DOMAIN_IDS",
        "DOUBLE",
        "DROP",
        "DUAL",
        "EACH",
        "ELSE",
        "ELSEIF",
        "ENCLOSED",
        "ESCAPED",
        "EXCEPT",
        "EXISTS",
        "EXIT",
        "EXPLAIN",
        "FALSE",
        "FETCH",
        "FLOAT",
        "FLOAT4",
        "FLOAT8",
        "FOR",
        "FORCE",
        "FOREIGN",
        "FROM",
        "FULLTEXT",
        "GENERAL",
        "GRANT",
        "GROUP",
        "HAVING",
        "HIGH_PRIORITY",
        "HOUR_MICROSECOND",
        "HOUR_MINUTE",
        "HOUR_SECOND",
        "IF",
        "IGNORE",
        "IGNORE_DOMAIN_IDS",
        "IGNORE_SERVER_IDS",
        "IN",
        "INDEX",
        "INFILE",
        "INNER",
        "INOUT",
        "INSENSITIVE",
        "INSERT",
        "INT",
        "INT1",
        "INT2",
        "INT3",
        "INT4",
        "INT8",
        "INTEGER",
        "INTERSECT",
        "INTERVAL",
        "INTO",
        "IS",
        "ITERATE",
        "JOIN",
        "KEY",
        "KEYS",
        "KILL",
        "LEADING",
        "LEAVE",
        "LEFT",
        "LIKE",
        "LIMIT",
        "LINEAR",
        "LINES",
        "LOAD",
        "LOCALTIME",
        "LOCALTIMESTAMP",
        "LOCK",
        "LONG",
        "LONGBLOB",
        "LONGTEXT",
        "LOOP",
        "LOW_PRIORITY",
        "MASTER_HEARTBEAT_PERIOD",
        "MASTER_SSL_VERIFY_SERVER_CERT",
        "MATCH",
        "MAXVALUE",
        "MEDIUMBLOB",
        "MEDIUMINT",
        "MEDIUMTEXT",
        "MIDDLEINT",
        "MINUTE_MICROSECOND",
        "MINUTE_SECOND",
        "MOD",
        "MODIFIES",
        "NATURAL",
        "NOT",
        "NO_WRITE_TO_BINLOG",
        "NULL",
        "NUMERIC",
        "OFFSET",
        "ON",
        "OPTIMIZE",
        "OPTION",
        "OPTIONALLY",
        "OR",
        "ORDER",
        "OUT",
        "OUTER",
        "OUTFILE",
        "OVER",
        "PAGE_CHECKSUM",
        "PARSE_VCOL_EXPR",
        "PARTITION",
        "POSITION",
        "PRECISION",
        "PRIMARY",
        "PROCEDURE",
        "PURGE",
        "RANGE",
        "READ",
        "READS",
        "READ_WRITE",
        "REAL",
        "RECURSIVE",
        "REF_SYSTEM_ID",
        "REFERENCES",
        "REGEXP",
        "RELEASE",
        "RENAME",
        "REPEAT",
        "REPLACE",
        "REQUIRE",
        "RESIGNAL",
        "RESTRICT",
        "RETURN",
        "RETURNING",
        "REVOKE",
        "RIGHT",
        "RLIKE",
        "ROWS",
        "SCHEMA",
        "SCHEMAS",
        "SECOND_MICROSECOND",
        "SELECT",
        "SENSITIVE",
        "SEPARATOR",
        "SET",
        "SHOW",
        "SIGNAL",
        "SLOW",
        "SMALLINT",
        "SPATIAL",
        "SPECIFIC",
        "SQL",
        "SQLEXCEPTION",
        "SQLSTATE",
        "SQLWARNING",
        "SQL_BIG_RESULT",
        "SQL_CALC_FOUND_ROWS",
        "SQL_SMALL_RESULT",
        "SSL",
        "STARTING",
        "STATS_AUTO_RECALC",
        "STATS_PERSISTENT",
        "STATS_SAMPLE_PAGES",
        "STRAIGHT_JOIN",
        "TABLE",
        "TERMINATED",
        "THEN",
        "TINYBLOB",
        "TINYINT",
        "TINYTEXT",
        "TO",
        "TRAILING",
        "TRIGGER",
        "TRUE",
        "UNDO",
        "UNION",
        "UNIQUE",
        "UNLOCK",
        "UNSIGNED",
        "UPDATE",
        "USAGE",
        "USE",
        "USING",
        "UTC_DATE",
        "UTC_TIME",
        "UTC_TIMESTAMP",
        "VALUES",
        "VARBINARY",
        "VARCHAR",
        "VARCHARACTER",
        "VARYING",
        "WHEN",
        "WHERE",
        "WHILE",
        "WINDOW",
        "WITH",
        "WRITE",
        "XOR",
        "YEAR_MONTH",
        "ZEROFILL"
    ]

    EXCEPTIONS = [
        "ACTION",
        "BIT",
        "DATE",
        "ENUM",
        "NO",
        "TEXT",
        "TIME",
        "TIMESTAMP"
    ]

    ORACLE_MODE = [
        "BODY",
        "ELSIF",
        "GOTO",
        "HISTORY",
        "OTHERS",
        "PACKAGE",
        "PERIOD",
        "RAISE",
        "ROWTYPE",
        "SYSTEM",
        "SYSTEM_TIME",
        "VERSIONING",
        "WITHOUT"
    ]

    def __init__(self, inipath = None):
        """ Initializes with a decrypted config.ini file """

        path_current_directory = os.path.dirname(__file__)
        path_config_file = os.path.join(path_current_directory, '', 'config.ini')

        self._config = configparser.ConfigParser()
        self._config.read(path_config_file)
        self._query = ""
        self._isconn = False


    def bindErrorCallback(self, errcall):
        """
        !!! YET TO BE TESTED !!!
        Binds a remote callback function to print out error messages.
        """
        self.err = errcall


    def resetQuery(self):
        """ Clears the current query. """
        self._query = ""


    def checkString(self, string):
        """
        Checks if a string or a list of strings are potentially harmful to the integrity of the database.
            Throws: `PotentialSQLInjectionAttempt`
        """
        if type(string) is list:
            for s in string:
                self.checkString(s)
        elif type(string) is str:
            if string in MariaDBHelper.KEYWORDS:
                self.resetQuery()
                raise PotentialSQLInjectionAttempt(f"{string} is a reserved keyword!")
            if string in MariaDBHelper.EXCEPTIONS:
                self.resetQuery()
                raise PotentialSQLInjectionAttempt(f"{string} is a reserved exception!")
            if string in MariaDBHelper.ORACLE_MODE:
                self.resetQuery()
                raise PotentialSQLInjectionAttempt(f"{string} is a reserved special keyword!")


    def connect(self):
        """
        Tries to connect to the MariaDB database, and returns the respective cursor if available.
        """
        try:
            self.connection = mariadb.connect(
                user     = self._config['DATABASE']['user'],
                password = self._config['DATABASE']['password'],
                host     = self._config['DATABASE']['host'],
                port     = int(self._config['DATABASE']['port']),
                database = self._config['DATABASE']['database']
            )
            self._isconn = True
        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            return None
        self.cursor = self.connection.cursor()
        return self.getCursor()


    def isConnected(self):
        """ Indicates if the helper has a connection running. """
        return self._isconn


    def disconnect(self):
        """ Disconnects from the database. """
        self.connection.close()
        self._isconn = False


    def getHMACKey(self):
        """
        Gets HMAC Key from the config.ini file.
        Returns:
            str: HMAC key
        """
        return self._config['VALIDATION']['hmac']


    def commit(self):
        """ Commits the last queries to the database. """
        self.connection.commit()


    def getCursor(self):
        """ Returns the cursor of the connection to the database. """
        return self.cursor


    def Select(self, fields, distinct=False):
        """
        Query constructor: `SELECT`
            Adds from a list of tuples (field, alias), such that
            `SELECT field AS alias`.
            If no alias is desired, put `None` or an empty string.
        """
        self._query += "SELECT" + (" DISTINCT " if distinct else " ")
        for field, alias in fields:
            self.checkString([field, alias])
            self._query += field
            if alias != "" and alias is not None:
                self._query += f" AS '{alias}'"
            self._query += ", "
        self._query = self._query[:-2] + " "
        return self


    def SelectAll(self):
        """
        Query constructor: `SELECT *`
        """
        self._query += "SELECT * "
        return self


    def Update(self, table):
        self._query += f"UPDATE {table} "
        return self


    def Set(self, fields):
        self._query += "SET "
        for field in fields:
            self.checkString(field)
            self._query += f"{field}=?, "
        self._query = self._query[:-2] + " "
        return self


    def Delete(self, table):
        self._query += f"DELETE FROM {table} "
        return self


    def From(self, table, alias=""):
        """
        Query constructor: `FROM`
            Adds a table and alias from the database, such that
            `FROM table alias`.
            If no alias is desired, put `None` or an empty string.
        """
        self.checkString([table, alias])
        self._query += f"FROM {table} {alias} "
        return self


    def Where(self, condition):
        """
        Query constructor: `WHERE`
            Adds the WHERE clause to a query, such that
            `WHERE condition`.
        """
        self.checkString(condition)
        self._query += f"WHERE {condition} "
        return self


    def InnerJoin(self, table, alias="", on="", using=""):
        """
        Query constructor: `INNER JOIN`
            Adds a table and a condition, such that
            `INNER JOIN table ON condition USING predicate`.
        """
        self.checkString([table, on, using])
        self._query += f"INNER JOIN {table} {alias} " + (f"ON {on} " if on != "" else "") + (f"USING {using} " if using != "" else "")
        return self


    def LeftJoin(self, table, alias="", on="", using=""):
        """
        Query constructor: `LEFT JOIN`
            Adds a table and a condition, such that
            `LEFT JOIN table ON condition USING predicate`.
        """
        self.checkString([table, on, using])
        self._query += f"LEFT JOIN {table} {alias} " + (f"ON {on} " if on != "" else "") + (f"USING {using} " if using != "" else "")
        return self


    def InsertInto(self, table, keys):
        """
        Query constructor: `INSERT INTO`
            Creates an entire query to insert values into a table, such that
            `INSERT INTO table ([keys]) VALUES (?, ...)`
        """
        self.checkString([table, keys])
        self._query += f"INSERT INTO {table} ("
        for key in keys:
            self._query += f"{key}, "
        self._query = self._query[:-2] + ") VALUES (" + (", ".join(['?' for _ in range(len(keys))])) + ") "
        return self


    def OrderBy(self, predicate, desc=False, limit=0):
        """
        Query constructor: `ORDER BY`
            Adds a predicate to order by, such that
            `ORDER BY predicate [DESC] [LIMIT limit]`.
            `limit` will only be considered if it is a positive, non-negative, integer number.
        """
        self.checkString(predicate)
        self._query += f"ORDER BY {predicate} "
        if desc:
            self._query += "DESC "
        if limit > 0:
            self._query += f"LIMIT {limit} "
        return self


    def GroupBy(self, predicate):
        self.checkString(predicate)
        self._query += f"GROUP BY {predicate} "
        return self


    def Except(self):
        self._query += "EXCEPT "
        return self


    def OpenSubQuery(self):
        """
        Query constructor: `(` (OPEN SUBQUERY)
            Adds left parenthesis.
        """
        self._query += " ( "
        return self


    def CloseSubQuery(self, alias=""):
        """
        Query constructor: `)` (CLOSE SUBQUERY)
            Adds right parenthesis.
        """
        self._query += f" ) {alias} "
        return self


    def AddCustomQuery(self, query):
        """
        Query constructor: CUSTOM QUERY
            Temporary fix while the helper is not exhaustive enough.
            THIS METHOD IS NOT SAFE AND DOES NOT CHECK FOR SQL INJECTION!
        """
        self._query += f"{query} "
        return self


    def getQuery(self):
        """ Returns the current query. """
        return self._query


    def execute(self, args=None):
        """ Executes the current query. """
        if args is not None and type(args) is tuple:
            self.checkString(list(args))
            self.cursor.execute(self._query, args)
        else:
            self.cursor.execute(self._query)


    def do(self, args=None):
        """
        Does the following methods in order: `execute(args)`, `commit()`, `resetQuery()`.
        `commit()` is executed only if `execute()` does not return any exception.
        Despite any exception that might occur, the query will be emptied.
        The exception will be thrown.
        """
        exc = None
        try:
            self.execute(args)
            self.commit()
        except Exception as e:
            exc = e
        finally:
            self.resetQuery()
            raise exc
