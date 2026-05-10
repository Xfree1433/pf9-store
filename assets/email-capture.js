/**
 * PF9 storefront email capture modal.
 *
 * Triggers:
 *   - Desktop: exit-intent (mouse moves toward top of viewport, signaling
 *     the user is about to close the tab or click the address bar)
 *   - Mobile: scroll past 60% of the page (exit-intent doesn't fire on mobile)
 *   - Both: minimum 8 seconds on page before any trigger fires
 *
 * Skip conditions:
 *   - sessionStorage 'pf9_email_modal_shown' — already shown this session
 *   - localStorage 'pf9_email_captured' — already captured forever
 *   - localStorage 'pf9_email_dismissed_until' — within 7-day cooldown after dismissal
 *
 * On submit: POSTs to /demo-request with product='STOREFRONT (email capture)' and
 * a message naming the source page. Lead lands in HubSpot Contacts (no specific
 * list assignment — _hubspot_list_for_product returns None for this tag).
 *
 * GA4 events fired:
 *   - email_capture_modal_shown (with source_page)
 *   - email_capture_modal_dismiss (with source_page)
 *   - email_capture_submit (with source_page)
 *
 * Loaded via <script src="/assets/email-capture.js" defer></script> on storefront,
 * vertical landing pages, and comparison pages. Not loaded on tools/, contact, or
 * legal pages (they have their own capture or aren't conversion surfaces).
 */
