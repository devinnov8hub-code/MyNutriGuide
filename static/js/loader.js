document.addEventListener("DOMContentLoaded", function() {
    const loader = document.getElementById('global-loader');
    const fillWrapper = document.getElementById('fillWrapper');
    const loaderContainer = document.getElementById('loader');

    // Function to start the animation
    function startAnimation() {
        // Reset animation by cloning and replacing the element
        if (fillWrapper) {
            const newWrapper = fillWrapper.cloneNode(true);
            fillWrapper.parentNode.replaceChild(newWrapper, fillWrapper);
            
            // Re-attach event listener
            newWrapper.addEventListener('animationend', () => {
                loaderContainer.classList.add('heartbeat');
            });
            
            // Update reference
            return newWrapper;
        }
    }

    // Initial animation setup
    if (fillWrapper && loaderContainer) {
        fillWrapper.addEventListener('animationend', () => {
            loaderContainer.classList.add('heartbeat');
        });
    }

    // Global function to show loader
    window.showLoader = function() {
        if (loader) {
            loader.classList.remove('hidden');
            loaderContainer.classList.remove('heartbeat');
            
            // Restart the fill animation
            const currentWrapper = document.getElementById('fillWrapper');
            const newWrapper = currentWrapper.cloneNode(true);
            currentWrapper.parentNode.replaceChild(newWrapper, currentWrapper);
            
            newWrapper.addEventListener('animationend', () => {
                loaderContainer.classList.add('heartbeat');
            });
        }
    };

    // Global function to hide loader
    window.hideLoader = function() {
        if (loader) {
            loader.classList.add('hidden');
        }
    };

    // Hide loader after initial load (simulating app load time)
    // You can adjust the timeout or remove it if you want it to disappear immediately after DOM load
    setTimeout(window.hideLoader, 2000); 
});
