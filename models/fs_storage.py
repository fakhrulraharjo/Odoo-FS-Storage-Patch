# -*- coding: utf-8 -*-

import logging
import fsspec
from odoo import models

_logger = logging.getLogger(__name__)

# Apply nest_asyncio globally when module loads (if gevent is active)
try:
    import odoo
    if hasattr(odoo, 'evented') and odoo.evented:
        try:
            import nest_asyncio
            nest_asyncio.apply()
            _logger.info(
                "vrt_fs_storage_async_patch: Successfully applied nest_asyncio "
                "for fsspec compatibility with gevent workers"
            )
        except ImportError:
            _logger.warning(
                "vrt_fs_storage_async_patch: nest_asyncio not available but gevent workers "
                "are enabled. fsspec operations may fail. Please install: pip install nest-asyncio"
            )
except Exception as e:
    _logger.error("vrt_fs_storage_async_patch: Failed to apply nest_asyncio: %s", e)


class FSStorageGeventPatch(models.Model):
    """Extends fs.storage to be compatible with gevent workers.

    This patch solves the "NotImplementedError: Calling sync() from within a running loop"
    error that occurs when using fs_storage with Odoo workers > 0 (gevent mode).

    The patch applies nest_asyncio globally when the module loads (see module-level code above).
    This allows fsspec's asyncio operations to work within gevent's monkey-patched event loop.
    """
    _inherit = "fs.storage"

    # No need to override methods - nest_asyncio is applied globally at module load
