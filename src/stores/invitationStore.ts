import type { AxiosError } from "axios";
import type { Country } from "src/types/country";
import type { MeetingEvent } from "src/types/event";
import type { Contact, EventNomination } from "src/types/nomination";
import type { Organization } from "src/types/organization";

import { api } from "boot/axios";
import { defineStore } from "pinia";
import { useQuasar } from "quasar";
import { computed, ref } from "vue";
import { useRoute } from "vue-router";

export const useInvitationStore = defineStore("invitation", () => {
  const $q = useQuasar();
  const route = useRoute();
  const initialized = ref(false);
  const roles = ref<string[]>([]);
  const contacts = ref<Contact[]>([]);
  const events = ref<MeetingEvent[]>([]);
  const nominations = ref<EventNomination[]>([]);
  const organizations = ref<Organization[]>([]);
  const countries = ref<Country[]>([]);
  const token = computed(() => route.params.invitationToken as string);
  const participantId = computed(() => route.params.participantId as string);
  const participant = computed(() => contacts.value.find((c) => c.id === Number(participantId.value)));

  const actions = {
    async load() {
      try {
        await Promise.all([
          this.loadEvents(),
          this.loadNominations(),
          this.loadOrganizations(),
          this.loadContacts(),
          this.loadRoles(),
          this.loadCountries(),
        ]);
      } catch (e) {
        switch ((e as AxiosError).status) {
          case 404:
            $q.notify({
              message: "Invalid token!",
              type: "negative",
            });
            break;
          default:
            $q.notify({
              message: "Error while loading invitation data!",
              type: "negative",
            });
            throw e;
        }
      }
      initialized.value = true;
    },
    async loadContacts() {
      contacts.value = (await api.get<Contact[]>(`/events-nominations/${token.value}/available-contacts/`)).data;
    },
    async loadCountries() {
      countries.value = (await api.get<Country[]>(`/events-nominations/${token.value}/countries/`)).data;
    },
    async loadEvents() {
      events.value = (await api.get<MeetingEvent[]>(`/events-nominations/${token.value}/events/`)).data;
    },
    async loadNominations() {
      nominations.value = (await api.get<EventNomination[]>(`/events-nominations/${token.value}/`)).data;
    },
    async loadOrganizations() {
      organizations.value = (await api.get<Organization[]>(`/events-nominations/${token.value}/organizations/`)).data;
    },
    async loadRoles() {
      roles.value = (await api.get<string[]>(`/events-nominations/${token.value}/roles/`)).data;
    },
  };

  return {
    contacts,
    countries,
    events,
    initialized,
    nominations,
    organizations,
    participant,
    participantId,
    roles,
    token,
    ...actions,
  };
});
