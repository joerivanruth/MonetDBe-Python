import unittest
from sys import platform
import numpy as np
from monetdbe._lowlevel import lib
from monetdbe import connect
from monetdbe.exceptions import ProgrammingError


class TestCffi(unittest.TestCase):
    def test_cffi(self):
        if platform == 'win32':
            # windows has 128 bit disabled
            self.assertEqual(lib.monetdbe_type_unknown, 13)
        else:
            self.assertEqual(lib.monetdbe_type_unknown, 14)

    def test_append_too_many_columns(self):
        with connect() as con:
            con.execute("CREATE TABLE test (i int)")
            data = {'i': np.array([1, 2, 3]), 'j': np.array([1, 2, 3])}
            with self.assertRaises(ProgrammingError):
                con._internal.append(table='test', data=data)

    def test_append_too_little_columns(self):
        with connect() as con:
            con.execute("CREATE TABLE test (i int, j int)")
            data = {'i': np.array([1, 2, 3])}
            with self.assertRaises(ProgrammingError):
                con._internal.append(table='test', data=data)

    def test_append_wrong_type(self):
        """
        we now convert this automatically, so should not raise error
        """
        with connect() as con:
            con.execute("CREATE TABLE test (i int)")
            data = {'i': np.array([0.1, 0.2, 0.3], dtype=np.float32)}
            con._internal.append(table='test', data=data)

    def test_append_wrong_size(self):
        """
        we now convert this automatically, so should not raise error
        """
        with connect() as con:

            con.execute("CREATE TABLE test (i int)")  # SQL int is 32 bit
            data = {'i': np.array([1, 2, 3], dtype=np.int64)}
            con._internal.append(table='test', data=data)

    def test_append_supported_types(self):
        with connect() as con:
            con.execute("CREATE TABLE test (t tinyint, s smallint, i int, h bigint, r real, f float, b bool)")
            con.execute(
                """
                INSERT INTO test VALUES (2^8,  2^16,  2^32,  2^64,  0.12345,  0.123456789, true),
                                        (NULL, NULL,  NULL,  NULL,  NULL,     NULL, NULL),
                                        (0,    0,     0,     0,     0.0,      0.0, false),
                                        (-2^8, -2^16, -2^32, -2^64, -0.12345, -0.123456789, false)
                """
            )
            data = con.execute("select * from test").fetchnumpy()
            con._internal.append(schema='sys', table='test', data=data)
            con.cursor().insert(table='test', values=data)

    def test_append_numpy_only_types(self):
        """
        test numpy types don't have have a direct 1-on-1 sql mapping
        """
        with connect() as con:
            table = 'i'
            con.execute(f"CREATE TABLE {table} (i int)")
            data = {'i': np.ndarray([0], dtype=np.uint32)}
            con._internal.append(schema='sys', table=table, data=data)
            con.cursor().insert(table=table, values=data)

    def test_append_unsupported_types(self):
        with connect() as con:
            con.execute("CREATE TABLE test (s string, b blob, d date, t time, ts timestamp)")
            con.execute(
                """
                INSERT INTO test VALUES ('hi',    '01020308', '2020-01-02', '10:20:30', '2020-01-02 10:20:30' ),
                                        ('World', NULL,       NULL,         NULL,       NULL )
                """
            )

            data = con.execute("select * from test").fetchnumpy()
            with self.assertRaises(con.ProgrammingError):
                con._internal.append(schema='sys', table='test', data=data)
            con.cursor().insert(table='test', values=data)

    def test_append_blend(self):
        """
        numpy.datetime64 is now supported.
        """
        with connect() as con:
            con.execute("CREATE TABLE test (i int, f float, s string, ts timestamp)")
            con.execute(
                """
                INSERT INTO test VALUES (1, 1.2, 'bla', '2020-01-02 10:20:30'),
                                        (NULL, NULL, NULL, NULL)
                """
            )

            data = con.execute("select * from test").fetchnumpy()

            con._internal.append(schema='sys', table='test', data=data)
            con.cursor().insert(table='test', values=data)

            data = con.execute("select * from test").fetchnumpy()

    def test_get_columns(self):
        with connect() as con:
            con.execute("CREATE TABLE test (i int)")
            con.execute("INSERT INTO test VALUES (1)")
            result = list(con._internal.get_columns(table='test'))
            self.assertEqual(result, [('i', 3)])
