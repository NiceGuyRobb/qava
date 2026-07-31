import type { Component } from 'vue'

import AddressField from './AddressField.vue'
import BooleanField from './BooleanField.vue'
import ChoiceField from './ChoiceField.vue'
import DateTimeField from './DateTimeField.vue'
import FileReferenceField from './FileReferenceField.vue'
import MoneyField from './MoneyField.vue'
import NumberField from './NumberField.vue'
import RepeatableGroup from './RepeatableGroup.vue'
import StructuredForm from './StructuredForm.vue'
import TextField from './TextField.vue'

export type ComponentSpec = {
  name: string
  version: number
  props: Record<string, unknown>
  fallback?: string | null
}

interface DerivedField {
  key: string
  label: string
  required: boolean
  type: 'string' | 'number' | 'boolean' | 'select' | 'group' | 'collection'
  options?: { value: string | number | boolean; label: string }[]
  fields?: DerivedField[]
  min?: number
  max?: number
  step?: number
  minItems?: number
  maxItems?: number
}

type AnswerShape =
  | 'string'
  | 'number'
  | 'boolean'
  | 'scalar'
  | 'object'
  | 'array'
  | 'money'
  | 'date'
  | 'datetime'
type RendererFamily =
  | 'text'
  | 'number'
  | 'boolean'
  | 'choice'
  | 'object'
  | 'array'
  | 'address'
  | 'file'
  | 'money'
  | 'datetime'

interface RegistryEntry {
  answerShape: AnswerShape
  family: RendererFamily
  component: Component
  defaults?: Record<string, unknown>
}

export interface RendererResolution {
  supported: boolean
  requestedName: string
  resolvedName?: string
  usedFallback: boolean
  component?: Component
  props?: Record<string, unknown>
  reason?: string
}

const entries = {
  short_text: { answerShape: 'string', family: 'text', component: TextField },
  long_text: {
    answerShape: 'string',
    family: 'text',
    component: TextField,
    defaults: { multiline: true },
  },
  number: { answerShape: 'number', family: 'number', component: NumberField },
  single_select: { answerShape: 'scalar', family: 'choice', component: ChoiceField },
  multi_select: {
    answerShape: 'array',
    family: 'choice',
    component: ChoiceField,
    defaults: { multiple: true },
  },
  boolean: { answerShape: 'boolean', family: 'boolean', component: BooleanField },
  address: { answerShape: 'object', family: 'address', component: AddressField },
  measurement: { answerShape: 'object', family: 'object', component: StructuredForm },
  budget_tiers: { answerShape: 'scalar', family: 'choice', component: ChoiceField },
  ranking: {
    answerShape: 'array',
    family: 'choice',
    component: ChoiceField,
    defaults: { multiple: true },
  },
  structured_form: { answerShape: 'object', family: 'object', component: StructuredForm },
  repeatable_group: { answerShape: 'array', family: 'array', component: RepeatableGroup },
  room_programme: { answerShape: 'object', family: 'object', component: StructuredForm },
  visual_cards: { answerShape: 'scalar', family: 'choice', component: ChoiceField },
  file_upload: { answerShape: 'array', family: 'file', component: FileReferenceField },
  tradeoff: { answerShape: 'object', family: 'object', component: StructuredForm },
  confirmation: { answerShape: 'boolean', family: 'boolean', component: BooleanField },
  money_input: { answerShape: 'money', family: 'money', component: MoneyField },
  date_picker: {
    answerShape: 'date',
    family: 'datetime',
    component: DateTimeField,
    defaults: { type: 'date' },
  },
  datetime_picker: {
    answerShape: 'datetime',
    family: 'datetime',
    component: DateTimeField,
    defaults: { type: 'datetime-local' },
  },
} satisfies Record<string, RegistryEntry>

export const catalogComponentNames = Object.freeze(Object.keys(entries))

export function resolveRenderer(
  componentSpec: ComponentSpec,
  answerSchema: Record<string, unknown>,
  options: { label: string; draftValue: unknown; disabled?: boolean },
): RendererResolution {
  const primary = resolveCandidate(componentSpec.name, componentSpec, answerSchema, options)
  if (primary.supported) return primary

  const fallbackName = componentSpec.fallback
  if (!fallbackName) return primary

  const fallback = resolveCandidate(fallbackName, componentSpec, answerSchema, options)
  if (fallback.supported) {
    return { ...fallback, requestedName: componentSpec.name, usedFallback: true }
  }

  return {
    supported: false,
    requestedName: componentSpec.name,
    usedFallback: false,
    reason: `Component "${componentSpec.name}" is unsupported or incompatible; fallback "${fallbackName}" is incompatible: ${fallback.reason ?? 'no compatible renderer'}`,
  }
}

