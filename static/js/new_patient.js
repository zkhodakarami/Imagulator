
/**
 * New Patient Form - Image Upload Management
 * Handles dynamic addition/removal of image upload forms
 */

class ImageUploadManager {
    constructor() {
        this.imageCount = 1;
        this.maxImages = 10;
        this.init();
    }

    init() {
        this.bindEvents();
        this.updateRemoveButtonVisibility();
    }

    bindEvents() {
        // Add image button
        const addImageBtn = document.getElementById('add-image-btn');
        if (addImageBtn) {
            addImageBtn.addEventListener('click', () => this.addImageForm());
        }

        // Initial file input change handlers
        this.bindFileInputHandlers();
    }

    bindFileInputHandlers() {
        const fileInputs = document.querySelectorAll('.image-file-input');
        fileInputs.forEach((input, index) => {
            input.addEventListener('change', () => this.updateImageName(index));
        });
    }

    updateImageName(index) {
        const fileInput = document.getElementById(`image_file_${index}`);
        if (fileInput && fileInput.files.length > 0) {
            const fileName = fileInput.files[0].name;
            console.log(`Image ${index + 1} selected: ${fileName}`);

            // Optional: You can add visual feedback here
            this.showFileSelectedFeedback(fileInput, fileName);
        }
    }

    showFileSelectedFeedback(fileInput, fileName) {
        // Add a small visual indicator that file was selected
        const feedbackEl = fileInput.parentNode.querySelector('.file-selected-feedback');
        if (feedbackEl) {
            feedbackEl.remove();
        }

        const feedback = document.createElement('small');
        feedback.className = 'file-selected-feedback text-success';
        feedback.textContent = `Selected: ${fileName}`;
        fileInput.parentNode.appendChild(feedback);
    }

