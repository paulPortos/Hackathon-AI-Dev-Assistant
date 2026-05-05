import { Link } from 'react-router-dom';

import SectionCard from '../components/SectionCard';

export default function NotFoundPage() {
  return (
    <SectionCard title="Page not found" eyebrow="404">
      <p>The route does not exist in the mocked client.</p>
      <Link className="button" to="/">
        Back to home
      </Link>
    </SectionCard>
  );
}
