function notifyCard(card, message) {
  let badge = card.querySelector('.card-notice');
  if (!badge) {
    badge = document.createElement('div');
    badge.className = 'card-notice';
    card.appendChild(badge);
  }
  badge.textContent = message;
  badge.classList.add('visible');
  window.setTimeout(() => badge.classList.remove('visible'), 1200);
}

async function saveAllLogs(logs, date) {
  try {
    const response = await fetch('/api/log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fish_logs: logs, date }),
    });
    const result = await response.json();
    return response.ok && result.success;
  } catch (error) {
    return false;
  }
}

function initTrackerPage() {
  const form = document.getElementById('tracker-form');
  const date = form.dataset.date;
  const cards = Array.from(document.querySelectorAll('.fish-card'));

  cards.forEach((card) => {
    const input = card.querySelector('.counter-input');
    const btnPlus = card.querySelector('.increment');
    const btnMinus = card.querySelector('.decrement');
    const image = card.querySelector('.fish-image');

    const updateInput = (value) => {
      input.value = Math.max(0, value);
    };

    btnPlus.addEventListener('click', () => {
      updateInput(Number(input.value) + 1);
    });

    btnMinus.addEventListener('click', () => {
      updateInput(Number(input.value) - 1);
    });

    image.addEventListener('click', () => {
      updateInput(Number(input.value) + 1);
    });

    input.addEventListener('change', () => {
      updateInput(Number(input.value));
    });
  });

  const saveButton = document.getElementById('save-all-btn');
  saveButton.addEventListener('click', async () => {
    const logs = cards.map((card) => {
      const fishId = card.dataset.fishId;
      const input = card.querySelector('.counter-input');
      return {
        fish_id: fishId,
        pellets: Math.max(0, Number(input.value)),
      };
    });
    const success = await saveAllLogs(logs, date);
    if (success) {
      cards.forEach((card) => notifyCard(card, 'Saved'));
    } else {
      cards.forEach((card) => notifyCard(card, 'Save failed'));
    }
  });

  const dateInput = document.getElementById('selected-date');
  if (dateInput) {
    dateInput.addEventListener('change', () => {
      if (!dateInput.value) {
        return;
      }
      const url = new URL(window.location.href);
      url.searchParams.set('date', dateInput.value);
      window.location.href = url.toString();
    });
  }
}

function initLocationsPage() {
  const addFishButton = document.getElementById('add-fish-btn');
  const fishFields = document.querySelector('.fish-fields');
  const fishCountInput = document.getElementById('new-fish-count');
  const template = document.getElementById('new-fish-template');

  if (!addFishButton || !fishFields || !fishCountInput || !template) {
    return;
  }

  let newFishCount = Number(fishCountInput.value || 0);

  addFishButton.addEventListener('click', () => {
    newFishCount += 1;
    fishCountInput.value = newFishCount;

    const clone = template.content.cloneNode(true);
    const card = clone.querySelector('.new-fish-card');
    if (!card) {
      return;
    }

    const nameInput = card.querySelector('input[name="fish_name_new_INDEX"]');
    const descInput = card.querySelector('textarea[name="fish_desc_new_INDEX"]');
    const fileInput = card.querySelector('input[name="fish_image_new_INDEX"]');

    if (nameInput) {
      nameInput.name = `fish_name_new_${newFishCount}`;
    }
    if (descInput) {
      descInput.name = `fish_desc_new_${newFishCount}`;
    }
    if (fileInput) {
      fileInput.name = `fish_image_new_${newFishCount}`;
    }

    const removeButton = card.querySelector('.remove-fish-btn');
    removeButton?.addEventListener('click', () => {
      card.remove();
    });

    fishFields.appendChild(card);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.body.classList.contains('tracker-page')) {
    initTrackerPage();
  }
  if (document.body.classList.contains('locations-page')) {
    initLocationsPage();
  }
});
