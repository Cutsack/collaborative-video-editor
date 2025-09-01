import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import App from './App'

// Mock the pages to avoid complex dependencies
jest.mock('./pages/Home', () => () => <div>Home Page</div>)
jest.mock('./pages/Login', () => () => <div>Login Page</div>)
jest.mock('./pages/Register', () => () => <div>Register Page</div>)
jest.mock('./pages/Dashboard', () => () => <div>Dashboard Page</div>)
jest.mock('./pages/ProjectEditor', () => () => <div>Project Editor Page</div>)
jest.mock('./components/Layout', () => ({ children }: { children: React.ReactNode }) => <div>{children}</div>)
jest.mock('./components/ProtectedRoute', () => ({ children }: { children: React.ReactNode }) => <div>{children}</div>)

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  )
}

describe('App', () => {
  test('renders without crashing', () => {
    renderWithRouter(<App />)
    expect(screen.getByText('Home Page')).toBeInTheDocument()
  })
})
