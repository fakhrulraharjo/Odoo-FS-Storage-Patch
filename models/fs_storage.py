# -*- coding: utf-8 -*-
"""
FSStorage Gevent Async Patch - Defense-in-depth layer.

This module provides a supplementary fsspec real-thread patch at Odoo module
load time, for cases where sitecustomize.py didn't fire (e.g., non-Docker
environments or when PYTHONPATH wasn't set correctly).

Primary fix: sitecustomize.py in the HA base image
This layer: Safety net at Odoo module load time
"""
import logging
import sys

_logger = logging.getLogger(__name__)


def _apply_fsspec_gevent_patch():
    """Apply fsspec real-thread patch if running under gevent.

    Check odoo.evented flag (set True when Odoo runs with workers>0 and gevent).
    If True, verify fsspec.asyn.get_loop hasn't already been patched by
    sitecustomize.py, and if not, apply the same real-thread patch.
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
                        import asyncio
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
