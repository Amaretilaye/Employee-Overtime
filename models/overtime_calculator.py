from odoo import models, fields, api


class OvertimeLine(models.Model):
    _name = 'overtime.line'
    _description = 'Overtime Line'

    date = fields.Date(string="Date", required=True)
    overtime_type_id = fields.Many2one('overtime.rate', string="Overtime Type", tracking=True)
    hours = fields.Float(string="Hours", required=True)
    value = fields.Float(string="Value", compute="_compute_value", store=True)
    overtime_calculator_id = fields.Many2one('overtime.calculator', string="Overtime Calculator", ondelete='cascade')

    @api.depends('overtime_calculator_id.employee_id', 'hours', 'overtime_type_id')
    def _compute_value(self):
        for line in self:
            contract = line.overtime_calculator_id.contract_id
            if contract:
                weekly_hours = contract.resource_calendar_id.weekly_working_hour
                total_hours = weekly_hours * 4
                if total_hours > 0:
                    salary_per_hour = contract.wage / total_hours
                    if line.overtime_type_id:
                        overtime_type = line.overtime_type_id

                        if overtime_type.name == "Working Days(10PM-6PM":
                            line.value = salary_per_hour * overtime_type.rate * line.hours
                        elif overtime_type.name == "Working Days(6PM-10PM)":
                            line.value = salary_per_hour * overtime_type.rate * line.hours
                        elif overtime_type.name == "Weekend":
                            line.value = salary_per_hour * overtime_type.rate * line.hours
                        elif overtime_type.name == "Holiday":
                            line.value = salary_per_hour * overtime_type.rate * line.hours
                        else:
                            line.value = 0.0
                    else:
                        line.value = 0.0
                else:
                    line.value = 0.0
            else:
                line.value = 0.0


class OvertimeCalculator(models.Model):
    _name = 'overtime.calculator'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    start_date = fields.Date(string="Start Date", tracking=True)
    end_date = fields.Date(string="End Date", tracking=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", tracking=True, readonly=True)

    department_id = fields.Many2one('hr.department', string="Department", related="employee_id.department_id")
    company_id = fields.Many2one('res.company', string="Company", related="employee_id.company_id")
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    division_id = fields.Many2one('hr.division', string="Division", related="employee_id.division_id")
    requesting_reason = fields.Text(string="Request Reason")
    rejection_reason = fields.Text(string="Rejection Reason")
    contract_id = fields.Many2one('hr.contract', string="Contract", related='employee_id.contract_id')
    currency_id = fields.Many2one('res.currency', related='contract_id.currency_id')
    overtime_line_ids = fields.One2many('overtime.line', 'overtime_calculator_id', string="Overtime Lines")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('department_approve', 'Check'),
        ('reject', 'Rejected'),
        ('hr_approve', 'Approved'),
        ('gm_approve', 'Approved'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid')
    ], string="State", default="draft", tracking=True)
    user = fields.Many2one('res.users', string="User", default=lambda self: self.env.user)

    requested_by = fields.Many2one('hr.employee', string="Prepared By", compute="_compute_requested_by", store=True)
    dep_manager = fields.Many2one('res.users', string="Checked By", compute="_compute_dep_manager", store=True)
    general_manager = fields.Many2one('res.users', string="Approved By", compute="_compute_general_manager", store=True)
    reject_by = fields.Many2one('res.users', string="Rejected By", compute="_compute_reject_by", store=True)
    total_value = fields.Float(string="Total Overtime", compute="_compute_total_value", store=True)
    rejected_date = fields.Date(string="Rejected Date", tracking=True, store=True)
    approved_date = fields.Date(string="Approved Date", tracking=True, store=True)


    @api.depends('overtime_type_id')
    def _compute_overtime_type_display(self):
        for line in self:
            if line.overtime_type_id:
                line.overtime_type_display = dict(line.overtime_type_id._fields['name'].selection).get(line.overtime_type_id.name)
            else:
                line.overtime_type_display = ''
    @api.model
    def default_get(self, fields_list):
        defaults = super(OvertimeCalculator, self).default_get(fields_list)
        defaults['employee_id'] = self.env.user.employee_id.id
        return defaults

    @api.depends('overtime_line_ids.value')
    def _compute_total_value(self):
        for calculator in self:
            calculator.total_value = sum(line.value for line in calculator.overtime_line_ids)

    @api.depends('state')
    def _compute_requested_by(self):
        for calculator in self:
            if calculator.state == 'submit':
                calculator.requested_by = calculator.employee_id

    @api.depends('state')
    def _compute_dep_manager(self):
        for calculator in self:
            if calculator.state == 'department_approve':
                calculator.dep_manager = self.env.user

    @api.depends('state')
    def _compute_general_manager(self):
        for calculator in self:
            if calculator.state == 'hr_approve':
                calculator.general_manager = self.env.user
                calculator.approved_date = fields.Date.today()

    @api.depends('state')
    def _compute_reject_by(self):
        for calculator in self:
            if calculator.state == 'reject':
                calculator.reject_by = self.env.user
                calculator.rejected_date = fields.Date.today()

    def write(self, vals):
        if 'state' in vals:
            if vals['state'] != 'draft':
                vals['requested_by'] = self.employee_id.id
            elif vals['state'] == 'department_approve':
                vals['dep_manager'] = self.env.user.id
            elif vals['state'] == 'hr_approve':
                vals['general_manager'] = self.env.user.id
                vals['approved_date'] = fields.Date.today()
            elif vals['state'] == 'reject':
                vals['reject_by'] = self.env.user.id
                vals['rejected_date'] = fields.Date.today()
        return super(OvertimeCalculator, self).write(vals)
    def action_submit(self):
        self.state = 'submit'

    def action_dept_approve(self):
        self.state = 'department_approve'

    def action_reject(self):
        self.state = 'reject'

    # def action_gm_apprve(self):
    #     self.state = 'gm_approve'

    def action_paid(self):
        self.state = 'paid'

    def action_in_payment(self):
        self.state = 'in_payment'

    def action_hr(self):
        self.state = 'hr_approve'

    def action_paid(self):
        self.state = 'paid'



class OvertimeRate(models.Model):
    _name = 'overtime.rate'

    name = fields.Selection([
                                      ('Working Days(6PM-10PM)', 'Working Days(6PM-10PM'),
                                      ('Working Days(10PM-6PM', 'Working Days(10PM-6PM'),
                                      ('Weekend', 'Weekend'),
                                      ('Holiday', 'Holiday')
                                      ], string="Overtime type")
    rate = fields.Float(string="Rate")


class WorkingWeek(models.Model):
    _inherit = 'resource.calendar'


    weekly_working_hour = fields.Float(string='Weekly Working Hour')

    # total_hour = fields.Float(string='Total Hour', comute="_get_total")



