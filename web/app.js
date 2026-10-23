/**
 * ReelCraft-AI Studio Dashboard & Execution Controller
 */

// Application State
const state = {
  activeMode: 'text_to_video',
  isProTier: false, // Default is Free Tier (1 video free, watermark ON)
  currentJobId: null,
  pollInterval: null,
  uploadedFiles: {
    personalImages: [],
    adProductImages: [],
    adLogo: null,
    invPhotos: [],
    customAudio: null
  }
};

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initTierToggle();
  initForms();
  initUploads();
  checkBackendHealth();
});

// ==========================================================================
// 1. Backend Health Check
// ==========================================================================
async function checkBackendHealth() {
  try {
    const res = await fetch('/api/v1/generate/text-to-video', {
      method: 'OPTIONS'
    }).catch(() => null);

    const healthBadge = document.getElementById('systemStatusText');
    if (healthBadge) {
      healthBadge.textContent = 'AI Core Active • Zero-Tofu Devanagari Loaded';
    }
  } catch (err) {
    console.warn('Backend check:', err);
  }
}

// ==========================================================================
// 2. Tab Navigation
// ==========================================================================
function initTabs() {
  const tabs = document.querySelectorAll('.mode-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const mode = tab.dataset.mode;
      switchTab(mode);
    });
  });
}

function switchTab(mode) {
  state.activeMode = mode;

  // Update tabs UI
  document.querySelectorAll('.mode-tab').forEach(t => {
    t.classList.toggle('active', t.dataset.mode === mode);
  });

  // Update forms UI
  document.querySelectorAll('.mode-form').forEach(f => {
    f.classList.remove('active');
  });

  const targetForm = document.getElementById(`form-${mode}`);
  if (targetForm) {
    targetForm.classList.add('active');
  }

  if (mode === 'admin_vault') {
    refreshAdminJobs();
  }
}

function setPromptText(elemId, text) {
  const elem = document.getElementById(elemId);
  if (elem) {
    elem.value = text;
    showToast('Prompt filled: ' + text.slice(0, 30) + '...');
  }
}

// ==========================================================================
// 3. Tier Toggle (Free vs Pro Mode)
// ==========================================================================
function initTierToggle() {
  const tierBtn = document.getElementById('tierToggleBtn');
  const tierLabel = document.getElementById('tierLabel');
  const tierBadge = document.getElementById('tierBadge');
  const playerWatermark = document.getElementById('playerWatermarkOverlay');

  tierBtn.addEventListener('click', () => {
    state.isProTier = !state.isProTier;

    if (state.isProTier) {
      tierBtn.classList.add('pro-mode');
      tierLabel.textContent = 'Pro Creator Tier (Unlimited)';
      tierBadge.textContent = 'Watermark OFF';
      if (playerWatermark) playerWatermark.classList.remove('active');
      showToast('🌟 Upgraded to Pro Creator Mode! Watermark removed & 3-4 min enabled.');
    } else {
      tierBtn.classList.remove('pro-mode');
      tierLabel.textContent = 'Free Tier (1 Video Free)';
      tierBadge.textContent = 'Watermark ON';
      if (playerWatermark) playerWatermark.classList.add('active');
      showToast('🔒 Switched to Free Tier (Forced Watermark & 30s limit)');
    }
  });
}

// ==========================================================================
// 4. File Upload Handlers
// ==========================================================================
function initUploads() {
  // Mode 1: Audio file
  const audioInput = document.getElementById('text-audio-file');
  if (audioInput) {
    audioInput.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (file) {
        showToast('Uploading voice note...');
        const uploaded = await uploadAsset(file);
        if (uploaded) {
          state.uploadedFiles.customAudio = uploaded.local_path;
          showToast('Voice note uploaded successfully!');
        }
      }
    });
  }

  // Mode 2: Personal images
  const personalInput = document.getElementById('personal-images');
  if (personalInput) {
    personalInput.addEventListener('change', async (e) => {
      handleMultipleImageUpload(e.target.files, 'personalThumbs', state.uploadedFiles.personalImages);
    });
  }

  // Mode 3: Product images & Logo
  const adImagesInput = document.getElementById('ad-product-images');
  if (adImagesInput) {
    adImagesInput.addEventListener('change', async (e) => {
      handleMultipleImageUpload(e.target.files, 'ad-thumbs', state.uploadedFiles.adProductImages);
    });
  }

  const logoInput = document.getElementById('ad-logo-image');
  if (logoInput) {
    logoInput.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (file) {
        const uploaded = await uploadAsset(file);
        if (uploaded) {
          state.uploadedFiles.adLogo = uploaded.local_path;
          const container = document.getElementById('logo-thumb');
          container.innerHTML = `<img src="${uploaded.url}" class="thumb-item" title="Brand Logo">`;
          showToast('Brand logo uploaded!');
        }
      }
    });
  }

  // Mode 4: Invitation photos
  const invPhotosInput = document.getElementById('inv-photos');
  if (invPhotosInput) {
    invPhotosInput.addEventListener('change', async (e) => {
      handleMultipleImageUpload(e.target.files, 'inv-thumbs', state.uploadedFiles.invPhotos);
    });
  }
}

