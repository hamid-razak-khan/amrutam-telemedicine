import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { Login } from '../pages/auth/Login';
import { Register } from '../pages/auth/Register';
import { AuthProvider } from '../context/AuthContext';

describe('Frontend Authentication Tests', () => {
  it('renders login form with email and password fields', () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <Login />
        </BrowserRouter>
      </AuthProvider>
    );

    expect(screen.getByPlaceholderText(/name@example.com/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/••••••••/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign In to Platform/i })).toBeInTheDocument();
  });

  it('validates password mismatch during patient registration', async () => {
    render(
      <BrowserRouter>
        <Register />
      </BrowserRouter>
    );

    const firstNameInput = screen.getByPlaceholderText(/Aarav/i);
    const lastNameInput = screen.getByPlaceholderText(/Verma/i);
    const emailInput = screen.getByPlaceholderText(/name@example.com/i);
    const passInputs = screen.getAllByPlaceholderText(/••••••••/i);
    const submitBtn = screen.getByRole('button', { name: /Complete Registration/i });

    fireEvent.change(firstNameInput, { target: { value: 'Aarav' } });
    fireEvent.change(lastNameInput, { target: { value: 'Kumar' } });
    fireEvent.change(emailInput, { target: { value: 'patient@example.com' } });
    fireEvent.change(passInputs[0], { target: { value: 'Password123!' } });
    fireEvent.change(passInputs[1], { target: { value: 'DifferentPass123!' } });

    fireEvent.click(submitBtn);

    expect(await screen.findByText(/Password and confirmation password do not match/i)).toBeInTheDocument();
  });
});