function resolveCandidate(
  name: string,
  componentSpec: ComponentSpec,
  answerSchema: Record<string, unknown>,
  options: { label: string; draftValue: unknown; disabled?: boolean },
): RendererResolution {
  const entry = entries[name as keyof typeof entries] as RegistryEntry | undefined
  if (!entry) {
    return {
      supported: false,
      requestedName: name,
      usedFallback: false,
      reason: `Component "${name}" is not registered.`,
    }
  }

  if (!isShapeCompatible(entry.answerShape, answerSchema)) {
    return {
      supported: false,
      requestedName: name,
      usedFallback: false,
      reason: `Component "${name}" is incompatible with answer schema type "${schemaTypeLabel(answerSchema)}".`,
    }
  }

  const props = buildAdapterProps(entry, componentSpec.props, answerSchema, options)
  if (!props) {
    return {
      supported: false,
      requestedName: name,
      usedFallback: false,
      reason: `Component "${name}" cannot derive the required renderer props from the answer schema.`,
    }
  }

  return {
    supported: true,
    requestedName: name,
    resolvedName: name,
    usedFallback: false,
    component: entry.component,
    props,
  }
}

function isShapeCompatible(shape: AnswerShape, schema: Record<string, unknown>): boolean {
  const schemaType = schema.type
  if (typeof schemaType !== 'string') return false
  if (shape === 'scalar') return ['string', 'number', 'integer', 'boolean'].includes(schemaType)
  if (shape === 'number') return schemaType === 'number' || schemaType === 'integer'
  if (shape === 'money') return ['number', 'integer', 'object'].includes(schemaType)
  if (shape === 'date' || shape === 'datetime') return schemaType === 'string'
  return schemaType === shape
}

function buildAdapterProps(
  entry: RegistryEntry,
  specProps: Record<string, unknown>,
  schema: Record<string, unknown>,
  options: { label: string; draftValue: unknown; disabled?: boolean },
): Record<string, unknown> | undefined {
  const props: Record<string, unknown> = {
    ...entry.defaults,
    modelValue: initialRendererValue(entry.answerShape, options.draftValue),
    label: options.label,
    disabled: options.disabled ?? false,
  }

  copyString(specProps, props, 'placeholder')
  copyString(specProps, props, 'currency')
  copyString(specProps, props, 'trueLabel')
  copyString(specProps, props, 'falseLabel')
  copyString(specProps, props, 'unansweredLabel')
  copyString(specProps, props, 'itemLabel')
  copyString(specProps, props, 'addLabel')
  copyNumber(specProps, props, 'rows')

  if (entry.family === 'datetime') {
    copyString(specProps, props, 'min')
    copyString(specProps, props, 'max')
  }

  const minimum = finiteNumber(schema.minimum)
  const maximum = finiteNumber(schema.maximum)
  const multipleOf = finiteNumber(schema.multipleOf)
  if (minimum !== undefined) props.min = minimum
  if (maximum !== undefined) props.max = maximum
  if (multipleOf !== undefined && multipleOf > 0) props.step = multipleOf

  if (entry.family === 'choice') {
    const choices = deriveChoices(specProps, schema, entry.defaults?.multiple === true)
    if (!choices) return undefined
    props.choices = choices
  }

  if (entry.family === 'object') {
    const fields = deriveDeclaredFields(specProps, schema) ?? deriveFields(schema)
    props.fields = fields ?? []
    props.legend = options.label
  }

  if (entry.family === 'array') {
    const itemSchema = recordValue(schema.items)
    const fields = itemSchema ? deriveFields(itemSchema) : undefined
    props.fields = fields ?? []
    props.legend = options.label
    const minItems = nonNegativeInteger(schema.minItems)
    const maxItems = nonNegativeInteger(schema.maxItems)
    if (minItems !== undefined) props.minItems = minItems
    if (maxItems !== undefined) props.maxItems = maxItems
  }

  if (entry.family === 'address' || entry.family === 'file') props.legend = options.label
  if (entry.family === 'file') {
    const maxItems = nonNegativeInteger(schema.maxItems)
    if (maxItems !== undefined) props.maxItems = maxItems
  }

  return props
}

function initialRendererValue(shape: AnswerShape, draftValue: unknown): unknown {
  if (draftValue !== null && draftValue !== undefined) return draftValue
  if (shape === 'object') return {}
  if (shape === 'array') return []
  return draftValue
}

function deriveChoices(
  specProps: Record<string, unknown>,
  schema: Record<string, unknown>,
  multiple: boolean,
): { id: string | number | boolean | null; label: string }[] | undefined {
  const declared = Array.isArray(specProps.choices)
    ? specProps.choices
    : Array.isArray(specProps.options)
      ? specProps.options
      : undefined
  if (declared) {
    const choices = declared.map(normalizeChoice)
    if (choices.every((choice) => choice !== undefined)) return choices
  }

  const valueSchema = multiple ? recordValue(schema.items) : schema
  if (!valueSchema || !Array.isArray(valueSchema.enum)) return undefined
  const values = valueSchema.enum.filter(isChoiceId)
  if (values.length !== valueSchema.enum.length) return undefined
  return values.map((value) => ({ id: value, label: String(value) }))
}

