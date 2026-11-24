// Copie fidèle de src/utils/parsing.ts du plugin Chrome (ray-harvey-chrome-plugin), compilée en JavaScript.
// Le robot l'injecte dans les pages Matrix : parse() lit une fiche, parseBrokerPage() lit la page des courtiers.
// Quand le plugin change, recopier ces deux fonctions ici pour que le robot lise exactement la même chose.

function parse() {
    function parseCentrisNo() {
        const spans = document.querySelectorAll('span.heading2, span.heading1, span.label');
        for (let i = 0; i < spans.length; i++) {
            if (!(spans[i].textContent || '').trim().includes('No Centris'))
                continue;
            const td = spans[i].closest('td');
            if (!td)
                continue;
            const nextTd = td.nextElementSibling;
            if (!nextTd)
                continue;
            const numMatch = (nextTd.textContent || '').match(/\d{5,}/);
            if (numMatch)
                return numMatch[0];
        }
        return '';
    }
    const parseCurrency = (value) => {
        const cleaned = value
            .replace(/\$/g, '')
            .replace(/,/g, '')
            .replace(/[\s\u00a0]/g, '');
        const parsed = parseFloat(cleaned);
        return isNaN(parsed) ? null : parsed;
    };
    const extractNumber = (value) => {
        const match = value.replace(/[\s\u00a0]/g, '').match(/\d+/);
        return match ? parseInt(match[0]) : null;
    };
    function valueAfterLabel(labelText) {
        var _a;
        const spans = document.querySelectorAll('span.label, span.field');
        for (let i = 0; i < spans.length; i++) {
            const span = spans[i];
            if (((_a = span.textContent) === null || _a === void 0 ? void 0 : _a.trim()) !== labelText)
                continue;
            const td = span.closest('td');
            if (!td)
                continue;
            const nextTd = td.nextElementSibling;
            if (!nextTd)
                continue;
            const valEl = nextTd.querySelector('span.field, span.formula, span.label, span.wrapped-field');
            const val = ((valEl === null || valEl === void 0 ? void 0 : valEl.textContent) || nextTd.textContent || '').trim();
            if (val)
                return val;
        }
        return '';
    }
    function contentAfterHeading(headingText) {
        var _a, _b;
        const headings = document.querySelectorAll('span.heading2, span.heading1');
        for (let i = 0; i < headings.length; i++) {
            if (((_a = headings[i].textContent) === null || _a === void 0 ? void 0 : _a.trim()) !== headingText)
                continue;
            const tr = headings[i].closest('tr');
            if (!tr)
                continue;
            const nextTr = tr.nextElementSibling;
            if (!nextTr)
                continue;
            const content = nextTr.querySelector('span.formula, span.field, span.wrapped-field');
            return ((_b = content === null || content === void 0 ? void 0 : content.textContent) === null || _b === void 0 ? void 0 : _b.trim()) || '';
        }
        return '';
    }
    function parseHeader() {
        var _a, _b, _c;
        const postalCodeRegex = /^[A-Z]\d[A-Z]\s?\d[A-Z]\d$/;
        const allFieldSpans = document.querySelectorAll('span.field');
        let postalCodeSpan = null;
        for (let i = 0; i < allFieldSpans.length; i++) {
            if (postalCodeRegex.test(((_a = allFieldSpans[i].textContent) === null || _a === void 0 ? void 0 : _a.trim()) || '')) {
                postalCodeSpan = allFieldSpans[i];
                break;
            }
        }
        if (!postalCodeSpan) {
            return { address: '', postalCode: '', askingPrice: null };
        }
        const postalCode = ((_b = postalCodeSpan.textContent) === null || _b === void 0 ? void 0 : _b.trim()) || '';
        const dynamicClass = Array.from(postalCodeSpan.classList).find(c => /^d\d+m\d+$/.test(c));
        if (!dynamicClass) {
            return { address: '', postalCode, askingPrice: null };
        }
        const sameClassSpans = document.querySelectorAll(`span.${dynamicClass}`);
        let askingPrice = null;
        let address = '';
        for (let i = 0; i < sameClassSpans.length; i++) {
            const text = ((_c = sameClassSpans[i].textContent) === null || _c === void 0 ? void 0 : _c.trim()) || '';
            if (!askingPrice && text.includes('$') && /\d/.test(text)) {
                askingPrice = parseCurrency(text);
            }
            else if (!address && /^\d/.test(text) && !text.includes('$') && text.length > 3) {
                address = text;
            }
        }
        return { address, postalCode, askingPrice };
    }
    const LEASE_LABELS = [
        'Numéro log.', 'Fin de bail', 'Nbre pièces', 'Loyer mensuel',
        'Nbre chambres', 'Nbre SDB + SE', 'Nbre SDB', 'Inst. lav/séch.',
        'Nbre stationnements', 'Inclus selon bail', 'Exclus selon bail',
        'Valeur Locative', 'Particularités',
    ];
    function assignLeaseField(lease, labelText, val) {
        if (labelText.includes('Numéro log'))
            lease.unitNumber = val;
        else if (labelText.includes('Fin de bail'))
            lease.leaseEnd = val;
        else if (labelText === 'Nbre pièces' || (labelText.includes('Nbre pièces') && !labelText.includes('chambres')))
            lease.rooms = extractNumber(val);
        else if (labelText.includes('Loyer mensuel'))
            lease.monthlyRent = parseCurrency(val);
        else if (labelText.includes('Nbre chambres'))
            lease.bedrooms = extractNumber(val);
        else if (labelText.includes('SDB'))
            lease.bathrooms = val;
        else if (labelText.includes('lav') && labelText.includes('séch'))
            lease.washerDryer = val;
        else if (labelText.includes('stationnements'))
            lease.parking = val;
        else if (labelText.includes('Inclus selon bail'))
            lease.included = val;
        else if (labelText.includes('Exclus selon bail'))
            lease.excluded = val;
        else if (labelText.toLowerCase().includes('valeur locative'))
            lease.rentalValue = val;
        else if (labelText.includes('Particularités'))
            lease.details = val;
    }
    function buildLease(partial) {
        var _a, _b, _c;
        if (!partial.unitNumber)
            return null;
        return {
            unitNumber: partial.unitNumber || '',
            leaseEnd: partial.leaseEnd || '',
            rooms: (_a = partial.rooms) !== null && _a !== void 0 ? _a : null,
            monthlyRent: (_b = partial.monthlyRent) !== null && _b !== void 0 ? _b : null,
            bedrooms: (_c = partial.bedrooms) !== null && _c !== void 0 ? _c : null,
            bathrooms: partial.bathrooms || '',
            washerDryer: partial.washerDryer || '',
            parking: partial.parking || '',
            included: partial.included || '',
            excluded: partial.excluded || '',
            rentalValue: partial.rentalValue || '',
            details: partial.details || '',
        };
    }
    function parseLeases() {
        var _a, _b;
        const leases = [];
        const allLabels = document.querySelectorAll('span.label');
        const seen = new Set();
        for (let i = 0; i < allLabels.length; i++) {
            if (((_a = allLabels[i].textContent) === null || _a === void 0 ? void 0 : _a.trim()) !== 'Numéro log.')
                continue;
            const container = allLabels[i].closest('div.multiLineDisplay') ||
                allLabels[i].closest('table.DisplayRow');
            if (!container || seen.has(container))
                continue;
            seen.add(container);
            const lease = {};
            const labels = container.querySelectorAll('span.label');
            for (let j = 0; j < labels.length; j++) {
                const text = ((_b = labels[j].textContent) === null || _b === void 0 ? void 0 : _b.trim()) || '';
                const td = labels[j].closest('td');
                if (!td)
                    continue;
                const nextTd = td.nextElementSibling;
                if (!nextTd)
                    continue;
                const valEl = nextTd.querySelector('span.field, span.wrapped-field');
                const val = ((valEl === null || valEl === void 0 ? void 0 : valEl.textContent) || nextTd.textContent || '').trim().replace(/\s+/g, ' ');
                assignLeaseField(lease, text, val);
            }
            const built = buildLease(lease);
            if (built)
                leases.push(built);
        }
        return leases;
    }
    function parseLeasesFallback() {
        var _a, _b, _c;
        const leases = [];
        const seen = new Set();
        const allTds = document.querySelectorAll('td');
        for (let i = 0; i < allTds.length; i++) {
            const td = allTds[i];
            const tdText = ((_a = td.textContent) === null || _a === void 0 ? void 0 : _a.trim().replace(/\s+/g, ' ')) || '';
            if (tdText !== 'Numéro log.')
                continue;
            const table = td.closest('table');
            if (!table || seen.has(table))
                continue;
            const rowCount = table.querySelectorAll(':scope > tbody > tr, :scope > tr').length;
            if (rowCount > 15)
                continue;
            seen.add(table);
            const lease = {};
            const rows = table.querySelectorAll(':scope > tbody > tr, :scope > tr');
            for (let r = 0; r < rows.length; r++) {
                const cells = rows[r].querySelectorAll(':scope > td');
                for (let c = 0; c < cells.length - 1; c++) {
                    const labelText = ((_b = cells[c].textContent) === null || _b === void 0 ? void 0 : _b.trim().replace(/\s+/g, ' ')) || '';
                    const isKnown = LEASE_LABELS.some(l => labelText.includes(l));
                    if (!isKnown)
                        continue;
                    const val = (((_c = cells[c + 1]) === null || _c === void 0 ? void 0 : _c.textContent) || '').trim().replace(/\s+/g, ' ');
                    assignLeaseField(lease, labelText, val);
                    c++;
                }
            }
            const built = buildLease(lease);
            if (built)
                leases.push(built);
        }
        return leases;
    }
    function parseLeasesTabular() {
        var _a, _b, _c, _d, _e, _f, _g;
        const leases = [];
        const unitTypePattern = /\d+\s*(1\/2|½)/;
        const allRows = document.querySelectorAll('tr');
        for (let r = 0; r < allRows.length; r++) {
            const cells = allRows[r].querySelectorAll(':scope > td');
            if (cells.length < 4 || cells.length > 8)
                continue;
            const typeText = (cells[0].textContent || '').trim().replace(/\s+/g, ' ');
            if (!unitTypePattern.test(typeText))
                continue;
            const totalUnits = extractNumber(((_a = cells[1]) === null || _a === void 0 ? void 0 : _a.textContent) || '');
            if (totalUnits === null)
                continue;
            let hasCurrency = false;
            for (let c = 2; c < cells.length; c++) {
                if ((cells[c].textContent || '').includes('$')) {
                    hasCurrency = true;
                    break;
                }
            }
            if (!hasCurrency)
                continue;
            const occupiedUnits = (_c = extractNumber(((_b = cells[2]) === null || _b === void 0 ? void 0 : _b.textContent) || '')) !== null && _c !== void 0 ? _c : 0;
            const occupiedRevenue = parseCurrency(((_d = cells[3]) === null || _d === void 0 ? void 0 : _d.textContent) || '');
            const vacantUnits = cells.length > 4 ? ((_f = extractNumber(((_e = cells[4]) === null || _e === void 0 ? void 0 : _e.textContent) || '')) !== null && _f !== void 0 ? _f : 0) : 0;
            const vacantRevenue = cells.length > 5 ? parseCurrency(((_g = cells[5]) === null || _g === void 0 ? void 0 : _g.textContent) || '') : null;
            const rooms = parseInt(typeText) || null;
            const perUnitOccRent = (occupiedRevenue !== null && occupiedUnits > 0)
                ? Math.round(occupiedRevenue / occupiedUnits) : null;
            const perUnitVacRent = (vacantRevenue !== null && vacantUnits > 0)
                ? Math.round(vacantRevenue / vacantUnits) : null;
            let unitIndex = 1;
            for (let u = 0; u < occupiedUnits; u++) {
                leases.push({
                    unitNumber: totalUnits > 1 ? `${typeText} #${unitIndex}` : typeText,
                    leaseEnd: '',
                    rooms,
                    monthlyRent: perUnitOccRent,
                    bedrooms: null,
                    bathrooms: '',
                    washerDryer: '',
                    parking: '',
                    included: '',
                    excluded: '',
                    rentalValue: '',
                    details: 'Occupé',
                });
                unitIndex++;
            }
            for (let u = 0; u < vacantUnits; u++) {
                leases.push({
                    unitNumber: totalUnits > 1 ? `${typeText} #${unitIndex}` : typeText,
                    leaseEnd: '',
                    rooms,
                    monthlyRent: perUnitVacRent,
                    bedrooms: null,
                    bathrooms: '',
                    washerDryer: '',
                    parking: '',
                    included: '',
                    excluded: '',
                    rentalValue: '',
                    details: 'Inoccupé',
                });
                unitIndex++;
            }
        }
        return leases;
    }
    /**
     * Bandeau « PAC 2026-11-23 » posé sur la photo de certaines annonces
     * (promesse d'achat conditionnelle). Retourne la date au format AAAA-MM-JJ,
     * ou null quand l'annonce n'a pas de bandeau.
     */
    function parsePacDate() {
        var _a;
        const dateRegex = /\bPAC\b[\s\u00a0:\-–]*(\d{4})-(\d{2})-(\d{2})/i;
        const exactRegex = /^\s*PAC[\s\u00a0:\-–]*(\d{4})-(\d{2})-(\d{2})\s*$/i;
        const toIso = (match) => {
            if (!match)
                return null;
            const [, year, month, day] = match;
            const date = new Date(Date.UTC(Number(year), Number(month) - 1, Number(day)));
            const isValid = date.getUTCFullYear() === Number(year)
                && date.getUTCMonth() === Number(month) - 1
                && date.getUTCDate() === Number(day);
            return isValid ? `${year}-${month}-${day}` : null;
        };
        // 1) Un élément court dont tout le texte est le bandeau (le plus fiable).
        const candidates = document.querySelectorAll('div, span, td, p, a, b, strong, label');
        for (let i = 0; i < candidates.length; i++) {
            const text = candidates[i].textContent || '';
            if (text.length > 40 || !text.includes('PAC'))
                continue;
            const iso = toIso(text.match(exactRegex));
            if (iso)
                return iso;
        }
        // 2) Bandeau fourni comme attribut d'une image ou d'un bloc (alt, title...).
        const withAttributes = document.querySelectorAll('[alt], [title], [aria-label], [data-title]');
        for (let i = 0; i < withAttributes.length; i++) {
            const element = withAttributes[i];
            for (const name of ['alt', 'title', 'aria-label', 'data-title']) {
                const value = element.getAttribute(name) || '';
                if (value.length > 60)
                    continue;
                const iso = toIso(value.match(dateRegex));
                if (iso)
                    return iso;
            }
        }
        // 3) Dernier recours : le texte de la page (le mot PAC isolé suivi d'une date).
        return toIso((((_a = document.body) === null || _a === void 0 ? void 0 : _a.textContent) || '').match(dateRegex));
    }
    const centrisNo = parseCentrisNo();
    const header = parseHeader();
    let leases = parseLeases();
    if (leases.length === 0)
        leases = parseLeasesFallback();
    if (leases.length === 0)
        leases = parseLeasesTabular();
    const result = {
        centrisNo,
        address: header.address,
        askingPrice: header.askingPrice,
        postalCode: header.postalCode,
        buildingEvaluation: parseCurrency(valueAfterLabel('Évaluation du bâtiment')),
        lotEvaluation: parseCurrency(valueAfterLabel('Évaluation du terrain')),
        constructionYear: extractNumber(valueAfterLabel('Année de construction')),
        municipalTaxes: parseCurrency(valueAfterLabel('Taxe municipale')),
        scholarTaxes: parseCurrency(valueAfterLabel('Taxe scolaire')),
        electricityFees: parseCurrency(valueAfterLabel('Énergie - Électricité')),
        oilFees: parseCurrency(valueAfterLabel('Énergie - Mazout')),
        insuranceFees: parseCurrency(valueAfterLabel('Assurances')),
        snowRemovalFees: parseCurrency(valueAfterLabel('Déneigement')),
        internetFees: parseCurrency(valueAfterLabel('Internet') || valueAfterLabel('Câble (télé)') || valueAfterLabel('Internet/Télé')),
        otherFees: null,
        numberOfDoors: extractNumber(valueAfterLabel('Genre de propriété')),
        numberOfRooms: extractNumber(valueAfterLabel('Nombre total de pièces')),
        potentialGrossIncome: parseCurrency(valueAfterLabel('Revenus bruts potentiels annuels')),
        interiorArea: extractNumber(valueAfterLabel('Superficie habitable')),
        comments: contentAfterHeading('Remarques'),
        pacDate: parsePacDate(),
        brokers: [],
        collaborators: [],
        leases,
    };
    return JSON.stringify(result);
}
/**
 * Parses a broker popup page (DisplayITQPopup.aspx) and returns the Centris
 * number plus two lists as JSON:
 *  - `brokers`: courtiers inscripteurs (listing brokers);
 *  - `collaborators`: courtiers collaborateurs (they represented the buyer;
 *    the section only appears on some listings, e.g. once sold).
 * The function must stay self-contained: it is injected into the page.
 */