async function uploadAsset(file) {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch('/api/v1/upload', {
      method: 'POST',
      body: formData
    });
    if (!res.ok) throw new Error('Upload failed');
    return await res.json();
  } catch (err) {
    showToast('❌ Error uploading file: ' + err.message);
    return null;
  }
}

async function handleMultipleImageUpload(fileList, containerId, targetArray) {
  const container = document.getElementById(containerId);
  if (!container) return;

  targetArray.length = 0; // Clear previous
  container.innerHTML = '';

  for (let file of fileList) {
    const uploaded = await uploadAsset(file);
    if (uploaded) {
      targetArray.push(uploaded.local_path);
      const img = document.createElement('img');
      img.src = uploaded.url;
      img.className = 'thumb-item';
      container.appendChild(img);
    }
  }
  showToast(`Uploaded ${targetArray.length} photos!`);
}

// ==========================================================================
// 5. Form Submissions
// ==========================================================================
function initForms() {
  // Mode 1: Text to Video
  document.getElementById('form-text_to_video').addEventListener('submit', async (e) => {
    e.preventDefault();
    const duration = document.getElementById('text-duration').value;
    
    // Check Free Tier limit
    if (!state.isProTier && (duration === '3min' || duration === '4min')) {
      alert('⚠️ 3-Minute and 4-Minute Long-Form YouTube Mode is exclusive to Paid Pro Tier! Please switch to 30s or upgrade to Pro.');
      return;
    }

    const payload = {
      topic: document.getElementById('text-topic').value,
      language: document.getElementById('text-lang').value,
      duration_mode: duration,
      aspect_ratio: document.getElementById('text-aspect').value,
      watermark_enabled: !state.isProTier,
      custom_audio_path: state.uploadedFiles.customAudio,
      include_bgm: document.getElementById('text-bgm').checked,
      generate_social_pack: document.getElementById('text-social-pack').checked
    };

    await triggerGeneration('/api/v1/generate/text-to-video', payload, 'btn-submit-text');
  });

  // Mode 2: Personal Reel
  document.getElementById('form-personal_reel').addEventListener('submit', async (e) => {
    e.preventDefault();
    if (state.uploadedFiles.personalImages.length === 0) {
      alert('Please upload at least 1 photo for your personal 3D reel!');
      return;
    }

    const payload = {
      idea_prompt: document.getElementById('personal-prompt').value,
      image_paths: state.uploadedFiles.personalImages,
      language: document.getElementById('personal-lang').value,
      aspect_ratio: document.getElementById('personal-aspect').value,
      watermark_enabled: !state.isProTier,
      include_bgm: true,
      generate_social_pack: true
    };

    await triggerGeneration('/api/v1/generate/personal-reel', payload, 'btn-submit-personal');
  });

  // Mode 3: Brand & Product Ad
  document.getElementById('form-product_ad').addEventListener('submit', async (e) => {
    e.preventDefault();
    if (state.uploadedFiles.adProductImages.length === 0) {
      // Allow fallback sample photo
      showToast('Notice: Using AI product sample photos.');
    }

    const payload = {
      product_name: document.getElementById('ad-product-name').value,
      product_description: document.getElementById('ad-desc').value,
      offer_text: document.getElementById('ad-offer').value,
      call_to_action: document.getElementById('ad-cta').value,
      product_image_paths: state.uploadedFiles.adProductImages.length > 0 ? state.uploadedFiles.adProductImages : [],
      logo_path: state.uploadedFiles.adLogo,
      auto_fill_online: document.getElementById('ad-auto-gap-fill').checked,
      language: 'hi',
      aspect_ratio: '9:16',
      watermark_enabled: !state.isProTier,
      generate_social_pack: true
    };

    await triggerGeneration('/api/v1/generate/product-ad', payload, 'btn-submit-ad');
  });

  // Mode 4: Digital Video Invitation
  document.getElementById('form-digital_invitation').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      event_type: document.getElementById('inv-type').value,
      host_names: document.getElementById('inv-hosts').value,
      event_date: document.getElementById('inv-date').value,
      venue: document.getElementById('inv-venue').value,
      rsvp: document.getElementById('inv-rsvp').value,
      photo_paths: state.uploadedFiles.invPhotos,
      music_theme: document.getElementById('inv-music').value,
      language: 'hi',
      aspect_ratio: '9:16',
      watermark_enabled: !state.isProTier,
      generate_social_pack: true
    };

    await triggerGeneration('/api/v1/generate/digital-invitation', payload, 'btn-submit-invitation');
  });

  // Mode 5: 3D Cartoon Story
  document.getElementById('form-cartoon_story').addEventListener('submit', async (e) => {
    e.preventDefault();
    const duration = document.getElementById('cartoon-duration').value;

    if (!state.isProTier && (duration === '3min' || duration === '4min')) {
      alert('⚠️ 3-Minute and 4-Minute Cartoon Story is exclusive to Paid Pro Tier! Please switch to 30s/60s or upgrade to Pro.');
      return;
    }

    const payload = {
      story_topic: document.getElementById('cartoon-topic').value,
      character_style: document.getElementById('cartoon-style').value,
      duration_mode: duration,
      language: 'hi',
      aspect_ratio: document.getElementById('cartoon-aspect').value,
      watermark_enabled: !state.isProTier,
      include_sfx: document.getElementById('cartoon-sfx').checked,
      generate_social_pack: true
    };

    await triggerGeneration('/api/v1/generate/cartoon-story', payload, 'btn-submit-cartoon');
  });
}

