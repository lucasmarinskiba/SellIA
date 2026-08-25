import React from 'react';
import { render, screen } from '@testing-library/react';
import { PasswordStrengthIndicator } from './PasswordStrengthIndicator';

describe('PasswordStrengthIndicator', () => {
  describe('Password strength levels', () => {
    it('shows very weak for empty password', () => {
      render(<PasswordStrengthIndicator password="" />);
      // Should not render anything for empty password
      expect(screen.queryByText(/Seguridad/)).not.toBeInTheDocument();
    });

    it('shows very weak for short password', () => {
      render(<PasswordStrengthIndicator password="abc" />);
      expect(screen.getByText('Muy débil')).toBeInTheDocument();
    });

    it('shows weak for password with only lowercase', () => {
      render(<PasswordStrengthIndicator password="abcdefgh" />);
      expect(screen.getByText('Débil')).toBeInTheDocument();
    });

    it('shows regular for password with lowercase + uppercase', () => {
      render(<PasswordStrengthIndicator password="Abcdefgh" />);
      expect(screen.getByText('Regular')).toBeInTheDocument();
    });

    it('shows good for password with lowercase + uppercase + digit', () => {
      render(<PasswordStrengthIndicator password="Abcdefgh1" />);
      expect(screen.getByText('Buena')).toBeInTheDocument();
    });

    it('shows strong for password with all requirements', () => {
      render(<PasswordStrengthIndicator password="Abcdefgh1@" />);
      expect(screen.getByText('Fuerte')).toBeInTheDocument();
    });

    it('shows very strong for complex password', () => {
      render(<PasswordStrengthIndicator password="SecurePass123@#$" />);
      expect(screen.getByText('Muy fuerte')).toBeInTheDocument();
    });
  });

  describe('Requirements validation', () => {
    it('checks minimum length requirement', () => {
      render(<PasswordStrengthIndicator password="short1!" />);
      expect(screen.queryByText('Mínimo 8 caracteres')).not.toBeInTheDocument();

      render(<PasswordStrengthIndicator password="longpass1!" />);
      expect(screen.getByText('Mínimo 8 caracteres')).toBeInTheDocument();
    });

    it('checks uppercase requirement', () => {
      render(<PasswordStrengthIndicator password="lowercase123@" />);
      expect(screen.getByText('Mayúscula (A-Z)')).toBeInTheDocument();
    });

    it('checks lowercase requirement', () => {
      render(<PasswordStrengthIndicator password="UPPERCASE123@" />);
      expect(screen.getByText('Minúscula (a-z)')).toBeInTheDocument();
    });

    it('checks digit requirement', () => {
      render(<PasswordStrengthIndicator password="NoDigits@pass" />);
      expect(screen.getByText('Número (0-9)')).toBeInTheDocument();
    });

    it('checks special character requirement', () => {
      render(<PasswordStrengthIndicator password="NoSpecial123" />);
      expect(screen.getByText('Símbolo especial (@+-!#$%)')).toBeInTheDocument();
    });

    it('accepts all special characters', () => {
      const specialChars = '@+-!#$%';
      specialChars.split('').forEach((char) => {
        const { unmount } = render(
          <PasswordStrengthIndicator password={`Pass123${char}`} />
        );
        expect(screen.getByText('Símbolo especial (@+-!#$%)')).toBeInTheDocument();
        unmount();
      });
    });
  });

  describe('Strength change callback', () => {
    it('calls onStrengthChange with correct score', () => {
      const onStrengthChange = jest.fn();
      const { rerender } = render(
        <PasswordStrengthIndicator
          password="weak"
          onStrengthChange={onStrengthChange}
        />
      );

      expect(onStrengthChange).toHaveBeenCalledWith(1);

      rerender(
        <PasswordStrengthIndicator
          password="SecurePass123@"
          onStrengthChange={onStrengthChange}
        />
      );

      expect(onStrengthChange).toHaveBeenCalledWith(5);
    });
  });

  describe('Security tips', () => {
    it('shows tips for weak passwords', () => {
      render(<PasswordStrengthIndicator password="weak123" />);
      expect(screen.getByText(/Consejos de seguridad/)).toBeInTheDocument();
    });

    it('shows success message for strong passwords', () => {
      render(<PasswordStrengthIndicator password="SecurePass123@" />);
      expect(screen.getByText(/Contraseña segura/)).toBeInTheDocument();
    });
  });

  describe('Color indicators', () => {
    it('uses red for very weak passwords', () => {
      const { container } = render(
        <PasswordStrengthIndicator password="weak" />
      );
      const strengthBar = container.querySelector('.bg-red-600');
      expect(strengthBar).toBeInTheDocument();
    });

    it('uses green for very strong passwords', () => {
      const { container } = render(
        <PasswordStrengthIndicator password="SecurePass123@#$" />
      );
      const strengthBar = container.querySelector('.bg-green-600');
      expect(strengthBar).toBeInTheDocument();
    });
  });
});
