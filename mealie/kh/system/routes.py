"""KH: /api/kh/about for every member and /api/kh/admin/auto-update and /api/kh/admin/system for admins (P8). The
admin routes only read, except the checkbox, which writes one small file the host's auto_update.sh picks up."""

import shutil
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter

from mealie.core.config import get_app_dirs, get_app_settings
from mealie.kh.features.settings import get_kh_settings
from mealie.kh.nutrition.bls import load_bls
from mealie.kh.system import auto_update, checks
from mealie.kh.system.schemas import AboutOut, AutoUpdateIn, AutoUpdateOut, CheckOut
from mealie.routes._base import BaseAdminController, BaseUserController, controller
from mealie.routes._base.routers import AdminAPIRouter, UserAPIRouter

router = APIRouter()
user_router = UserAPIRouter()
admin_router = AdminAPIRouter(prefix="/admin")


def data_dir() -> Path:
    """Mealie's data folder, the one the host's scripts share with the container."""
    return get_app_dirs().DATA_DIR


def newest_backup(backups: Path) -> datetime | None:
    """When the newest Mealie backup in the folder was written, None if there is none."""
    times = [file.stat().st_mtime for file in backups.glob("*.zip")]
    return datetime.fromtimestamp(max(times), UTC) if times else None


@controller(user_router)
class KhAboutController(BaseUserController):
    @user_router.get("/about", response_model=AboutOut)
    def about(self) -> AboutOut:
        """The running release and the third-party notices, for the About page."""
        settings = get_kh_settings()
        try:
            notices = settings.notices_file.read_text(encoding="utf-8")
        except OSError:
            notices = ""  # running from source: the file is only copied into the image
        return AboutOut(version=checks.kh_version(settings.image), notices=notices)


@controller(admin_router)
class KhSystemController(BaseAdminController):
    @admin_router.get("/auto-update", response_model=AutoUpdateOut)
    def get_auto_update(self) -> AutoUpdateOut:
        """The checkbox and the last run's line, for the admin settings."""
        line = auto_update.read_status(data_dir())
        return AutoUpdateOut(
            enabled=auto_update.read_enabled(data_dir()), status=auto_update.parse_status(line)[0] if line else None
        )

    @admin_router.put("/auto-update", response_model=AutoUpdateOut)
    def put_auto_update(self, data: AutoUpdateIn) -> AutoUpdateOut:
        """Stores the checkbox for auto_update.sh (takes effect at the next run)."""
        auto_update.write_enabled(data_dir(), data.enabled)
        return self.get_auto_update()

    @admin_router.get("/system", response_model=list[CheckOut])
    def system(self) -> list[CheckOut]:
        """One traffic light per row of the system check; changes nothing."""
        settings, app_settings, folder = get_kh_settings(), get_app_settings(), data_dir()
        now = datetime.now(UTC)
        providers = len(self.repos.group_ai_providers.get_all())
        rows = [
            checks.version_check(settings.image),
            checks.database_check(app_settings.DB_ENGINE),
            checks.disk_check(shutil.disk_usage(folder).free),
            checks.backup_check(newest_backup(folder / "backups"), now),
            checks.ai_check(providers),
            checks.profile_check(settings.profile, providers),
            checks.signup_check(app_settings.ALLOW_SIGNUP),
            checks.default_account_check(self.repos.users.get_one(app_settings._DEFAULT_EMAIL, "email") is not None),
            checks.auto_update_check(auto_update.read_enabled(folder), auto_update.read_status(folder), now),
            checks.nutrition_check(len(load_bls())),
            *checks.module_checks(settings),
        ]
        return [CheckOut(key=row.key, state=row.state, value=row.value) for row in rows]


router.include_router(user_router)
router.include_router(admin_router)