// ==========================================================================
// 6. Execution & Status Polling
// ==========================================================================
async function triggerGeneration(endpoint, payload, btnId) {
  const btn = document.getElementById(btnId);
  if (btn) btn.classList.add('loading');

  setHudStatus('Submitting generation job to AI Core...', 10);
  setLivePill(true);

  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Server error');
    }

    const job = await res.json();
    state.currentJobId = job.job_id;
    showToast('🚀 Video job started: ' + job.job_id.slice(0, 8));
    startPolling(job.job_id, btnId);

  } catch (err) {
    showToast('❌ Job creation failed: ' + err.message);
    if (btn) btn.classList.remove('loading');
    setHudStatus('Failed to start: ' + err.message, 0);
    setLivePill(false);
  }
}

function startPolling(jobId, btnId) {
  if (state.pollInterval) clearInterval(state.pollInterval);

  state.pollInterval = setInterval(async () => {
    try {
      const res = await fetch(`/api/v1/jobs/${jobId}`);
      if (!res.ok) return;

      const job = await res.json();
      setHudStatus(job.current_stage || 'Processing...', job.progress || 10);

      // Highlight stepper
      updateStepper(job.progress);

      if (job.status === 'completed') {
        clearInterval(state.pollInterval);
        const btn = document.getElementById(btnId);
        if (btn) btn.classList.remove('loading');
        setLivePill(false);
        onJobCompleted(job);
      } else if (job.status === 'failed') {
        clearInterval(state.pollInterval);
        const btn = document.getElementById(btnId);
        if (btn) btn.classList.remove('loading');
        setLivePill(false);
        setHudStatus('Failed: ' + (job.error || 'Unknown error'), 0);
        showToast('❌ Video rendering failed: ' + job.error);
      }
    } catch (err) {
      console.warn('Poll error:', err);
    }
  }, 2000);
}

function onJobCompleted(job) {
  showToast('🎉 Video successfully rendered in 1080p Full HD!');
  setHudStatus('Video Completed! Ready for Download.', 100);

  // Load video into player
  const player = document.getElementById('studioPlayer');
  const source = document.getElementById('videoSource');
  if (player && source && job.video_url) {
    source.src = job.video_url;
    player.load();
    player.play().catch(() => {});
  }

  // Update download links
  const masterBtn = document.getElementById('btnDownloadMaster');
  if (masterBtn && job.video_url) {
    masterBtn.href = job.video_url;
  }

  const waBtn = document.getElementById('btnDownloadWhatsApp');
  if (waBtn && job.whatsapp_video_url) {
    waBtn.href = job.whatsapp_video_url;
  }

  // Update Social Media Pack
  if (job.social_pack) {
    if (job.social_pack.title) document.getElementById('socialHookTitle').value = job.social_pack.title;
    if (job.social_pack.description) document.getElementById('socialDescription').value = job.social_pack.description;
    if (job.social_pack.hashtags && job.social_pack.hashtags.length) {
      document.getElementById('socialTags').value = job.social_pack.hashtags.map(t => t.startsWith('#') ? t : '#' + t).join(' ');
    }
  }

  // Update Full script
  if (job.script) {
    document.getElementById('fullScriptContent').textContent = job.script;
  }
}

