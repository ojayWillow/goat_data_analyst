"""Tests for validation framework - Week 1 Hardening."""

import pytest
import pandas as pd
import numpy as np
from core.validators import (
    DataValidator,
    ValidationError,
    validate_input,
    validate_output,
    validate_dataframe_quality,
    validate_not_none,
    validate_positive_numbers,
    validate_size_limit,
)


class TestDataValidator:
    """Test suite for DataValidator class."""
    
    def test_is_dataframe_true(self):
        """Test is_dataframe with DataFrame."""
        df = pd.DataFrame({'a': [1, 2, 3]})
        assert DataValidator.is_dataframe(df) is True
    
    def test_is_dataframe_false(self):
        """Test is_dataframe with non-DataFrame."""
        assert DataValidator.is_dataframe([1, 2, 3]) is False
        assert DataValidator.is_dataframe({'a': 1}) is False
    
    def test_is_series_true(self):
        """Test is_series with Series."""
        s = pd.Series([1, 2, 3])
        assert DataValidator.is_series(s) is True
    
    def test_is_series_false(self):
        """Test is_series with non-Series."""
        assert DataValidator.is_series([1, 2, 3]) is False
    
    def test_is_list_true(self):
        """Test is_list with list."""
        assert DataValidator.is_list([1, 2, 3]) is True
    
    def test_is_list_false(self):
        """Test is_list with non-list."""
        assert DataValidator.is_list((1, 2, 3)) is False
        assert DataValidator.is_list({1, 2, 3}) is False
    
    def test_is_dict_true(self):
        """Test is_dict with dictionary."""
        assert DataValidator.is_dict({'a': 1, 'b': 2}) is True
    
    def test_is_dict_false(self):
        """Test is_dict with non-dict."""
        assert DataValidator.is_dict([1, 2, 3]) is False
    
    def test_is_array_true(self):
        """Test is_array with numpy array."""
        arr = np.array([1, 2, 3])
        assert DataValidator.is_array(arr) is True
    
    def test_is_array_false(self):
        """Test is_array with non-array."""
        assert DataValidator.is_array([1, 2, 3]) is False
    
    def test_is_numeric_int(self):
        """Test is_numeric with integer."""
        assert DataValidator.is_numeric(5) is True
    
    def test_is_numeric_float(self):
        """Test is_numeric with float."""
        assert DataValidator.is_numeric(5.5) is True
    
    def test_is_numeric_false(self):
        """Test is_numeric with non-numeric."""
        assert DataValidator.is_numeric('5') is False
    
    def test_is_string_true(self):
        """Test is_string with string."""
        assert DataValidator.is_string('hello') is True
    
    def test_is_string_false(self):
        """Test is_string with non-string."""
        assert DataValidator.is_string(5) is False
    
    def test_is_bool_true(self):
        """Test is_bool with boolean."""
        assert DataValidator.is_bool(True) is True
        assert DataValidator.is_bool(False) is True
    
    def test_is_bool_false(self):
        """Test is_bool with non-boolean."""
        assert DataValidator.is_bool(1) is False
    
    def test_dataframe_not_empty_true(self):
        """Test dataframe_not_empty with non-empty DataFrame."""
        df = pd.DataFrame({'a': [1, 2, 3]})
        assert DataValidator.dataframe_not_empty(df) is True
    
    def test_dataframe_not_empty_false(self):
        """Test dataframe_not_empty with empty DataFrame."""
        df = pd.DataFrame()
        assert DataValidator.dataframe_not_empty(df) is False
    
    def test_dataframe_has_columns_true(self):
        """Test dataframe_has_columns with all columns present."""
        df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
        assert DataValidator.dataframe_has_columns(df, ['a', 'b']) is True
    
    def test_dataframe_has_columns_false(self):
        """Test dataframe_has_columns with missing columns."""
        df = pd.DataFrame({'a': [1, 2]})
        assert DataValidator.dataframe_has_columns(df, ['a', 'b']) is False
    
    def test_dataframe_no_nans_true(self):
        """Test dataframe_no_nans with no NaNs."""
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        assert DataValidator.dataframe_no_nans(df) is True
    
    def test_dataframe_no_nans_false(self):
        """Test dataframe_no_nans with NaNs."""
        df = pd.DataFrame({'a': [1, np.nan, 3]})
        assert DataValidator.dataframe_no_nans(df) is False
    
    def test_dataframe_no_duplicates_true(self):
        """Test dataframe_no_duplicates with no duplicates."""
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        assert DataValidator.dataframe_no_duplicates(df) is True
    
    def test_dataframe_no_duplicates_false(self):
        """Test dataframe_no_duplicates with duplicates."""
        df = pd.DataFrame({'a': [1, 1, 3]})
        assert DataValidator.dataframe_no_duplicates(df) is False
    
    def test_list_not_empty_true(self):
        """Test list_not_empty with non-empty list."""
        assert DataValidator.list_not_empty([1, 2, 3]) is True
    
    def test_list_not_empty_false(self):
        """Test list_not_empty with empty list."""
        assert DataValidator.list_not_empty([]) is False
    
    def test_list_of_type_true(self):
        """Test list_of_type with correct types."""
        assert DataValidator.list_of_type([1, 2, 3], int) is True
    
    def test_list_of_type_false(self):
        """Test list_of_type with incorrect types."""
        assert DataValidator.list_of_type([1, '2', 3], int) is False
    
    def test_dict_has_keys_true(self):
        """Test dict_has_keys with all keys present."""
        d = {'a': 1, 'b': 2, 'c': 3}
        assert DataValidator.dict_has_keys(d, ['a', 'b']) is True
    
    def test_dict_has_keys_false(self):
        """Test dict_has_keys with missing keys."""
        d = {'a': 1}
        assert DataValidator.dict_has_keys(d, ['a', 'b']) is False
    
    def test_validate_dataframe_success(self):
        """Test validate with DataFrame."""
        df = pd.DataFrame({'a': [1, 2, 3]})
        assert DataValidator.validate(df, 'dataframe') is True
    
    def test_validate_dataframe_failure(self):
        """Test validate with wrong type."""
        with pytest.raises(ValidationError):
            DataValidator.validate([1, 2, 3], 'dataframe')
    
    def test_validate_list_success(self):
        """Test validate with list."""
        assert DataValidator.validate([1, 2, 3], 'list') is True
    
    def test_validate_list_failure(self):
        """Test validate with wrong list type."""
        with pytest.raises(ValidationError):
            DataValidator.validate('not a list', 'list')
    
    def test_validate_unknown_type(self):
        """Test validate with unknown type."""
        with pytest.raises(ValueError):
            DataValidator.validate([1, 2, 3], 'unknown_type')


