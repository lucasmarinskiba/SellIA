import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TwoFactorSetup } from './TwoFactorSetup';

global.fetch = jest.fn();

describe('TwoFactorSetup', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Intro step', () => {
    it('renders intro with benefits', () => {
      render(
        <TwoFactorSetup
          userId="user-123"
          onComplete={jest.fn()}
          onCancel={jest.fn()}
        />
      );

      expect(
        screen.getByText('Autenticación de dos factores')
      ).toBeInTheDocument();
      expect(screen.getByText(/¿Por qué necesitas 2FA?/)).toBeInTheDocument();
      expect(
        screen.getByText(/Protege tu cuenta incluso si alguien obtiene/i)
      ).toBeInTheDocument();
    });

    it('shows requirements', () => {
      render(
        <TwoFactorSetup
          userId="user-123"
          onComplete={jest.fn()}
          onCancel={jest.fn()}
        />
      );

      expect(screen.getByText(/App autenticadora/)).toBeInTheDocument();
      expect(screen.getByText(/Código QR o clave secreta/)).toBeInTheDocument();
    });

    it('has setup and cancel buttons', () => {
      render(
        <TwoFactorSetup
          userId="user-123"
          onComplete={jest.fn()}
          onCancel={jest.fn()}
        />
      );

      expect(screen.getByText('Configurar 2FA')).toBeInTheDocument();
      expect(screen.getByText('Ahora no')).toBeInTheDocument();
    });

    it('calls onCancel when cancel button clicked', () => {
      const onCancel = jest.fn();
      render(
        <TwoFactorSetup
          userId="user-123"
          onComplete={jest.fn()}
          onCancel={onCancel}
        />
      );

      const cancelButton = screen.getByText('Ahora no');
      fireEvent.click(cancelButton);

      expect(onCancel).toHaveBeenCalled();
    });
  });

  describe('Setup step', () => {
    it('fetches 2FA setup when clicking configure', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          secret: 'JBSWY3DPEBLW64TMMQ======',
          qr_code: 'data:image/png;base64,iVBORw0KGgo...',
          message: 'Scan QR code',
        }),
      });

      render(
        <TwoFactorSetup
          userId="user-123"
          onComplete={jest.fn()}
          onCancel={jest.fn()}
        />
      );

      const setupButton = screen.getByText('Configurar 2FA');
      fireEvent.click(setupButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          '/api/v1/auth/2fa/enable',
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('user-123'),
          })
        );
      });
    });

    it('displays QR code after setup', async () => {
      const qrCodeData = 'data:image/png;base64,iVBORw0KGgo...';
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          secret: 'JBSWY3DPEBLW64TMMQ======',
          qr_code: qrCodeData,
          message: 'Scan QR code',
        }),
      });

      render(
        <TwoFactorSetup
          userId="user-123"
          onComplete={jest.fn()}
          onCancel={jest.fn()}
        />
      );

      const setupButton = screen.getByText('Configurar 2FA');
      fireEvent.click(setupButton);

      await waitFor(() => {
        const qrImage = screen.getByAltText('QR Code') as HTMLImageElement;
        expect(qrImage.src).toBe(qrCodeData);
      });
    });

    it('displays manual secret key', async () => {
      const secret = 'JBSWY3DPEBLW64TMMQ======';
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          secret,
          qr_code: 'data:image/png;base64,...',
          message: 'Scan QR code',
        }),
      });

      render(
        <TwoFactorSetup
          userId="user-123"
          onComplete={jest.fn()}
          onCancel={jest.fn()}
        />
      );

      const setupButton = screen.getByText('Configurar 2FA');
      fireEvent.click(setupButton);

      await waitFor(() => {
        expect(screen.getByText(secret)).toBeInTheDocument();
      });
    });

    it('shows code input field', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          secret: 'JBSWY3DPEBLW64TMMQ======',
          qr_code: 'data:image/png;base64,...',
        }),
      });

      render(
        <TwoFactorSetup
          userId="user-123"
          onComplete={jest.fn()}
          onCancel={jest.fn()}
        />
      );

      const setupButton = screen.getByText('Configurar 2FA');
      fireEvent.click(setupButton);

      await waitFor(() => {
        expect(screen.getByPlaceholderText('000000')).toBeInTheDocument();
      });
    });
  });

  describe('Code verification', () => {
    it('only accepts 6 digits', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          secret: 'JBSWY3DPEBLW64TMMQ======',
          qr_code: 'data:image/png;base64,...',
        }),
      });

      render(
        <TwoFactorSetup
          userId="user-123"
          onComplete={jest.fn()}
          onCancel={jest.fn()}
        />
      );

      const setupButton = screen.getByText('Configurar 2FA');
      fireEvent.click(setupButton);

      await waitFor(() => {
        expect(screen.getByPlaceholderText('000000')).toBeInTheDocument();
      });

      const codeInput = screen.getByPlaceholderText('000000') as HTMLInputElement;
      await userEvent.type(codeInput, 'abc123xyz');

      // Should only contain digits
      expect(codeInput.value).toBe('123');
    });

    it('shows error for invalid code', async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            secret: 'JBSWY3DPEBLW64TMMQ======',
            qr_code: 'data:image/png;base64,...',
          }),
        })
        .mockResolvedValueOnce({
          ok: false,
          json: async () => ({ detail: 'Invalid 2FA code' }),
        });

      render(
        <TwoFactorSetup
          userId="user-123"
          onComplete={jest.fn()}
          onCancel={jest.fn()}
        />
      );

      const setupButton = screen.getByText('Configurar 2FA');
      fireEvent.click(setupButton);

      await waitFor(() => {
        const codeInput = screen.getByPlaceholderText('000000');
        expect(codeInput).toBeInTheDocument();
      });

      const codeInput = screen.getByPlaceholderText('000000');
      await userEvent.type(codeInput, '000000');

      const verifyButton = screen.getByText(/Verificar código/);
      fireEvent.click(verifyButton);

      await waitFor(() => {
        expect(screen.getByText('Código 2FA inválido')).toBeInTheDocument();
      });
    });

    it('disables verify button for incomplete code', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          secret: 'JBSWY3DPEBLW64TMMQ======',
          qr_code: 'data:image/png;base64,...',
        }),
      });

      render(
        <TwoFactorSetup
          userId="user-123"
          onComplete={jest.fn()}
          onCancel={jest.fn()}
        />
      );

      const setupButton = screen.getByText('Configurar 2FA');
      fireEvent.click(setupButton);

      await waitFor(() => {
        const verifyButton = screen.getByText(/Verificar código/) as HTMLButtonElement;
        expect(verifyButton.disabled).toBe(true);
      });
    });

    it('enables verify button for 6-digit code', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          secret: 'JBSWY3DPEBLW64TMMQ======',
          qr_code: 'data:image/png;base64,...',
        }),
      });

      render(
        <TwoFactorSetup
          userId="user-123"
          onComplete={jest.fn()}
          onCancel={jest.fn()}
        />
      );

      const setupButton = screen.getByText('Configurar 2FA');
      fireEvent.click(setupButton);

      await waitFor(() => {
        const codeInput = screen.getByPlaceholderText('000000');
        expect(codeInput).toBeInTheDocument();
      });

      const codeInput = screen.getByPlaceholderText('000000');
      await userEvent.type(codeInput, '123456');

      const verifyButton = screen.getByText(/Verificar código/) as HTMLButtonElement;
      expect(verifyButton.disabled).toBe(false);
    });
  });

  describe('Backup step', () => {
    it('shows backup warning after verification', async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            secret: 'JBSWY3DPEBLW64TMMQ======',
            qr_code: 'data:image/png;base64,...',
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ message: '2FA enabled' }),
        });

      render(
        <TwoFactorSetup
          userId="user-123"
          onComplete={jest.fn()}
          onCancel={jest.fn()}
        />
      );

      const setupButton = screen.getByText('Configurar 2FA');
      fireEvent.click(setupButton);

      await waitFor(() => {
        const codeInput = screen.getByPlaceholderText('000000');
        expect(codeInput).toBeInTheDocument();
      });

      const codeInput = screen.getByPlaceholderText('000000');
      await userEvent.type(codeInput, '123456');

      const verifyButton = screen.getByText(/Verificar código/);
      fireEvent.click(verifyButton);

      await waitFor(() => {
        expect(screen.getByText(/Guarda tu clave secreta/)).toBeInTheDocument();
        expect(screen.getByText('JBSWY3DPEBLW64TMMQ======')).toBeInTheDocument();
      });
    });
  });

  describe('Completion', () => {
    it('calls onComplete when setup finishes', async () => {
      const onComplete = jest.fn();
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            secret: 'JBSWY3DPEBLW64TMMQ======',
            qr_code: 'data:image/png;base64,...',
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ message: '2FA enabled' }),
        });

      render(
        <TwoFactorSetup
          userId="user-123"
          onComplete={onComplete}
          onCancel={jest.fn()}
        />
      );

      const setupButton = screen.getByText('Configurar 2FA');
      fireEvent.click(setupButton);

      await waitFor(() => {
        const codeInput = screen.getByPlaceholderText('000000');
        expect(codeInput).toBeInTheDocument();
      });

      const codeInput = screen.getByPlaceholderText('000000');
      await userEvent.type(codeInput, '123456');

      const verifyButton = screen.getByText(/Verificar código/);
      fireEvent.click(verifyButton);

      await waitFor(() => {
        const continueButton = screen.getByText('Continuar');
        expect(continueButton).toBeInTheDocument();
        fireEvent.click(continueButton);
      });

      expect(onComplete).toHaveBeenCalled();
    });
  });
});
