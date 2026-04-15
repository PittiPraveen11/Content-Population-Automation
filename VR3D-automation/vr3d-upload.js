const fs = require('fs');
const https = require('https');
const path = require('path');

// --- CONFIGURATION ---
const ACCESS_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzE3NDgyMTksInVzZXJfbmFtZSI6IjEiLCJhdXRob3JpdGllcyI6WyJST0xFX0REQVBQX1VTRVIiLCJST0xFX0REX1BVSkFfQ0FTSElFUiIsIlJPTEVfRERfUFVKQV9NQU5BR0VSIiwiUk9MRV9ESVZJTkVfRlJBTkNISVNFRV9DQVNISUVSIiwiUk9MRV9ERF9QVUpBX0FETUlOIiwiUk9MRV9EREFQUF9BRE1JTiIsIlJPTEVfRElWSU5FX0FETUlOIiwiUk9MRV9ESVZJTkVfRlJBTkNISVNFRV9PUEVSQVRPUiIsIlJPTEVfRElWSU5FX0ZSQU5DSElTRUVfQUNDT1VOVEFOVCIsIlJPTEVfRERBUFBfU1VQUE9SVCIsIlJPTEVfRElWSU5FX0ZSQU5DSElTRUVfTUFOQUdFUiIsIlJPTEVfRElWSU5FX0ZSQU5DSElTRUUiLCJST0xFX0REQVBQX0NPTlRFTlRfTUFOQUdFUiIsIlJPTEVfRERfUFVKQV9NT0RFUkFUT1IiXSwianRpIjoiMTlmWE05bDRGdFlfWVhLUlVrWEVUUWV3ZW5NIiwiY2xpZW50X2lkIjoidGVjaHhyIiwic2NvcGUiOlsiYWxsIl19.hqU10x9yJnnqtdIAkYr-62_UnEUfsVvyWlJ-tDh8HvyJ4A8FpS5C_Q89dwQpCeERQPD9we-IaXjMy9-5MhN_ZJIBt_1jZzyzw-8CTv1GweMhD18gc8QAlhOtW-PHsW6-J25dqqQV0et6k8u_epYYlBD2fLhZ3PY1DOdD65z6YLpKgFB7j05jOwMgZYwjDE-jNeSd6-XBE0bh5LRBWdRSOinpEJj1mVOOWy6PNR_3ho2Rt8bU0srev1NOzHXpAtlbHIchlgqFS_8H9XOuyPcPrLACfS0FzhCIjw1AHGVFy3BfMmebMCfokSxVA207F4n0Yfz2NCjuSzG2Xhm1l3IiMw"; // Set your token here
const HOST = "devgateway.techxrdev.in";
const API_PATH_PREFIX = "/api/content/cms/";
const VIDEO_THUMBNAILS_FILE = path.join(__dirname, 'VideoThumbnails_v2.json');
const RESPONSE_FILE = path.join(__dirname, 'response.json');

// Set LIMIT to a number (e.g., 2) to test on a few cards only. Set to null to run for all.
const LIMIT = null;

// Set to true for dry run (no API calls), false for real API calls.
const DRY_RUN = false;

const API_DELAY_MS = 2000;
// ---------------------

/**
 * Make HTTPS request (GET, POST, PUT)
 */
