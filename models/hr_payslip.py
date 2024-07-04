from odoo import models, api, fields

class PayslipOverTime(models.Model):
    _inherit = 'hr.payslip'
    overtime_ids = fields.Many2many('overtime.calculator')

    def get_inputs(self, contract_ids, date_from, date_to):
        res = super(PayslipOverTime, self).get_inputs(contract_ids, date_from, date_to)
        total_overtime_value = 0.0
        for payslip in self:
            emp_id = payslip.employee_id
            if emp_id:
                overtime_calculators = self.env['overtime.calculator'].search([
                    ('start_date', '>=', date_from),
                    ('end_date', '<=', date_to),
                    ('employee_id', '=', emp_id.id),
                    ('state', '=', 'in_payment')
                ])
                for calculator in overtime_calculators:
                    for line in calculator.overtime_line_ids.filtered(lambda x: date_from <= x.date <= date_to):
                        total_overtime_value += line.value

        for result in res:
            if result.get('code') == 'OT100':
                result['amount'] = total_overtime_value

        return res

    def action_payslip_done(self):
        for payslip in self:
            emp_id = payslip.employee_id
            if emp_id:
                overtime_calculators = self.env['overtime.calculator'].search([
                    ('start_date', '>=', payslip.date_from),
                    ('end_date', '<=', payslip.date_to),
                    ('employee_id', '=', emp_id.id),
                    ('state', '=', 'in_payment')
                ])
                for calculator in overtime_calculators:
                    calculator.action_paid()
        return super(PayslipOverTime, self).action_payslip_done()
