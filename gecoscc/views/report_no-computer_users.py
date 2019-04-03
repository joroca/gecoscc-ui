#
# Copyright 2018, Junta de Andalucia
# http://www.juntadeandalucia.es/
#
# Authors:
#   Jose M. Rodriguez <jmrodriguez@gruposolutia.com>
#
# All rights reserved - EUPL License V 1.1
# https://joinup.ec.europa.eu/software/page/eupl/licence-eupl
#

import logging
from bson import ObjectId

from gecoscc.views.reports import treatment_string_to_csv
from gecoscc.views.reports import treatment_string_to_pdf, get_html_node_link
from gecoscc.utils import get_filter_nodes_belonging_ou

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPBadRequest

from gecoscc.i18n import gettext as _

logger = logging.getLogger(__name__)


@view_config(route_name='report_file', renderer='csv',
             permission='edit',
             request_param=("type=no-computer_users", "format=csv"))
def report_no_computer_users_csv(context, request):
    filename = 'report_no-computer_users.csv'
    request.response.content_disposition = 'attachment;filename=' + filename
    return report_no_computer_users(context, request, 'csv')

@view_config(route_name='report_file', renderer='pdf',
             permission='edit',
             request_param=("type=no-computer_users", "format=pdf"))
def report_no_computer_users_pdf(context, request):
    filename = 'report_no-computer_users.pdf'
    request.response.content_disposition = 'attachment;filename=' + filename
    return report_no_computer_users(context, request, 'pdf')

@view_config(route_name='report_file', renderer='templates/report.jinja2',
             permission='edit',
             request_param=("type=no-computer_users", "format=html"))
def report_no_computer_users_html(context, request):
    return report_no_computer_users(context, request, 'html')


def report_no_computer_users(context, request, file_ext):
    '''
    Generate a report with all the no-computer users that belongs to a OU
    If the administrator is a superadmin the generated report will contain 
    all the users in the database. 
    
    Args:
        ou_id (string) : ID of the OU.

    Returns:
        headers (list) : The headers of the table to export
        rows (list)    : Rows with the report data
        widths (list)  : The witdhs of the columns of the table to export
        page           : Translation of the word "page" to the current language
        of             : Translation of the word "of" to the current language
        report_type    : Type of report (html, csv or pdf)
    '''    

    # Check current user permissions
    is_superuser = request.user.get('is_superuser', False)

    # Get managed ous
    ou_id = request.GET.get('ou_id', None)
    logger.debug("report_no_computer ::: ou_id = {}".format(ou_id))
    if ou_id is None:
        raise HTTPBadRequest()

    if not is_superuser: # Administrator: checks if ou is visible
        is_visible = ou_id in request.user.get('ou_managed', []) or \
                     ou_id in request.user.get('ou_readonly', [])
    else: # Superuser: only checks if exists
        is_visible = request.db.nodes.find_one({'_id': ObjectId(ou_id)})

    logger.debug("report_no_computer ::: is_visible = {}".format(is_visible))
    if not is_visible:
        raise HTTPBadRequest()

    # Get user data
    query = request.db.nodes.find(
        {'type': 'user', 'path': get_filter_nodes_belonging_ou(ou_id), 'computers': []})

    rows = []
    
    if file_ext == 'pdf':
        rows = [(treatment_string_to_pdf(item, 'name', 15),
                treatment_string_to_pdf(item, 'first_name', 15),
                treatment_string_to_pdf(item, 'last_name', 15),
                treatment_string_to_pdf(item, 'email', 35),
                treatment_string_to_pdf(item, 'phone', 15),
                treatment_string_to_pdf(item, 'address', 35),
                item['_id']) for item in query]
    else:
        rows = [(treatment_string_to_csv(item, 'name') if file_ext == 'csv' else get_html_node_link(item),
                treatment_string_to_csv(item, 'first_name'),
                treatment_string_to_csv(item, 'last_name'),
                treatment_string_to_csv(item, 'email'),
                treatment_string_to_csv(item, 'phone'),
                treatment_string_to_csv(item, 'address'),
                item['_id']) for item in query]
                      
                
    
    header = (_(u'Username').encode('utf-8'),
              _(u'First name').encode('utf-8'),
              _(u'Last name').encode('utf-8'),
              _(u'Email').encode('utf-8'),
              _(u'Phone').encode('utf-8'),
              _(u'Address').encode('utf-8'),
              _(u'Id').encode('utf-8'))
    
    # Column widths in percentage
    widths = (15, 15, 10, 15, 10, 20, 15)
    title =  _(u'No-computer users report')
        
        
    return {'headers': header,
            'rows': rows,
            'widths': widths,
            'report_title': title,
            'page': _(u'Page').encode('utf-8'),
            'of': _(u'of').encode('utf-8'),
            'report_type': file_ext}
