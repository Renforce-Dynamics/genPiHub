"""Obs-term dispatch and history buffering for HoloMotion.

Direct port of ``HoloMotion/holomotion/src/evaluation/obs/obs_builder.py`` and
the deployment variant at
``HoloMotion/deployment/unitree_g1_ros2_29dof/src/humanoid_policy/obs_builder/obs_builder.py``.

Key properties preserved from the original:
  * Each atomic term is resolved by calling ``evaluator._get_obs_<name>()``.
  * Terms with ``history_length > 0`` are pushed through a per-term circular
    buffer and **always flattened** on output (``[hist, feat] -> [hist*feat]``).
  * Terms without ``history_length`` are appended as-is (their computed vector
    already bakes in whatever temporal dimension the term has, e.g. future
    frames for ``*_fut`` terms).
  * First push warm-starts the buffer by duplicating the frame across all
    history slots — matches training-time IsaacLab behavior.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import numpy as np


class _CircularBuffer:
    """History buffer for a single term. Stores [max_len, 1, feat_dim]."""

    def __init__(self, max_len: int, feat_dim: int) -> None:
        if max_len < 1:
            raise ValueError(f"max_len must be >= 1, got {max_len}")
        self._max_len = int(max_len)
        self._feat_dim = int(feat_dim)
        self._pointer = -1
        self._num_pushes = 0
        self._buffer = np.zeros((self._max_len, 1, self._feat_dim), dtype=np.float32)

    def reset(self) -> None:
        self._pointer = -1
        self._num_pushes = 0
        self._buffer.fill(0.0)

    def append(self, data: np.ndarray) -> None:
        if data.shape != (1, self._feat_dim):
            raise ValueError(
                f"Expected shape (1, {self._feat_dim}), got {tuple(data.shape)}"
            )
        self._pointer = (self._pointer + 1) % self._max_len
        self._buffer[self._pointer] = data
        if self._num_pushes == 0:
            self._buffer[:] = data  # warm start
        self._num_pushes += 1

    @property
    def oldest_first(self) -> np.ndarray:
        """Return buffer rolled to oldest->newest along axis 0. Shape [max_len, feat]."""
        if self._num_pushes == 0:
            raise RuntimeError("Empty history buffer.")
        shift = self._max_len - self._pointer - 1
        rolled = np.roll(self._buffer, shift, axis=0)  # [max_len, 1, feat]
        return rolled[:, 0, :]  # [max_len, feat]


class HoloMotionObsBuilder:
    """Build the flat ONNX actor input from atomic obs terms.

    Parameters
    ----------
    atomic_obs_list
        List of ``{term_name: term_cfg}`` dicts, **already filtered to the
        actor's terms and re-ordered to match the actor obs_schema**.
    evaluator
        Object exposing ``_get_obs_<term_name>()`` methods returning 1-D
        ``np.ndarray`` (already in ONNX joint order when dof-valued).
    """

    def __init__(
        self,
        atomic_obs_list: Sequence[Dict[str, Any]],
        evaluator: Any,
    ) -> None:
        self.term_specs: List[Dict[str, Any]] = []
        for term_dict in atomic_obs_list:
            for name, cfg in term_dict.items():
                spec = {**(cfg or {})}
                spec["name"] = name
                self.term_specs.append(spec)
        self.evaluator = evaluator
        self._buffers: Dict[str, _CircularBuffer] = {}

    def reset(self) -> None:
        for buf in self._buffers.values():
            buf.reset()

    def _compute_term(self, name: str) -> np.ndarray:
        meth = getattr(self.evaluator, f"_get_obs_{name}", None)
        if not callable(meth):
            raise ValueError(
                f"Evaluator missing _get_obs_{name}() for term '{name}'."
            )
        return np.asarray(meth(), dtype=np.float32).reshape(-1)

    def build(self) -> np.ndarray:
        values: Dict[str, np.ndarray] = {}
        for spec in self.term_specs:
            name = spec["name"]
            scale = float(spec.get("scale", 1.0))
            values[name] = self._compute_term(name) * scale

        # Lazy buffer init on first call.
        if not self._buffers:
            for spec in self.term_specs:
                name = spec["name"]
                hist_len = int(spec.get("history_length", 0) or 0)
                if hist_len <= 0:
                    continue
                feat_dim = int(values[name].shape[0])
                self._buffers[name] = _CircularBuffer(hist_len, feat_dim)

        # Push current step to every buffered term.
        for spec in self.term_specs:
            name = spec["name"]
            if name in self._buffers:
                self._buffers[name].append(values[name][None, :])

        # Assemble: buffered terms flatten their full history, unbuffered pass
        # through the current computed value unchanged.
        flat: List[np.ndarray] = []
        for spec in self.term_specs:
            name = spec["name"]
            if name in self._buffers:
                flat.append(
                    self._buffers[name].oldest_first.reshape(-1).astype(np.float32)
                )
            else:
                flat.append(values[name].astype(np.float32))
        if not flat:
            return np.zeros(0, dtype=np.float32)
        return np.concatenate(flat, axis=0).astype(np.float32)


def resolve_actor_atomic_obs_list(
    config: Dict[str, Any],
    group_name: str = "unified",
    actor_prefix: str = "actor_",
) -> List[Dict[str, Any]]:
    """Extract the actor's atomic obs list from the HoloMotion training config.

    Mirrors ``PolicyNode._get_policy_atomic_obs_list`` — pulls entries with the
    configured prefix out of ``obs_groups.<group_name>.atomic_obs_list`` and
    re-orders them to follow ``modules.actor.obs_schema`` leaf keys.
    """
    obs_cfg = config.get("obs") or {}
    obs_groups = obs_cfg.get("obs_groups") or {}

    actor_entries: List[tuple] = []  # (term_name, term_cfg)

    if "policy" in obs_groups and obs_groups["policy"] is not None:
        # Legacy layout: obs_groups.policy.atomic_obs_list (no prefix filter).
        for td in obs_groups["policy"]["atomic_obs_list"]:
            name = next(iter(td.keys()))
            actor_entries.append((name, td[name] or {}))
    elif group_name in obs_groups and obs_groups[group_name] is not None:
        for td in obs_groups[group_name]["atomic_obs_list"]:
            name = next(iter(td.keys()))
            if name.startswith(actor_prefix):
                actor_entries.append((name, td[name] or {}))
        if not actor_entries:
            raise ValueError(
                f"obs_groups.{group_name} has no terms with prefix '{actor_prefix}'."
            )
    else:
        raise ValueError(
            "Unsupported obs config: expected obs_groups.policy or "
            f"obs_groups.{group_name}."
        )

    # Optional re-ordering according to actor obs_schema leaf keys.
    schema_terms: List[str] = []
    modules_cfg = config.get("modules") or {}
    actor_cfg = (modules_cfg.get("actor") or {})
    obs_schema = actor_cfg.get("obs_schema") or {}

    def _collect(node) -> None:
        if isinstance(node, dict):
            if "terms" in node and isinstance(node["terms"], list):
                schema_terms.extend(str(t) for t in node["terms"])
                return
            for v in node.values():
                _collect(v)
        elif isinstance(node, list):
            for v in node:
                _collect(v)

    _collect(obs_schema)

    if not schema_terms:
        return [{name: cfg} for name, cfg in actor_entries]

    by_leaf: Dict[str, tuple] = {}
    ambiguous: set = set()
    for name, cfg in actor_entries:
        if name in by_leaf:
            ambiguous.add(name)
        else:
            by_leaf[name] = (name, cfg)

    ordered: List[Dict[str, Any]] = []
    for term in schema_terms:
        leaf = str(term).split("/")[-1]
        if leaf in ambiguous:
            raise ValueError(
                f"Ambiguous obs_schema term '{term}': leaf '{leaf}' appears twice."
            )
        if leaf not in by_leaf:
            raise ValueError(
                f"obs_schema term '{term}' not found in atomic_obs_list "
                f"(available: {sorted(by_leaf)})."
            )
        name, cfg = by_leaf[leaf]
        ordered.append({name: cfg})
    return ordered
