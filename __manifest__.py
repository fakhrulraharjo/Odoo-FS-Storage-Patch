# -*- coding: utf-8 -*-
{
    'name': "VRT FS Storage Async Patch",
    'version': '18.0.1.0.0',
    'summary': "",
    'description': """

    """,
    'author': "Fakhrul Raharjo",
    'website': "https://vortex.so",
    'category': 'Customizations',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