    addImageForm() {
        if (this.imageCount >= this.maxImages) {
            this.showAlert(`Maximum ${this.maxImages} images allowed`, 'warning');
            return;
        }

        const container = document.getElementById('image-upload-container');
        const newIndex = this.imageCount;

        const newForm = this.createImageFormElement(newIndex);
        container.appendChild(newForm);

        this.imageCount++;
        this.updateRemoveButtonVisibility();
        this.bindNewFormHandlers(newIndex);

        // Scroll to the new form
        newForm.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    createImageFormElement(index) {
        const formDiv = document.createElement('div');
        formDiv.className = 'image-upload-form';
        formDiv.id = `image-form-${index}`;

        formDiv.innerHTML = this.getImageFormHTML(index);
        return formDiv;
    }

    getImageFormHTML(index) {
        return `
            <div class="card mb-3">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h6 class="mb-0">Image #${index + 1}</h6>
                    <button type="button" class="btn btn-sm btn-outline-danger remove-image" 
                            onclick="imageUploadManager.removeImageForm(${index})">
                        Remove
                    </button>
                </div>
                <div class="card-body">
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <label for="mri_date_${index}" class="form-label">MRI Date *</label>
                            <input type="date" class="form-control" id="mri_date_${index}" name="mri_date_${index}">
                        </div>
                        <div class="col-md-6">
                            <label for="modality_${index}" class="form-label">Modality *</label>
                            <select class="form-select" id="modality_${index}" name="modality_${index}">
                                <option value="">Select modality...</option>
                                <option value="CT">CT</option>
                                <option value="T1">T1</option>
                                <option value="T2">T2</option>
                                <option value="Flair">FLAIR</option>
                                <option value="Pet">PET</option>
                            </select>
                        </div>
                    </div>

                    <div class="mb-3">
                        <label for="image_file_${index}" class="form-label">Select Image File *</label>
                        <input type="file" class="form-control image-file-input" id="image_file_${index}" name="image_file_${index}"
                               accept=".nii,.nii.gz,.dcm,.jpg,.jpeg,.png">
                        <div class="form-text">
                            Upload MRI image (NIFTI, DICOM, or standard image formats).
                        </div>
                    </div>

                    <div class="mb-3">
                        <label for="image_notes_${index}" class="form-label">Image Notes</label>
                        <textarea class="form-control" id="image_notes_${index}" name="image_notes_${index}"
                                  rows="2" placeholder="Additional notes about this image"></textarea>
                    </div>
                </div>
            </div>
        `;
    }

    bindNewFormHandlers(index) {
        const fileInput = document.getElementById(`image_file_${index}`);
        if (fileInput) {
            fileInput.addEventListener('change', () => this.updateImageName(index));
        }
    }

    removeImageForm(index) {
        const formToRemove = document.getElementById(`image-form-${index}`);
        if (!formToRemove) return;

        // Confirm removal if form has data
        if (this.formHasData(formToRemove)) {
            if (!confirm('This image form contains data. Are you sure you want to remove it?')) {
                return;
            }
        }

        formToRemove.remove();
        this.imageCount--;

        this.updateRemoveButtonVisibility();
        this.renumberForms();

        this.showAlert('Image form removed', 'info');
    }

    formHasData(formElement) {
        const inputs = formElement.querySelectorAll('input, select, textarea');
        return Array.from(inputs).some(input => {
            if (input.type === 'file') {
                return input.files && input.files.length > 0;
            }
            return input.value.trim() !== '';
        });
    }

    updateRemoveButtonVisibility() {
        const removeButtons = document.querySelectorAll('.remove-image');
        const firstFormRemoveBtn = document.querySelector('#image-form-0 .remove-image');

        if (firstFormRemoveBtn) {
            firstFormRemoveBtn.style.display = this.imageCount > 1 ? 'inline-block' : 'none';
        }
    }

    renumberForms() {
        const forms = document.querySelectorAll('.image-upload-form');
        forms.forEach((form, index) => {
            const header = form.querySelector('.card-header h6');
            if (header) {
                header.textContent = `Image #${index + 1}`;
            }
        });
    }

    showAlert(message, type = 'info') {
        // Create a temporary alert
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.setAttribute('role', 'alert');
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Insert at the top of the container
        const container = document.querySelector('.container.mt-4');
        const existingAlerts = container.querySelector('.alert');

        if (existingAlerts) {
            container.insertBefore(alertDiv, existingAlerts);
        } else {
            container.insertBefore(alertDiv, container.firstChild.nextSibling);
        }

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    // Form validation helper
    validateImageForms() {
        const forms = document.querySelectorAll('.image-upload-form');
        let isValid = true;
        const errors = [];

        forms.forEach((form, index) => {
            const mriDate = form.querySelector(`[name="mri_date_${index}"]`);
            const modality = form.querySelector(`[name="modality_${index}"]`);
            const imageFile = form.querySelector(`[name="image_file_${index}"]`);

            // Only validate if any field in the form has data
            const hasAnyData = [mriDate, modality, imageFile].some(field => {
                if (field.type === 'file') return field.files && field.files.length > 0;
                return field.value.trim() !== '';
            });

            if (hasAnyData) {
                if (!mriDate.value) {
                    errors.push(`Image #${index + 1}: MRI Date is required`);
                    isValid = false;
                }
                if (!modality.value) {
                    errors.push(`Image #${index + 1}: Modality is required`);
                    isValid = false;
                }
                if (!imageFile.files || imageFile.files.length === 0) {
                    errors.push(`Image #${index + 1}: Image file is required`);
                    isValid = false;
                }
            }
        });

        if (!isValid) {
            this.showAlert('Please fix the following errors:<br>• ' + errors.join('<br>• '), 'danger');
        }

        return isValid;
    }
}

// Global instance
let imageUploadManager;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    imageUploadManager = new ImageUploadManager();

    // Form submission validation
    const form = document.querySelector('form[action="/new-patient"]');
    if (form) {
        form.addEventListener('submit', function(e) {
            const action = e.submitter ? e.submitter.value : 'patient_only';

            if (action === 'patient_and_images') {
                if (!imageUploadManager.validateImageForms()) {
                    e.preventDefault();
                    return false;
                }
            }
        });
    }
});