from typing import List, Dict, Union, Tuple
from datetime import datetime as datetime_type, timedelta

import pandas as pd
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import Column, DateTime, Float, Interval, ForeignKey, Integer
from sqlalchemy.orm import Query, Session

from bvp.data.services.time_series import collect_time_series_data


class TimedValue(object):
    """
    A mixin of all tables that store time series data, either forecasts or measurements.
    Represents one row.
    """

    @declared_attr
    def __tablename__(cls):  # noqa: B902
        return cls.__name__.lower()

    """The time at which the value is supposed to (have) happen(ed)."""

    @declared_attr
    def datetime(cls):  # noqa: B902
        return Column(DateTime(timezone=True), primary_key=True)

    """The time delta of measuring or forecasting.
    This should be a duration in ISO8601, e.g. "-PT10M", which you can turn into a timedelta with
    isodate.parse_duration.
    Positive durations indicate a forecast, negative ones a measurement after the fact.
    """

    @declared_attr
    def horizon(cls):  # noqa: B902
        return Column(Interval(), nullable=False, primary_key=True)

    """The value."""

    @declared_attr
    def value(cls):  # noqa: B902
        return Column(Float, nullable=False)

    """The data source."""

    @declared_attr
    def data_source(cls):  # noqa: B902
        return Column(Integer, ForeignKey("data_sources.id"), primary_key=True)

    @classmethod
    def make_query(
        cls,
        generic_asset_name: str,
        query_window: Tuple[datetime_type, datetime_type],
        horizon_window: Tuple[Union[None, timedelta], Union[None, timedelta]] = (
            None,
            None,
        ),
        session: Session = None,
    ) -> Query:
        """
        Should be overwritten with the make_query function in subclasses.
        We identify the asset by name, this assumes a unique string field can be used.
        The query window expects start as well as end TODO: in/exclusive?
        The horizon window expects first the earliest horizon (e.g. 6H) and then the latest horion (e.g. 24H).
        The session can be supplied, but if None, the implementation should find a session itself.
        """
        pass

    @classmethod
    def collect(
        cls,
        generic_asset_names: List[str],
        query_window: Tuple[datetime_type, datetime_type] = (None, None),
        horizon_window: Tuple[Union[None, timedelta], Union[None, timedelta]] = (
            None,
            None,
        ),
        resolution: str = None,
        sum_multiple: bool = True,
        create_if_empty: bool = False,
        zero_if_nan: bool = False,
    ) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """Basically a convenience wrapper for services.collect_time_series_data,
        where time series data collection is implemented.
        -PT15M is our default right-after-the-fact measurement."""
        if horizon_window == (None, None):
            horizon_window = (None, timedelta(minutes=-15))
        return collect_time_series_data(
            generic_asset_names=generic_asset_names,
            make_query=cls.make_query,
            query_window=query_window,
            horizon_window=horizon_window,
            resolution=resolution,
            sum_multiple=sum_multiple,
            create_if_empty=create_if_empty,
            zero_if_nan=zero_if_nan,
        )
