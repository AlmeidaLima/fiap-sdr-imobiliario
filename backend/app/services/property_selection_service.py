from app.core.exceptions import ApplicationException
from app.schemas.conversation import ConversationState


class PropertySelectionService:
    def select_property(
            self,
            state: ConversationState,
            property_id: int,
    ) -> ConversationState:
        if property_id not in state.presented_property_ids:
            raise ApplicationException(
                detail="O imóvel selecionado não foi apresentado nesta conversa.",
                status_code=400,
                error="invalid_property_selection",
            )

        update = {"selected_property_id": property_id}

        if (
                state.selected_property_id != property_id
                or state.appointment_stage == "NONE"
        ):
            update.update(
                {
                    "appointment_stage": "SELECTED",
                    "appointment_type": None,
                    "appointment_date": None,
                    "appointment_time": None,
                    "appointment_id": None,
                }
            )

        return state.model_copy(update=update)

    def register_presented_properties(
            self,
            state: ConversationState,
            property_ids: list[int],
    ) -> ConversationState:
        unique_property_ids = list(dict.fromkeys(property_ids))
        selected_property_id = state.selected_property_id

        if selected_property_id not in unique_property_ids:
            selected_property_id = None

        update = {
            "presented_property_ids": unique_property_ids,
            "selected_property_id": selected_property_id,
        }

        if selected_property_id is None:
            update.update(
                {
                    "appointment_stage": "NONE",
                    "appointment_type": None,
                    "appointment_date": None,
                    "appointment_time": None,
                    "appointment_id": None,
                }
            )

        return state.model_copy(update=update)
