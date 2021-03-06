#
# Copyright 2013, Junta de Andalucia
# http://www.juntadeandalucia.es/
#
# Authors:
#   Pablo Martin <goinnn@gmail.com>
#
# All rights reserved - EUPL License V 1.1
# https://joinup.ec.europa.eu/software/page/eupl/licence-eupl
#

from cornice.resource import resource

from gecoscc.api import PassiveResourcePaginated
from gecoscc.models import Printer, Printers
from gecoscc.permissions import api_login_required


@resource(collection_path='/api/printers/',
          path='/api/printers/{oid}/',
          description='Printers resource',
          validators=(api_login_required,))
class PrinterResource(PassiveResourcePaginated):

    schema_collection = Printers
    schema_detail = Printer
    objtype = 'printer'

    mongo_filter = {
        'type': objtype,
    }
    collection_name = 'nodes'
