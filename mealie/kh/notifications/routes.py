"""KH: /api/kh/notifications (D75): the server's public key, this person's devices and choices, and a test message."""

from fastapi import Header, Request, status

from mealie.kh.i18n.messages import request_locale, say
from mealie.kh.notifications import keys, sender, service
from mealie.kh.notifications.schemas import NotificationSettings, SubscriptionIn, SubscriptionOut
from mealie.routes._base import BaseUserController, controller
from mealie.routes._base.routers import UserAPIRouter

router = UserAPIRouter(prefix="/notifications")


@controller(router)
class KhNotificationsController(BaseUserController):
    """A person's push notifications."""

    @router.get("/key")
    def get_key(self) -> dict[str, str]:
        """The public VAPID key the browser needs to subscribe."""
        return {"key": keys.public_key()}

    @router.get("/settings", response_model=NotificationSettings)
    def get_settings(self) -> NotificationSettings:
        """The person's switches; all off until they turn notifications on."""
        return service.get_settings(self.session, self.user.id)

    @router.put("/settings", response_model=NotificationSettings)
    def put_settings(self, data: NotificationSettings) -> NotificationSettings:
        """Saves the switches and the evening time."""
        service.put_settings(self.session, self.user.id, data)
        return data

    @router.get("/subscriptions", response_model=list[SubscriptionOut])
    def get_devices(self) -> list[SubscriptionOut]:
        """The person's devices."""
        return [SubscriptionOut.model_validate(row) for row in service.devices(self.session, self.user.id)]

    @router.post("/subscriptions", status_code=status.HTTP_204_NO_CONTENT)
    def subscribe(self, data: SubscriptionIn, request: Request, user_agent: str = Header("")) -> None:
        """Adds this device. The first device switches on plan, evening and wishes."""
        service.subscribe(
            self.session,
            self.user.id,
            data.endpoint,
            data.keys.p256dh,
            data.keys.auth,
            user_agent,
            request_locale(self.session, self.user.id, request),
        )

    @router.delete("/subscriptions", status_code=status.HTTP_204_NO_CONTENT)
    def unsubscribe(self, endpoint: str) -> None:
        """Removes one of the person's own devices, named by its endpoint (a query parameter: DELETE has no body)."""
        service.unsubscribe(self.session, self.user.id, endpoint)

    @router.post("/test")
    def test(self, request: Request) -> dict[str, int]:
        """Sends "Test von Kochheft" to the person's devices; says how many accepted it. Waits for the push service,
        because the person is watching for the answer."""
        locale = request_locale(self.session, self.user.id, request)
        sent = sender.send_to_users(
            self.session, [self.user.id], say("push_test_title", locale), say("push_test", locale), "/"
        )
        return {"sent": sent}
