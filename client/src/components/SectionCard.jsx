import PropTypes from 'prop-types';

export default function SectionCard({ title, eyebrow, actions, children }) {
  return (
    <section className="section-card">
      {eyebrow ? <div className="pill">{eyebrow}</div> : null}
      {title ? <h3>{title}</h3> : null}
      {children}
      {actions ? <div className="inline-actions">{actions}</div> : null}
    </section>
  );
}

SectionCard.propTypes = {
  title: PropTypes.string,
  eyebrow: PropTypes.string,
  actions: PropTypes.node,
  children: PropTypes.node,
};
