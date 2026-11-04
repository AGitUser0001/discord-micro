"""Durable typed work queues: each job is processed by exactly one worker."""

from ._work import WorkQueue

__all__ = ("WorkQueue",)
