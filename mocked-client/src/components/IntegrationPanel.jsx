import PropTypes from 'prop-types';

export default function IntegrationPanel({ title = 'Backend integration', items = [], note }) {
  return (
    <div className="integration-panel">
      <h4>{title}</h4>
      {items.length ? (
        <ul>
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : null}
      {note ? <p className="subtle">{note}</p> : null}
    </div>
  );
}

IntegrationPanel.propTypes = {
  title: PropTypes.string,
  items: PropTypes.arrayOf(PropTypes.string),
  note: PropTypes.string,
};
