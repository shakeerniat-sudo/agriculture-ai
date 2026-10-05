const analysisForm = document.getElementById('analysis-form');
const translationForm = document.getElementById('translation-form');
const analyzeButton = document.getElementById('analyze-button');
const translateButton = document.getElementById('translate-button');
const statusMessage = document.getElementById('status-message');
const reportCard = document.getElementById('report-card');
const reportPlaceholder = document.getElementById('report-placeholder');
const resultContent = document.getElementById('result-content');
const languageSelect = document.getElementById('language-select');
const menuToggle = document.querySelector('.menu-toggle');
const mainNav = document.getElementById('main-nav');
const cropProblemInput = document.getElementById('crop_problem');
const suggestionChips = document.querySelectorAll('.suggestion-chip');

let originalReport = '';

suggestionChips.forEach((chip) => {
  chip.addEventListener('click', () => {
    cropProblemInput.value = chip.dataset.request || '';
    cropProblemInput.focus();
    cropProblemInput.setSelectionRange(cropProblemInput.value.length, cropProblemInput.value.length);
  });
});

function setStatus(message, type = '') {
  statusMessage.textContent = message;
  statusMessage.classList.remove('error', 'success');
  if (type) statusMessage.classList.add(type);
}

function setAnalyzeLoading(isLoading) {
  const label = analyzeButton.querySelector('.button-label');
  const loader = analyzeButton.querySelector('.button-loader');
  analyzeButton.disabled = isLoading;
  label.textContent = isLoading ? 'AI Agent is analyzing your farm…' : 'Analyze My Farm';
  loader.classList.toggle('hidden', !isLoading);
}

function setTranslateLoading(isLoading) {
  const label = translateButton.querySelector('.translate-button-text');
  const loader = translateButton.querySelector('.translate-loader');
  translateButton.disabled = isLoading;
  label.textContent = isLoading ? 'Translating report…' : '🌐 Translate Report';
  loader.classList.toggle('hidden', !isLoading);
}

function addText(parent, tagName, text) {
  const element = document.createElement(tagName);
  element.textContent = cleanReportFormatting(text);
  parent.append(element);
  return element;
}

function cleanReportFormatting(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/__(.*?)__/g, '$1')
    .replace(/(^|[^*])\*(\S(?:.*?\S)?)\*(?!\*)/g, '$1$2')
    .replace(/(^|\s)_(\S(?:.*?\S)?)_(?=\s|$)/g, '$1$2');
}

function parseReportSections(report) {
  const sections = [];
  let currentSection = null;
  const lines = String(report || '').replace(/\r\n/g, '\n').split('\n');

  for (const line of lines) {
    const headingMatch = line.match(/^\s{0,3}(#{1,4})\s+(.+?)\s*#*\s*$/);
    if (headingMatch) {
      const heading = headingMatch[2].trim();
      if (heading.toLowerCase() === 'your agriculture intelligence report') {
        currentSection = null;
        continue;
      }
      currentSection = { heading: cleanReportFormatting(heading), body: [] };
      sections.push(currentSection);
    } else if (line.trim()) {
      if (!currentSection) {
        currentSection = { heading: 'Agriculture guidance', body: [] };
        sections.push(currentSection);
      }
      currentSection.body.push(cleanReportFormatting(line.trim()));
    }
  }

  return sections;
}

function renderReport(report, analysis = {}, sourceReport = '') {
  resultContent.replaceChildren();
  if (!analysis || typeof analysis !== 'object') analysis = {};

  let sections = parseReportSections(report);
  const sourceSections = sourceReport ? parseReportSections(sourceReport) : [];
  let usedSourceFallback = false;
  if (
    sourceSections.length > 0
    && sections.length === sourceSections.length + 1
    && sections[0].body.length === 0
  ) {
    sections.shift();
  }
  if (sourceSections.length > 0 && sections.length !== sourceSections.length) {
    sections = sourceSections;
    usedSourceFallback = true;
  }

  sections.forEach((section, index) => {
    if (!section.body.length) {
      const heading = section.heading.toLowerCase();
      const analysisKey = heading.includes('future weather')
        ? 'future_weather'
        : heading.includes('agriculture analysis') || heading.includes('crop analysis')
          ? 'crop'
          : heading.includes('irrigation')
            ? 'irrigation'
            : heading.includes('crop problem')
              ? 'health'
              : heading.includes('recommended actions')
                ? 'actions'
                : heading.includes('precautions')
                  ? 'precautions'
                  : null;
      const fallbackText = analysisKey ? analysis[analysisKey] : null;
      const sourceBody = sourceSections[index]?.body.join('\n');
      if (typeof fallbackText === 'string' && fallbackText.trim()) {
        section.body.push(fallbackText.trim());
      } else if (sourceBody) {
        section.body.push(sourceBody);
        usedSourceFallback = true;
      } else {
        section.body.push('No details were returned for this section. Please review your request and try the analysis again.');
      }
    }

    const block = document.createElement('section');
    block.className = 'report-block';
    addText(block, 'h3', section.heading);

    let paragraph = [];
    let list = null;
    let listType = '';
    const flushParagraph = () => {
      if (paragraph.length) {
        addText(block, 'p', paragraph.join(' '));
        paragraph = [];
      }
    };
    const flushList = () => {
      list = null;
      listType = '';
    };

    for (const line of section.body) {
      const listMatch = line.match(/^\s*(?:[-*•]\s+|(\d+)[.)]\s+)(.+)$/);
      if (listMatch) {
        flushParagraph();
        const nextType = listMatch[1] ? 'ol' : 'ul';
        if (!list || listType !== nextType) {
          flushList();
          listType = nextType;
          list = document.createElement(nextType);
          block.append(list);
        }
        addText(list, 'li', listMatch[2].trim());
      } else {
        flushList();
        paragraph.push(line);
      }
    }
    flushParagraph();
    resultContent.append(block);
  });

  if (!sections.length) {
    const block = document.createElement('section');
    block.className = 'report-block';
    addText(block, 'h3', 'Agriculture guidance');
    addText(block, 'p', String(report || 'No report content was returned.'));
    resultContent.append(block);
  }
  return usedSourceFallback;
}

function getFarmPayload() {
  const formData = new FormData(analysisForm);
  return {
    crop: String(formData.get('crop') || '').trim(),
    soil_type: String(formData.get('soil_type') || '').trim(),
    season: String(formData.get('season') || '').trim(),
    soil_moisture: Number(formData.get('soil_moisture')),
    location: String(formData.get('location') || '').trim(),
    crop_problem: String(formData.get('crop_problem') || '').trim(),
  };
}

function validateFarmPayload(payload) {
  const numericValues = [
    ['Soil moisture', payload.soil_moisture, 0, 100],
  ];

  for (const [label, value, min, max] of numericValues) {
    if (!Number.isFinite(value)) return `${label} must be a valid number.`;
    if (min !== undefined && value < min) return `${label} must be at least ${min}.`;
    if (max !== undefined && value > max) return `${label} must be no more than ${max}.`;
  }
  if (!payload.crop || !payload.soil_type || !payload.season || !payload.location || !payload.crop_problem) {
    return 'Complete each farm detail, enter your location, and add your farming question or request before analyzing.';
  }
  return '';
}

async function readApiResponse(response, fallbackMessage) {
  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error(fallbackMessage);
  }
  if (!response.ok || !data.success) {
    throw new Error(data.error || fallbackMessage);
  }
  return data;
}

