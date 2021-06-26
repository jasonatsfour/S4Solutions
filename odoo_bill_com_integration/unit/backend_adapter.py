from odoo import models, api, fields, _


class Billcom_ImportExport(object):

    """ Models for Bill.com export import """

    def __init__(self, backend):
        """ Initialized all variables """
        self.name = backend.name
        self.location = backend.location
        self.username = backend.username
        self.password = backend.password
        self.org_key = backend.org_key
        self.dev_key = backend.dev_key

