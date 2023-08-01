"""
This file contains a minimal set of tests for compliance with the extension
array interface test suite, and should contain no other tests.
The test suite for the full functionality of the array is located in
`pandas/tests/arrays/`.

The tests in this file are inherited from the BaseExtensionTests, and only
minimal tweaks should be applied to get the tests passing (by overwriting a
parent method).

Additional tests should either be added to one of the BaseExtensionTests
classes (if they are relevant for the extension interface for all dtypes), or
be added to the array-specific tests in `pandas/tests/arrays/`.

"""
import numpy as np
import pytest

from pandas.compat import (
    IS64,
    is_platform_windows,
)

import pandas as pd
import pandas._testing as tm
from pandas.core.arrays.floating import (
    Float32Dtype,
    Float64Dtype,
)
from pandas.core.arrays.integer import (
    Int8Dtype,
    Int16Dtype,
    Int32Dtype,
    Int64Dtype,
    UInt8Dtype,
    UInt16Dtype,
    UInt32Dtype,
    UInt64Dtype,
)
from pandas.tests.extension import base

pytestmark = [
    pytest.mark.filterwarnings(
        "ignore:invalid value encountered in divide:RuntimeWarning"
    ),
    pytest.mark.filterwarnings("ignore:Mean of empty slice:RuntimeWarning"),
    # overflow only relevant for Floating dtype cases cases
    pytest.mark.filterwarnings("ignore:overflow encountered in reduce:RuntimeWarning"),
]


def make_data():
    return list(range(1, 9)) + [pd.NA] + list(range(10, 98)) + [pd.NA] + [99, 100]


def make_float_data():
    return (
        list(np.arange(0.1, 0.9, 0.1))
        + [pd.NA]
        + list(np.arange(1, 9.8, 0.1))
        + [pd.NA]
        + [9.9, 10.0]
    )


@pytest.fixture(
    params=[
        Int8Dtype,
        Int16Dtype,
        Int32Dtype,
        Int64Dtype,
        UInt8Dtype,
        UInt16Dtype,
        UInt32Dtype,
        UInt64Dtype,
        Float32Dtype,
        Float64Dtype,
    ]
)
def dtype(request):
    return request.param()


@pytest.fixture
def data(dtype):
    if dtype.kind == "f":
        data = make_float_data()
    else:
        data = make_data()
    return pd.array(data, dtype=dtype)


@pytest.fixture
def data_for_twos(dtype):
    return pd.array(np.ones(100) * 2, dtype=dtype)


@pytest.fixture
def data_missing(dtype):
    if dtype.kind == "f":
        return pd.array([pd.NA, 0.1], dtype=dtype)
    return pd.array([pd.NA, 1], dtype=dtype)


@pytest.fixture
def data_for_sorting(dtype):
    if dtype.kind == "f":
        return pd.array([0.1, 0.2, 0.0], dtype=dtype)
    return pd.array([1, 2, 0], dtype=dtype)


@pytest.fixture
def data_missing_for_sorting(dtype):
    if dtype.kind == "f":
        return pd.array([0.1, pd.NA, 0.0], dtype=dtype)
    return pd.array([1, pd.NA, 0], dtype=dtype)


@pytest.fixture
def na_cmp():
    # we are pd.NA
    return lambda x, y: x is pd.NA and y is pd.NA


@pytest.fixture
def na_value():
    return pd.NA


@pytest.fixture
def data_for_grouping(dtype):
    if dtype.kind == "f":
        b = 0.1
        a = 0.0
        c = 0.2
    else:
        b = 1
        a = 0
        c = 2
    na = pd.NA
    return pd.array([b, b, na, na, a, a, b, c], dtype=dtype)


class TestDtype(base.BaseDtypeTests):
    pass


