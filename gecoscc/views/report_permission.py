#
# Copyright 2018, Junta de Andalucia
# http://www.juntadeandalucia.es/
#
# Authors:
#   Abraham Macias <amacias@gruposolutia.com>
#
# All rights reserved - EUPL License V 1.1
# https://joinup.ec.europa.eu/software/page/eupl/licence-eupl
#

import logging

from gecoscc.views.reports import treatment_string_to_csv
from gecoscc.views.reports import treatment_string_to_pdf
from gecoscc.utils import get_filter_nodes_belonging_ou

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPBadRequest

from bson import ObjectId

from gecoscc.i18n import gettext as _

logger = logging.getLogger(__name__)


@view_config(route_name='report_file', renderer='csv',
             permission='is_superuser',
             request_param=("type=permission", "format=csv"))
def report_permission_csv(context, request):
    filename = 'report_permission.csv'
    request.response.content_disposition = 'attachment;filename=' + filename
    return report_permission(context, request, 'csv')

@view_config(route_name='report_file', renderer='pdf',
             permission='is_superuser',
             request_param=("type=permission", "format=pdf"))
def report_permission_pdf(context, request):
    filename = 'report_permission.pdf'
    request.response.content_disposition = 'attachment;filename=' + filename
    return report_permission(context, request, 'pdf')

@view_config(route_name='report_file', renderer='templates/report.jinja2',
             permission='is_superuser',
             request_param=("type=permission", "format=html"))
def report_permission_html(context, request):
    return report_permission(context, request, 'html')


def report_permission(context, request, file_ext):
    '''
    Generate a report with all the admin permissions.
    
    Args:

    Returns:
        headers (list) : The headers of the table to export
        rows (list)    : Rows with the report data
        widths (list)  : The witdhs of the columns of the table to export
        page           : Translation of the word "page" to the current language
        of             : Translation of the word "of" to the current language
        report_type    : Type of report (html, csv or pdf)
    '''    

    items = []
    total_ous = []
    vmark_html = "<div class='centered'><img src='/static/images/checkmark.jpg'/></div>"
    xmark_html = "<div class='centered'><img src='/static/images/xmark.jpg'/></div>"

    # Get all admins
    admins = request.db.adminusers.find()

    for admin in admins:
        ou_readonly = admin.get('ou_readonly', [])
        ou_availables = admin.get('ou_availables', [])
        ou_remote = admin.get('ou_remote', [])
        ou_managed = admin.get('ou_managed', [])
        admin_ous = set(ou_readonly + ou_availables + ou_remote + ou_managed)
        total_ous += admin_ous

        for ou in admin_ous:
            item = {}
            item['_id'] = str(admin['_id'])
            item['username'] = admin['username']
            item['OU'] = ou
            if file_ext == 'csv':
                item['readonly'] = _('Yes') if ou in ou_readonly else _('No')
                item['link'] = _('Yes') if ou in ou_availables else _('No')
                item['remote'] = _('Yes') if ou in ou_remote else _('No')
                item['managed'] = _('Yes') if ou in ou_managed else _('No')
            else:
                item['readonly'] = vmark_html if ou in ou_readonly else xmark_html
                item['link'] = vmark_html if ou in ou_availables else xmark_html
                item['remote'] =  vmark_html if ou in ou_remote else xmark_html
                item['managed'] = vmark_html if ou in ou_managed else xmark_html
            items.append(item)

    logger.debug("report_permission: items = {}".format(items))
            
    # Get all OU names
    ids = map(lambda x: ObjectId(x), total_ous)
    result = request.db.nodes.find({'_id': {'$in': ids}},{'_id':1, 'name':1})
    ou_names = {}
    for r in result:
        ou_names.update({str(r['_id']):r['name']})

    logger.debug("report_permission: ou_names = {}".format(ou_names))

    rows = []

    for item in items:    
        row = []
        item['OU'] = ou_names.get(item['OU'], item['OU'])
        if file_ext == 'pdf':
            row.append(treatment_string_to_pdf(item, 'username', 15))
            row.append(treatment_string_to_pdf(item, 'OU', 15))
            row.append(item['_id'])
            row.append(treatment_string_to_pdf(item, 'readonly', 80))
            row.append(treatment_string_to_pdf(item, 'link', 80))
            row.append(treatment_string_to_pdf(item, 'remote', 80))
            row.append(treatment_string_to_pdf(item, 'managed', 80))
        else:
            row.append(treatment_string_to_csv(item, 'username'))
            row.append(treatment_string_to_csv(item, 'OU'))
            row.append(item['_id'])
            row.append(treatment_string_to_csv(item, 'readonly'))
            row.append(treatment_string_to_csv(item, 'link'))
            row.append(treatment_string_to_csv(item, 'remote'))
            row.append(treatment_string_to_csv(item, 'managed'))

        rows.append(row)
                
    
    header = (_(u'Username').encode('utf-8'),
              _(u'Organizational Unit').encode('utf-8'),
              _(u'Id').encode('utf-8'),
              _(u'Read Only').encode('utf-8'),
              _(u'Link').encode('utf-8'),
              _(u'Remote').encode('utf-8'),
              _(u'Manage').encode('utf-8'))
    
    # Column widths in percentage
    widths = (20, 20, 20, 10, 10, 10, 10)
    title =  _(u'Permissions report')
        
        
    return {'headers': header,
            'rows': rows,
            'widths': widths,
            'report_title': title,
            'page': _(u'Page').encode('utf-8'),
            'of': _(u'of').encode('utf-8'),
            'report_type': file_ext}