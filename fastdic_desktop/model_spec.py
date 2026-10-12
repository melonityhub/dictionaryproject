# -*- coding: utf-8 -*-
"""Lightweight parser for the public fields used in an ML Kit translation_model.pb.

Kept separate from the inference runtime so model archives can be inspected and
validated without importing NumPy or creating a TFLite interpreter.
"""
import os
from typing import Dict, List


def _varint(data: bytes, offset: int):
    result = shift = 0
    while True:
        if offset >= len(data) or shift > 70:
            raise ValueError('Malformed protobuf varint')
        byte = data[offset]
        offset += 1
        result |= (byte & 0x7f) << shift
        shift += 7
        if not byte & 0x80:
            return result, offset


def parse_pb(data: bytes) -> List[tuple]:
    """Parse protobuf wire data into ``(field_number, wire_type, value)`` tuples."""
    offset = 0
    result = []
    while offset < len(data):
        key, offset = _varint(data, offset)
        field, wire_type = key >> 3, key & 7
        if field == 0:
            raise ValueError('Invalid protobuf field number')
        if wire_type == 0:
            value, offset = _varint(data, offset)
        elif wire_type == 1:
            value = data[offset:offset + 8]
            if len(value) != 8:
                raise ValueError('Truncated protobuf fixed64 field')
            offset += 8
        elif wire_type == 5:
            value = data[offset:offset + 4]
            if len(value) != 4:
                raise ValueError('Truncated protobuf fixed32 field')
            offset += 4
        elif wire_type == 2:
            length, offset = _varint(data, offset)
            end = offset + length
            if end > len(data):
                raise ValueError('Truncated protobuf bytes field')
            value = data[offset:end]
            offset = end
        else:
            raise ValueError('Unsupported protobuf wire type: %d' % wire_type)
        result.append((field, wire_type, value))
    return result


class ModelSpec:
    """Fields needed to identify a translation package and load its resources."""

    def __init__(self, folder: str):
        with open(os.path.join(folder, 'translation_model.pb'), 'rb') as model_file:
            top = parse_pb(model_file.read())

        self.src_lang = next(value for field, _, value in top if field == 1).decode('utf-8')
        self.tgt_lang = next(value for field, _, value in top if field == 2).decode('utf-8')
        self.files: Dict[str, str] = {}
        for field, _, value in top:
            if field == 5:
                mapping = {number: item for number, _, item in parse_pb(value)}
                self.files[mapping[1].decode('utf-8')] = mapping[2].decode('utf-8')

        config = parse_pb(next(value for field, _, value in top if field == 4))
        source = parse_pb(next(value for field, _, value in config if field == 1))
        target = parse_pb(next(value for field, _, value in config if field == 6))
        self.src_model = next(value for field, _, value in source if field == 1).decode('utf-8')
        self.src_vocab = next(value for field, _, value in source if field == 2).decode('utf-8')
        self.tgt_model = next(value for field, _, value in target if field == 1).decode('utf-8')
        self.tgt_vocab = next(value for field, _, value in target if field == 2).decode('utf-8')
