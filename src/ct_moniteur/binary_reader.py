"""
Binary data reader with automatic offset tracking and type-safe reads.
"""

from enum import Enum
from typing import Literal, Union, overload


class DataType(Enum):
    """Types that can be read from binary data."""

    UINT = "unsigned"
    INT = "signed"
    BOOL = "bool"
    BYTES = "bytes"


class Endianness(Enum):
    """Byte order for multi-byte values."""

    BIG = "big"
    LITTLE = "little"


class BinaryReader:
    """
    Helper class for reading binary data with automatic offset tracking.
    Replaces manual struct.unpack calls with a cleaner API.
    """

    def __init__(self, data: bytes, endianness: Endianness = Endianness.BIG):
        """
        Initialize binary reader.

        Args:
            data: Bytes to read from
            endianness: Byte order (default: BIG)
        """
        self._data = memoryview(data)
        self._offset = 0
        self._endianness = endianness

    @property
    def offset(self) -> int:
        """Current read position."""
        return self._offset

    @property
    def remaining(self) -> int:
        """Number of bytes remaining."""
        return len(self._data) - self._offset

    @property
    def size(self) -> int:
        """Total size of the data."""
        return len(self._data)

    def has_bytes(self, count: int) -> bool:
        """Check if count bytes are available from current position."""
        return self._offset + count <= len(self._data)

    @overload
    def read(self, data_type: Literal[DataType.UINT], size: int) -> int: ...

    @overload
    def read(self, data_type: Literal[DataType.INT], size: int) -> int: ...

    @overload
    def read(self, data_type: Literal[DataType.BOOL], size: Literal[1]) -> bool: ...

    @overload
    def read(self, data_type: Literal[DataType.BYTES], size: int) -> bytes: ...

    def read(self, data_type: DataType, size: int) -> Union[int, bool, bytes]:
        """
        Read data of specified type and size.

        Args:
            data_type: Type of data to read (UINT, INT, BOOL, or BYTES)
            size: Number of bytes to read

        Returns:
            int for UINT/INT, bool for BOOL, bytes for BYTES

        Raises:
            ValueError: If size is invalid or not enough data available
        """
        if size <= 0:
            raise ValueError(f"Size must be positive, got {size}")

        if not self.has_bytes(size):
            raise ValueError(
                f"Cannot read {size} bytes at offset {self._offset} (size: {len(self._data)})"
            )

        data_view = self._data[self._offset : self._offset + size]
        self._offset += size

        if data_type == DataType.BYTES:
            return bytes(data_view)

        if data_type == DataType.BOOL:
            if size != 1:
                raise ValueError(f"Bool must be 1 byte, got {size}")
            return data_view[0] != 0

        # Handle integer types of any size
        if data_type == DataType.UINT:
            # Convert bytes to unsigned integer
            return int.from_bytes(data_view, byteorder=self._endianness.value, signed=False)
        elif data_type == DataType.INT:
            # Convert bytes to signed integer
            return int.from_bytes(data_view, byteorder=self._endianness.value, signed=True)
        else:
            raise ValueError(f"Unknown data type: {data_type}")

    def skip(self, count: int) -> None:
        """Skip count bytes."""
        if not self.has_bytes(count):
            raise ValueError(
                f"Cannot skip {count} bytes at offset {self._offset} (size: {len(self._data)})"
            )
        self._offset += count

    def seek(self, offset: int) -> None:
        """Seek to absolute position."""
        if offset < 0 or offset > len(self._data):
            raise ValueError(f"Invalid seek offset {offset} (size: {len(self._data)})")
        self._offset = offset

    def peek(self, size: int) -> bytes:
        """Peek at bytes without advancing offset."""
        if not self.has_bytes(size):
            raise ValueError(
                f"Cannot peek {size} bytes at offset {self._offset} (size: {len(self._data)})"
            )
        return bytes(self._data[self._offset : self._offset + size])

    def __repr__(self) -> str:
        return f"BinaryReader(offset={self._offset}, size={len(self._data)}, remaining={self.remaining})"
