from app.models.lead_follow_up import LeadFollowUp


class LeadFollowUpMessageService:

    def generate(self, follow_up: LeadFollowUp) -> str:
        lead_name = (
            follow_up.lead.name.strip()
            if follow_up.lead and follow_up.lead.name
            else None
        )

        greeting = (
            f"Olá, {lead_name}!"
            if lead_name
            else "Olá!"
        )

        appointment = follow_up.appointment

        if appointment is None:
            context = (
                "Estou entrando em contato para dar continuidade "
                "ao seu atendimento."
            )
        elif appointment.appointment_type == "VISITA":
            context = (
                "Estou entrando em contato para dar continuidade "
                "ao atendimento sobre sua visita."
            )
        elif appointment.appointment_type == "REUNIAO":
            context = (
                "Estou entrando em contato para dar continuidade "
                "ao atendimento sobre nossa reunião."
            )
        else:
            context = (
                "Estou entrando em contato para dar continuidade "
                "ao seu atendimento."
            )

        return f"{greeting} {context} Podemos conversar?"