function httpsRequest(method, path, body = null) {
    return new Promise((resolve, reject) => {
        const options = {
            hostname: HOST,
            path: path.startsWith('/') ? path : API_PATH_PREFIX + path,
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${ACCESS_TOKEN}`
            }
        };

        let data = '';
        if (body !== null) {
            data = JSON.stringify(body);
            options.headers['Content-Length'] = Buffer.byteLength(data);
        }

        const req = https.request(options, (res) => {
            let resBody = '';
            res.on('data', (chunk) => resBody += chunk);
            res.on('end', () => {
                if (res.statusCode >= 200 && res.statusCode < 300) {
                    try {
                        const parsed = resBody ? JSON.parse(resBody) : {};
                        resolve({ status: res.statusCode, body: parsed });
                    } catch {
                        resolve({ status: res.statusCode, body: resBody });
                    }
                } else {
                    reject({ status: res.statusCode, body: resBody });
                }
            });
        });

        req.on('error', (e) => reject(e));
        if (data) req.write(data);
        req.end();
    });
}

async function createCard(payload) {
    if (DRY_RUN) return { body: { id: 'dry-run-id', ...payload } };
    return httpsRequest('POST', 'createCard', payload);
}

async function updateCardThumbnail(cardId, thumbnail) {
    if (DRY_RUN) return { status: 200 };
    return httpsRequest('PUT', `cards/${cardId}/thumbnail`, thumbnail);
}

async function createEpisode(cardId, payload) {
    if (DRY_RUN) return { body: { id: 'dry-run-ep-id', ...payload } };
    return httpsRequest('POST', `cards/${cardId}/episodes`, payload);
}

async function updateEpisodeThumbnail(episodeId, thumbnail) {
    if (DRY_RUN) return { status: 200 };
    return httpsRequest('PUT', `episodes/${episodeId}/thumbnail`, thumbnail);
}

async function updateEpisodeStreamingOptions(episodeId, streamingOptions) {
    if (DRY_RUN) return { status: 200 };
    return httpsRequest('PUT', `episodes/${episodeId}/streamingOptions`, streamingOptions);
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Normalize title for fuzzy matching.
 */
function normalizeTitleForMatch(str) {
    if (!str || typeof str !== 'string') return '';
    let s = str.trim().toLowerCase();
    s = s.replace(/^(shri|shree|sri)\s+/i, '');
    s = s.replace(/\bpart\s+/gi, '');
    s = s.replace(/&/g, 'and');
    s = s.replace(/saptshati/g, 'saptashati');
    s = s.replace(/[\s._\-]+/g, '');
    s = s.replace(/[^\w]/g, '');
    return s;
}

function findMatchingCard(cards, sourceTitle) {
    const srcNorm = normalizeTitleForMatch(sourceTitle);
    if (!srcNorm) return null;

    let exact = cards.find(c => (c.thumbnail?.title?.en || '').trim() === (sourceTitle || '').trim());
    if (exact) return exact;

    const candidates = cards.filter(c => {
        const respTitle = (c.thumbnail?.title?.en || '').trim();
        const respNorm = normalizeTitleForMatch(respTitle);
        if (!respNorm) return false;
        return respNorm === srcNorm || srcNorm.includes(respNorm) || respNorm.includes(srcNorm);
    });

    if (candidates.length === 0) return null;
    if (candidates.length === 1) return candidates[0];
    return candidates.sort((a, b) => {
        const aNorm = normalizeTitleForMatch(a.thumbnail?.title?.en || '');
        const bNorm = normalizeTitleForMatch(b.thumbnail?.title?.en || '');
        return aNorm.length - bNorm.length;
    })[0];
}

function findMatchingEpisode(episodes, sourceTitle) {
    const cleanSrc = (sourceTitle || '').trim().replace(/"$/, '');
    const srcNorm = normalizeTitleForMatch(cleanSrc);
    if (!srcNorm) return null;

    let exact = episodes.find(e => {
        const en = (e.thumbnail?.title?.en || '').trim().replace(/"$/, '');
        return en === cleanSrc;
    });
    if (exact) return exact;

    const candidates = episodes.filter(e => {
        const respTitle = (e.thumbnail?.title?.en || '').trim().replace(/"$/, '');
        const respNorm = normalizeTitleForMatch(respTitle);
        if (!respNorm) return false;
        return respNorm === srcNorm || srcNorm.includes(respNorm) || respNorm.includes(srcNorm);
    });

    if (candidates.length === 0) return null;
    if (candidates.length === 1) return candidates[0];
    return candidates.sort((a, b) => {
        const aNorm = normalizeTitleForMatch(a.thumbnail?.title?.en || '');
        const bNorm = normalizeTitleForMatch(b.thumbnail?.title?.en || '');
        return aNorm.length - bNorm.length;
    })[0];
}

/**
 * Build streamingOptions from VR3D entry data.
 * Reuses Theater3D logic: prefer AdaptiveStreamingVideoURL, fallback to highQualityVideoUrl (master.m3u8).
 * For mp4-only entries, add single best-effort option.
 */
function buildStreamingOptions(entryData) {
    const baseUrl = entryData.highQualityVideoUrl || entryData.AdaptiveStreamingVideoURL;
    const awsKey = entryData.highQualityVideoKeyAWSObjectId || entryData.AdaptiveStreamVideoKeyAWSObjectId || '';

    if (!baseUrl) return [];

    const options = [];

    // ADAPTIVE (master.m3u8)
    if (entryData.AdaptiveStreamingVideoURL) {
        options.push({
            contentUrl: entryData.AdaptiveStreamingVideoURL,
            streamingQuality: 'ADAPTIVE',
            awsKey: entryData.AdaptiveStreamVideoKeyAWSObjectId || awsKey,
            sizeInKb: null
        });
    } else if (baseUrl.includes('master.m3u8')) {
        options.push({
            contentUrl: baseUrl,
            streamingQuality: 'ADAPTIVE',
            awsKey: awsKey,
            sizeInKb: null
        });
    } else {
        // mp4 or other: single best-effort option
        const bestUrl = entryData.highQualityVideoUrl || entryData.mediumQualityVideoUrl || entryData.lowQualityVideoUrl;
        if (bestUrl) {
            options.push({
                contentUrl: bestUrl,
                streamingQuality: 'ADAPTIVE',
                awsKey: awsKey,
                sizeInKb: null
            });
        }
        return options;
    }

    // Quality URLs: use explicit if present (and not master.m3u8), else derive from master path
    const baseForQualities = baseUrl.includes('master.m3u8') ? baseUrl : baseUrl.replace(/\/?$/, '/master.m3u8');
    const useExplicit = (url) => url && url.trim() && !url.includes('master.m3u8');
    const qualities = [
        { quality: 'P_240', path: '240p/playlist.m3u8', url: entryData.lowQualityVideoUrl },
        { quality: 'P_360', path: '360p/playlist.m3u8', url: entryData.mediumQualityVideoUrl },
        { quality: 'P_540', path: '540p/playlist.m3u8', url: null },
        { quality: 'P_720', path: '720p/playlist.m3u8', url: entryData.highQualityVideoUrl }
    ];

    for (const q of qualities) {
        const contentUrl = useExplicit(q.url) ? q.url : baseForQualities.replace('master.m3u8', q.path);
        options.push({
            contentUrl: contentUrl,
            streamingQuality: q.quality,
            awsKey: awsKey,
            sizeInKb: null
        });
    }

    return options;
}

/**
 * Check if card thumbnail differs from source.
 */
function cardThumbnailDiffers(card, entryData) {
    const t = card.thumbnail || {};
    const img = entryData.v_thumbnailUrl || entryData.thumbnailUrl || entryData.thumbnailIconUrl || '';
    const en = entryData.videoTitle || '';
    const hi = entryData.hindiTitleText || '';
    const descEn = entryData.description || entryData.city || '';
    const descHi = entryData.hindiCityText || '';
    return (
        (t.imageUrl || '') !== img ||
        (t.title?.en || '') !== en ||
        (t.title?.hi || '') !== hi ||
        (t.description?.en || '') !== descEn ||
        (t.description?.hi || '') !== descHi
    );
}

/**
 * Check if episode thumbnail differs from source.
 */
function episodeThumbnailDiffers(ep, entryData) {
    const t = ep.thumbnail || {};
    const img = entryData.v_thumbnailUrl || entryData.thumbnailUrl || entryData.thumbnailIconUrl || '';
    const en = entryData.videoTitle || '';
    const hi = entryData.hindiTitleText || '';
    const descEn = entryData.description || entryData.city || '';
    const descHi = entryData.hindiCityText || '';
    return (
        (t.imageUrl || '') !== img ||
        (t.title?.en || '') !== en ||
        (t.title?.hi || '') !== hi ||
        (t.description?.en || '') !== descEn ||
        (t.description?.hi || '') !== descHi
    );
}

/**
 * Check if streamingOptions differ from source.
 */
function streamingOptionsDiffer(ep, entryData) {
    const expected = buildStreamingOptions(entryData);
    const actual = ep.streamingOptions || [];

    if (actual.length !== expected.length) return true;

    for (let i = 0; i < expected.length; i++) {
        const a = actual[i];
        const e = expected[i];
        if (!a || (a.contentUrl || '') !== (e.contentUrl || '') || (a.awsKey || '') !== (e.awsKey || '')) {
            return true;
        }
    }
    return false;
}

function getCardThumbnailChanges(card, entryData) {
    const t = card.thumbnail || {};
    const img = entryData.v_thumbnailUrl || entryData.thumbnailUrl || entryData.thumbnailIconUrl || '';
    const en = entryData.videoTitle || '';
    const hi = entryData.hindiTitleText || '';
    const descEn = entryData.description || entryData.city || '';
    const descHi = entryData.hindiCityText || '';
    return {
        imageUrl: (t.imageUrl || '') !== img,
        titleEn: (t.title?.en || '') !== en,
        titleHi: (t.title?.hi || '') !== hi,
        descEn: (t.description?.en || '') !== descEn,
        descHi: (t.description?.hi || '') !== descHi
    };
}

function getEpisodeThumbnailChanges(ep, entryData) {
    const t = ep.thumbnail || {};
    const img = entryData.v_thumbnailUrl || entryData.thumbnailUrl || entryData.thumbnailIconUrl || '';
    const en = entryData.videoTitle || '';
    const hi = entryData.hindiTitleText || '';
    const descEn = entryData.description || entryData.city || '';
    const descHi = entryData.hindiCityText || '';
    return {
        imageUrl: (t.imageUrl || '') !== img,
        titleEn: (t.title?.en || '').replace(/"$/, '') !== en,
        titleHi: (t.title?.hi || '') !== hi,
        descEn: (t.description?.en || '') !== descEn,
        descHi: (t.description?.hi || '') !== descHi
    };
}

function getStreamingOptionsChangedQualities(ep, entryData) {
    const expected = buildStreamingOptions(entryData);
    const actual = ep.streamingOptions || [];
    const changed = [];
    for (let i = 0; i < Math.max(expected.length, actual.length); i++) {
        const a = actual[i];
        const e = expected[i];
        if (!e) continue;
        const quality = e.streamingQuality || `option${i}`;
        if (!a || (a.contentUrl || '') !== (e.contentUrl || '') || (a.awsKey || '') !== (e.awsKey || '')) {
            changed.push(quality);
        }
    }
    return changed;
}

async function main() {
    try {
        console.log(`Mode: ${DRY_RUN ? 'DRY RUN (no API calls)' : 'LIVE (real API calls)'}`);
        console.log('Loading data files...');
        let vtRaw = fs.readFileSync(VIDEO_THUMBNAILS_FILE, 'utf8').replace(/^\uFEFF/, '');
        let resRaw = fs.readFileSync(RESPONSE_FILE, 'utf8').replace(/^\uFEFF/, '');

        const vtData = JSON.parse(vtRaw);
        const keys = Object.keys(vtData).sort((a, b) => parseInt(a, 10) - parseInt(b, 10));
        const entries = keys.map(k => vtData[k]).filter(Boolean);

        let responseCards = [];
        try {
            const parsed = JSON.parse(resRaw);
            responseCards = Array.isArray(parsed) ? parsed : (parsed.data?.cards || parsed.cards || []);
        } catch (e) {
            console.log('response.json empty or invalid, starting fresh.');
        }

        const limitedEntries = LIMIT ? entries.slice(0, LIMIT) : entries;

        console.log(`Source: ${entries.length} entries`);
        console.log(`Response: ${responseCards.length} cards`);
        console.log(`Processing: ${limitedEntries.length} entries`);
        console.log('');

        for (let idx = 0; idx < limitedEntries.length; idx++) {
            const entryData = limitedEntries[idx];
            const cardTitle = entryData.videoTitle;
            const locked = entryData.isFreeShow !== 'true';

            let existingCard = findMatchingCard(responseCards, cardTitle);
            const isFuzzyMatch = existingCard && (existingCard.thumbnail?.title?.en || '').trim() !== (cardTitle || '').trim();

            let cardId;

            if (!existingCard) {
                console.log(`[Card] CREATE: "${cardTitle}"`);
                if (DRY_RUN) console.log(`[DRY RUN] Would POST createCard`);
                const payload = {
                    thumbnail: {
                        title: { hi: entryData.hindiTitleText || '', en: entryData.videoTitle || '' },
                        imageUrl: entryData.v_thumbnailUrl || entryData.thumbnailUrl || entryData.thumbnailIconUrl || '',
                        description: { hi: entryData.hindiCityText || '', en: entryData.description || entryData.city || '' },
                        displayOrientation: 'PORTRAIT'
                    },
                    contentType: 'VR_3D',
                    series: false,
                    episodes: []
                };

                const result = await createCard(payload);
                if (DRY_RUN) {
                    cardId = 'dry-run-id';
                } else {
                    const created = result.body;
                    cardId = created.id;
                }
                existingCard = {
                    id: cardId,
                    thumbnail: payload.thumbnail,
                    series: false,
                    episodes: []
                };
                if (!DRY_RUN) responseCards.push(existingCard);
                if (!DRY_RUN) await delay(API_DELAY_MS);
            } else {
                cardId = existingCard.id;

                if (cardThumbnailDiffers(existingCard, entryData)) {
                    const changes = getCardThumbnailChanges(existingCard, entryData);
                    const changeParts = [];
                    if (changes.titleEn) changeParts.push(`title.en ("${(existingCard.thumbnail?.title?.en || '').trim()}" -> "${cardTitle}")`);
                    if (changes.titleHi) changeParts.push('title.hi');
                    if (changes.imageUrl) changeParts.push('imageUrl');
                    if (changes.descEn) changeParts.push('description.en');
                    if (changes.descHi) changeParts.push('description.hi');

                    console.log(`[Card] UPDATE: PUT cards/${cardId}/thumbnail`);
                    if (isFuzzyMatch) console.log(`  Matched: "${(existingCard.thumbnail?.title?.en || '').trim()}" -> "${cardTitle}"`);
                    console.log(`  Changes: ${changeParts.join(', ')}`);
                    if (DRY_RUN) console.log(`[DRY RUN] Would PUT cards/${cardId}/thumbnail`);

                    const thumb = {
                        title: { hi: entryData.hindiTitleText || '', en: entryData.videoTitle || '' },
                        imageUrl: entryData.v_thumbnailUrl || entryData.thumbnailUrl || entryData.thumbnailIconUrl || '',
                        description: { hi: entryData.hindiCityText || '', en: entryData.description || entryData.city || '' },
                        displayOrientation: 'PORTRAIT'
                    };
                    await updateCardThumbnail(cardId, thumb);
                    existingCard.thumbnail = thumb;
                    if (!DRY_RUN) await delay(API_DELAY_MS);
                } else {
                    console.log(`[Card] SKIP: "${cardTitle}" (unchanged)`);
                    if (isFuzzyMatch) console.log(`  Matched: "${(existingCard.thumbnail?.title?.en || '').trim()}" -> "${cardTitle}"`);
                }
            }

            if (!existingCard.episodes) existingCard.episodes = [];

            const epTitle = entryData.videoTitle;
            let existingEp = findMatchingEpisode(existingCard.episodes, epTitle);
            const isEpFuzzyMatch = existingEp && (existingEp.thumbnail?.title?.en || '').trim().replace(/"$/, '') !== (epTitle || '').trim();

            if (!existingEp) {
                console.log(`  [Episode] CREATE: "${epTitle}"`);
                if (DRY_RUN) console.log(`  [DRY RUN] Would POST cards/${cardId}/episodes`);
                const streamingOpts = buildStreamingOptions(entryData);
                const payload = {
                    thumbnail: {
                        title: { hi: entryData.hindiTitleText || '', en: entryData.videoTitle || '' },
                        description: { hi: entryData.hindiCityText || '', en: entryData.description || entryData.city || '' },
                        imageUrl: entryData.v_thumbnailUrl || entryData.thumbnailUrl || entryData.thumbnailIconUrl || '',
                        displayOrientation: 'PORTRAIT'
                    },
                    streamingOptions: streamingOpts,
                    episodeNumber: '1',
                    locked: locked,
                    status: 'PUBLISHED',
                    contentType: 'VR_3D',
                    sequenceNo: 0
                };

                const result = await createEpisode(cardId, payload);
                if (!DRY_RUN) {
                    const created = result.body;
                    existingEp = {
                        id: created.id,
                        thumbnail: payload.thumbnail,
                        streamingOptions: streamingOpts,
                        episodeNumber: payload.episodeNumber,
                        sequenceNo: payload.sequenceNo
                    };
                    existingCard.episodes.push(existingEp);
                }
                if (!DRY_RUN) await delay(API_DELAY_MS);
            } else {
                let needsUpdate = false;
                if (episodeThumbnailDiffers(existingEp, entryData)) {
                    const changes = getEpisodeThumbnailChanges(existingEp, entryData);
                    const changeParts = [];
                    if (changes.imageUrl) changeParts.push('imageUrl');
                    if (changes.titleEn) changeParts.push(`title.en ("${(existingEp.thumbnail?.title?.en || '').trim()}" -> "${epTitle}")`);
                    if (changes.titleHi) changeParts.push('title.hi');
                    if (changes.descEn) changeParts.push('description.en');
                    if (changes.descHi) changeParts.push('description.hi');

                    console.log(`  [Episode] UPDATE: PUT episodes/${existingEp.id}/thumbnail`);
                    if (isEpFuzzyMatch) console.log(`    Matched: "${(existingEp.thumbnail?.title?.en || '').trim()}" -> "${epTitle}"`);
                    console.log(`    Changes: ${changeParts.join(', ')}`);
                    if (DRY_RUN) console.log(`  [DRY RUN] Would PUT episodes/${existingEp.id}/thumbnail`);

                    const thumb = {
                        title: { hi: entryData.hindiTitleText || '', en: entryData.videoTitle || '' },
                        description: { hi: entryData.hindiCityText || '', en: entryData.description || entryData.city || '' },
                        imageUrl: entryData.v_thumbnailUrl || entryData.thumbnailUrl || entryData.thumbnailIconUrl || '',
                        displayOrientation: 'PORTRAIT'
                    };
                    await updateEpisodeThumbnail(existingEp.id, thumb);
                    existingEp.thumbnail = thumb;
                    needsUpdate = true;
                    if (!DRY_RUN) await delay(API_DELAY_MS);
                }
                if (streamingOptionsDiffer(existingEp, entryData)) {
                    const changedQualities = getStreamingOptionsChangedQualities(existingEp, entryData);
                    console.log(`  [Episode] UPDATE: PUT episodes/${existingEp.id}/streamingOptions`);
                    if (isEpFuzzyMatch) console.log(`    Matched: "${(existingEp.thumbnail?.title?.en || '').trim()}" -> "${epTitle}"`);
                    console.log(`    Changes: contentUrl, awsKey (${changedQualities.join(', ')})`);
                    if (DRY_RUN) console.log(`  [DRY RUN] Would PUT episodes/${existingEp.id}/streamingOptions`);

                    const opts = buildStreamingOptions(entryData);
                    await updateEpisodeStreamingOptions(existingEp.id, opts);
                    existingEp.streamingOptions = opts;
                    needsUpdate = true;
                    if (!DRY_RUN) await delay(API_DELAY_MS);
                }
                if (!needsUpdate) {
                    console.log(`  [Episode] SKIP: "${epTitle}" (unchanged)`);
                    if (isEpFuzzyMatch) console.log(`    Matched: "${(existingEp.thumbnail?.title?.en || '').trim()}" -> "${epTitle}"`);
                }
            }
        }

        if (!DRY_RUN) {
            fs.writeFileSync(RESPONSE_FILE, JSON.stringify(responseCards, null, 4), 'utf8');
            console.log(`\nSaved updated state to ${RESPONSE_FILE}`);
        }

        console.log('\nUpload process completed.');
    } catch (error) {
        console.error(`Critical Error: ${error.message}`);
        if (error.body) console.error('Response:', error.body);
        process.exit(1);
    }
}

main();
