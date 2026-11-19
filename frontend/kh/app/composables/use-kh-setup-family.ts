// KH: the setup wizard's "Familie" step (D83) as one shared state, so the summary can name the people: the rows being
// typed, the people created so far (with the temporary password, kept only until the wizard is left), and the creation
// itself with Mealie's admin API, the tour (D59) and the simple view (D79).
import { emptyRow, generatePassword, isBlankRow, rowProblems, type FamilyRow, type RowProblem } from "../lib/setup-wizard";
import { KhNavigationApi } from "../lib/api/navigation";
import { KhOnboardingApi } from "../lib/api/onboarding";
import { OWN_ERRORS } from "../lib/api/own-errors";
import { useAdminApi } from "~/composables/api";
import { useRequests } from "~/composables/api/api-client";
import { useGlobalI18n } from "~/composables/use-global-i18n";
import { alert } from "~/composables/use-toast";
import type { UserIn } from "~/lib/api/types/user";

export interface CreatedPerson {
  name: string;
  username: string;
  password: string;
}

export const khFamily = reactive({
  rows: [emptyRow()] as FamilyRow[],
  created: [] as CreatedPerson[],
  /** The server's answer per row index: the username or address is taken ("taken") or the call failed ("failed"). */
  failures: {} as Record<number, "taken" | "failed">,
});

/** A person who exists, but whose tour (D59) or simple view (D79) could not be set. */
export interface FollowUpFailure {
  name: string;
  failed: "tour" | "simple";
}

/** How many filled rows are waiting to be created. */
export function pendingCount(): number {
  return khFamily.rows.filter(row => !isBlankRow(row)).length;
}

/** Drops the rows that were typed but not created, e.g. when the admin moves on without them. */
export function discardRows(): void {
  khFamily.rows = [emptyRow()];
  khFamily.failures = {};
}

/** Forgets the rows and the shown passwords; the wizard calls it when it is left. */
export function resetKhFamily(): void {
  khFamily.rows = [emptyRow()];
  khFamily.created = [];
  khFamily.failures = {};
}

/** What the wizard needs of the step: the rows, who exists now, and creating the valid rows. */
export function useKhSetupFamily() {
  const auth = useMealieAuth();
  const adminApi = useAdminApi();

  const problems = computed<(RowProblem | null)[]>(() => rowProblems(khFamily.rows));
  const filled = computed(() => khFamily.rows.filter(row => !isBlankRow(row)));
  const canCreate = computed(() => filled.value.length > 0 && problems.value.every(problem => !problem));

  function addRow(): void {
    khFamily.rows.push(emptyRow());
  }

  function removeRow(index: number): void {
    khFamily.rows.splice(index, 1);
    khFamily.failures = {};
    if (!khFamily.rows.length) addRow();
  }

  /** The row was edited: what the server said about it no longer applies. */
  function clearFailure(index: number): void {
    khFamily.failures = Object.fromEntries(Object.entries(khFamily.failures).filter(([key]) => Number(key) !== index));
  }

  /** Creates one person: the follow-ups that failed (empty: all fine), or why the person was not created. */
  async function createPerson(row: FamilyRow): Promise<FollowUpFailure["failed"][] | "taken" | "failed"> {
    const password = generatePassword();
    const user = auth.user.value!;
    const { response, data, error } = await adminApi.users.createOne({
      username: row.username.trim(),
      fullName: row.name.trim(),
      email: row.email.trim(),
      password,
      group: user.group,
      household: user.household,
      authMethod: "Mealie",
    } as UserIn, OWN_ERRORS);
    if (response?.status !== 201 || !data) {
      return (error as { response?: { status?: number } } | null)?.response?.status === 409 ? "taken" : "failed";
    }
    const tour = row.tour ? await new KhOnboardingApi(useRequests()).setTour(data.id, true) : null;
    const simple = row.simple ? await new KhNavigationApi(useRequests()).putSimple(data.id, true) : null;
    khFamily.created.push({ name: row.name.trim(), username: row.username.trim(), password });
    return [...(tour?.error ? ["tour" as const] : []), ...(simple?.error ? ["simple" as const] : [])];
  }

  /** Creates every filled row one after the other. Created rows leave the list, failed ones stay with their reason.
   * Returns the people whose tour or simple view could not be set. */
  async function createAll(): Promise<FollowUpFailure[]> {
    const kept: FamilyRow[] = [];
    const failures: Record<number, "taken" | "failed"> = {};
    const followUps: FollowUpFailure[] = [];
    for (const row of khFamily.rows.filter(row => !isBlankRow(row))) {
      const result = await createPerson(row);
      if (typeof result === "string") failures[kept.push(row) - 1] = result;
      else followUps.push(...result.map(failed => ({ name: row.name.trim(), failed })));
    }
    khFamily.rows = kept.length ? kept : [emptyRow()];
    khFamily.failures = failures;
    return followUps;
  }

  /** createAll, and a message per person whose tour or simple view could not be set. Returns whether every row was
   * created. */
  async function create(): Promise<boolean> {
    const t = useGlobalI18n().t;
    for (const { name, failed } of await createAll()) alert.error(t(`kh.wizard.family.${failed}-failed`, { name }));
    return pendingCount() === 0;
  }

  return { problems, filled, canCreate, addRow, removeRow, clearFailure, createAll, create };
}
