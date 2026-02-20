# -*- coding: utf-8 -*-
"""
FSStorage Gevent Async Patch - Defense-in-depth layer (v2.1 - Three-layer fix).

This module provides three layers of fsspec patching at Odoo module load time
to fix the "NotImplementedError: Calling sync() from within a running loop"
crash that occurs under gevent workers.

ROOT CAUSE:
After gevent.monkey.patch_all(), threading.Thread becomes a greenlet. fsspec's
get_loop() creates its IO event loop on a threading.Thread (now a greenlet),
which runs on the SAME OS thread. CPython's asyncio._running_loop is tracked
at the C level per-OS-thread (NOT per-greenlet). So ALL greenlets on that
thread see the loop as "running". When fsspec.asyn.sync() calls
asyncio.events.get_running_loop(), it gets the IO loop back. Since
loop0 is loop → True → NotImplementedError.

Layer 1 (CRITICAL): Patch fsspec.asyn.sync directly (fixes the crash site)
Layer 2: Force-reset existing loop + patch get_loop() (prevents the condition)
Layer 3: nest_asyncio.apply() (fallback safety net)
"""
import asyncio
import logging
import sys

_logger = logging.getLogger(__name__)


def _patch_fsspec_sync_for_gevent():
    """Patch fsspec.asyn.sync to handle gevent's false-positive running loop detection."""
    try:
        import odoo
        if not getattr(odoo, 'evented', False):
            return
    except ImportError:
        return

    try:
        import fsspec.asyn
        from fsspec.exceptions import FSTimeoutError

        if hasattr(fsspec.asyn.sync, '_gevent_patched'):
            _logger.info("fsspec sync already patched for gevent")
            return

        _original_sync = fsspec.asyn.sync

        def _gevent_safe_sync(loop, func, *args, timeout=None, **kwargs):
            """Gevent-aware sync that handles false-positive running loop detection.

            After gevent.monkey.patch_all(), asyncio's C-level _running_loop is
            per-OS-thread, not per-greenlet. fsspec's IO loop runs in a greenlet
            on the same OS thread, so get_running_loop() falsely reports a conflict.

            Fix: submit coroutine via run_coroutine_threadsafe and wait cooperatively.
            concurrent.futures.Future.result() uses gevent-patched Condition.wait()
            which yields to the hub, letting the IO greenlet process the coro.
            """
            timeout = timeout if timeout else None
            if loop is None or loop.is_closed():
                raise RuntimeError("Loop is not running")

            # Check for running loop conflict (gevent false positive)
            in_running_loop = False
            try:
                loop0 = asyncio.events.get_running_loop()
                in_running_loop = (loop0 is loop)
            except RuntimeError:
                pass

            if in_running_loop:
                # Gevent: submit coro and wait cooperatively
                coro = func(*args, **kwargs)
                future = asyncio.run_coroutine_threadsafe(coro, loop)
                try:
                    return future.result(timeout=timeout)
                except asyncio.TimeoutError:
                    raise FSTimeoutError from None
            else:
                # Normal path: no conflict, delegate to original
                return _original_sync(loop, func, *args, timeout=timeout, **kwargs)

        _gevent_safe_sync._gevent_patched = True
        fsspec.asyn.sync = _gevent_safe_sync
        _logger.info("fsspec sync patched for gevent (running-loop bypass)")

    except ImportError as e:
        _logger.debug("fsspec sync patch skipped: %s", e)
    except Exception as e:
        _logger.warning("fsspec sync patch failed: %s", e)


def _apply_fsspec_gevent_patch():
    """Apply fsspec real-thread patch if running under gevent.

    Check odoo.evented flag (set True when Odoo runs with workers>0 and gevent).
    If True, verify fsspec.asyn.get_loop hasn't already been patched by
    sitecustomize.py, and if not, apply the same real-thread patch.

    Enhanced: Force-resets any existing loop[0] that was created in a greenlet
    before applying the get_loop patch.
    """
    try:
        import odoo
        if not getattr(odoo, 'evented', False):
            return  # Not using gevent workers, no patch needed
    except ImportError:
        return

    try:
        import fsspec.asyn
        import gevent.monkey

        # Check if already patched by sitecustomize.py
        current_get_loop = fsspec.asyn.get_loop
        if hasattr(current_get_loop, '_gevent_patched'):
            _logger.info("fsspec get_loop already patched by sitecustomize.py")
            return

        # Force-reset any existing loop that was created in a greenlet
        existing_loop = fsspec.asyn.loop[0]
        if existing_loop is not None:
            _logger.info("Force-resetting existing fsspec loop (was greenlet-based)")
            try:
                existing_loop.call_soon_threadsafe(existing_loop.stop)
            except Exception:
                pass
            fsspec.asyn.loop[0] = None
            fsspec.asyn.iothread[0] = None

        # Get the real unpatched Thread class
        _RealThread = gevent.monkey.get_original('threading', 'Thread')
        _RealEvent = gevent.monkey.get_original('threading', 'Event')

        # Verify gevent actually patched threading
        import threading
        if _RealThread is threading.Thread:
            _logger.warning("gevent hasn't patched threading - skipping fsspec patch")
            return

        def _gevent_aware_get_loop():
            """Get or create fsspec's IO loop on a REAL OS thread (not greenlet)."""
            if fsspec.asyn.loop[0] is None:
                loop_lock = fsspec.asyn.get_lock()
                with loop_lock:
                    if fsspec.asyn.loop[0] is None:
                        new_loop = asyncio.new_event_loop()
                        done = _RealEvent()

                        def _run_loop():
                            asyncio.set_event_loop(new_loop)
                            done.set()
                            new_loop.run_forever()

                        th = _RealThread(target=_run_loop, name="fsspecIO", daemon=True)
                        th.start()
                        done.wait()
                        fsspec.asyn.loop[0] = new_loop
                        fsspec.asyn.iothread[0] = th
            return fsspec.asyn.loop[0]

        _gevent_aware_get_loop._gevent_patched = True
        fsspec.asyn.get_loop = _gevent_aware_get_loop
        _logger.info("fsspec get_loop patched with real OS thread (module-level)")

    except ImportError as e:
        _logger.debug("fsspec gevent patch skipped: %s", e)
    except Exception as e:
        _logger.warning("fsspec gevent patch failed: %s", e)


def _apply_nest_asyncio():
    """Apply nest_asyncio as fallback safety net."""
    try:
        import nest_asyncio
        nest_asyncio.apply()
    except ImportError:
        pass


# Apply patches at module load time
# ORDER MATTERS: sync patch first (fixes the crash), then get_loop (prevents the condition)
_patch_fsspec_sync_for_gevent()
_apply_fsspec_gevent_patch()
_apply_nest_asyncio()


from odoo import models


class FSStorageGeventPatch(models.Model):
    """Marker model for vrt_fs_storage_async_patch module.

    The actual patching happens at module import time (above).
    This empty model exists only so Odoo recognizes this as a valid module.
    """
    _inherit = 'fs.storage'
    _name = 'fs.storage'