function normalizeChoice(value: unknown) {
  if (isChoiceId(value)) return { id: value, label: String(value) }
  const choice = recordValue(value)
  if (!choice || typeof choice.label !== 'string') return undefined
  const id = choice.id ?? choice.value
  if (!isChoiceId(id)) return undefined
  return { id, label: choice.label }
}

function deriveFields(schema: Record<string, unknown>): DerivedField[] | undefined {
  const properties = recordValue(schema.properties)
  if (!properties) return undefined
  const required = new Set(Array.isArray(schema.required) ? schema.required.filter(isString) : [])
  const fields = Object.entries(properties).map(([key, value]) => deriveField(key, value, required.has(key)))
  if (!fields.every((field): field is DerivedField => field !== undefined)) return undefined
  return fields
}

function deriveDeclaredFields(
  specProps: Record<string, unknown>,
  schema: Record<string, unknown>,
) {
  if (!Array.isArray(specProps.fields)) return undefined
  const required = new Set(Array.isArray(schema.required) ? schema.required.filter(isString) : [])
  const fields = specProps.fields.map((value) => deriveDeclaredField(value, required))
  if (!fields.every((field) => field !== undefined)) return undefined
  return fields
}

function deriveDeclaredField(value: unknown, required: ReadonlySet<string>) {
  const field = recordValue(value)
  if (!field || typeof field.key !== 'string' || typeof field.label !== 'string') return undefined
  const base = { key: field.key, label: field.label, required: required.has(field.key) }

  if (field.component === 'single_select' && Array.isArray(field.options)) {
    const options = field.options.map(normalizeChoice)
    const validOptions = options.filter(
      (option): option is { id: string | number | boolean; label: string } =>
        option !== undefined && option.id !== null,
    )
    if (validOptions.length !== options.length) return undefined
    return {
      ...base,
      type: 'select' as const,
      options: validOptions.map((option) => ({ value: option.id, label: option.label })),
    }
  }
  if (field.component === 'number') return { ...base, type: 'number' as const }
  if (field.component === 'boolean') return { ...base, type: 'boolean' as const }
  if (field.component === 'short_text' || field.component === 'long_text') {
    return { ...base, type: 'string' as const }
  }
  return undefined
}

function deriveField(key: string, value: unknown, required: boolean): DerivedField | undefined {
  const schema = recordValue(value)
  if (!schema || typeof schema.type !== 'string') return undefined
  const base = {
    key,
    label: typeof schema.title === 'string' ? schema.title : humanize(key),
    required,
  }

  if (Array.isArray(schema.enum) && schema.enum.every(isNonNullChoiceId)) {
    return {
      ...base,
      type: 'select' as const,
      options: schema.enum.map((option) => ({ value: option, label: String(option) })),
    }
  }
  if (schema.type === 'string') return { ...base, type: 'string' as const }
  if (schema.type === 'boolean') return { ...base, type: 'boolean' as const }
  if (schema.type === 'number' || schema.type === 'integer') {
    return {
      ...base,
      type: 'number' as const,
      min: finiteNumber(schema.minimum),
      max: finiteNumber(schema.maximum),
      step: schema.type === 'integer' ? 1 : finiteNumber(schema.multipleOf),
    }
  }
  if (schema.type === 'object') {
    const fields = deriveFields(schema)
    if (!fields) return undefined
    return { ...base, type: 'group' as const, fields }
  }
  if (schema.type === 'array') {
    const itemSchema = recordValue(schema.items)
    const fields = itemSchema ? deriveFields(itemSchema) : undefined
    if (!fields) return undefined
    return {
      ...base,
      type: 'collection' as const,
      fields,
      minItems: nonNegativeInteger(schema.minItems),
      maxItems: nonNegativeInteger(schema.maxItems),
    }
  }
  return undefined
}

function schemaTypeLabel(schema: Record<string, unknown>): string {
  return typeof schema.type === 'string' ? schema.type : 'unspecified'
}

function recordValue(value: unknown): Record<string, unknown> | undefined {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : undefined
}

function finiteNumber(value: unknown): number | undefined {
  return typeof value === 'number' && Number.isFinite(value) ? value : undefined
}

function nonNegativeInteger(value: unknown): number | undefined {
  return typeof value === 'number' && Number.isInteger(value) && value >= 0 ? value : undefined
}

function copyString(source: Record<string, unknown>, target: Record<string, unknown>, key: string) {
  if (typeof source[key] === 'string') target[key] = source[key]
}

function copyNumber(source: Record<string, unknown>, target: Record<string, unknown>, key: string) {
  const value = finiteNumber(source[key])
  if (value !== undefined) target[key] = value
}

function isString(value: unknown): value is string {
  return typeof value === 'string'
}

function isChoiceId(value: unknown): value is string | number | boolean | null {
  return value === null || ['string', 'number', 'boolean'].includes(typeof value)
}

function isNonNullChoiceId(value: unknown): value is string | number | boolean {
  return value !== null && isChoiceId(value)
}

function humanize(value: string): string {
  const words = value.replace(/([a-z])([A-Z])/g, '$1 $2').replace(/[_-]+/g, ' ')
  return words.charAt(0).toUpperCase() + words.slice(1)
}