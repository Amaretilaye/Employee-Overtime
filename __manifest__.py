{
    'name': 'Overtime',
    'version': '1.0',
    'summary': 'employee overtime in odoo based on working hour and over time type it is configerable by any company rule',
    'description': """this module requires odoo mate payroll module """,
    'category': '',
    'aouther':'Amare Tilaye,
    'website': '',
    'depends': [
        'hr',
        'base',
        'base_setup',
        'hr_contract',
        'om_hr_payroll',


    ],

    'license': 'LGPL-3',

    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/data.xml',
        'views/overtime_calculation.xml',
        'views/overtime_rate.xml',
    ],
    'assets': {},
    'installable': True,
    'application': False,
}