class TestValidateInputDecorator:
    """Test suite for @validate_input decorator."""
    
    def test_valid_input(self):
        """Test decorator with valid input."""
        @validate_input({'data': 'list', 'count': 'numeric'})
        def process(data, count):
            return len(data) * count
        
        result = process([1, 2, 3], 2)
        assert result == 6
    
    def test_invalid_input_type(self):
        """Test decorator with invalid input type."""
        @validate_input({'data': 'dataframe'})
        def process(data):
            return len(data)
        
        with pytest.raises(ValidationError):
            process([1, 2, 3])  # list instead of dataframe
    
    def test_with_dataframe(self):
        """Test decorator with DataFrame input."""
        @validate_input({'data': 'dataframe'})
        def process(data):
            return len(data)
        
        df = pd.DataFrame({'a': [1, 2, 3]})
        result = process(df)
        assert result == 3
    
    def test_with_kwargs(self):
        """Test decorator with keyword arguments."""
        @validate_input({'x': 'numeric', 'y': 'numeric'})
        def add(x, y):
            return x + y
        
        result = add(x=5, y=3)
        assert result == 8
    
    def test_with_mixed_args_kwargs(self):
        """Test decorator with mixed args and kwargs."""
        @validate_input({'data': 'list', 'factor': 'numeric'})
        def multiply_list(data, factor=2):
            return [x * factor for x in data]
        
        result = multiply_list([1, 2, 3], factor=3)
        assert result == [3, 6, 9]


class TestValidateOutputDecorator:
    """Test suite for @validate_output decorator."""
    
    def test_valid_output(self):
        """Test decorator with valid output."""
        @validate_output('dataframe')
        def create_df():
            return pd.DataFrame({'a': [1, 2, 3]})
        
        result = create_df()
        assert isinstance(result, pd.DataFrame)
    
    def test_invalid_output_type(self):
        """Test decorator with invalid output type."""
        @validate_output('dataframe')
        def return_list():
            return [1, 2, 3]
        
        with pytest.raises(ValidationError):
            return_list()
    
    def test_valid_list_output(self):
        """Test decorator with list output."""
        @validate_output('list')
        def create_list():
            return [1, 2, 3, 4, 5]
        
        result = create_list()
        assert result == [1, 2, 3, 4, 5]
    
    def test_valid_array_output(self):
        """Test decorator with array output."""
        @validate_output('array')
        def create_array():
            return np.array([1, 2, 3])
        
        result = create_array()
        assert isinstance(result, np.ndarray)