class TestArithmeticOps(base.BaseArithmeticOpsTests):
    def _check_op(self, s, op, other, op_name, exc=NotImplementedError):
        if exc is None:
            sdtype = tm.get_dtype(s)

            if hasattr(other, "dtype") and isinstance(other.dtype, np.dtype):
                if sdtype.kind == "f":
                    if other.dtype.kind == "f":
                        # other is np.float64 and would therefore always result
                        # in upcasting, so keeping other as same numpy_dtype
                        other = other.astype(sdtype.numpy_dtype)

                else:
                    # i.e. sdtype.kind in "iu""
                    if other.dtype.kind in "iu" and sdtype.is_unsigned_integer:
                        # TODO: comment below is inaccurate; other can be int8
                        #  int16, ...
                        #  and the trouble is that e.g. if s is UInt8 and other
                        #  is int8, then result is UInt16
                        # other is np.int64 and would therefore always result in
                        # upcasting, so keeping other as same numpy_dtype
                        other = other.astype(sdtype.numpy_dtype)

            result = op(s, other)
            expected = self._combine(s, other, op)

            if sdtype.kind in "iu":
                if op_name in ("__rtruediv__", "__truediv__", "__div__"):
                    expected = expected.fillna(np.nan).astype("Float64")
                else:
                    # combine method result in 'biggest' (int64) dtype
                    expected = expected.astype(sdtype)
            else:
                # combine method result in 'biggest' (float64) dtype
                expected = expected.astype(sdtype)

            tm.assert_equal(result, expected)
        else:
            with pytest.raises(exc):
                op(s, other)

    def check_opname(self, ser: pd.Series, op_name: str, other, exc=None):
        # overwriting to indicate ops don't raise an error
        super().check_opname(ser, op_name, other, exc=None)

    def _check_divmod_op(self, ser: pd.Series, op, other, exc=None):
        super()._check_divmod_op(ser, op, other, None)


class TestComparisonOps(base.BaseComparisonOpsTests):
    def _check_op(
        self, ser: pd.Series, op, other, op_name: str, exc=NotImplementedError
    ):
        if exc is None:
            result = op(ser, other)
            # Override to do the astype to boolean
            expected = ser.combine(other, op).astype("boolean")
            tm.assert_series_equal(result, expected)
        else:
            with pytest.raises(exc):
                op(ser, other)

    def check_opname(self, ser: pd.Series, op_name: str, other, exc=None):
        super().check_opname(ser, op_name, other, exc=None)

    def _compare_other(self, ser: pd.Series, data, op, other):
        op_name = f"__{op.__name__}__"
        self.check_opname(ser, op_name, other)


class TestInterface(base.BaseInterfaceTests):
    pass


class TestConstructors(base.BaseConstructorsTests):
    pass


class TestReshaping(base.BaseReshapingTests):
    pass

    # for test_concat_mixed_dtypes test
    # concat of an Integer and Int coerces to object dtype
    # TODO(jreback) once integrated this would


class TestGetitem(base.BaseGetitemTests):
    pass


class TestSetitem(base.BaseSetitemTests):
    pass


class TestIndex(base.BaseIndexTests):
    pass


class TestMissing(base.BaseMissingTests):
    pass


class TestMethods(base.BaseMethodsTests):
    _combine_le_expected_dtype = object  # TODO: can we make this boolean?


class TestCasting(base.BaseCastingTests):
    pass


class TestGroupby(base.BaseGroupbyTests):
    pass


