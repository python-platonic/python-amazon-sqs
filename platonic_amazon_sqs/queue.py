import dataclasses
from abc import ABC
from typing import Generic, TypeVar, Optional, Type

import typing
from boto3_type_annotations import sqs

import boto3

from platonic_amazon_sqs.conversions import to_string, from_string

T = TypeVar('T')


@dataclasses.dataclass(frozen=True)
class Message(Generic[T]):
    """Container of a value pulled from queue."""

    value: T


def get_type_args(obj: T) -> tuple:
    for cls in obj.__orig_bases__:
        type_args = typing.get_args(cls)
        if type_args:
            return type_args

    return ()


class AcknowledgementQueue(Generic[T], ABC):
    """This will go to `platonic`."""
    _value_type: Type[T] = None

    @property
    def value_type(self) -> Type[T]:
        if self._value_type is None:
            args = get_type_args(self)
            (self._value_type, ) = args

        return self._value_type

    def put(self, value: T):
        """Add an item to the queue."""

    def get(self) -> Message[T]:
        """Get item from queue."""

    def acknowledge(self, message: Message[T]):
        """Acknowledge that the message was processed."""


@dataclasses.dataclass(frozen=True)
class SQSMessage(Message):
    id: str


class SQSQueue(AcknowledgementQueue[T]):
    """SQS backend for a queue."""

    url: str
    max_number_of_messages: int = 10

    def __init__(
        self,
        url: Optional[str] = None,
        max_number_of_messages: Optional[int] = None,
    ):
        if url is not None:
            self.url = url

        if max_number_of_messages is not None:
            self.max_number_of_messages = max_number_of_messages

    @property
    def client(self) -> sqs.Client:
        return boto3.client('sqs')

    def serialize(self, value: T) -> str:
        return to_string(value)

    def deserialize(self, raw_value: str) -> T:
        return from_string(
            destination_type=self.value_type,
            raw_value=raw_value
        )

    def put(self, value: T):
        self.client.send_message(
            QueueUrl=self.url,
            MessageBody=self.serialize(value)
        )
