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

let originalReport = '';

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
  analyzeButton.classList.toggle('is-loading', isLoading);
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
  element.textContent = text;
  parent.append(element);
  return element;
}

function renderReport(report) {
  resultContent.replaceChildren();

  const sections = [];
  let currentSection = null;
  const lines = String(report || '').replace(/\r\n/g, '\n').split('\n');

  for (const line of lines) {
    const headingMatch = line.match(/^\s{0,3}#{1,4}\s+(.+?)\s*#*\s*$/);
    if (headingMatch) {
      currentSection = { heading: headingMatch[1].trim(), body: [] };
      sections.push(currentSection);
    } else if (line.trim()) {
      if (!currentSection) {
        currentSection = { heading: 'Agriculture guidance', body: [] };
        sections.push(currentSection);
      }
      currentSection.body.push(line.trim());
    }
  }

  for (const section of sections) {
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
  }

  if (!sections.length) {
    const block = document.createElement('section');
    block.className = 'report-block';
    addText(block, 'h3', 'Agriculture guidance');
    addText(block, 'p', String(report || 'No report content was returned.'));
    resultContent.append(block);
  }
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
    renderReport(originalReport);
    reportPlaceholder.classList.add('hidden');
    reportCard.classList.remove('hidden');
    setStatus('Your farm analysis is ready.', 'success');
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

    renderReport(data.translated_report);
    setStatus(`Your report is now shown in ${language}.`, 'success');
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