async function submitAnalysis(event) {
  event.preventDefault();
  const payload = getFarmPayload();
  const validationMessage = validateFarmPayload(payload);
  if (validationMessage) {
    setStatus(validationMessage, 'error');
    return;
  }

  setAnalyzeLoading(true);
  setStatus('Fetching live weather for your location and preparing your farm analysis...');

  try {
    const response = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(90000),
    });
    const data = await readApiResponse(response, 'Farm analysis could not be completed. Please try again.');
    if (typeof data.report !== 'string' || !data.report.trim()) {
      throw new Error('The AI service returned an empty report. Please run the analysis again.');
    }

    originalReport = data.report;
    renderReport(originalReport, data.analysis);
    reportPlaceholder.classList.add('hidden');
    reportCard.classList.remove('hidden');
    if (data.mode === 'local_fallback') {
      setStatus(
        'The AI service could not be reached. Built-in guidance based on your farm details is shown below.',
        'info',
      );
    } else {
      setStatus('Your farm analysis is ready.', 'success');
    }
    document.getElementById('ai-report').scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (error) {
    const message = error.name === 'TimeoutError'
      ? 'The analysis took too long. Please check your connection and try again.'
      : error.message || 'Farm analysis failed. Please try again.';
    setStatus(message, 'error');
  } finally {
    setAnalyzeLoading(false);
  }
}

async function translateReport(event) {
  event.preventDefault();
  if (!originalReport) {
    setStatus('Run a farm analysis before translating a report.', 'error');
    document.getElementById('farm-advisor').scrollIntoView({ behavior: 'smooth' });
    return;
  }

  const language = languageSelect.value;
  setTranslateLoading(true);
  try {
    const response = await fetch('/api/translate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ report: originalReport, language }),
      signal: AbortSignal.timeout(90000),
    });
    const data = await readApiResponse(response, 'Translation could not be completed. Please try again.');
    if (typeof data.translated_report !== 'string' || !data.translated_report.trim()) {
      throw new Error('The translation service returned an empty report. Please try again.');
    }

    const usedSourceFallback = renderReport(data.translated_report, {}, originalReport);
    setStatus(
      usedSourceFallback
        ? `Some translated content was incomplete, so the original report text is shown for those sections.`
        : `Your report is now shown in ${language}.`,
      usedSourceFallback ? 'info' : 'success',
    );
  } catch (error) {
    const message = error.name === 'TimeoutError'
      ? 'Translation took too long. Please check your connection and try again.'
      : error.message || 'Translation failed. Please try again.';
    setStatus(message, 'error');
  } finally {
    setTranslateLoading(false);
  }
}

function setMenuOpen(isOpen) {
  mainNav.classList.toggle('is-open', isOpen);
  menuToggle.setAttribute('aria-expanded', String(isOpen));
  menuToggle.setAttribute('aria-label', isOpen ? 'Close navigation' : 'Open navigation');
}

analysisForm.addEventListener('submit', submitAnalysis);
translationForm.addEventListener('submit', translateReport);

menuToggle.addEventListener('click', () => {
  setMenuOpen(menuToggle.getAttribute('aria-expanded') !== 'true');
});

mainNav.querySelectorAll('a').forEach((link) => {
  link.addEventListener('click', () => setMenuOpen(false));
});

window.addEventListener('resize', () => {
  if (window.innerWidth > 820) setMenuOpen(false);
});
