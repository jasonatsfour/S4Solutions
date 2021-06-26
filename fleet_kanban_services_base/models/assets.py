# -*- coding: utf-8 -*-
# Part of Odoo, S4 Solutions, LLC.
# See LICENSE file for full copyright & licensing details.

def return_action_to_open(self, xml_id, domain=[]):
    """ This opens the xml view specified in
    xml_id for the current vehicle """
    res = self.env['ir.actions.act_window'].for_xml_id(
        'fleet_kanban_services_base', xml_id)
    res.update(
        context=dict(
            self.env.context,
            default_vehicle_id=self.id,
            group_by=False
        ),
        domain=domain
    )
    return res
