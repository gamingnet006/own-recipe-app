import { fieldTypes } from "../forms";
import { validators } from "../use-validators";
import type { AutoFormItems } from "~/types/auto-forms";

export const useUserForm = () => {
  const i18n = useI18n();

  const userForm: AutoFormItems = [
    {
      section: i18n.t("user.user-details"),
      label: i18n.t("user.user-name"),
      varName: "username",
      type: fieldTypes.TEXT,
      rules: [validators.required],
    },
    {
      label: i18n.t("user.full-name"),
      varName: "fullName",
      type: fieldTypes.TEXT,
      rules: [validators.required],
    },
    {
      label: i18n.t("user.email"),
      varName: "email",
      type: fieldTypes.TEXT,
      // KH: the e-mail address is optional (D53); a filled one must still look like an address
      hint: i18n.t("kh.onboarding.admin.create-email-hint"),
      rules: [(v: string | null) => !v || validators.email(v)],
    },
    {
      cols: 6,
      label: i18n.t("user.password"),
      varName: "password",
      disableUpdate: true,
      type: fieldTypes.PASSWORD,
      rules: [validators.required, validators.minLength(8)],
    },
    {
      cols: 6,
      label: i18n.t("user.authentication-method"),
      varName: "authMethod",
      type: fieldTypes.SELECT,
      hint: i18n.t("user.authentication-method-hint"),
      disableCreate: true,
      options: [{ text: "Mealie" }, { text: "LDAP" }, { text: "OIDC" }],
    },
    // KH: the permission fields are replaced by the account kind (KhAccountKind) on the admin user pages
  ];

  return {
    userForm,
  };
};
