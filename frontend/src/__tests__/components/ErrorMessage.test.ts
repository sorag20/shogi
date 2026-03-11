import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ErrorMessage from '../../components/ErrorMessage.vue'

describe('ErrorMessage', () => {
  it('should render when error is provided', () => {
    const wrapper = mount(ErrorMessage, {
      props: {
        error: 'Test error message',
      },
    })
    expect(wrapper.find('.error-message').exists()).toBe(true)
    expect(wrapper.text()).toContain('Test error message')
  })

  it('should not render when error is null', () => {
    const wrapper = mount(ErrorMessage, {
      props: {
        error: null,
      },
    })
    expect(wrapper.find('.error-message').exists()).toBe(false)
  })

  it('should display custom title', () => {
    const wrapper = mount(ErrorMessage, {
      props: {
        error: 'Test error',
        title: 'Custom Title',
      },
    })
    expect(wrapper.text()).toContain('Custom Title')
  })

  it('should emit dismiss event when close button is clicked', async () => {
    const wrapper = mount(ErrorMessage, {
      props: {
        error: 'Test error',
        dismissible: true,
      },
    })
    await wrapper.find('.close-btn').trigger('click')
    expect(wrapper.emitted('dismiss')).toBeTruthy()
  })
})
