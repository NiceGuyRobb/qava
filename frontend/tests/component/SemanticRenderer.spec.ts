import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import catalog from '../../../data/components/catalog.v1.json'
import SemanticRenderer from '../../src/components/interview/SemanticRenderer.vue'
import {
  catalogComponentNames,
  resolveRenderer,
  type ComponentSpec,
} from '../../src/components/renderers/registry'

const spec = (name: string, fallback?: string, props: Record<string, unknown> = {}): ComponentSpec => ({
  name,
  version: 1,
  props,
  fallback,
})

const objectSchema = {
  type: 'object',
  properties: { value: { type: 'string', title: 'Value' } },
}
const arraySchema = { type: 'array', items: objectSchema }

describe('SemanticRenderer', () => {
  it('resolves known components and reports shape incompatibility explicitly', () => {
    expect(resolveRenderer(spec('short_text'), { type: 'string' }, options()).resolvedName).toBe('short_text')

    const incompatible = resolveRenderer(spec('number'), { type: 'string' }, options())
    expect(incompatible.supported).toBe(false)
    expect(incompatible.reason).toContain('incompatible')
  })

  it('requires a registered, schema-compatible explicit fallback', () => {
    const missing = resolveRenderer(spec('unknown'), { type: 'string' }, options())
    expect(missing.reason).toBe('Component "unknown" is not registered.')

    const compatible = resolveRenderer(spec('unknown', 'short_text'), { type: 'string' }, options())
    expect(compatible).toMatchObject({ supported: true, resolvedName: 'short_text', usedFallback: true })

    const incompatible = resolveRenderer(spec('unknown', 'number'), { type: 'string' }, options())
    expect(incompatible.supported).toBe(false)
    expect(incompatible.reason).toContain('fallback "number" is incompatible')
  })

  it('covers every checked-in catalog name with a compatible representative schema', () => {
    const schemasByShape: Record<string, Record<string, unknown>> = {
      string: { type: 'string' },
      number: { type: 'number' },
      boolean: { type: 'boolean' },
      scalar: { type: 'string', enum: ['choice-a', 'choice-b'] },
      object: objectSchema,
      array: { type: 'array', items: { type: 'string', enum: ['choice-a', 'choice-b'] } },
      asset_reference_array: arraySchema,
      money: { type: 'number' },
      date: { type: 'string' },
      datetime: { type: 'string' },
    }

    expect(catalogComponentNames).toEqual(catalog.components.map((entry) => entry.name))
    for (const entry of catalog.components) {
      const schema = ['repeatable_group'].includes(entry.name)
        ? arraySchema
        : schemasByShape[entry.answer_shape]
      if (!schema) throw new Error(`Missing representative schema for ${entry.answer_shape}`)
      const resolution = resolveRenderer(spec(entry.name), schema, options())
      expect(resolution.supported, `${entry.name}: ${resolution.reason}`).toBe(true)
    }
  })

  it('preserves a stable choice ID emitted by the production choice renderer', async () => {
    const wrapper = mount(SemanticRenderer, {
      props: {
        componentSpec: spec('single_select', undefined, {
          options: [
            { value: 'machine-a', label: 'Display A' },
            { value: 'machine-b', label: 'Display B' },
          ],
        }),
        answerSchema: { type: 'string', enum: ['machine-a', 'machine-b'] },
        draftValue: 'machine-a',
        prompt: 'Choose one',
      },
    })

    await wrapper.findAll('input')[1]?.trigger('change')
    expect(wrapper.emitted('update:modelValue')).toEqual([['machine-b']])
  })

  it('uses server-resolved structured fields when object properties are not repeated', () => {
    const resolution = resolveRenderer(
      spec('structured_form', undefined, {
        fields: [
          {
            component: 'single_select',
            key: 'build_type',
            label: 'What kind of project is this?',
            options: ['New build', 'Renovation'],
          },
        ],
      }),
      { type: 'object', required: ['build_type'] },
      options(),
    )

    expect(resolution).toMatchObject({
      supported: true,
      props: {
        fields: [
          {
            key: 'build_type',
            label: 'What kind of project is this?',
            required: true,
            type: 'select',
            options: [
              { value: 'New build', label: 'New build' },
              { value: 'Renovation', label: 'Renovation' },
            ],
          },
        ],
      },
    })
  })

  it('renders an unanswered structured form with an empty object draft', () => {
    const wrapper = mount(SemanticRenderer, {
      props: {
        componentSpec: spec('structured_form', undefined, {
          fields: [
            {
              component: 'single_select',
              key: 'build_type',
              label: 'What kind of project is this?',
              options: ['New build', 'Renovation'],
            },
          ],
        }),
        answerSchema: { type: 'object', required: ['build_type'] },
        draftValue: null,
        label: 'Project basics',
      },
    })

    expect(wrapper.find('select').exists()).toBe(true)
    expect(wrapper.find('[data-unsupported-component]').exists()).toBe(false)
  })

  it('captures an unconstrained object as valid JSON', async () => {
    const wrapper = mount(SemanticRenderer, {
      props: {
        componentSpec: spec('structured_form'),
        answerSchema: { type: 'object' },
        draftValue: null,
        label: 'Output contract',
      },
    })

    const editor = wrapper.get('textarea')
    await editor.setValue('{"type":"object","properties":{"name":{"type":"string"}}}')

    expect(wrapper.find('[data-unsupported-component]').exists()).toBe(false)
    expect(wrapper.emitted('update:modelValue')).toEqual([
      [{ type: 'object', properties: { name: { type: 'string' } } }],
    ])
  })

  it('captures an unconstrained object collection as valid JSON', async () => {
    const wrapper = mount(SemanticRenderer, {
      props: {
        componentSpec: spec('repeatable_group'),
        answerSchema: { type: 'array', items: { type: 'object' } },
        draftValue: null,
        label: 'Questions',
      },
    })

    const editor = wrapper.get('textarea')
    await editor.setValue('[{"id":"project-name","prompt":"What is the project name?"}]')

    expect(wrapper.find('[data-unsupported-component]').exists()).toBe(false)
    expect(wrapper.emitted('update:modelValue')).toEqual([
      [[{ id: 'project-name', prompt: 'What is the project name?' }]],
    ])
  })

  it.each([
    ['number', { type: 'number' }, 42],
    ['boolean', { type: 'boolean' }, false],
    ['structured_form', objectSchema, { value: 'kept' }],
    ['repeatable_group', arraySchema, [{ value: 'kept' }]],
  ])('submits the current %s draft without coercion', async (name, answerSchema, draftValue) => {
    const wrapper = mount(SemanticRenderer, {
      props: { componentSpec: spec(name), answerSchema, draftValue, label: 'Answer' },
    })

    await wrapper.get('.semantic-renderer__submit').trigger('click')
    expect(wrapper.emitted('submit')?.[0]?.[0]).toBe(draftValue)
  })

  it('recursively renders nested repeatable groups', async () => {
    const nestedArraySchema = {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          name: { type: 'string', title: 'Name' },
          windows: {
            type: 'array',
            title: 'Windows',
            items: {
              type: 'object',
              properties: { width: { type: 'number', title: 'Width' } },
            },
          },
        },
      },
    }
    const wrapper = mount(SemanticRenderer, {
      props: {
        componentSpec: spec('repeatable_group'),
        answerSchema: nestedArraySchema,
        draftValue: [{ name: 'Kitchen', windows: [{ width: 3 }] }],
        label: 'Rooms',
      },
    })

    // Nested collection legend and pre-populated nested scalar render.
    expect(wrapper.text()).toContain('Windows')
    const numberInputs = wrapper.findAll('input[type="number"]')
    const widthInput = numberInputs.find(
      (input) => (input.element as HTMLInputElement).value === '3',
    )
    expect(widthInput).toBeDefined()

    // Editing a nested scalar propagates up through the recursive tree.
    await widthInput!.setValue('5')
    const updates = wrapper.emitted('update:modelValue')
    expect(updates?.at(-1)?.[0]).toEqual([{ name: 'Kitchen', windows: [{ width: 5 }] }])
  })

  it('renders an accessible explicit unsupported state', () => {
    const wrapper = mount(SemanticRenderer, {
      props: {
        componentSpec: spec('number'),
        answerSchema: { type: 'object' },
        draftValue: {},
        label: 'Answer',
      },
    })

    expect(wrapper.get('[role="alert"]').text()).toContain('incompatible')
    expect(wrapper.find('.semantic-renderer__submit').exists()).toBe(false)
  })
})

function options() {
  return { label: 'Answer', draftValue: null }
}
