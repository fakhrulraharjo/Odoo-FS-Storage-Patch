# -*- coding: utf-8 -*-
{
    'name': "VRT FS Storage Async Patch",
    'version': '18.0.1.0.0',
    'summary': "Gevent compatibility patch for fs_storage with asyncio",
    'description': """
FS Storage Gevent Compatibility Patch
======================================

This module extends fs_storage to work with Odoo's gevent workers (workers > 0).

Problem:
--------
When Odoo runs with workers > 0, gevent monkey-patches Python's asyncio.
The fs_storage module uses fsspec, which internally uses asyncio.
This creates a nested event loop conflict: "NotImplementedError: Calling sync() from within a running loop"

Solution:
---------
This module inherits fs.storage and overrides _get_filesystem() to apply nest_asyncio
before calling fsspec.filesystem(). This allows nested asyncio event loops to coexist
with gevent's monkey-patched asyncio.

Technical Details:
------------------
- Only applies patch when odoo.evented = True (workers > 0)
- Uses nest_asyncio to allow nested event loops
- Preserves all original fs_storage functionality
- No changes needed to fs_storage configuration

Requirements:
-------------
- nest_asyncio Python package (added to base image requirements.txt)
    """,
    'author': "Fakhrul Raharjo",
    'website': "https://vortex.so",
    'category': 'Technical',
    'depends': ['fs_storage'],
    'data': [],
    'external_dependencies': {
        'python': ['nest_asyncio'],
    },
    'installable': True,
    'application': False,
    'auto_install': True,
    'license': 'LGPL-3',
}