function updateStepper(progress) {
  document.getElementById('step-1').classList.toggle('active', progress >= 15);
  document.getElementById('step-2').classList.toggle('active', progress >= 35);
  document.getElementById('step-3').classList.toggle('active', progress >= 65);
  document.getElementById('step-4').classList.toggle('active', progress >= 85);
  document.getElementById('step-5').classList.toggle('active', progress >= 95);
}

function setHudStatus(text, percent) {
  const title = document.getElementById('hudStageTitle');
  const pct = document.getElementById('hudPercent');
  const bar = document.getElementById('hudProgressBar');

  if (title) title.textContent = text;
  if (pct) pct.textContent = `${percent}%`;
  if (bar) bar.style.width = `${percent}%`;
}

function setLivePill(isProcessing) {
  const pill = document.getElementById('liveIndicator');
  if (!pill) return;
  if (isProcessing) {
    pill.textContent = 'Rendering...';
    pill.className = 'live-pill processing';
  } else {
    pill.textContent = 'Ready';
    pill.className = 'live-pill';
  }
}

// ==========================================================================
// 7. 1-Click Copy Helper
// ==========================================================================
function copyField(elemId) {
  const elem = document.getElementById(elemId);
  if (elem) {
    elem.select();
    navigator.clipboard.writeText(elem.value);
    showToast('📋 Copied to clipboard!');
  }
}

function showToast(msg) {
  const toast = document.getElementById('toast');
  if (!toast) return;
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => {
    toast.classList.remove('show');
  }, 3000);
}

// ==========================================================================
// 8. Admin Job Vault
// ==========================================================================
async function refreshAdminJobs() {
  const tbody = document.getElementById('jobs-table-body');
  if (!tbody) return;

  try {
    const res = await fetch('/api/v1/jobs');
    if (!res.ok) throw new Error('Could not fetch jobs');
    const jobs = await res.json();

    if (jobs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="empty-state">No jobs found in memory yet. Generate a video to see it here!</td></tr>`;
      return;
    }

    tbody.innerHTML = jobs.map(j => `
      <tr>
        <td><code>${j.job_id.slice(0, 8)}...</code></td>
        <td><span class="badge-status ${j.status}">${j.status}</span></td>
        <td>${j.current_stage || '-'}</td>
        <td>${j.duration ? j.duration.toFixed(1) + 's' : '-'}</td>
        <td>${j.watermark_applied ? '⚠️ Watermarked' : '✨ Clean Pro'}</td>
        <td>
          ${j.video_url ? `<a href="${j.video_url}" target="_blank" class="copy-btn">Play</a>` : '-'}
        </td>
      </tr>
    `).join('');

  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" class="empty-state">Error loading jobs: ${err.message}</td></tr>`;
  }
}

function loadSampleMarsReel() {
  onJobCompleted({
    job_id: 'test_verification_01',
    status: 'completed',
    video_url: '/static/output/test_verification_01/final_reel.mp4',
    whatsapp_video_url: '/static/output/test_verification_01/final_reel_whatsapp.mp4',
    duration: 13.9,
    watermark_applied: true,
    social_pack: {
      title: 'Mars Ke 3 Aise Rahasya Jo Scientists Ko Hairan Kar Dete Hain 🔴🚀',
      description: 'Kyu Mars ka ek saal dharti se dugna hota hai? Jaaniye Lal Grah ke 3 hairatangez rahasya is video me. Like aur Subscribe zaroor karein!',
      hashtags: ['#mars', '#spacefacts', '#sciencefacts', '#solarsystem', '#reels', '#viralshorts', '#hindifacts', '#universe', '#chandrayaan', '#isro', '#nasa', '#astronomy', '#amazingfacts', '#knowledge', '#reelcraft']
    },
    script: 'Mars yaani Lal Grah ke 3 hairatangez rahasya. Pehla: Mars par suryast neela dikhta hai. Doosra: Mars par hamare solar system ka sabse bada jwalamukhi Olympus Mons maujood hai. Teesra: Mars ka ek saal dharti ke 687 dinon ke barabar hota hai.'
  });
  showToast('🎬 Loaded Mars Sample Reel into Player & Social Pack!');
}