function parseBrokerPage() {
    function parseCentrisNo() {
        const spans = document.querySelectorAll('span.heading2, span.heading1, span.label');
        for (let i = 0; i < spans.length; i++) {
            if (!(spans[i].textContent || '').trim().includes('No Centris'))
                continue;
            const td = spans[i].closest('td');
            if (!td)
                continue;
            const nextTd = td.nextElementSibling;
            if (!nextTd)
                continue;
            const numMatch = (nextTd.textContent || '').match(/\d{5,}/);
            if (numMatch)
                return numMatch[0];
        }
        return '';
    }
    function normalize(text) {
        return text
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .toLowerCase();
    }
    /** Reads the brokers listed under one section heading. */
    function parseSection(headingEl) {
        var _a, _b, _c;
        const brokers = [];
        const tr = headingEl.closest('tr');
        const courtierTd = ((_a = tr === null || tr === void 0 ? void 0 : tr.nextElementSibling) === null || _a === void 0 ? void 0 : _a.querySelector('td')) || null;
        if (!courtierTd)
            return brokers;
        const brokerDivs = courtierTd.querySelectorAll('div.multiLineDisplay');
        for (let d = 0; d < brokerDivs.length; d++) {
            const div = brokerDivs[d];
            const allTables = div.querySelectorAll('table');
            if (allTables.length < 3)
                continue;
            let agencyTable = null;
            let personTable = null;
            for (let t = 0; t < allTables.length; t++) {
                const rows = allTables[t].querySelectorAll(':scope > tbody > tr, :scope > tr');
                if (rows.length === 0)
                    continue;
                const firstRowCells = rows[0].querySelectorAll(':scope > td');
                if (firstRowCells.length >= 3) {
                    agencyTable = firstRowCells[0].querySelector('table');
                    for (let c = firstRowCells.length - 1; c >= 1; c--) {
                        const tbl = firstRowCells[c].querySelector('table');
                        if (tbl) {
                            personTable = tbl;
                            break;
                        }
                    }
                    break;
                }
            }
            let agency = '';
            if (agencyTable) {
                const firstSpan = agencyTable.querySelector('span.field');
                agency = ((_b = firstSpan === null || firstSpan === void 0 ? void 0 : firstSpan.textContent) === null || _b === void 0 ? void 0 : _b.trim()) || '';
            }
            let name = '';
            let title = '';
            let phone = '';
            let email = '';
            if (personTable) {
                const rows = personTable.querySelectorAll(':scope > tbody > tr, :scope > tr');
                for (let r = 0; r < rows.length; r++) {
                    const mailto = rows[r].querySelector('a[href^="mailto:"]');
                    const text = (rows[r].textContent || '').trim();
                    if (mailto) {
                        email = ((_c = mailto.textContent) === null || _c === void 0 ? void 0 : _c.trim()) || '';
                    }
                    else if (!name && text) {
                        name = text;
                    }
                    else if (name && !title && text && !/\d{3}/.test(text)) {
                        title = text;
                    }
                    else if (!phone && /\d{3}.*\d{4}/.test(text)) {
                        phone = text;
                    }
                }
            }
            if (name) {
                brokers.push({ name, agency, title, phone, email });
            }
        }
        return brokers;
    }
    const centrisNo = parseCentrisNo();
    const brokers = [];
    const collaborators = [];
    let sawQualifiedHeading = false;
    const headings = document.querySelectorAll('span.heading2');
    // 1) Sections explicitly named « inscripteur » / « collaborateur ».
    for (let i = 0; i < headings.length; i++) {
        const text = normalize(headings[i].textContent || '');
        if (!text.includes('courtier'))
            continue;
        if (text.includes('collaborateur')) {
            sawQualifiedHeading = true;
            collaborators.push(...parseSection(headings[i]));
        }
        else if (text.includes('inscripteur')) {
            sawQualifiedHeading = true;
            brokers.push(...parseSection(headings[i]));
        }
    }
    // 2) Older pages: a single « Courtier » heading without qualifier = listing brokers.
    if (!sawQualifiedHeading) {
        for (let i = 0; i < headings.length; i++) {
            if (normalize(headings[i].textContent || '').includes('courtier')) {
                brokers.push(...parseSection(headings[i]));
                break;
            }
        }
    }
    return JSON.stringify({ centrisNo, brokers, collaborators });
}
