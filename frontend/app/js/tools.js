/**
 * tools.js
 * Powers the Calculators page with various mineral industry calculators
 *
 * This file contains:
 * - ODI (Overriding Royalty Interest) calculator
 * - NRI (Net Revenue Interest) calculator
 * - Bonus calculator
 * - Royalty calculator
 * - Acreage calculator
 */

/**
 * calculateODI()
 * Calculates Overriding Royalty Interest as numerator / denominator
 */
function calculateODI() {
    const num = parseFloat(document.getElementById('odi-numerator').value) || 0;
    const denom = parseFloat(document.getElementById('odi-denominator').value) || 1;
    const result = denom > 0 ? (num / denom) : 0;
    document.getElementById('odi-value').textContent = result.toFixed(8);
    document.getElementById('odi-result').classList.remove('hidden');
}

/**
 * calculateNRI()
 * Calculates Net Revenue Interest with gross MI and royalty deduction
 */
function calculateNRI() {
    const mi = parseFloat(document.getElementById('nri-gross').value) || 0;
    const royalty = parseFloat(document.getElementById('nri-royalty').value) || 0;
    const acres = 640; // standard section
    const nri = mi * (1 - royalty / 100);
    const nma = mi * acres;
    document.getElementById('nri-value').textContent = nri.toFixed(8);
    document.getElementById('nri-result').classList.remove('hidden');
}

/**
 * calculateBonus()
 * Calculates bonus value from acreage and per-acre rate
 */
function calculateBonus() {
    const acres = parseFloat(document.getElementById('bonus-acreage').value) || 0;
    const mi = parseFloat(document.getElementById('bonus-per-acre').value) || 0;
    // bonus-per-acre is actually $/acre rate
    const nma = acres * mi;
    const total = nma;
    document.getElementById('bonus-value').textContent = formatCurrency(total);
    document.getElementById('bonus-result').classList.remove('hidden');
}

/**
 * calculateRoyalty()
 * Calculates royalty payment from NRI percentage and revenue
 */
function calculateRoyalty() {
    const nri = parseFloat(document.getElementById('royalty-nri').value) || 0;
    const revenue = parseFloat(document.getElementById('royalty-revenue').value) || 0;
    const royalty = (nri / 100) * revenue;
    document.getElementById('royalty-value').textContent = formatCurrency(royalty);
    document.getElementById('royalty-result').classList.remove('hidden');
}

/**
 * calculateAcreage()
 * Calculates total acreage from sections and additional acres
 */
function calculateAcreage() {
    const sections = parseFloat(document.getElementById('acreage-sections').value) || 0;
    const additional = parseFloat(document.getElementById('acreage-additional').value) || 0;
    const total = (sections * 640) + additional;
    document.getElementById('acreage-value').textContent = total.toFixed(2) + ' acres';
    document.getElementById('acreage-result').classList.remove('hidden');
}