(function () {
    'use strict';

    if (localStorage.getItem('pf9_email_captured') === '1') return;
    var dismissedUntil = parseInt(localStorage.getItem('pf9_email_dismissed_until') || '0', 10);
    if (Date.now() < dismissedUntil) return;
    if (sessionStorage.getItem('pf9_email_modal_shown') === '1') return;

    var API = 'https://app.plainspokenfoundrynine.com/store-api/demo-request';
    var MIN_TIME_ON_PAGE_MS = 8000;
    var DISMISS_COOLDOWN_MS = 7 * 24 * 60 * 60 * 1000;
    var pageLoadAt = Date.now();
    var shown = false;
    var scrollFired = false;

    function readyToShow() {
        return Date.now() - pageLoadAt >= MIN_TIME_ON_PAGE_MS;
    }

    function show() {
        if (shown || !readyToShow()) return;
        shown = true;
        sessionStorage.setItem('pf9_email_modal_shown', '1');

        var overlay = document.createElement('div');
        overlay.id = 'pf9-email-modal';
        overlay.innerHTML =
            '<div class="fixed inset-0 z-50 flex items-center justify-center p-4" style="background:rgba(0,0,0,0.5);backdrop-filter:blur(4px);">' +
            '  <div class="bg-white rounded-2xl shadow-xl w-full p-6 sm:p-8 relative" style="max-width:28rem;">' +
            '    <button id="pf9-em-close" class="absolute top-4 right-4 text-gray-400 hover:text-gray-600" aria-label="Close">' +
            '      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>' +
            '    </button>' +
            '    <h3 class="text-xl font-bold mb-2">Before you go — keep tabs on PF9?</h3>' +
            '    <p class="text-sm text-gray-600 mb-6">One short email a month. What we shipped, what we learned. Unsubscribe in two clicks.</p>' +
            '    <form id="pf9-em-form" class="flex flex-col gap-3" novalidate>' +
            '      <input id="pf9-em-email" type="email" required autocomplete="email" placeholder="you@example.com" class="w-full px-4 py-3 border border-gray-300 rounded-lg text-sm" style="outline:none;" />' +
            '      <button type="submit" id="pf9-em-submit" class="bg-black text-white font-semibold py-3 px-4 rounded-lg text-sm hover:bg-gray-800 transition-colors">Send it</button>' +
            '    </form>' +
            '    <p id="pf9-em-msg" class="text-sm mt-3 hidden"></p>' +
            '    <button id="pf9-em-decline" class="text-xs text-gray-400 hover:text-gray-600 mt-4 underline" style="background:none;border:none;cursor:pointer;padding:0;">No thanks, just browsing</button>' +
            '  </div>' +
            '</div>';
        document.body.appendChild(overlay);

        var emailInput = document.getElementById('pf9-em-email');
        if (emailInput) {
            setTimeout(function () { try { emailInput.focus(); } catch (e) {} }, 50);
        }

        if (typeof gtag === 'function') {
            gtag('event', 'email_capture_modal_shown', { source_page: location.pathname });
        }

        document.getElementById('pf9-em-close').addEventListener('click', dismiss);
        document.getElementById('pf9-em-decline').addEventListener('click', dismiss);
        document.getElementById('pf9-em-form').addEventListener('submit', submit);
        document.addEventListener('keydown', escClose);
    }

    function escClose(e) {
        if (e.key === 'Escape') dismiss();
    }

    function dismiss() {
        var overlay = document.getElementById('pf9-email-modal');
        if (overlay) overlay.remove();
        document.removeEventListener('keydown', escClose);
        localStorage.setItem('pf9_email_dismissed_until', String(Date.now() + DISMISS_COOLDOWN_MS));
        if (typeof gtag === 'function') {
            gtag('event', 'email_capture_modal_dismiss', { source_page: location.pathname });
        }
    }

    function submit(e) {
        e.preventDefault();
        var email = (document.getElementById('pf9-em-email').value || '').trim();
        var msg = document.getElementById('pf9-em-msg');
        var btn = document.getElementById('pf9-em-submit');
        if (!email || email.indexOf('@') < 0) return;

        btn.textContent = 'Sending...';
        btn.disabled = true;

        fetch(API, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: email.split('@')[0],
                email: email,
                company: '',
                message: 'Email capture modal on ' + location.pathname,
                product: 'STOREFRONT (email capture)'
            })
        }).then(function (r) {
            if (r.ok) {
                msg.textContent = "Done — we won't spam you.";
                msg.className = 'text-sm mt-3 text-green-600';
                msg.classList.remove('hidden');
                document.getElementById('pf9-em-form').classList.add('hidden');
                document.getElementById('pf9-em-decline').classList.add('hidden');
                localStorage.setItem('pf9_email_captured', '1');
                if (typeof gtag === 'function') {
                    gtag('event', 'email_capture_submit', { source_page: location.pathname });
                }
                setTimeout(function () {
                    var overlay = document.getElementById('pf9-email-modal');
                    if (overlay) overlay.remove();
                    document.removeEventListener('keydown', escClose);
                }, 1800);
            } else {
                msg.textContent = "Couldn't send. Try email support@plainspokenfoundrynine.com instead?";
                msg.className = 'text-sm mt-3 text-red-600';
                msg.classList.remove('hidden');
                btn.textContent = 'Send it';
                btn.disabled = false;
            }
        }).catch(function () {
            msg.textContent = 'Connection issue. Try again or email support@plainspokenfoundrynine.com.';
            msg.className = 'text-sm mt-3 text-red-600';
            msg.classList.remove('hidden');
            btn.textContent = 'Send it';
            btn.disabled = false;
        });
    }

    // Desktop exit-intent
    if (window.matchMedia && window.matchMedia('(min-width: 768px)').matches) {
        document.addEventListener('mouseout', function (e) {
            if (!e.relatedTarget && e.clientY < 20) show();
        });
    }

    // Mobile scroll-depth trigger
    if (window.matchMedia && window.matchMedia('(max-width: 767px)').matches) {
        window.addEventListener('scroll', function () {
            if (scrollFired || shown) return;
            var scrollPos = window.scrollY + window.innerHeight;
            var docHeight = document.documentElement.scrollHeight;
            if (docHeight > 0 && scrollPos / docHeight > 0.6) {
                scrollFired = true;
                show();
            }
        }, { passive: true });
    }
})();
