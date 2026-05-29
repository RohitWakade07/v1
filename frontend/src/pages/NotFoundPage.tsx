import { Link } from 'react-router-dom'

const NotFoundPage = () => (
  <div className="flex min-h-screen flex-col items-center justify-center bg-navy-950 px-4 text-center">
    <h1 className="font-display text-3xl font-semibold text-text-primary">
      Page not found
    </h1>
    <p className="mt-2 text-sm text-text-secondary">
      The page you are looking for does not exist.
    </p>
    <Link
      to="/"
      className="mt-4 rounded-lg bg-accent-blue px-4 py-2 text-sm font-medium text-white"
    >
      Return to Dashboard
    </Link>
  </div>
)

export default NotFoundPage
