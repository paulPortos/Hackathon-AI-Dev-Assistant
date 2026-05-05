import PropTypes from 'prop-types';

export default function Modal({ isOpen, title, onClose, children }) {
  if (!isOpen) {
    return null;
  }

  return (
    <dialog className="modal-backdrop" open>
      <div className="modal">
        <div className="modal-header">
          <h3>{title}</h3>
          <button className="button ghost" type="button" onClick={onClose}>
            Close
          </button>
        </div>
        {children}
      </div>
    </dialog>
  );
}

Modal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  title: PropTypes.string.isRequired,
  onClose: PropTypes.func.isRequired,
  children: PropTypes.node,
};
