# -*- coding: utf-8 -*-
{
    'name': "VRT FS Storage Async Patch",
    'version': '18.0.2.0.0',
    'summary': "Real-thread fsspec patch for gevent workers (defense-in-depth)",
    'description': """
FS Storage Gevent Async Patch (v2 - Real Thread)
=================================================

Defense-in-depth layer that patches fsspec to use real OS threads under gevent.

Problem:
--------
When Odoo runs with workers > 0, gevent monkey-patches threading/asyncio.
fsspec's internal IO loop runs on a greenlet instead of a real OS thread,
causing "NotImplementedError: Calling sync() from within a running loop".

Solution (dual-layer):
----------------------
1. PRIMARY: sitecustomize.py in the HA base Docker image patches fsspec at
   Python startup, before any imports.
2. SECONDARY (this module): At Odoo module load time, checks if the patch
   was already applied. If not, applies the same real-thread patch as a
   safety net for non-Docker environments.

Technical Details:
------------------
- Replaces fsspec.asyn.get_loop with a version that spawns a real OS thread
- Uses gevent.monkey.get_original() to obtain unpatched Thread/Event classes
- Marks patched function with _gevent_patched attribute to prevent double-patching
- Falls back to nest_asyncio.apply() as additional safety net
- Only activates when odoo.evented = True (gevent workers mode)
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
