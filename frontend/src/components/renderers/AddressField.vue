<script setup lang="ts">
type AddressFieldKey =
  | 'addressLine1'
  | 'addressLine2'
  | 'locality'
  | 'region'
  | 'postalCode'
  | 'country'

type AddressValue = Partial<Record<AddressFieldKey, string>>

interface AddressFieldDescriptor {
  key: AddressFieldKey
  label: string
  autocomplete?: string
  required?: boolean
}

interface Props {
  modelValue: AddressValue
  fields?: readonly AddressFieldDescriptor[]
  legend?: string
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  fields: () => [
    { key: 'addressLine1', label: 'Address line 1', autocomplete: 'address-line1', required: true },
    { key: 'addressLine2', label: 'Address line 2', autocomplete: 'address-line2' },
    { key: 'locality', label: 'City or locality', autocomplete: 'address-level2', required: true },
    { key: 'region', label: 'State, province, or region', autocomplete: 'address-level1' },
    { key: 'postalCode', label: 'Postal code', autocomplete: 'postal-code' },
    { key: 'country', label: 'Country', autocomplete: 'country-name', required: true },
  ] satisfies readonly AddressFieldDescriptor[],
  legend: 'Address',
  disabled: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: AddressValue]
}>()

function updateField(key: AddressFieldKey, event: unknown) {
  const input = (event as { currentTarget: { value: string } }).currentTarget
  emit('update:modelValue', { ...props.modelValue, [key]: input.value })
}
</script>

<template>
  <fieldset class="address-field" :disabled="disabled">
    <legend class="address-field__legend">{{ legend }}</legend>
    <div class="address-field__grid">
      <label
        v-for="field in fields"
        :key="field.key"
        class="address-field__item"
        :class="{ 'address-field__item--wide': field.key.startsWith('addressLine') }"
      >
        <span class="address-field__label">{{ field.label }}</span>
        <input
          class="address-field__input"
          type="text"
          :value="modelValue[field.key] ?? ''"
          :autocomplete="field.autocomplete"
          :required="field.required"
          @input="updateField(field.key, $event)"
        />
      </label>
    </div>
  </fieldset>
</template>

<style scoped>
.address-field {
  min-width: 0;
  margin: 0;
  padding: 1rem;
  border: 1px solid var(--qava-line, #dbe3eb);
  border-radius: 8px;
  color: var(--qava-ink, #111317);
  background: var(--qava-surface, #ffffff);
}

.address-field__legend {
  padding: 0 0.375rem;
  font-size: 0.9375rem;
  font-weight: 700;
}

.address-field__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.875rem;
}

.address-field__item {
  display: grid;
  gap: 0.375rem;
  min-width: 0;
}

.address-field__item--wide {
  grid-column: 1 / -1;
}

.address-field__label {
  color: var(--qava-ink-muted, #5f6875);
  font-size: 0.8125rem;
  font-weight: 650;
}

.address-field__input {
  width: 100%;
  min-width: 0;
  min-height: 2.625rem;
  box-sizing: border-box;
  padding: 0 0.75rem;
  border: 1px solid var(--qava-line, #dbe3eb);
  border-radius: 6px;
  outline: 0;
  color: inherit;
  background: var(--qava-surface, #ffffff);
  font: inherit;
}

.address-field__input:focus-visible {
  border-color: var(--qava-focus, #1677c8);
  box-shadow: 0 0 0 3px rgb(22 119 200 / 0.16);
}

.address-field:disabled {
  color: var(--qava-ink-muted, #5f6875);
  background: var(--qava-surface-soft, #f8fafc);
}

@media (max-width: 36rem) {
  .address-field__grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .address-field__item--wide {
    grid-column: auto;
  }
}
</style>