class TestValidateDataframeQualityDecorator:
    """Test suite for @validate_dataframe_quality decorator."""
    
    def test_quality_check_pass(self):
        """Test quality check passes."""
        @validate_dataframe_quality()
        def create_df():
            return pd.DataFrame({'a': [1, 2, 3]})
        
        result = create_df()
        assert len(result) == 3
    
    def test_quality_check_no_nans(self):
        """Test quality check fails with NaNs."""
        @validate_dataframe_quality(require_no_nans=True)
        def create_df_with_nans():
            return pd.DataFrame({'a': [1, np.nan, 3]})
        
        with pytest.raises(ValidationError):
            create_df_with_nans()
    
    def test_quality_check_no_duplicates(self):
        """Test quality check fails with duplicates."""
        @validate_dataframe_quality(require_no_duplicates=True)
        def create_df_with_dups():
            return pd.DataFrame({'a': [1, 1, 3]})
        
        with pytest.raises(ValidationError):
            create_df_with_dups()
    
    def test_quality_check_required_columns(self):
        """Test quality check fails with missing columns."""
        @validate_dataframe_quality(require_columns=['a', 'b'])
        def create_df_missing_cols():
            return pd.DataFrame({'a': [1, 2, 3]})
        
        with pytest.raises(ValidationError):
            create_df_missing_cols()
    
    def test_quality_check_all_conditions(self):
        """Test quality check with all conditions."""
        @validate_dataframe_quality(
            require_no_nans=True,
            require_no_duplicates=True,
            require_columns=['a', 'b']
        )
        def create_good_df():
            return pd.DataFrame({
                'a': [1, 2, 3],
                'b': ['x', 'y', 'z']
            })
        
        result = create_good_df()
        assert len(result) == 3


class TestValidateNotNoneDecorator:
    """Test suite for @validate_not_none decorator."""
    
    def test_not_none_pass(self):
        """Test decorator passes with non-None value."""
        @validate_not_none()
        def return_value():
            return 'something'
        
        result = return_value()
        assert result == 'something'
    
    def test_not_none_fail(self):
        """Test decorator fails with None value."""
        @validate_not_none()
        def return_none():
            return None
        
        with pytest.raises(ValidationError):
            return_none()


class TestValidatePositiveNumbersDecorator:
    """Test suite for @validate_positive_numbers decorator."""
    
    def test_positive_list(self):
        """Test decorator passes with positive list."""
        @validate_positive_numbers()
        def positive_list():
            return [1, 2, 3, 4, 5]
        
        result = positive_list()
        assert result == [1, 2, 3, 4, 5]
    
    def test_non_positive_list(self):
        """Test decorator fails with non-positive list."""
        @validate_positive_numbers()
        def non_positive_list():
            return [1, 0, 3]
        
        with pytest.raises(ValidationError):
            non_positive_list()
    
    def test_positive_number(self):
        """Test decorator passes with positive number."""
        @validate_positive_numbers()
        def positive_number():
            return 42
        
        result = positive_number()
        assert result == 42
    
    def test_non_positive_number(self):
        """Test decorator fails with non-positive number."""
        @validate_positive_numbers()
        def non_positive_number():
            return -5
        
        with pytest.raises(ValidationError):
            non_positive_number()


class TestValidateSizeLimitDecorator:
    """Test suite for @validate_size_limit decorator."""
    
    def test_within_size_limit(self):
        """Test decorator passes within size limit."""
        @validate_size_limit(max_size=100)
        def small_list():
            return [1, 2, 3, 4, 5]
        
        result = small_list()
        assert len(result) == 5
    
    def test_exceeds_size_limit(self):
        """Test decorator fails exceeding size limit."""
        @validate_size_limit(max_size=5)
        def large_list():
            return [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        with pytest.raises(ValidationError):
            large_list()
    
    def test_dataframe_size_limit(self):
        """Test decorator with DataFrame size limit."""
        @validate_size_limit(max_size=100)
        def create_df():
            return pd.DataFrame({'a': range(50)})
        
        result = create_df()
        assert len(result) == 50
    
    def test_dataframe_exceeds_size_limit(self):
        """Test decorator fails with DataFrame exceeding limit."""
        @validate_size_limit(max_size=5)
        def create_large_df():
            return pd.DataFrame({'a': range(10)})
        
        with pytest.raises(ValidationError):
            create_large_df()


class TestValidatorIntegration:
    """Integration tests for validation framework."""
    
    def test_multiple_decorators(self):
        """Test combining multiple validation decorators."""
        @validate_size_limit(max_size=10)
        @validate_output('dataframe')
        def create_validated_df():
            return pd.DataFrame({'a': [1, 2, 3]})
        
        result = create_validated_df()
        assert len(result) == 3
    
    def test_input_and_output_validation(self):
        """Test both input and output validation."""
        @validate_output('dataframe')
        @validate_input({'data': 'dataframe'})
        def process_df(data):
            return data.copy()
        
        df = pd.DataFrame({'a': [1, 2, 3]})
        result = process_df(df)
        assert isinstance(result, pd.DataFrame)
    
    def test_validation_error_messages(self):
        """Test validation error messages are informative."""
        @validate_input({'data': 'dataframe'})
        def process(data):
            return data
        
        with pytest.raises(ValidationError) as exc_info:
            process([1, 2, 3])
        
        assert 'dataframe' in str(exc_info.value).lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
