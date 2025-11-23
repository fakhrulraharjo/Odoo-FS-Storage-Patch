# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class vrt_fs_storage_async_patch(models.Model):
#     _name = 'vrt_fs_storage_async_patch.vrt_fs_storage_async_patch'
#     _description = 'vrt_fs_storage_async_patch.vrt_fs_storage_async_patch'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

