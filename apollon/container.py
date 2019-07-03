# Licensed under the terms of the BSD-3-Clause license.
# Copyright (C) 2019 Michael Blaß
# michael.blass@uni-hamburg.de

"""apollon/io.py -- Container Classes.

Classes:
    FeatureSpace
"""

import json
from typing import Any, Dict, List, Optional, Tuple


class FeatureSpace:
    """Container class for feature vectors."""
    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            if isinstance(val, dict):
                val = FeatureSpace(**val)
            self.update(key, val)

    def update(self, key: str, val: Any) -> None:
        """Update the FeatureSpace.

        Args:
            key:  Field name.
            val:  Field value.
        """
        self.__dict__[key] = val

    def items(self) -> List[Tuple[str, Any]]:
        """Provides the the FeatureSpace's items.

        Returns:
            List of (key, value) pairs.
        """
        return list(self.__dict__.items())

    def keys(self) -> List[str]:
        """Provides the FeatureSpaces's keys.

        Returns:
            List of keys.
        """
        return list(self.__dict__.keys())

    def values(self) -> List[Any]:
        """Provides the FeatureSpace's values.

        Returns:
            List of values.
        """
        return list(self.__dict__.values())

    def as_dict(self) -> Dict[str, Any]:
        """Returns the FeatureSpace converted to a dict."""
        flat_dict = {}
        for key, val in self.__dict__.items():
            try:
                flat_dict[key] = val.as_dict()
            except AttributeError:
                flat_dict[key] = val
        return flat_dict

    def to_csv(self, path: str = None) -> None:
        """Write FeatureSpace to csv file.

        If ``path`` is ``None``, comma separated values are written stdout.

        Args:
            path:  Output file path.

        Returns:
            FeatureSpace as csv-formatted string if ``path`` is ``None``,
            else ``None``.
        """
        features = {}
        for name, space in self.items():
            try:
                features.update({feat: val for feat, val in space.items()})
            except AttributeError:
                features.update({name: space})

        field_names = ['']
        field_names.extend(features.keys())

        if path is None:
            csv_writer = _csv.DictWriter(_sys.stdout, delimiter=',', fieldnames=field_names)
            self._write(csv_writer, features)
        else:
            with open(path, 'w', newline='') as csv_file:
                csv_writer = _csv.DictWriter(csv_file, delimiter=',', fieldnames=field_names)
                self._write(csv_writer, features)

    def __getitem__(self, key):
        return self.__dict__[key]

    @staticmethod
    def _write(csv_writer, features):
        csv_writer.writeheader()

        i = 0
        while True:
            try:
                row = {key: val[i] for key, val in features.items()}
                row[''] = i
                csv_writer.writerow(row)
                i += 1
            except IndexError:
                break

    def to_json(self, path: str = None) -> Optional[str]:
        """Convert FeaturesSpace to JSON.

        If ``path`` is ``None``, this method returns of the data of the
        ``FeatureSpace`` in JSON format. Otherwise, data is written to
        ``path``.

        Args:
            path:  Output file path.

        Returns:
            FeatureSpace as JSON-formatted string if path is not ``None``,
            else ``None``.
        """
        if path is None:
            return _json.dumps(self.as_dict(), cls=ArrayEncoder)

        with open(path, 'w') as json_file:
            _json.dump(self.as_dict(), json_file, cls=ArrayEncoder)

        return None