class TestNumericReduce(base.BaseNumericReduceTests):
    def check_reduce(self, ser: pd.Series, op_name: str, skipna: bool):
        # overwrite to ensure pd.NA is tested instead of np.nan
        # https://github.com/pandas-dev/pandas/issues/30958

        cmp_dtype = "int64"
        if ser.dtype.kind == "f":
            # Item "dtype[Any]" of "Union[dtype[Any], ExtensionDtype]" has
            # no attribute "numpy_dtype"
            cmp_dtype = ser.dtype.numpy_dtype  # type: ignore[union-attr]

        if op_name == "count":
            result = getattr(ser, op_name)()
            expected = getattr(ser.dropna().astype(cmp_dtype), op_name)()
        else:
            result = getattr(ser, op_name)(skipna=skipna)
            expected = getattr(ser.dropna().astype(cmp_dtype), op_name)(skipna=skipna)
            if not skipna and ser.isna().any():
                expected = pd.NA
        tm.assert_almost_equal(result, expected)

    def check_reduce_frame(self, ser: pd.Series, op_name: str, skipna: bool):
        if op_name in ["count", "kurt", "sem"]:
            assert not hasattr(ser.array, op_name)
            pytest.skip(f"{op_name} not an array method")

        arr = ser.array
        df = pd.DataFrame({"a": arr})

        is_windows_or_32bit = is_platform_windows() or not IS64

        if tm.is_float_dtype(arr.dtype):
            cmp_dtype = arr.dtype.name
        elif op_name in ["mean", "median", "var", "std", "skew"]:
            cmp_dtype = "Float64"
        elif op_name in ["max", "min"]:
            cmp_dtype = arr.dtype.name
        elif arr.dtype in ["Int64", "UInt64"]:
            cmp_dtype = arr.dtype.name
        elif tm.is_signed_integer_dtype(arr.dtype):
            cmp_dtype = "Int32" if is_windows_or_32bit else "Int64"
        elif tm.is_unsigned_integer_dtype(arr.dtype):
            cmp_dtype = "UInt32" if is_windows_or_32bit else "UInt64"
        else:
            raise TypeError("not supposed to reach this")

        if not skipna and ser.isna().any():
            expected = pd.array([pd.NA], dtype=cmp_dtype)
        else:
            exp_value = getattr(ser.dropna().astype(cmp_dtype), op_name)()
            expected = pd.array([exp_value], dtype=cmp_dtype)

        result1 = arr._reduce(op_name, skipna=skipna, keepdims=True)
        result2 = getattr(df, op_name)(skipna=skipna).array

        tm.assert_extension_array_equal(result1, result2)
        tm.assert_extension_array_equal(result2, expected)


@pytest.mark.skip(reason="Tested in tests/reductions/test_reductions.py")
class TestBooleanReduce(base.BaseBooleanReduceTests):
    pass


class TestAccumulation(base.BaseAccumulateTests):
    @pytest.mark.parametrize("skipna", [True, False])
    def test_accumulate_series_raises(self, data, all_numeric_accumulations, skipna):
        pass

    def check_accumulate(self, ser: pd.Series, op_name: str, skipna: bool):
        # overwrite to ensure pd.NA is tested instead of np.nan
        # https://github.com/pandas-dev/pandas/issues/30958
        length = 64
        if not IS64 or is_platform_windows():
            # Item "ExtensionDtype" of "Union[dtype[Any], ExtensionDtype]" has
            # no attribute "itemsize"
            if not ser.dtype.itemsize == 8:  # type: ignore[union-attr]
                length = 32

        if ser.dtype.name.startswith("U"):
            expected_dtype = f"UInt{length}"
        elif ser.dtype.name.startswith("I"):
            expected_dtype = f"Int{length}"
        elif ser.dtype.name.startswith("F"):
            # Incompatible types in assignment (expression has type
            # "Union[dtype[Any], ExtensionDtype]", variable has type "str")
            expected_dtype = ser.dtype  # type: ignore[assignment]

        if op_name == "cumsum":
            result = getattr(ser, op_name)(skipna=skipna)
            expected = pd.Series(
                pd.array(
                    getattr(ser.astype("float64"), op_name)(skipna=skipna),
                    dtype=expected_dtype,
                )
            )
            tm.assert_series_equal(result, expected)
        elif op_name in ["cummax", "cummin"]:
            result = getattr(ser, op_name)(skipna=skipna)
            expected = pd.Series(
                pd.array(
                    getattr(ser.astype("float64"), op_name)(skipna=skipna),
                    dtype=ser.dtype,
                )
            )
            tm.assert_series_equal(result, expected)
        elif op_name == "cumprod":
            result = getattr(ser[:12], op_name)(skipna=skipna)
            expected = pd.Series(
                pd.array(
                    getattr(ser[:12].astype("float64"), op_name)(skipna=skipna),
                    dtype=expected_dtype,
                )
            )
            tm.assert_series_equal(result, expected)

        else:
            raise NotImplementedError(f"{op_name} not supported")


class TestPrinting(base.BasePrintingTests):
    pass


class TestParsing(base.BaseParsingTests):
    pass


class Test2DCompat(base.Dim2CompatTests):
    pass
