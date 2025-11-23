# -*- coding: utf-8 -*-

import logging
import fsspec
from odoo import models

_logger = logging.getLogger(__name__)


class FSStorageGeventPatch(models.Model):
    """Extends fs.storage to be compatible with gevent workers.

    This patch solves the "NotImplementedError: Calling sync() from within a running loop"
    error that occurs when using fs_storage with Odoo workers > 0 (gevent mode).
    """
    _inherit = "fs.storage"

    def _get_filesystem(self) -> fsspec.AbstractFileSystem:
        """Override to apply nest_asyncio for gevent compatibility.

        When Odoo runs with workers > 0, gevent monkey-patches asyncio.
        fsspec uses asyncio internally, which creates a nested event loop conflict.
        nest_asyncio allows nested event loops to coexist.

        This method:
        1. Checks if gevent is active (odoo.evented = True)
        2. Applies nest_asyncio if available
        3. Calls the parent _get_filesystem() method normally

        Returns:
            fsspec.AbstractFileSystem: The filesystem instance
        """
        # Check if gevent is active (workers > 0)
        try:
            import odoo
            if hasattr(odoo, 'evented') and odoo.evented:
                try:
                    import nest_asyncio
                    nest_asyncio.apply()
                    _logger.debug(
                        "Applied nest_asyncio for gevent compatibility with fsspec "
                        "(storage: %s, protocol: %s)",
                        self.name if self else "unknown",
                        self.protocol if self else "unknown"
                    )
                except ImportError:
                    _logger.warning(
                        "nest_asyncio not available but gevent workers are enabled. "
                        "fsspec operations may fail with 'NotImplementedError: Calling sync() "
                        "from within a running loop'. Please install nest_asyncio: "
                        "pip install nest-asyncio"
                    )
        except Exception as e:
            _logger.error("Failed to check/apply nest_asyncio: %s", e)

        # Call the original method
        return super()._get_filesystem()
