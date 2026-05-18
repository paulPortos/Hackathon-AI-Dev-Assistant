import PropTypes from 'prop-types';

export default function Modal({ isOpen, title, onClose, children }) {
  if (!isOpen) {
    return null;
  }

  return (
    <div className="modal-backdrop">
      <div className="modal">
        <div className="modal-header">
          <h3>{title}</h3>
          <button className="button ghost" type="button" onClick={onClose} style={{ boxShadow: 'none' }}>
            ✕
          </button>
        </div>
        <div className="modal-body">
          {children}
        </div>
      </div>
    </div>
  );
}

Modal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  title: PropTypes.string.isRequired,
  onClose: PropTypes.func.isRequired,
  children: PropTypes.node,
};
