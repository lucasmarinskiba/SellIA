import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SecureSignupForm } from './SecureSignupForm';

// Mock fetch
global.fetch = jest.fn();

describe('SecureSignupForm', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Form validation', () => {
    it('renders all form fields', () => {
      render(
        <SecureSignupForm
          onSuccess={jest.fn()}
          onError={jest.fn()}
        />
      );

      expect(screen.getByPlaceholderText('Juan García')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('tu@correo.com')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('MiContraseña123@')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Repite tu contraseña')).toBeInTheDocument();
    });

    it('shows error for missing full name', async () => {
      render(
        <SecureSignupForm
          onSuccess={jest.fn()}
          onError={jest.fn()}
        />
      );

      const submitButton = screen.getByText('Crear cuenta');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('El nombre es requerido')).toBeInTheDocument();
      });
    });

    it('shows error for invalid email', async () => {
      render(
        <SecureSignupForm
          onSuccess={jest.fn()}
          onError={jest.fn()}
        />
      );

      const emailInput = screen.getByPlaceholderText('tu@correo.com');
      await userEvent.type(emailInput, 'invalid-email');

      const submitButton = screen.getByText('Crear cuenta');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Email inválido')).toBeInTheDocument();
      });
    });

    it('shows error for weak password', async () => {
      render(
        <SecureSignupForm
          onSuccess={jest.fn()}
          onError={jest.fn()}
        />
      );

      const fullNameInput = screen.getByPlaceholderText('Juan García');
      const emailInput = screen.getByPlaceholderText('tu@correo.com');
      const passwordInput = screen.getByPlaceholderText('MiContraseña123@');

      await userEvent.type(fullNameInput, 'John Doe');
      await userEvent.type(emailInput, 'john@example.com');
      await userEvent.type(passwordInput, 'weak');

      const submitButton = screen.getByText('Crear cuenta');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(
          screen.getByText('La contraseña no es lo suficientemente segura')
        ).toBeInTheDocument();
      });
    });

    it('shows error for mismatched passwords', async () => {
      render(
        <SecureSignupForm
          onSuccess={jest.fn()}
          onError={jest.fn()}
        />
      );

      const passwordInput = screen.getByPlaceholderText('MiContraseña123@');
      const confirmInput = screen.getByPlaceholderText('Repite tu contraseña');

      await userEvent.type(passwordInput, 'SecurePass123@');
      await userEvent.type(confirmInput, 'DifferentPass123@');

      const submitButton = screen.getByText('Crear cuenta');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Las contraseñas no coinciden')).toBeInTheDocument();
      });
    });

    it('shows success message when passwords match', async () => {
      render(
        <SecureSignupForm
          onSuccess={jest.fn()}
          onError={jest.fn()}
        />
      );

      const passwordInput = screen.getByPlaceholderText('MiContraseña123@');
      const confirmInput = screen.getByPlaceholderText('Repite tu contraseña');

      await userEvent.type(passwordInput, 'SecurePass123@');
      await userEvent.type(confirmInput, 'SecurePass123@');

      await waitFor(() => {
        expect(
          screen.getByText('✓ Las contraseñas coinciden')
        ).toBeInTheDocument();
      });
    });
  });

  describe('Password visibility toggle', () => {
    it('toggles password visibility', async () => {
      render(
        <SecureSignupForm
          onSuccess={jest.fn()}
          onError={jest.fn()}
        />
      );

      const passwordInput = screen.getByPlaceholderText(
        'MiContraseña123@'
      ) as HTMLInputElement;
      expect(passwordInput.type).toBe('password');

      const toggleButton = screen.getAllByText(/[👁️🙈]/)[0];
      fireEvent.click(toggleButton);

      expect(passwordInput.type).toBe('text');
    });
  });

  describe('Form submission', () => {
    it('submits form with valid data', async () => {
      const onSuccess = jest.fn();
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          user_id: 'uuid-123',
          email: 'john@example.com',
          full_name: 'John Doe',
        }),
      });

      render(
        <SecureSignupForm
          onSuccess={onSuccess}
          onError={jest.fn()}
        />
      );

      const fullNameInput = screen.getByPlaceholderText('Juan García');
      const emailInput = screen.getByPlaceholderText('tu@correo.com');
      const passwordInput = screen.getByPlaceholderText('MiContraseña123@');
      const confirmInput = screen.getByPlaceholderText('Repite tu contraseña');

      await userEvent.type(fullNameInput, 'John Doe');
      await userEvent.type(emailInput, 'john@example.com');
      await userEvent.type(passwordInput, 'SecurePass123@');
      await userEvent.type(confirmInput, 'SecurePass123@');

      const submitButton = screen.getByText('Crear cuenta');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          '/api/v1/auth/signup',
          expect.objectContaining({
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: expect.stringContaining('john@example.com'),
          })
        );

        expect(onSuccess).toHaveBeenCalledWith({
          userId: 'uuid-123',
          email: 'john@example.com',
        });
      });
    });

    it('shows error on API failure', async () => {
      const onError = jest.fn();
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: 'Email already registered' }),
      });

      render(
        <SecureSignupForm
          onSuccess={jest.fn()}
          onError={onError}
        />
      );

      const fullNameInput = screen.getByPlaceholderText('Juan García');
      const emailInput = screen.getByPlaceholderText('tu@correo.com');
      const passwordInput = screen.getByPlaceholderText('MiContraseña123@');
      const confirmInput = screen.getByPlaceholderText('Repite tu contraseña');

      await userEvent.type(fullNameInput, 'John Doe');
      await userEvent.type(emailInput, 'john@example.com');
      await userEvent.type(passwordInput, 'SecurePass123@');
      await userEvent.type(confirmInput, 'SecurePass123@');

      const submitButton = screen.getByText('Crear cuenta');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(onError).toHaveBeenCalledWith('Email already registered');
        expect(screen.getByText('Email already registered')).toBeInTheDocument();
      });
    });

    it('disables submit button for weak passwords', async () => {
      render(
        <SecureSignupForm
          onSuccess={jest.fn()}
          onError={jest.fn()}
        />
      );

      const submitButton = screen.getByText('Crear cuenta') as HTMLButtonElement;
      expect(submitButton.disabled).toBe(true);

      const passwordInput = screen.getByPlaceholderText('MiContraseña123@');
      await userEvent.type(passwordInput, 'SecurePass123@');

      // Wait for password strength to be calculated
      await waitFor(() => {
        expect(submitButton.disabled).toBe(false);
      });
    });
  });

  describe('Security indicators', () => {
    it('displays security notice', () => {
      render(
        <SecureSignupForm
          onSuccess={jest.fn()}
          onError={jest.fn()}
        />
      );

      expect(screen.getByText('Protección de seguridad')).toBeInTheDocument();
      expect(screen.getByText(/Contraseña cifrada con bcrypt/)).toBeInTheDocument();
      expect(screen.getByText(/Autenticación de dos factores/)).toBeInTheDocument();
    });
  });
});
