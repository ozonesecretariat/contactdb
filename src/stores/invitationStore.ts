import type { MeetingEvent } from "src/types/event";
import type { Organization } from "src/types/organization";
import type { Contact, EventNomination } from "src/types/registration";

import { api } from "boot/axios";
import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { useRoute } from "vue-router";

export const useInvitationStore = defineStore("invitation", () => {
  const route = useRoute();
  const initialized = ref(false);
  const contacts = ref<Contact[]>([]);
  const events = ref<MeetingEvent[]>([]);
  const nominations = ref<EventNomination[]>([]);
  const organizations = ref<Organization[]>([]);
  const token = computed(() => route.params.invitationToken as string);
  const participantId = computed(() => route.params.participantId as string);
  const participant = computed(() => contacts.value.find((c) => c.id === Number(participantId.value)));

  const actions = {
    async load() {
      await Promise.all([this.loadEvents(), this.loadNominations(), this.loadOrganizations(), this.loadContacts()]);
      initialized.value = true;
    },
    async loadContacts() {
      contacts.value = (await api.get<Contact[]>(`/events-nominations/${token.value}/available-contacts/`)).data;
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
  };

  return {
    contacts,
    events,
    initialized,
    nominations,
    organizations,
    participant,
    participantId,
    token,
    ...actions,
  };
});
