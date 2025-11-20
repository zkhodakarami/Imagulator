// DEBUG VERSION - Papaya Image Loader with extensive logging

var params = [];
var papayaViewer = null;

console.log('=== PAPAYA DEBUG SCRIPT LOADED ===');

// Check dependencies on load
window.addEventListener('load', function() {
    console.log('Page loaded, checking dependencies:');
    console.log('- jQuery loaded:', typeof jQuery !== 'undefined');
    console.log('- Papaya loaded:', typeof papaya !== 'undefined');
    console.log('- Papaya.Container:', typeof papaya !== 'undefined' && papaya.Container ? 'YES' : 'NO');
});

document.addEventListener('DOMContentLoaded', function() {
    console.log('=== DOM READY - Setting up image selectors ===');

    var noImageMessage = document.getElementById('noImageMessage');
    var papayaContainer = document.getElementById('papayaViewer');

    console.log('- noImageMessage element:', noImageMessage ? 'FOUND' : 'NOT FOUND');
    console.log('- papayaViewer element:', papayaContainer ? 'FOUND' : 'NOT FOUND');

    var imageSelectors = document.querySelectorAll('.image-selector');
    console.log('- Found', imageSelectors.length, 'image selectors');

    // Log all image URLs
    imageSelectors.forEach(function(item, index) {
        var url = item.getAttribute('url');
        console.log('  Image', index + 1, ':', url);
    });

    imageSelectors.forEach(function(item, index) {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('\n=== IMAGE CLICKED ===');
            console.log('Image index:', index + 1);

            var imageUrl = this.getAttribute('url');
            console.log('Image URL:', imageUrl);

            if (!imageUrl || imageUrl === 'None' || imageUrl === 'null') {
                console.error('ERROR: Invalid URL');
                alert('Invalid image URL: ' + imageUrl);
                return;
            }

            // Test if URL is accessible
            console.log('Testing URL accessibility...');
            fetch(imageUrl, { method: 'HEAD' })
                .then(function(response) {
                    console.log('URL test response status:', response.status);
                    if (response.ok) {
                        console.log('✓ URL is accessible');
                        loadImage(imageUrl);
                    } else {
                        console.error('✗ URL returned error:', response.status);
                        alert('Image URL returned error: ' + response.status);
                    }
                })
                .catch(function(error) {
                    console.error('✗ URL test failed:', error);
                    alert('Cannot access image URL: ' + error.message);
                });

            // Highlight selected
            imageSelectors.forEach(function(el) {
                el.classList.remove('active');
            });
            this.classList.add('active');
        });
    });

    console.log('=== Setup complete ===\n');
});

function loadImage(imageUrl) {
    console.log('\n=== LOADING IMAGE ===');
    console.log('URL:', imageUrl);

    var noImageMessage = document.getElementById('noImageMessage');
    var papayaContainer = document.getElementById('papayaViewer');

    // Hide message, show viewer
    if (noImageMessage) {
        noImageMessage.style.display = 'none';
        console.log('✓ Hidden "select image" message');
    }
    papayaContainer.style.display = 'block';
    console.log('✓ Showing papaya container');

    if (papayaViewer && papayaViewer.viewer) {
        console.log('Using existing viewer...');
        try {
            papayaViewer.viewer.loadImage(imageUrl, false, false);
            console.log('✓ Image loaded into existing viewer');
        } catch (error) {
            console.error('✗ Error loading into existing viewer:', error);
            alert('Error loading image: ' + error.message);
        }
    } else {
        console.log('No viewer exists, initializing new one...');
        initializePapaya(imageUrl);
    }
}

function initializePapaya(imageUrl) {
    console.log('\n=== INITIALIZING PAPAYA ===');

    var papayaContainer = document.getElementById('papayaViewer');

    // Check if Papaya is loaded
    if (typeof papaya === 'undefined') {
        console.error('✗ Papaya library not loaded!');
        alert('Papaya library not loaded. Check /static/papaya/papaya.js');
        return;
    }
    console.log('✓ Papaya library loaded');

    // Clear container
    papayaContainer.innerHTML = '';
    console.log('✓ Cleared container');

    // Create div
    var viewerDiv = document.createElement('div');
    viewerDiv.className = 'papaya';
    viewerDiv.setAttribute('data-params', 'papayaParams');
    papayaContainer.appendChild(viewerDiv);
    console.log('✓ Created viewer div');

    // Set params
    params = [];
    params["papayaParams"] = {
        "images": [imageUrl],
        "kioskMode": true,
        "showControls": true,
        "radiological": true,
        "worldSpace": false,
        "showOrientation": true
    };
    console.log('✓ Configured params:', params["papayaParams"]);

    // Initialize
    setTimeout(function() {
        console.log('Calling papaya.Container.startPapaya()...');
        try {
            papaya.Container.startPapaya();
            console.log('✓ startPapaya() called');

            // Get reference
            setTimeout(function() {
                if (window.papayaContainers && window.papayaContainers.length > 0) {
                    papayaViewer = window.papayaContainers[window.papayaContainers.length - 1];
                    console.log('✓ Got viewer reference');
                    console.log('Viewer object:', papayaViewer);
                } else {
                    console.error('✗ No papayaContainers found');
                }
            }, 500);
        } catch (error) {
            console.error('✗ Error calling startPapaya:', error);
            alert('Error initializing Papaya: ' + error.message);
        }
    }, 100);
}