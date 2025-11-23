# -*- coding: utf-8 -*-
# from odoo import http


# class VrtFsStorageAsyncPatch(http.Controller):
#     @http.route('/vrt_fs_storage_async_patch/vrt_fs_storage_async_patch', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/vrt_fs_storage_async_patch/vrt_fs_storage_async_patch/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('vrt_fs_storage_async_patch.listing', {
#             'root': '/vrt_fs_storage_async_patch/vrt_fs_storage_async_patch',
#             'objects': http.request.env['vrt_fs_storage_async_patch.vrt_fs_storage_async_patch'].search([]),
#         })

#     @http.route('/vrt_fs_storage_async_patch/vrt_fs_storage_async_patch/objects/<model("vrt_fs_storage_async_patch.vrt_fs_storage_async_patch"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('vrt_fs_storage_async_patch.object', {
#             'object': obj
#         })

